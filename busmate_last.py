import streamlit as st
import requests
import time
import re
import uuid
import json
import streamlit.components.v1 as components
import os

# --- IMPORT DỮ LIỆU VÀ PROMPT TỪ FILE MỚI ---
try:
    from data_and_prompts import get_full_system_instruction, BUS_DATA
except ImportError:
    # Fallback nếu file chưa tồn tại (để tránh lỗi crash ban đầu)
    def get_full_system_instruction(): return "Bạn là trợ lý xe buýt."
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
    page_title="BusMate Pro", 
    page_icon="🚌",
    layout="wide"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3, h4, h5, h6, p, li, span, div, label { color: #000000 !important; }
    .stButton > button {
        background-color: #007BFF !important; color: white !important;
        font-weight: bold; border-radius: 10px; border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #0056b3 !important; transform: translateY(-2px);
    }
    .stTextInput > div > div > input {
        color: #000000; background-color: #F0F8FF;
        border: 2px solid #007BFF; border-radius: 8px;
    }
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #007BFF; }
    .stAlert { border-radius: 8px; border: 1px solid rgba(0,0,0,0.1); }
    h1 { color: #007BFF !important; }
    
    /* CSS cho Tab */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F0F8FF;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007BFF;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR CONFIG =================
with st.sidebar:
    st.header("Cấu hình hệ thống")
    if "GOOGLE_MAPS_API_KEY" in st.secrets:
        GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        st.success("✅ Google Maps API: Đã kết nối")
    else:
        st.error("❌ Thiếu GOOGLE_MAPS_API_KEY")
        GOOGLE_MAPS_API_KEY = None

    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        st.success("✅ Gemini API: Đã kết nối")
    else:
        st.error("❌ Thiếu GEMINI_API_KEY")
        GEMINI_API_KEY = None
    
    st.markdown("---")
    enable_gps = st.checkbox("📍 Bật định vị GPS", value=True)
    st.info("Chế độ: Dẫn đường & Chatbot thông minh.")

# ================= AI CONFIG =================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Model cho tác vụ dẫn đường (Logic đơn giản)
    ai = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025")
    
    # Model cho Chatbot (Dùng System Prompt từ file data mới)
    bot_instruction = get_full_system_instruction()
    ai_chatbot = genai.GenerativeModel("gemini-2.5-flash-preview-09-2025", system_instruction=bot_instruction)

# ================= STATE =================
if "running" not in st.session_state: st.session_state.running = False
if "last_voice" not in st.session_state: st.session_state.last_voice = ""
if "map_origin" not in st.session_state: st.session_state.map_origin = ""
if "map_dest" not in st.session_state: st.session_state.map_dest = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Xin chào! Tôi là Trợ lý Giao thông Xanh VnBus. Bạn cần tìm tuyến xe nào? (Ví dụ: 'Xe 152 đi đâu?', 'Vé xe 19 bao nhiêu?')"}
    ]

# ================= UTILS =================
def speak(text):
    """Phát giọng nói vào khung cố định"""
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
    if not api_key:
        return """<div style="padding:20px; border:1px dashed #ccc; text-align:center">⚠️ Cần API Key</div>"""
    if origin and destination:
        src = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin}&destination={destination}&mode=transit"
    else:
        src = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center=10.7769,106.7009&zoom=14"
    return f"""<div style="width:100%; height:600px; border-radius:15px; overflow:hidden; border: 2px solid #007BFF;"><iframe width="100%" height="100%" frameborder="0" style="border:0" src="{src}" allowfullscreen></iframe></div>"""

def ai_parse_input(user_text):
    prompt = f"""
    Phân tích yêu cầu tìm đường: "{user_text}"
    Trả về JSON với 2 trường:
    - origin: Tên địa điểm đi (Nếu người dùng không nói rõ hoặc nói "tại đây", "vị trí của tôi", hãy để null).
    - destination: Tên địa điểm đến.
    Ví dụ: {{"origin": "Chợ Bến Thành", "destination": "Suối Tiên"}}
    """
    try:
        res = ai.generate_content(prompt).text
        json_str = res.replace("```json", "").replace("```", "").strip()
        return json.loads(json_str)
    except:
        return {}

# ================= UI LAYOUT CHÍNH =================
st.title("BusMate - Bạn đồng hành xe bus")

# Khung chứa âm thanh (Global)
sound_placeholder = st.empty()

# TẠO TABS
tab_nav, tab_chat = st.tabs(["🧭 Dẫn đường Real-time", "💬 Hỏi đáp Bot"])

# ================= TAB 1: DẪN ĐƯỜNG =================
with tab_nav:
    col_control, col_map = st.columns([1, 1.2])

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
                st.session_state.running = False 
                st.session_state.last_voice = "" 
                sound_placeholder.empty()
                
                if user_input and GEMINI_API_KEY:
                    parsed = ai_parse_input(user_input)
                    origin_found = parsed.get("origin")
                    dest_found = parsed.get("destination")
                    
                    if dest_found:
                        st.session_state.map_dest = dest_found
                        if origin_found:
                            st.session_state.map_origin = origin_found
                        else:
                            st.session_state.map_origin = "Current Location"
                
                st.session_state.running = True
                st.rerun()
                
        with c2:
            if st.button("⏹️ Dừng lại", use_container_width=True):
                st.session_state.running = False
                st.session_state.last_voice = ""
                sound_placeholder.empty()
                st.rerun()

    # --- TRACKING LOGIC (FRAGMENT) ---
    @fragment
    def tracking_logic():
        if st.session_state.running:
            if not GEMINI_API_KEY or not GOOGLE_MAPS_API_KEY:
                st.error("Thiếu API Key.")
                return

            # Lấy GPS
            lat, lng = 10.7769, 106.7009
            has_real_gps = False
            
            if HAS_GEOLOCATION and enable_gps:
                loc = get_geolocation() 
                if loc:
                    lat = loc["coords"]["latitude"]
                    lng = loc["coords"]["longitude"]
                    has_real_gps = True
                else:
                    st.warning("📡 Đang lấy vị trí GPS...")
                    time.sleep(3)
                    st.rerun()
                    return
            else:
                if st.session_state.map_origin == "Current Location":
                    st.warning("⚠️ Đang dùng tọa độ giả lập (GPS Tắt).")

            try:
                dest = st.session_state.map_dest
                user_origin = st.session_state.map_origin
                
                if not dest:
                    st.warning("Chưa có điểm đến.")
                    return

                # Logic chọn điểm xuất phát (Ưu tiên Input tay > GPS)
                is_gps_mode = not user_origin or any(x in str(user_origin).lower() for x in ["current location", "vị trí hiện tại", "tại đây"])

                if is_gps_mode:
                    if has_real_gps:
                        nav_origin = f"{lat},{lng}"
                        st.toast("📍 Đang dẫn đường từ vị trí GPS hiện tại.")
                    else:
                        nav_origin = "Hồ Chí Minh"
                else:
                    nav_origin = user_origin
                    st.toast(f"ℹ️ Đang dẫn đường từ: {user_origin}")

                # Gọi Google Directions API
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
                    duration = legs["duration"]["text"]
                    st.info(f"⏱️ Thời gian: **{duration}**")
                    
                    # Phân tích bước đầu tiên để đọc giọng nói
                    step0 = legs["steps"][0]
                    dist0 = step0["distance"]["text"]
                    instr0 = clean_html(step0["html_instructions"])
                    
                    if step0["travel_mode"] == "WALKING":
                        voice_msg = f"Đi bộ {dist0}. {instr0}."
                    elif step0["travel_mode"] == "TRANSIT":
                        bus = step0["transit_details"]["line"]["short_name"]
                        arr = step0["transit_details"]["departure_time"]["text"]
                        voice_msg = f"Xe {bus} sắp đến lúc {arr}."
                    
                    # Hiển thị chi tiết
                    st.markdown("#### 📝 Chi tiết:")
                    for s in legs["steps"]:
                        mode = s["travel_mode"]
                        if mode == "WALKING":
                            st.info(f"🚶 {s['distance']['text']}: {clean_html(s['html_instructions'])}")
                        elif mode == "TRANSIT":
                            td = s["transit_details"]
                            st.success(f"🚌 Bus {td['line']['short_name']}: {td['departure_stop']['name']} ➔ {td['arrival_stop']['name']}")
                else:
                    st.error("Không tìm thấy đường.")

                # Phát giọng nói
                if voice_msg and voice_msg != st.session_state.last_voice:
                    speak(voice_msg)
                    st.session_state.last_voice = voice_msg
                
                time.sleep(5)
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")

    with col_control:
        tracking_logic()

# ================= TAB 2: BOT CHAT HỎI ĐÁP =================
with tab_chat:
    st.markdown("### 🤖 Trợ lý ảo thông minh")
    st.caption("Chuyên gia xe buýt TP.HCM - Hỏi là đáp!")
    
    # Hiển thị lịch sử chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Xử lý input chat
    if prompt := st.chat_input("Hỏi tôi về xe buýt (VD: Giá vé xe 19? Xe nào đi Suối Tiên?)"):
        # Lưu tin nhắn user
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Logic Bot trả lời
        with st.chat_message("assistant"):
            with st.spinner("Bot đang tra cứu dữ liệu..."):
                try:
                    # Gọi Gemini Chatbot (đã cấu hình system_instruction từ file data)
                    if GEMINI_API_KEY:
                        chat = ai_chatbot.start_chat(history=[])
                        response = chat.send_message(prompt)
                        bot_reply = response.text
                        
                        # --- LIÊN KẾT THÔNG MINH (SMART LINKING) ---
                        # Nếu Bot trả về lệnh MAP_CMD, tự động cập nhật bản đồ ở Tab 1
                        if "MAP_CMD:" in bot_reply:
                            try:
                                # Lấy dòng chứa lệnh
                                cmd_line = [line for line in bot_reply.splitlines() if "MAP_CMD:" in line][0]
                                parts = cmd_line.replace("MAP_CMD:", "").split("|")
                                if len(parts) == 2:
                                    origin_cmd = parts[0].strip()
                                    dest_cmd = parts[1].strip()
                                    
                                    # Cập nhật state bản đồ
                                    st.session_state.map_origin = origin_cmd
                                    st.session_state.map_dest = dest_cmd
                                    st.toast(f"🗺️ Đã cập nhật bản đồ: {origin_cmd} ➔ {dest_cmd}. Hãy chuyển sang Tab Dẫn đường!")
                            except: pass
                            
                            # Xóa lệnh khỏi nội dung hiển thị
                            bot_reply = re.sub(r"MAP_CMD:.*", "", bot_reply).strip()

                    else:
                        bot_reply = "Xin lỗi, tôi chưa được kết nối với bộ não (Thiếu API Key)."

                    st.markdown(bot_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                    
                except Exception as e:
                    st.error(f"Lỗi Bot: {e}")
