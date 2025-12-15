import streamlit as st
import requests
import time
import re
import uuid
import json
import streamlit.components.v1 as components
import os

# --- IMPORT DỮ LIỆU TỪ FILE MỚI ---
try:
    from data_and_prompts import get_full_system_instruction, BUS_DATA
except ImportError:
    def get_full_system_instruction(): return "Bạn là trợ lý xe buýt thông minh."
    BUS_DATA = []

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

try:
    from streamlit import fragment
except ImportError:
    def fragment(func):
        return func

import google.generativeai as genai

# ================= CONFIG TRANG =================
st.set_page_config(
    page_title="BusMate - Kết nối cộng đồng xe buýt", 
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PHONG CÁCH FACEBOOK ---
st.markdown("""
<style>
    /* 1. Nền chính (Background) - Màu xám nhạt đặc trưng FB */
    .stApp { 
        background-color: #F0F2F5; 
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    }
    
    /* 2. Sidebar (Thanh bên) - Màu trắng sạch */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF; 
        box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        border-right: none;
    }
    
    /* 3. Tiêu đề & Chữ */
    h1, h2, h3 {
        color: #050505 !important;
        font-weight: 700 !important;
    }
    p, label, li, div {
        color: #050505;
    }
    
    /* 4. Thẻ nội dung (Card UI) */
    div.stMarkdown, div.stTextInput, div.stButton {
        /* Không style trực tiếp div bao ngoài để tránh vỡ layout, 
           nhưng tư duy là các khối nội dung sẽ nằm trên nền trắng */
    }
    
    /* 5. Ô nhập liệu (Input) - Bo tròn, viền nhạt */
    .stTextInput > div > div > input {
        background-color: #F0F2F5; 
        color: #050505;
        border: 1px solid #ddd;
        border-radius: 20px; /* Bo tròn kiểu FB search bar */
        padding: 10px 15px;
    }
    .stTextInput > div > div > input:focus {
        background-color: #FFFFFF;
        border-color: #1877F2;
        box-shadow: 0 0 0 2px rgba(24, 119, 242, 0.2);
    }
    
    /* 6. Nút bấm chính (Primary Button) - Xanh FB */
    .stButton > button {
        background-color: #1877F2 !important; 
        color: #FFFFFF !important;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #166FE5 !important; /* Xanh đậm hơn khi hover */
    }
    
    /* Nút phụ (Secondary) - Xám nhạt */
    /* Streamlit khó phân biệt nút phụ qua CSS thuần, nên dùng chung style */

    /* 7. Tabs (Thanh điều hướng) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #FFFFFF;
        padding: 10px 10px 0 10px;
        border-radius: 8px 8px 0 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        gap: 20px;
    }
    
    .stTabs button[data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        padding-bottom: 15px;
    }
    
    /* Tên Tab */
    .stTabs button[data-baseweb="tab"] div p {
        color: #65676B !important; /* Xám trung tính */
        font-weight: 600;
        font-size: 15px;
    }
    
    /* Tab đang chọn (Active) */
    .stTabs button[data-baseweb="tab"][aria-selected="true"] div p {
        color: #1877F2 !important; /* Xanh FB */
    }
    
    /* Gạch chân Tab Active */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #1877F2 !important;
        height: 3px;
        border-radius: 3px 3px 0 0;
    }
    
    /* 8. Chat Message (Bong bóng chat) */
    [data-testid="stChatMessage"] {
        background-color: transparent;
        padding: 10px;
    }
    /* User Message - Xanh dương */
    [data-testid="stChatMessage"][data-author="user"] {
        background-color: #E7F3FF; /* Xanh rất nhạt */
        border-radius: 15px;
        color: #050505;
    }
    /* Bot Message - Xám */
    [data-testid="stChatMessage"][data-author="assistant"] {
        background-color: #E4E6EB; /* Xám nhạt FB */
        border-radius: 15px;
        color: #050505;
    }
    
    /* 9. Các khung thông báo (Alerts) */
    .stAlert {
        background-color: #FFFFFF;
        color: #050505;
        border: 1px solid #ddd;
        border-left: 5px solid #1877F2; /* Điểm nhấn xanh */
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Tiêu đề chính ứng dụng */
    h1 { 
        color: #1877F2 !important;
        font-size: 2.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR CONFIG =================
with st.sidebar:
    st.markdown("### ⚙️ Cài đặt")
    if "GOOGLE_MAPS_API_KEY" in st.secrets:
        GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        st.success("Google Maps: Đã kết nối")
    else:
        st.error("Thiếu Google Maps Key")
        GOOGLE_MAPS_API_KEY = None

    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        st.success("Gemini AI: Đã kết nối")
    else:
        st.error("Thiếu Gemini Key")
        GEMINI_API_KEY = None
    
    st.markdown("---")
    enable_gps = st.checkbox("Bật định vị GPS", value=True)
    st.caption("Cho phép ứng dụng sử dụng vị trí của bạn để dẫn đường chính xác hơn.")

# ================= AI CONFIG =================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")
    
    bot_instruction = get_full_system_instruction()
    ai_chatbot = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025", system_instruction=bot_instruction)

# ================= STATE =================
if "running" not in st.session_state: st.session_state.running = False
if "last_voice" not in st.session_state: st.session_state.last_voice = ""
if "map_origin" not in st.session_state: st.session_state.map_origin = ""
if "map_dest" not in st.session_state: st.session_state.map_dest = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Xin chào! Mình là BusMate. Bạn cần tìm tuyến xe nào?"}
    ]

# ================= UTILS =================
def speak(text):
    if HAS_GTTS:
        try:
            import io
            fp = io.BytesIO()
            gTTS(text=text, lang="vi").write_to_fp(fp)
            fp.seek(0)
            with sound_placeholder.container():
                st.audio(fp, format='audio/mp3', autoplay=True)
        except: pass

def clean_html(t): return re.sub("<[^<]+?>", "", t)

def render_map(origin, destination, api_key):
    # Style bản đồ: Bo góc, bóng đổ nhẹ
    style = "width:100%; height:600px; border-radius:12px; overflow:hidden; border: 1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
    
    if not api_key:
        return f"""<div style="{style} display:flex; align-items:center; justify-content:center; background:#fff; color:#65676B;">Cần API Key để hiện bản đồ</div>"""
    
    if origin and destination:
        src = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin}&destination={destination}&mode=transit"
    else:
        src = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center=10.7769,106.7009&zoom=14"
    return f"""<div style="{style}"><iframe width="100%" height="100%" frameborder="0" style="border:0" src="{src}" allowfullscreen></iframe></div>"""

def ai_parse_input(user_text):
    prompt = f"""
    Phân tích yêu cầu: "{user_text}"
    Trả về JSON: {{"origin": "...", "destination": "..."}}
    Nếu không rõ điểm đi (ví dụ 'từ đây'), để null.
    """
    try:
        res = ai.generate_content(prompt).text
        json_str = res.replace("```json", "").replace("```", "").strip()
        return json.loads(json_str)
    except:
        return {}

# ================= UI LAYOUT =================
st.title("BusMate")

# Khung âm thanh (ẩn)
sound_placeholder = st.empty()

# --- TABS (NAVIGATION BAR) ---
# Tên tab ngắn gọn, không icon rườm rà
tab_nav, tab_chat = st.tabs(["Dẫn đường", "Trò chuyện"])

# ================= TAB 1: DẪN ĐƯỜNG =================
with tab_nav:
    col_control, col_map = st.columns([1, 1.5], gap="large")

    with col_map:
        st.markdown("### Bản đồ")
        map_html = render_map(st.session_state.map_origin, st.session_state.map_dest, GOOGLE_MAPS_API_KEY)
        components.html(map_html, height=620)

    with col_control:
        st.markdown("### Tìm lộ trình")
        # Card UI cho phần nhập liệu
        with st.container():
            user_input = st.text_input("Bạn muốn đi đâu?", placeholder="VD: Bến Thành đi Suối Tiên...")
            
            st.write("") # Spacer
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Bắt đầu"):
                    st.session_state.running = False 
                    st.session_state.last_voice = "" 
                    sound_placeholder.empty()
                    
                    if user_input and GEMINI_API_KEY:
                        parsed = ai_parse_input(user_input)
                        o_found = parsed.get("origin")
                        d_found = parsed.get("destination")
                        
                        if d_found:
                            st.session_state.map_dest = d_found
                            st.session_state.map_origin = o_found if o_found else "Current Location"
                    
                    st.session_state.running = True
                    st.rerun()
                    
            with c2:
                if st.button("Dừng lại"):
                    st.session_state.running = False
                    st.session_state.last_voice = ""
                    sound_placeholder.empty()
                    st.rerun()

    # --- FRAGMENT LOGIC (Dẫn đường) ---
    @fragment
    def tracking_logic():
        if st.session_state.running:
            if not GEMINI_API_KEY or not GOOGLE_MAPS_API_KEY:
                st.error("Thiếu API Key.")
                return

            lat, lng = 10.7769, 106.7009
            has_real_gps = False
            
            if HAS_GEOLOCATION and enable_gps:
                loc = get_geolocation() 
                if loc:
                    lat = loc["coords"]["latitude"]
                    lng = loc["coords"]["longitude"]
                    has_real_gps = True
                else:
                    st.info("Đang tìm vị trí...")
                    time.sleep(3)
                    st.rerun()
                    return
            else:
                if st.session_state.map_origin == "Current Location":
                    st.warning("GPS đang tắt. Dùng tọa độ giả lập.")

            try:
                dest = st.session_state.map_dest
                user_origin = st.session_state.map_origin
                
                if not dest:
                    st.warning("Chưa có điểm đến.")
                    return

                # Logic chọn điểm đi
                is_gps_mode = not user_origin or any(x in str(user_origin).lower() for x in ["current location", "vị trí hiện tại", "tại đây"])
                
                if is_gps_mode:
                    if has_real_gps:
                        nav_origin = f"{lat},{lng}"
                        st.success("Đang dẫn đường từ vị trí của bạn.")
                    else:
                        nav_origin = "Hồ Chí Minh"
                else:
                    nav_origin = user_origin
                    st.success(f"Dẫn đường từ: {user_origin}")

                # API Google
                transit_params = {
                    "origin": nav_origin, 
                    "destination": dest,
                    "mode": "transit", "transit_mode": "bus",
                    "departure_time": "now", "language": "vi",
                    "key": GOOGLE_MAPS_API_KEY
                }
                
                resp = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=transit_params).json()
                voice_msg = ""
                
                if resp.get("routes"):
                    legs = resp["routes"][0]["legs"][0]
                    st.info(f"Thời gian dự kiến: **{legs['duration']['text']}**")
                    
                    step0 = legs["steps"][0]
                    dist0 = step0["distance"]["text"]
                    instr0 = clean_html(step0["html_instructions"])
                    
                    if step0["travel_mode"] == "WALKING":
                        voice_msg = f"Đi bộ {dist0}. {instr0}."
                    elif step0["travel_mode"] == "TRANSIT":
                        bus = step0["transit_details"]["line"]["short_name"]
                        arr = step0["transit_details"]["departure_time"]["text"]
                        voice_msg = f"Xe {bus} sắp đến lúc {arr}."
                    
                    st.markdown("#### Chi tiết lộ trình")
                    for s in legs["steps"]:
                        mode = s["travel_mode"]
                        if mode == "WALKING":
                            st.write(f"🚶 **{s['distance']['text']}**: {clean_html(s['html_instructions'])}")
                        elif mode == "TRANSIT":
                            td = s["transit_details"]
                            st.write(f"🚌 **Bus {td['line']['short_name']}**: {td['departure_stop']['name']} ➝ {td['arrival_stop']['name']}")
                else:
                    st.error("Không tìm thấy đường đi.")

                if voice_msg and voice_msg != st.session_state.last_voice:
                    speak(voice_msg)
                    st.session_state.last_voice = voice_msg
                
                time.sleep(5)
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")

    with col_control:
        tracking_logic()

# ================= TAB 2: AI CHATBOT =================
with tab_chat:
    st.markdown("### Trợ lý ảo")
    
    # Khung chat - Thiết kế bong bóng hội thoại
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
            
    # Input Chat
    if prompt := st.chat_input("Hỏi gì đó... (VD: Xe 19 đi đâu?)"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Đang trả lời..."):
                try:
                    if GEMINI_API_KEY:
                        chat = ai_chatbot.start_chat(history=[])
                        response = chat.send_message(prompt)
                        bot_reply = response.text
                        
                        # --- SMART LINKING ---
                        if "MAP_CMD:" in bot_reply:
                            try:
                                cmd_line = [l for l in bot_reply.splitlines() if "MAP_CMD:" in l][0]
                                parts = cmd_line.replace("MAP_CMD:", "").split("|")
                                if len(parts) == 2:
                                    o_cmd = parts[0].strip()
                                    d_cmd = parts[1].strip()
                                    
                                    st.session_state.map_origin = o_cmd
                                    st.session_state.map_dest = d_cmd
                                    st.toast(f"Đã cập nhật bản đồ: {o_cmd} ➝ {d_cmd}. Xem ở tab Dẫn đường!", icon="🗺️")
                            except: pass
                            bot_reply = re.sub(r"MAP_CMD:.*", "", bot_reply).strip()

                    else:
                        bot_reply = "Vui lòng nhập API Key."

                    st.markdown(bot_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                    
                except Exception as e:
                    st.error(f"Lỗi: {e}")
