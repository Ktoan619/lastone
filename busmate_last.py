# ================= SIDEBAR CONFIG =================
with st.sidebar:
st.header("Cấu hình hệ thống")
    GOOGLE_MAPS_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
    if not GOOGLE_MAPS_API_KEY:
        GOOGLE_MAPS_API_KEY = st.text_input("🔑 Google Maps API Key", type="password")
        
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = st.text_input("✨ Gemini API Key", type="password")
    
    # 1. Lấy API Key từ Secrets (Bắt buộc)
    if "GOOGLE_MAPS_API_KEY" in st.secrets:
        GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        st.success("✅ Google Maps API: Đã kết nối")
    else:
        st.error("❌ Thiếu GOOGLE_MAPS_API_KEY trong secrets.toml")
        GOOGLE_MAPS_API_KEY = None

    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        st.success("✅ Gemini API: Đã kết nối")
    else:
        st.error("❌ Thiếu GEMINI_API_KEY trong secrets.toml")
        GEMINI_API_KEY = None

st.markdown("---")
    
    # 2. Nút điều khiển GPS (Mặc định Bật)
    enable_gps = st.checkbox("📍 Bật định vị GPS", value=True, help="Tự động lấy vị trí hiện tại của bạn để dẫn đường chính xác hơn.")
    
st.info("Chế độ: Dẫn đường Real-time & Giọng nói AI.")

# ================= AI CONFIG =================
@@ -60,7 +72,6 @@
st.title("BusMate - Dẫn đường thời gian thực")

# [QUAN TRỌNG] Tạo một khung cố định cho âm thanh để tránh chồng chéo
# Khung này sẽ luôn được làm mới mỗi khi trang rerun
sound_placeholder = st.empty()

col_control, col_map = st.columns([1, 1.2])
@@ -75,8 +86,6 @@ def speak(text):
gTTS(text=text, lang="vi").write_to_fp(fp)
fp.seek(0)

            # Sử dụng sound_placeholder để ghi đè âm thanh cũ
            # Thêm key=uuid để đảm bảo trình duyệt nhận diện đây là file audio mới
with sound_placeholder.container():
st.audio(fp, format='audio/mp3', autoplay=True)

@@ -140,7 +149,6 @@ def ai_parse_input(user_text):
if st.button("⏹️ Dừng lại", use_container_width=True):
st.session_state.running = False
st.session_state.last_voice = ""
            # Xóa âm thanh đang phát bằng cách làm rỗng placeholder
sound_placeholder.empty()
st.rerun()

@@ -154,7 +162,7 @@ def ai_parse_input(user_text):
st.stop()

if not GEMINI_API_KEY or not GOOGLE_MAPS_API_KEY:
            st.error("Thiếu API Key.")
            st.error("Hệ thống chưa được cấu hình API Key trong secrets.")
st.stop()

# 1. AI Parse
@@ -172,28 +180,32 @@ def ai_parse_input(user_text):
st.session_state.map_dest = destination_text
st.rerun()

        # 2. GPS Check
        # 2. GPS Check (Có kiểm tra nút enable_gps)
lat, lng = 10.7769, 106.7009
has_real_gps = False

        if HAS_GEOLOCATION:
        # Chỉ gọi get_geolocation nếu thư viện có sẵn VÀ người dùng bật GPS
        if HAS_GEOLOCATION and enable_gps:
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
        elif not enable_gps:
            st.warning("⚠️ GPS đã tắt. Sử dụng vị trí nhập tay.")
else:
            st.warning("⚠️ Không có GPS. Dùng tọa độ giả lập.")
            st.warning("⚠️ Trình duyệt không hỗ trợ GPS hoặc thiếu thư viện.")

# 3. Logic Real-time Navigation
try:
            # Nếu có GPS thực và được bật -> Dùng GPS làm điểm xuất phát
            # Nếu không -> Dùng điểm xuất phát người dùng nhập (origin_text)
nav_origin = f"{lat},{lng}" if has_real_gps else origin_text

transit_params = {
