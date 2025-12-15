import streamlit as st
import requests
import time
import re
import uuid
import json
import streamlit.components.v1 as components
import os

# --- IMPORT DATA ---
try:
    from data_and_prompts import get_full_system_instruction, BUS_DATA
except ImportError:
    def get_full_system_instruction(): return "You are a smart bus assistant."
    BUS_DATA = []

# --- LIBRARY HANDLING ---
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

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="BusMate Pro", 
    page_icon="🚌",
    layout="wide"
)

# --- CUSTOM CSS (DARK MODE) ---
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp { 
        background-color: #0E1117; 
        color: #FAFAFA;
    }
    
    /* 2. Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #262730; 
        border-right: 1px solid #41444C;
    }
    
    /* 3. Text Colors */
    h1, h2, h3, h4, h5, h6, span, div, label, p, li {
        color: #FAFAFA !important; 
    }
    .stCaption { color: #B0B0B0 !important; } 
    
    /* 4. Inputs */
    .stTextInput > div > div > input {
        color: #FAFAFA;
        background-color: #262730; 
        border: 1px solid #41444C;
        border-radius: 8px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #007BFF;
        box-shadow: 0 0 0 1px #007BFF;
    }
    
    /* 5. Buttons */
    .stButton > button {
        background-color: #007BFF !important; 
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #0056b3 !important;
        transform: translateY(-2px);
    }
    
    /* 6. Tabs */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid #41444C;
        gap: 8px;
    }
    .stTabs button[data-baseweb="tab"] {
        background-color: transparent;
        border: none;
    }
    
    /* Tab Title Colors */
    .stTabs button[data-baseweb="tab"] div p {
        color: #A6A9B4 !important; 
        font-weight: 600;
        font-size: 16px;
    }
    
    /* Active Tab */
    .stTabs button[data-baseweb="tab"][aria-selected="true"] div p {
        color: #007BFF !important; 
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #007BFF !important; 
    }
    
    /* 7. Alerts */
    .stAlert {
        background-color: #262730; 
        color: #FAFAFA;
        border: 1px solid #41444C;
    }
    
    /* Main Title */
    h1 { 
        color: #007BFF !important; 
    }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR CONFIG =================
with st.sidebar:
    st.header("⚙️ System Settings")
    if "GOOGLE_MAPS_API_KEY" in st.secrets:
        GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        st.success("✅ Google Maps: Connected")
    else:
        st.error("❌ Missing Google Maps Key")
        GOOGLE_MAPS_API_KEY = None

    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        st.success("✅ Gemini AI: Connected")
    else:
        st.error("❌ Missing Gemini Key")
        GEMINI_API_KEY = None
    
    st.markdown("---")
    enable_gps = st.checkbox("📍 Enable GPS", value=True)
    st.info("💡 Tip: Switch to '💬 AI Chatbot' tab to ask questions.")

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
        {"role": "assistant", "content": "Hello! I am BusMate 🚌. How can I help you? (Ví dụ: 'Xe 152 đi đâu?', 'Vé xe 19 bao nhiêu?')"}
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
    if not api_key:
        return """<div style="padding:20px; border:2px dashed #444; border-radius:10px; text-align:center; color: #aaa;">⚠️ API Key Required</div>"""
    if origin and destination:
        src = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={origin}&destination={destination}&mode=transit"
    else:
        src = f"https://www.google.com/maps/embed/v1/view?key={api_key}&center=10.7769,106.7009&zoom=14"
    return f"""<div style="width:100%; height:600px; border-radius:15px; overflow:hidden; border: 2px solid #007BFF; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"><iframe width="100%" height="100%" frameborder="0" style="border:0" src="{src}" allowfullscreen></iframe></div>"""

def ai_parse_input(user_text):
    prompt = f"""
    Analyze user request: "{user_text}"
    Return JSON: {{"origin": "...", "destination": "..."}}
    If origin is unclear (e.g. 'from here'), leave null.
    """
    try:
        res = ai.generate_content(prompt).text
        json_str = res.replace("```json", "").replace("```", "").strip()
        return json.loads(json_str)
    except:
        return {}

# ================= UI LAYOUT =================
st.title("BusMate - Your Bus Companion")

# Audio Placeholder
sound_placeholder = st.empty()

# --- TABS ---
tab_nav, tab_chat = st.tabs(["🧭 REAL-TIME NAVIGATION", "💬 AI CHATBOT"])

# ================= TAB 1: NAVIGATION =================
with tab_nav:
    col_control, col_map = st.columns([1, 1.2])

    with col_map:
        st.markdown("### 🗺️ Live Map")
        map_html = render_map(st.session_state.map_origin, st.session_state.map_dest, GOOGLE_MAPS_API_KEY)
        components.html(map_html, height=620)

    with col_control:
        st.markdown("### 🎙️ Input Route")
        # Giữ placeholder tiếng Việt theo yêu cầu
        user_input = st.text_input("Enter route:", placeholder="Ví dụ: Bến Thành đi Suối Tiên...")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ Start", use_container_width=True):
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
            if st.button("⏹️ Stop", use_container_width=True):
                st.session_state.running = False
                st.session_state.last_voice = ""
                sound_placeholder.empty()
                st.rerun()

    # --- FRAGMENT LOGIC (Navigation) ---
    @fragment
    def tracking_logic():
        if st.session_state.running:
            if not GEMINI_API_KEY or not GOOGLE_MAPS_API_KEY:
                st.error("Missing API Key.")
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
                    st.warning("📡 Searching for GPS...")
                    time.sleep(3)
                    st.rerun()
                    return
            else:
                if st.session_state.map_origin == "Current Location":
                    st.warning("⚠️ GPS disabled. Using simulated location.")

            try:
                dest = st.session_state.map_dest
                user_origin = st.session_state.map_origin
                
                if not dest:
                    st.warning("No destination set.")
                    return

                # Logic to determine origin
                is_gps_mode = not user_origin or any(x in str(user_origin).lower() for x in ["current location", "vị trí hiện tại", "tại đây"])
                
                if is_gps_mode:
                    if has_real_gps:
                        nav_origin = f"{lat},{lng}"
                        st.toast("📍 Navigating from current GPS location.")
                    else:
                        nav_origin = "Hồ Chí Minh"
                else:
                    nav_origin = user_origin
                    st.toast(f"ℹ️ Navigating from: {user_origin}")

                # API Google
                transit_params = {
                    "origin": nav_origin, 
                    "destination": dest,
                    "mode": "transit", "transit_mode": "bus",
                    "departure_time": "now", "language": "vi", # Giữ language='vi' để Google trả về tên đường tiếng Việt
                    "key": GOOGLE_MAPS_API_KEY
                }
                
                resp = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=transit_params).json()
                voice_msg = ""
                
                if resp.get("routes"):
                    legs = resp["routes"][0]["legs"][0]
                    st.info(f"⏱️ Time: **{legs['duration']['text']}**")
                    
                    step0 = legs["steps"][0]
                    dist0 = step0["distance"]["text"]
                    instr0 = clean_html(step0["html_instructions"])
                    
                    if step0["travel_mode"] == "WALKING":
                        voice_msg = f"Đi bộ {dist0}. {instr0}."
                    elif step0["travel_mode"] == "TRANSIT":
                        bus = step0["transit_details"]["line"]["short_name"]
                        arr = step0["transit_details"]["departure_time"]["text"]
                        voice_msg = f"Xe {bus} sắp đến lúc {arr}."
                    
                    st.markdown("#### 📝 Route Details:")
                    for s in legs["steps"]:
                        mode = s["travel_mode"]
                        if mode == "WALKING":
                            st.info(f"🚶 {s['distance']['text']}: {clean_html(s['html_instructions'])}")
                        elif mode == "TRANSIT":
                            td = s["transit_details"]
                            st.success(f"🚌 Bus {td['line']['short_name']}: {td['departure_stop']['name']} ➔ {td['arrival_stop']['name']}")
                else:
                    st.error("No route found.")

                if voice_msg and voice_msg != st.session_state.last_voice:
                    speak(voice_msg)
                    st.session_state.last_voice = voice_msg
                
                time.sleep(5)
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")

    with col_control:
        tracking_logic()

# ================= TAB 2: AI CHATBOT =================
with tab_chat:
    st.markdown("### 🤖 Smart AI Assistant")
    st.caption("HCMC Bus Expert - Ask me anything!")
    
    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Input Chat (Giữ placeholder tiếng Việt)
    if prompt := st.chat_input("Ask about buses (VD: Xe 19 đi đâu? Giá vé xe 152?)"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
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
                                    st.toast(f"🗺️ Map updated: {o_cmd} ➔ {d_cmd}. Switch to Navigation Tab!", icon="🚀")
                            except: pass
                            bot_reply = re.sub(r"MAP_CMD:.*", "", bot_reply).strip()

                    else:
                        bot_reply = "Please enter API Key."

                    st.markdown(bot_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                    
                except Exception as e:
                    st.error(f"Error: {e}")
