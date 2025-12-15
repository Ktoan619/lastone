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
    page_title="BusMate - Threads Style", 
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PHONG CÁCH THREADS (ĐEN - TRẮNG - XÁM) ---
st.markdown("""
<style>
    /* 1. Nền chính (Threads Background) */
    .stApp { 
        background-color: #101010; /* Đen sâu */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #F3F5F7;
    }
    
    /* 2. Sidebar (Minimalist) */
    [data-testid="stSidebar"] { 
        background-color: #101010; 
        border-right: 1px solid #333333; /* Viền xám tối */
    }
    
    /* 3. Typography (Chữ) */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px; /* Phong cách hiện đại */
    }
    p, label, li, span, div {
        color: #F3F5F7;
    }
    .stCaption { color: #777777 !important; } /* Xám trung tính cho chú thích */
    
    /* 4. Ô nhập liệu (Input Fields) - Bo tròn kiểu Threads */
    .stTextInput > div > div > input {
        background-color: #1E1E1E; /* Xám đen nhẹ */
        color: #FFFFFF;
        border: 1px solid #333333;
        border-radius: 16px; /* Bo tròn nhiều */
        padding: 12px 15px;
        font-size: 15px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #555555;
        background-color: #262626;
    }
    
    /* 5. Nút bấm (Buttons) */
    /* Nút chính: Trắng trên nền Đen (High Contrast) */
    .stButton > button {
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        font-weight: 600;
        border-radius: 20px; /* Pill shape */
        border: 1px solid #FFFFFF;
        padding: 0.5rem 1.2rem;
        transition: transform 0.1s, background-color 0.2s;
    }
    .stButton > button:hover {
        background-color: #D1D1D1 !important;
        border-color: #D1D1D1;
        transform: scale(0.98);
    }
    
    /* 6. TABS (THIẾT KẾ ĐẶC BIỆT: BOX STYLE) */
    /* Ẩn thanh gạch chân mặc định của Streamlit */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    
    /* Container chứa các tab */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 8px;
        padding-bottom: 10px;
        border-bottom: 1px solid #333333; /* Đường kẻ phân cách mờ */
    }
    
    /* Style chung cho từng Tab */
    .stTabs button[data-baseweb="tab"] {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 12px; /* Bo góc tab */
        padding: 8px 16px;
        height: auto;
        transition: all 0.2s;
    }
    
    /* Tab chưa chọn */
    .stTabs button[data-baseweb="tab"] div p {
        color: #777777 !important; /* Màu xám */
        font-weight: 600;
        font-size: 15px;
    }
    
    /* TAB ĐƯỢC CHỌN (ACTIVE) - CÓ Ô BAO QUANH */
    .stTabs button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #1E1E1E !important; /* Nền xám đen nổi bật hơn nền chính */
        border: 1px solid #333333 !important; /* Viền bao quanh */
    }
    
    .stTabs button[data-baseweb="tab"][aria-selected="true"] div p {
        color: #FFFFFF !important; /* Chữ trắng sáng */
    }
    
    /* 7. Chat Bubbles (Bong bóng chat) */
    [data-testid="stChatMessage"] {
        background-color: transparent;
        padding: 12px 0;
        border-bottom: 1px solid #222; /* Đường kẻ ngăn cách giống thread list */
    }
    /* User: Căn phải (hoặc style khác biệt chút) */
    [data-testid="stChatMessage"][data-author="user"] {
        background-color: transparent;
    }
    /* Avatar */
    [data-testid="stChatMessageAvatar"] {
        background-color: #333;
        color: #FFF;
    }
    
    /* 8. Alerts/Toasts */
    .stAlert {
        background-color: #1E1E1E;
        color: #FFF;
        border: 1px solid #333;
        border-radius: 12px;
    }
    
    /* Bản đồ Border */
    iframe {
        border-radius: 16px !important;
        border: 1px solid #333 !important;
    }
    
    /* Title */
    h1 { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR CONFIG =================
with st.sidebar:
    st.title("⚙️ Cài đặt")
    st.markdown("---")
    
    if "GOOGLE_MAPS_API_KEY" in st.secrets:
        GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        st.success("Maps: Đã kết nối")
    else:
        st.error("Thiếu Maps Key")
        GOOGLE_MAPS_API_KEY = None

    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        st.success("AI: Đã kết nối")
    else:
        st.error("Thiếu AI Key")
        GEMINI_API_KEY = None
    
    st.markdown("---")
    enable_gps = st.checkbox("Bật định vị GPS", value=True)
    st.caption("Cho phép truy cập vị trí để dẫn đường thời gian thực.")

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
        {"role": "assistant", "content": "Xin chào, mình là BusMate. @busmate_ai"}
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
    # Style bản đồ: Bo góc lớn, viền tối
    style = "width:100%; height:600px; border-radius:16px; overflow:hidden; border: 1px solid #333;"
    
    if not api_key:
        return f"""<div style="{style} display:flex; align-items:center; justify-content:center; background:#1E1E1E; color:#777;">Cần API Key</div>"""
    
    if origin and destination:
        src = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin}&destination={destination}&mode=transit&maptype=roadmap&style=feature:all|element:all|saturation:-100|lightness:-50" # Darker map hint
    else:
        src = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center=10.7769,106.7009&zoom=14"
    return f"""<div style="{style}"><iframe width="100%" height="100%" frameborder="0" style="border:0" src="{src}" allowfullscreen></iframe></div>"""

def ai_parse_input(user_text):
    prompt = f"""
    Phân tích: "{user_text}"
    JSON: {{"origin": "...", "destination": "..."}}
    (origin=null nếu không rõ).
    """
    try:
        res = ai.generate_content(prompt).text
        json_str = res.replace("```json", "").replace("```", "").strip()
        return json.loads(json_str)
    except:
        return {}

# ================= UI LAYOUT =================
st.title("BusMate")
st.caption("Trợ lý xe buýt thông minh • @busmate_ai")

# Khung âm thanh
sound_placeholder = st.empty()

# --- TABS (PHONG CÁCH THREADS) ---
# Tabs sẽ có box bao quanh khi được chọn nhờ CSS ở trên
tab_nav, tab_chat = st.tabs(["Dẫn đường", "Hỏi đáp Bot"])

# ================= TAB 1: DẪN ĐƯỜNG =================
with tab_nav:
    col_control, col_map = st.columns([1, 1.5], gap="large")

    with col_map:
        st.markdown("### Bản đồ")
        map_html = render_map(st.session_state.map_origin, st.session_state.map_dest, GOOGLE_MAPS_API_KEY)
        components.html(map_html, height=620)

    with col_control:
        st.markdown("### Tìm đường")
        with st.container():
            user_input = st.text_input("Bạn muốn đi đâu?", placeholder="Bến Thành đến Suối Tiên...")
            st.write("") 
            
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
                # Nút dừng có style mặc định (border 1px solid white do CSS chung)
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
                st.error("Thiếu Key.")
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
                    st.info("📡 Đang định vị...")
                    time.sleep(3)
                    st.rerun()
                    return
            else:
                if st.session_state.map_origin == "Current Location":
                    st.caption("⚠️ GPS tắt. Dùng vị trí giả lập.")

            try:
                dest = st.session_state.map_dest
                user_origin = st.session_state.map_origin
                
                if not dest:
                    st.warning("Chưa có điểm đến.")
                    return

                is_gps_mode = not user_origin or any(x in str(user_origin).lower() for x in ["current location", "vị trí hiện tại", "tại đây"])
                
                if is_gps_mode:
                    if has_real_gps:
                        nav_origin = f"{lat},{lng}"
                        st.toast("📍 Từ vị trí của bạn")
                    else:
                        nav_origin = "Hồ Chí Minh"
                else:
                    nav_origin = user_origin
                    st.toast(f"ℹ️ Từ: {user_origin}")

                transit_params = {
                    "origin": nav_origin, "destination": dest,
                    "mode": "transit", "transit_mode": "bus",
                    "departure_time": "now", "language": "vi",
                    "key": GOOGLE_MAPS_API_KEY
                }
                
                resp = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=transit_params).json()
                voice_msg = ""
                
                if resp.get("routes"):
                    legs = resp["routes"][0]["legs"][0]
                    st.markdown(f"⏱️ **{legs['duration']['text']}**")
                    
                    step0 = legs["steps"][0]
                    dist0 = step0["distance"]["text"]
                    instr0 = clean_html(step0["html_instructions"])
                    
                    if step0["travel_mode"] == "WALKING":
                        voice_msg = f"Đi bộ {dist0}. {instr0}."
                    elif step0["travel_mode"] == "TRANSIT":
                        bus = step0["transit_details"]["line"]["short_name"]
                        arr = step0["transit_details"]["departure_time"]["text"]
                        voice_msg = f"Xe {bus} sắp đến lúc {arr}."
                    
                    # Danh sách chỉ dẫn phong cách tối giản
                    st.markdown("---")
                    for s in legs["steps"]:
                        mode = s["travel_mode"]
                        if mode == "WALKING":
                            st.caption(f"🚶 **{s['distance']['text']}**: {clean_html(s['html_instructions'])}")
                        elif mode == "TRANSIT":
                            td = s["transit_details"]
                            st.write(f"🚌 **{td['line']['short_name']}**: {td['departure_stop']['name']} ➝ {td['arrival_stop']['name']}")
                else:
                    st.error("Không tìm thấy đường.")

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
    # Container chat
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
            
    # Input Chat
    if prompt := st.chat_input("Bắt đầu cuộc trò chuyện..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("..."):
                try:
                    if GEMINI_API_KEY:
                        chat = ai_chatbot.start_chat(history=[])
                        response = chat.send_message(prompt)
                        bot_reply = response.text
                        
                        if "MAP_CMD:" in bot_reply:
                            try:
                                cmd_line = [l for l in bot_reply.splitlines() if "MAP_CMD:" in l][0]
                                parts = cmd_line.replace("MAP_CMD:", "").split("|")
                                if len(parts) == 2:
                                    o_cmd = parts[0].strip()
                                    d_cmd = parts[1].strip()
                                    st.session_state.map_origin = o_cmd
                                    st.session_state.map_dest = d_cmd
                                    st.toast(f"Đã ghim bản đồ: {d_cmd}", icon="📍")
                            except: pass
                            bot_reply = re.sub(r"MAP_CMD:.*", "", bot_reply).strip()

                    else:
                        bot_reply = "Thiếu Key."

                    st.markdown(bot_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                    
                except Exception as e:
                    st.error(f"Error: {e}")
