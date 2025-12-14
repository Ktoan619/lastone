import streamlit as st
import requests
import time
import re
import uuid
import streamlit.components.v1 as components

# --- Xử lý thư viện ---
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

# ================= CONFIG TRANG =================
st.set_page_config(
    page_title="BusMate Pro", 
    page_icon="🚌",
    layout="wide"
)

# ================= SIDEBAR CONFIG =================
with st.sidebar:
    st.header("Cấu hình hệ thống")
    GOOGLE_MAPS_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
    if not GOOGLE_MAPS_API_KEY:
        GOOGLE_MAPS_API_KEY = st.text_input("🔑 Google Maps API Key", type="password")
        
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = st.text_input("✨ Gemini API Key", type="password")
    
    st.markdown("---")
    st.info("Chế độ: Dẫn đường Real-time & Giọng nói AI.")

# ================= AI CONFIG =================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")

# ================= STATE =================
if "running" not in st.session_state:
    st.session_state.running = False

if "last_voice" not in st.session_state:
    st.session_state.last_voice = ""

if "map_origin" not in st.session_state: st.session_state.map_origin = ""
if "map_dest" not in st.session_state: st.session_state.map_dest = ""

# ================= UI LAYOUT & PLACEHOLDERS =================
st.title("BusMate - Dẫn đường thời gian thực")

# [QUAN TRỌNG] Tạo một khung cố định cho âm thanh để tránh chồng chéo
# Khung này sẽ luôn được làm mới mỗi khi trang rerun
sound_placeholder = st.empty()

col_control, col_map = st.columns([1, 1.2])

# ================= UTILS =================
def speak(text):
    """Phát giọng nói AI vào khung cố định (sound_placeholder)"""
    if HAS_GTTS:
        try:
            import io
            fp = io.BytesIO()
            gTTS(text=text, lang="vi").write_to_fp(fp)
            fp.seek(0)
            
            # Sử dụng sound_placeholder để ghi đè âm thanh cũ
            # Thêm key=uuid để đảm bảo trình duyệt nhận diện đây là file audio mới
            with sound_placeholder.container():
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

def render_map(origin, destination, api_key):
    if not api_key:
        return """<div style="padding:20px; border:1px dashed #ccc; text-align:center">⚠️ Cần Google Maps API Key để hiện bản đồ</div>"""
    
    if origin and destination:
        src = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin}&destination={destination}&mode=transit"
    else:
        src = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center=10.7769,106.7009&zoom=14"
        
    return f"""
    <div style="width:100%; height:600px; border-radius:15px; overflow:hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: 2px solid #4CAF50;">
        <iframe width="100%" height="100%" frameborder="0" style="border:0" src="{src}" allowfullscreen></iframe>
    </div>
    """

def ai_parse_input(user_text):
    prompt = f"""
    Người dùng khiếm thị nói: "{user_text}"
    Trích xuất: điểm đi (origin), điểm đến (destination).
    Nếu người dùng chỉ nói điểm đến (ví dụ "Đến chợ Bến Thành"), hãy để origin là "Current Location".
    Format trả về: origin=... \n destination=...
    """
    try:
        return ai.generate_content(prompt).text
    except:
        return ""

# ================= UI IMPLEMENTATION =================

with col_map:
    st.markdown("### 🗺️ Bản đồ hỗ trợ")
    map_html = render_map(st.session_state.map_origin, st.session_state.map_dest, GOOGLE_MAPS_API_KEY)
    components.html(map_html, height=620)

with col_control:
    st.markdown("### 🎙️ Nhập lệnh")
    user_input = st.text_input("Nhập lộ trình:", placeholder="Ví dụ: Bến Thành đi Suối Tiên...")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Bắt đầu Dẫn đường", use_container_width=True):
            st.session_state.running = True
            st.session_state.last_voice = "" # Reset giọng nói khi bắt đầu mới
            st.rerun()
    with c2:
        if st.button("⏹️ Dừng lại", use_container_width=True):
            st.session_state.running = False
            st.session_state.last_voice = ""
            # Xóa âm thanh đang phát bằng cách làm rỗng placeholder
            sound_placeholder.empty()
            st.rerun()

    # ================= MAIN LOGIC =================
    if st.session_state.running:
        st.info("🟢 Đang theo dõi lộ trình & Giọng nói...")
        
        if not user_input:
            speak("Vui lòng nhập điểm đi và đến")
            st.warning("Vui lòng nhập liệu.")
            st.stop()
            
        if not GEMINI_API_KEY or not GOOGLE_MAPS_API_KEY:
            st.error("Thiếu API Key.")
            st.stop()

        # 1. AI Parse
        ai_result = ai_parse_input(user_input)
        lines = ai_result.splitlines()
        origin_text = destination_text = ""
        for l in lines:
            if "origin" in l: origin_text = l.split("=")[1].strip()
            if "destination" in l: destination_text = l.split("=")[1].strip()

        # Update Map State
        if origin_text and destination_text:
            if origin_text != st.session_state.map_origin or destination_text != st.session_state.map_dest:
                st.session_state.map_origin = origin_text
                st.session_state.map_dest = destination_text
                st.rerun()

        # 2. GPS Check
        lat, lng = 10.7769, 106.7009
        has_real_gps = False
        
        if HAS_GEOLOCATION:
            loc = get_geolocation()
            if loc:
                lat = loc["coords"]["latitude"]
                lng = loc["coords"]["longitude"]
                has_real_gps = True
                st.success(f"📍 GPS: {lat:.4f}, {lng:.4f}")
            else:
                # Tăng thời gian chờ lên 5s để tránh loop quá nhanh gây chồng tiếng
                speak("Đang tìm tín hiệu GPS")
                st.warning("📡 Đang lấy vị trí GPS...")
                time.sleep(5) 
                st.rerun()
        else:
            st.warning("⚠️ Không có GPS. Dùng tọa độ giả lập.")

        # 3. Logic Real-time Navigation
        try:
            nav_origin = f"{lat},{lng}" if has_real_gps else origin_text
            
            transit_params = {
                "origin": nav_origin, 
                "destination": destination_text,
                "mode": "transit",
                "transit_mode": "bus",
                "departure_time": "now",
                "language": "vi",
                "key": GOOGLE_MAPS_API_KEY
            }
            
            resp = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=transit_params).json()
            
            voice_instruction = ""
            
            if resp.get("routes"):
                legs = resp["routes"][0]["legs"][0]
                
                # --- DISPLAY ---
                duration = legs["duration"]["text"]
                st.markdown(f"**⏱️ Thời gian còn lại:** {duration}")
                
                # --- VOICE LOGIC ---
                first_step = legs["steps"][0]
                first_dist = first_step["distance"]["text"]
                first_instr = clean_html(first_step["html_instructions"])
                
                if first_step["travel_mode"] == "WALKING":
                    voice_instruction = f"Đi bộ {first_dist}. {first_instr}."
                elif first_step["travel_mode"] == "TRANSIT":
                    bus_line = first_step["transit_details"]["line"]["short_name"]
                    arr_time = first_step["transit_details"]["departure_time"]["text"]
                    voice_instruction = f"Đón xe số {bus_line}. Xe đến lúc {arr_time}."
                
                # Hiển thị chi tiết
                st.markdown("#### 📝 Lộ trình chi tiết:")
                for step in legs["steps"]:
                    mode = step["travel_mode"]
                    dist = step["distance"]["text"]
                    if mode == "WALKING":
                        instr = clean_html(step["html_instructions"])
                        st.info(f"🚶 **{dist}:** {instr}")
                    elif mode == "TRANSIT":
                        td = step["transit_details"]
                        line = td["line"]["short_name"]
                        st.success(f"🚌 **Bus {line}:** {td['departure_stop']['name']} ➔ {td['arrival_stop']['name']}")

            elif resp.get("status") == "ZERO_RESULTS":
                voice_instruction = "Không tìm thấy lộ trình phù hợp."
                st.error(voice_instruction)

            # --- KÍCH HOẠT GIỌNG NÓI AN TOÀN ---
            st.toast(f"🗣️ AI: {voice_instruction}")

            if voice_instruction and voice_instruction != st.session_state.last_voice:
                speak(voice_instruction)
                st.session_state.last_voice = voice_instruction

            # Refresh mỗi 10s
            time.sleep(10)
            st.rerun()
            
        except Exception as e:
            st.error(f"Lỗi API: {e}")
            st.stop()

    else:
        st.info("Sẵn sàng. Nhấn Bắt đầu để dẫn đường.")
