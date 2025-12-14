import streamlit as st
import requests
import time
import re
import uuid
import io
from gtts import gTTS
from streamlit_js_eval import get_geolocation
import google.generativeai as genai
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH TRANG & CSS (MÀU XANH LÁ + CHỮ ĐEN) ---
st.set_page_config(
    page_title="VnBus Green AI Pro",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Nền trang xanh nhạt */
    .stApp { background-color: #ecfdf5; }
    
    /* Chỉnh màu chữ đen toàn bộ để tương phản tốt */
    h1, h2, h3, h4, h5, h6, p, div, span, label, li {
        color: #000000 !important;
    }
    
    /* Input field */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #000000;
        border: 2px solid #10b981;
        border-radius: 10px;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #10b981 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #059669 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #10b981;
    }
    
    /* Audio player */
    audio { width: 100%; height: 30px; margin-top: 5px; }
    
    /* Status Box */
    .status-box {
        padding: 15px;
        background-color: #ffffff;
        border-radius: 10px;
        border-left: 5px solid #10b981;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API & STATE ---

# Lấy Key từ Secrets hoặc Sidebar (để linh hoạt)
with st.sidebar:
    st.title("🍃 VnBus Green AI")
    st.markdown("---")
    
    GOOGLE_MAPS_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY")
    if not GOOGLE_MAPS_API_KEY:
        GOOGLE_MAPS_API_KEY = st.text_input("🔑 Google Maps API Key", type="password")
        
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = st.text_input("✨ Gemini API Key", type="password")
    
    st.markdown("---")
    st.info("💡 Ứng dụng tự động cập nhật lộ trình và giọng nói mỗi 8 giây.")

# Cấu hình Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai = genai.GenerativeModel("gemini-1.5-flash") # Sử dụng model flash như code gốc

# State Init
if "running" not in st.session_state:
    st.session_state.running = False
if "last_voice" not in st.session_state:
    st.session_state.last_voice = ""
# State cho Map (để hiển thị ở cột phải)
if "map_origin" not in st.session_state: st.session_state.map_origin = ""
if "map_dest" not in st.session_state: st.session_state.map_dest = ""

# --- 3. CÁC HÀM UTILS (GIỮ NGUYÊN TỪ CODE GỐC) ---
def speak(text):
    # Lưu file tạm thời để phát
    tts = gTTS(text=text, lang='vi')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    st.audio(audio_fp, format='audio/mp3', autoplay=True)

def clean_html(t):
    return re.sub("<[^<]+?>", "", t)

def normalize_direction(text):
    t = text.lower()
    if "trái" in t: return "Rẽ trái"
    if "phải" in t: return "Rẽ phải"
    return "Đi thẳng"

def ai_parse_input(user_text):
    prompt = f"""
    Người dùng khiếm thị nói: "{user_text}"
    Hãy trích xuất:
    - điểm đi
    - điểm đến
    - ưu tiên (ít đổi xe / ít đi bộ / nhanh nhất)
    Trả về dạng:
    origin=...
    destination=...
    priority=...
    """
    return ai.generate_content(prompt).text

def render_map_embed(origin, destination, api_key):
    if api_key and origin and destination:
        src = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin}&destination={destination}&mode=transit"
        return f"""<div style="width:100%; height:500px; border-radius:15px; overflow:hidden; border: 2px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"><iframe width="100%" height="100%" frameborder="0" style="border:0" src="{src}" allowfullscreen></iframe></div>"""
    return """<div style="padding:40px; text-align:center; border:2px dashed #10b981; border-radius:15px; color:#000;">🗺️ Bản đồ sẽ hiện tại đây khi bắt đầu lộ trình.</div>"""


# --- 4. GIAO DIỆN CHÍNH (LAYOUT 2 CỘT) ---
col1, col2 = st.columns([1, 1.3])

# --- CỘT PHẢI: BẢN ĐỒ (RENDER TRƯỚC ĐỂ LUÔN HIỂN THỊ) ---
with col2:
    st.subheader("🗺️ Bản đồ & Lộ trình")
    # Hiển thị Map dựa trên state đã lưu
    map_html = render_map_embed(st.session_state.map_origin, st.session_state.map_dest, GOOGLE_MAPS_API_KEY)
    components.html(map_html, height=520)

# --- CỘT TRÁI: ĐIỀU KHIỂN & LOGIC CHÍNH ---
with col1:
    st.subheader("🎙️ Trợ lý Giọng nói")
    
    user_input = st.text_input(
        "Nhập lộ trình (hoặc nói):", 
        placeholder="Ví dụ: Tôi đi từ Đại học Bách Khoa đến Chợ Bến Thành..."
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Bắt đầu"):
            st.session_state.running = True
            st.session_state.last_voice = ""
            st.rerun()
    with c2:
        if st.button("⏹️ Dừng lại"):
            st.session_state.running = False
            st.session_state.last_voice = ""
            st.rerun()

    # ================= MAIN LOGIC (CỐT LÕI BUSMATE) =================
    if st.session_state.running:
        st.markdown("<div class='status-box'>🟢 <b>Đang chạy:</b> Hệ thống đang theo dõi lộ trình...</div>", unsafe_allow_html=True)
        
        if not user_input:
            speak("Vui lòng nói hoặc nhập điểm đi và điểm đến")
            st.warning("⚠️ Vui lòng nhập điểm đi và điểm đến.")
            st.stop() # Dừng logic tại đây, nhưng Map bên phải vẫn hiển thị

        if not GOOGLE_MAPS_API_KEY or not GEMINI_API_KEY:
            st.error("⚠️ Vui lòng nhập đủ API Key ở Sidebar.")
            st.stop()

        # ===== AI hiểu yêu cầu =====
        try:
            ai_result = ai_parse_input(user_input)
            
            # Parse đơn giản
            lines = ai_result.splitlines()
            origin = destination = ""
            for l in lines:
                if "origin" in l: origin = l.split("=")[1].strip()
                if "destination" in l: destination = l.split("=")[1].strip()
            
            # [TÍNH NĂNG MỚI] Cập nhật Map State để cột phải hiển thị
            if origin and destination:
                st.session_state.map_origin = origin
                st.session_state.map_dest = destination

            st.write(f"📍 **Điểm đi:** {origin}")
            st.write(f"🏁 **Điểm đến:** {destination}")

            # ===== GPS (streamlit_js_eval) =====
            loc = get_geolocation()
            if loc is None:
                speak("Đang xác định vị trí của bạn")
                st.info("📡 Đang lấy tín hiệu GPS...")
                time.sleep(3) # Đợi 1 chút để GPS load
                st.rerun()
                st.stop()

            lat = loc["coords"]["latitude"]
            lng = loc["coords"]["longitude"]
            st.success(f"📡 GPS: {lat:.4f}, {lng:.4f}")

            # ===== WALK TO STOP (Google Directions API) =====
            walk_params = {
                "origin": f"{lat},{lng}",
                "destination": origin, # Logic gốc: đi bộ từ GPS đến điểm Origin (có thể là trạm xe)
                "mode": "walking",
                "language": "vi",
                "key": GOOGLE_MAPS_API_KEY
            }

            walk = requests.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params=walk_params
            ).json()

            direction = "Không tìm thấy đường đi bộ"
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

            bus_info = "Chưa có thông tin xe buýt"
            if transit.get("routes"):
                for s in transit["routes"][0]["legs"][0]["steps"]:
                    if s["travel_mode"] == "TRANSIT":
                        td = s["transit_details"]
                        line = td["line"].get("short_name", "")
                        time_txt = td["departure_time"]["text"]
                        bus_info = f"Xe số {line} sẽ đến lúc {time_txt}"
                        break
            
            # ===== FINAL VOICE =====
            voice = f"{direction}. {bus_info}"
            
            # Hiển thị text ra màn hình
            st.info(f"🔊 **AI:** {voice}")

            if voice != st.session_state.last_voice:
                speak(voice)
                st.session_state.last_voice = voice

            # Tự động chạy lại sau 8s để cập nhật
            time.sleep(8)
            st.rerun()
            
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")
            time.sleep(5)
            st.rerun()

    else:
        st.info("👋 Ứng dụng đang chờ. Nhấn **Bắt đầu** để sử dụng.")
