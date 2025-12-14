import streamlit as st
import requests
import time
import re
import uuid
import streamlit.components.v1 as components

# --- Xử lý thư viện (Thêm try-except để tránh crash nếu chưa cài) ---
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    from streamlit_js_eval import get_geolocation
    HAS_GEOLOCATION = True
except ImportError:
    HAS_GEOLOCATION = False

import google.generativeai as genai

# ================= CONFIG TRANG (LAYOUT WIDE ĐỂ CÓ CHỖ CHO MAP) =================
st.set_page_config(
    page_title="BusMate Pro", 
    page_icon="🚌",
    layout="wide" # Quan trọng: Mở rộng giao diện để chia cột
)

# ================= SIDEBAR CONFIG (SỬA ĐỔI ĐỂ DỄ NHẬP KEY) =================
with st.sidebar:
    st.header("Cấu hình hệ thống")
    # Ưu tiên lấy từ secrets, nếu không có thì hiện ô nhập
    GOOGLE_MAPS_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
    if not GOOGLE_MAPS_API_KEY:
        GOOGLE_MAPS_API_KEY = st.text_input("🔑 Google Maps API Key", type="password")
        
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = st.text_input("✨ Gemini API Key", type="password")
    
    st.markdown("---")
    st.info("Logic chỉ đường giữ nguyên bản (Sử dụng Google Directions API).")

# ================= AI CONFIG =================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Cập nhật model mới nhất để tránh lỗi
    ai = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")

# ================= STATE =================
if "running" not in st.session_state:
    st.session_state.running = False

if "last_voice" not in st.session_state:
    st.session_state.last_voice = ""

# State mới để lưu vị trí hiển thị trên bản đồ (Cần thiết cho UI)
if "map_origin" not in st.session_state: st.session_state.map_origin = ""
if "map_dest" not in st.session_state: st.session_state.map_dest = ""

# ================= UTILS =================
def speak(text):
    if HAS_GTTS:
        try:
            # Dùng file tạm dạng BytesIO thay vì lưu file rác mp3
            import io
            fp = io.BytesIO()
            gTTS(text=text, lang="vi").write_to_fp(fp)
            fp.seek(0)
            st.audio(fp, format='audio/mp3', autoplay=True)
        except Exception as e:
            st.warning(f"Lỗi âm thanh: {e}")

def clean_html(t):
    return re.sub("<[^<]+?>", "", t)

def normalize_direction(text):
    t = text.lower()
    if "trái" in t: return "Rẽ trái"
    if "phải" in t: return "Rẽ phải"
    return "Đi thẳng"

# Hàm hiển thị bản đồ (Phần SỬA ĐỔI THÊM)
def render_map(origin, destination, api_key):
    if not api_key:
        return """<div style="padding:20px; border:1px dashed #ccc; text-align:center">⚠️ Cần Google Maps API Key để hiện bản đồ</div>"""
    
    if origin and destination:
        # Mode: Directions
        src = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin}&destination={destination}&mode=transit"
    else:
        # Mode: View (Mặc định Sài Gòn)
        src = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center=10.7769,106.7009&zoom=14"
        
    return f"""
    <div style="width:100%; height:600px; border-radius:15px; overflow:hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: 2px solid #4CAF50;">
        <iframe width="100%" height="100%" frameborder="0" style="border:0" src="{src}" allowfullscreen></iframe>
    </div>
    """

# ================= AI: PARSE USER INTENT =================
def ai_parse_input(user_text):
    prompt = f"""
    Người dùng khiếm thị nói: "{user_text}"
    Hãy trích xuất:
    - điểm đi (origin)
    - điểm đến (destination)
    - ưu tiên (priority)
    Trả về dạng chính xác:
    origin=...
    destination=...
    priority=...
    Nếu không rõ, để trống.
    """
    try:
        return ai.generate_content(prompt).text
    except:
        return ""

# ================= UI LAYOUT (CHIA CỘT) =================
st.title("BusMate - Bạn đồng hành xe bus")

# Chia giao diện thành 2 cột: Trái (Điều khiển) - Phải (Bản đồ)
col_control, col_map = st.columns([1, 1.2])

# --- CỘT PHẢI: BẢN ĐỒ ---
with col_map:
    st.markdown("### 🗺️ Bản đồ hỗ trợ")
    # Render map dựa trên state đã lưu
    map_html = render_map(st.session_state.map_origin, st.session_state.map_dest, GOOGLE_MAPS_API_KEY)
    components.html(map_html, height=620)

# --- CỘT TRÁI: ĐIỀU KHIỂN & LOGIC ---
with col_control:
    st.markdown("### 🎙️ Nhập lệnh")
    user_input = st.text_input(
        "Nhập lộ trình:",
        placeholder="Ví dụ: Tôi đi từ Đại học Bách Khoa đến Chợ Bến Thành..."
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Bắt đầu", use_container_width=True):
            st.session_state.running = True
            st.session_state.last_voice = ""
            st.rerun()
    with c2:
        if st.button("⏹️ Dừng lại", use_container_width=True):
            st.session_state.running = False
            st.session_state.last_voice = ""
            st.rerun()

    # ================= MAIN LOGIC (GIỮ NGUYÊN CỐT LÕI) =================
    if st.session_state.running:
        st.info("🟢 Hệ thống đang chạy...")
        
        if not user_input:
            speak("Vui lòng nói hoặc nhập điểm đi và điểm đến")
            st.warning("Vui lòng nhập liệu.")
            st.stop()
            
        if not GEMINI_API_KEY or not GOOGLE_MAPS_API_KEY:
            st.error("Thiếu API Key (Nhập bên trái)")
            st.stop()

        # ===== AI hiểu yêu cầu =====
        ai_result = ai_parse_input(user_input)

        # Parse đơn giản
        lines = ai_result.splitlines()
        origin = destination = ""
        for l in lines:
            if "origin" in l:
                origin = l.split("=")[1].strip()
            if "destination" in l:
                destination = l.split("=")[1].strip()

        # [SỬA ĐỔI] Cập nhật Map State nếu có dữ liệu mới
        if origin and destination:
            if origin != st.session_state.map_origin or destination != st.session_state.map_dest:
                st.session_state.map_origin = origin
                st.session_state.map_dest = destination
                st.rerun() # Refresh để cập nhật bản đồ ngay lập tức

        # ===== GPS (SỬA ĐỔI: LINH HOẠT HƠN) =====
        lat, lng = 10.7769, 106.7009 # Tọa độ mặc định (HCM) để tránh lỗi biến
        has_real_gps = False # Cờ đánh dấu có GPS thực hay không

        if HAS_GEOLOCATION:
            loc = get_geolocation()
            if loc:
                lat = loc["coords"]["latitude"]
                lng = loc["coords"]["longitude"]
                has_real_gps = True
            elif not (origin and destination):
                # Chỉ bắt buộc chờ GPS nếu KHÔNG CÓ đủ điểm đi/đến (Người dùng cần định vị)
                speak("Đang xác định vị trí của bạn")
                st.warning("📡 Đang chờ tín hiệu GPS để xác định điểm xuất phát...")
                st.stop()
            else:
                # Có đủ điểm đi & đến -> Chấp nhận chạy tiếp (Tra cứu A -> B)
                st.info("ℹ️ Đang tra cứu lộ trình nhập tay (Bỏ qua GPS).")
        else:
            # Fallback nếu không có thư viện GPS
            st.warning("⚠️ Module GPS không khả dụng. Dùng tọa độ giả lập.")

        # ===== WALK TO STOP (Google Directions API) =====
        try:
            direction = "Di chuyển đến điểm xuất phát" # Mặc định

            # Chỉ gọi API chỉ đường đi bộ nếu có GPS thực sự
            if has_real_gps:
                walk_params = {
                    "origin": f"{lat},{lng}",
                    "destination": origin,
                    "mode": "walking",
                    "language": "vi",
                    "key": GOOGLE_MAPS_API_KEY
                }

                walk = requests.get(
                    "https://maps.googleapis.com/maps/api/directions/json",
                    params=walk_params
                ).json()

                if walk.get("routes"):
                    step = clean_html(walk["routes"][0]["legs"][0]["steps"][0]["html_instructions"])
                    direction = normalize_direction(step)
            
            # ===== BUS ETA (Google Directions API) =====
            transit_params = {
                "origin": origin,
                "destination": destination,
                "mode": "transit",
                "transit_mode": "bus",
                "departure_time": "now",
                "language": "vi",
                "key": GOOGLE_MAPS_API_KEY
            }

            transit = requests.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params=transit_params
            ).json()

            # --- SỬA ĐỔI: PHÂN TÍCH CHI TIẾT LỘ TRÌNH (Đón ở đâu, đi bộ đâu) ---
            route_steps = [] # Danh sách chứa các bước di chuyển
            voice_summary = "" # Nội dung tóm tắt để AI nói

            if transit.get("routes"):
                legs = transit["routes"][0]["legs"][0]
                
                # 1. Hiển thị tổng quan
                duration = legs["duration"]["text"]
                arrival = legs.get("arrival_time", {}).get("text", "N/A")
                st.markdown(f"⏱️ **Tổng thời gian:** {duration} (Dự kiến đến: {arrival})")
                
                # 2. Duyệt qua từng chặng (Đi bộ -> Xe Bus -> Đi bộ...)
                for step in legs["steps"]:
                    mode = step["travel_mode"]
                    
                    if mode == "WALKING":
                        dist = step["distance"]["text"]
                        instr = clean_html(step["html_instructions"])
                        # Thêm hướng dẫn đi bộ vào list
                        route_steps.append(f"🚶 **Đi bộ ({dist}):** {instr}")
                        
                    elif mode == "TRANSIT":
                        td = step["transit_details"]
                        line = td["line"]["short_name"]
                        dep_stop = td["departure_stop"]["name"]
                        arr_stop = td["arrival_stop"]["name"]
                        dep_time = td["departure_time"]["text"]
                        num_stops = td["num_stops"]
                        
                        # Thêm thông tin xe bus vào list
                        detail = f"🚌 **Bus {line}:** Đón tại trạm **{dep_stop}** lúc **{dep_time}**.\n   (Đi {num_stops} trạm, xuống tại **{arr_stop}**)"
                        route_steps.append(detail)
                        
                        # Lưu thông tin xe đầu tiên để AI nhắc bằng giọng nói
                        if not voice_summary:
                            voice_summary = f"Đón xe số {line} tại trạm {dep_stop} lúc {dep_time}."

            elif transit.get("status") == "ZERO_RESULTS":
                route_steps.append("⚠️ Không tìm thấy tuyến xe buýt nào phù hợp.")
                voice_summary = "Không tìm thấy tuyến xe."
            
            # --- HIỂN THỊ GIAO DIỆN ---
            st.markdown("#### 📝 Chi tiết di chuyển:")
            for step_msg in route_steps:
                if "Bus" in step_msg:
                    st.success(step_msg) # Màu xanh cho xe bus
                else:
                    st.info(step_msg)    # Màu xanh dương cho đi bộ

            # ===== FINAL VOICE =====
            # Kết hợp hướng dẫn từ GPS (nếu có) và hướng dẫn đón xe
            full_voice = ""
            if has_real_gps and direction != "Di chuyển đến điểm xuất phát":
                full_voice = f"{direction}. Sau đó {voice_summary}"
            else:
                full_voice = voice_summary if voice_summary else "Đang tìm dữ liệu..."
            
            st.write(f"🗣️ **AI:** {full_voice}")

            if full_voice != st.session_state.last_voice:
                speak(full_voice)
                st.session_state.last_voice = full_voice

            time.sleep(15) # Tăng thời gian đọc lên 15s để người dùng kịp xem
            st.rerun()
            
        except Exception as e:
            st.error(f"Lỗi API: {e}")
            st.stop()

    else:
        st.info("Ứng dụng đang chờ. Nhấn Bắt đầu để sử dụng.")
