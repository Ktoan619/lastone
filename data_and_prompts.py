# --- 1. CẤU HÌNH NHÂN CÁCH CHATBOT (SYSTEM PROMPT) ---
BOT_PERSONA = """
Bạn là "Trợ lý AI Thông Minh BusMate" - chuyên gia bản đồ số 1 về xe buýt TP.HCM.
Bạn nắm giữ dữ liệu chi tiết của hơn 150 tuyến xe đang hoạt động (bao gồm xe trợ giá, xe liên tỉnh, xe điện VinBus và City Tour).

Tính cách:
- Thông thái, nhiệt tình, luôn khuyến khích lối sống xanh 🌿.
- Trả lời CHÍNH XÁC thông tin: Mã tuyến, Giá vé, Giờ chạy, và Lộ trình đi qua.
- Dùng emoji sinh động (🚌, 📍, 🎫, ⏰).

QUY TẮC QUAN TRỌNG KHI TRẢ LỜI:
1. NẾU HỎI ĐƯỜNG (Vd: "Từ Bến Thành đi Suối Tiên"):
   - Dòng 1 bắt buộc: `MAP_CMD: [Điểm đi] | [Điểm đến]`
   - Dòng 2 trở đi: Hướng dẫn chi tiết cách bắt xe.

2. NẾU HỎI THÔNG TIN TUYẾN (Vd: "Tuyến 152 chạy mấy giờ?"):
   - Trích xuất dữ liệu từ kho bên dưới.
   *tra cứu thêm giá vé nếu là học sinh, sinh viên.
   - Luôn hiển thị: Tên tuyến, Giá vé, Thời gian, và các điểm dừng chính.
   
#. NẾU HỎI CÁC THÔNG TIN KHÁC VỀ XE TÙY VÀO CÂU HỎI ĐƯA RA CÂU TRẢ LỜI DƯỚI 100 CHỮ
"""

# --- 2. KHO DỮ LIỆU XE BUÝT (DATABASE - 150+ ROUTES) ---
BUS_DATA = [
    # --- NHÓM 1: TRUNG TÂM & NỘI THÀNH (01 - 30) ---
    {"id": "01", "name": "Bến Thành - Chợ Lớn", "price": "6.000đ", "time": "05:00 - 20:30", "stops": ["Bến Thành", "Trần Hưng Đạo", "Nguyễn Tri Phương", "Hùng Vương", "Chợ Lớn"], "color": "#10b981"},
    {"id": "03", "name": "Bến Thành - Thạnh Lộc", "price": "6.000đ", "time": "04:55 - 20:45", "stops": ["Bến Thành", "Phan Đăng Lưu", "Nguyễn Oanh", "Hà Huy Giáp", "Thạnh Lộc"], "color": "#10b981"},
    {"id": "04", "name": "Bến Thành - Cộng Hòa - An Sương", "price": "6.000đ", "time": "05:00 - 20:30", "stops": ["Bến Thành", "3/2", "Cộng Hòa", "Trường Chinh", "An Sương"], "color": "#10b981"},
    {"id": "05", "name": "Bến xe Chợ Lớn - Biên Hòa", "price": "12.000đ", "time": "04:50 - 17:50", "stops": ["Chợ Lớn", "Hàng Xanh", "Xa lộ Hà Nội", "Biên Hòa"], "color": "#ef4444"},
    {"id": "06", "name": "Bến xe Chợ Lớn - ĐH Nông Lâm", "price": "6.000đ", "time": "04:55 - 21:00", "stops": ["Chợ Lớn", "Hồng Bàng", "Võ Văn Ngân", "ĐH Nông Lâm"], "color": "#10b981"},
    {"id": "07", "name": "Bến xe Chợ Lớn - Gò Vấp", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Chợ Lớn", "Lê Quang Định", "Phan Văn Trị", "Bến xe Gò Vấp"], "color": "#10b981"},
    {"id": "08", "name": "Bến xe Quận 8 - ĐH Quốc Gia", "price": "7.000đ", "time": "04:40 - 20:30", "stops": ["Bến xe Q8", "Lý Thường Kiệt", "Phạm Văn Đồng", "ĐHQG"], "color": "#10b981"},
    {"id": "09", "name": "Bến xe Chợ Lớn - Hưng Long", "price": "6.000đ", "time": "05:30 - 18:30", "stops": ["Chợ Lớn", "QL1A", "Hương Lộ 11", "Hưng Long"], "color": "#8b5cf6"},
    {"id": "10", "name": "ĐH Quốc Gia - Bến xe Miền Tây", "price": "7.000đ", "time": "05:00 - 18:45", "stops": ["ĐHQG", "Suối Tiên", "XLHN", "Kinh Dương Vương", "BX Miền Tây"], "color": "#10b981"},
    {"id": "11", "name": "Bến Thành - Đầm Sen", "price": "6.000đ", "time": "05:30 - 18:30", "stops": ["Bến Thành", "Lý Thái Tổ", "Lãnh Binh Thăng", "Đầm Sen"], "color": "#f59e0b"},
    {"id": "13", "name": "Bến Thành - Bến xe Củ Chi", "price": "10.000đ", "time": "03:30 - 20:30", "stops": ["Bến Thành", "CMT8", "An Sương", "QL22", "Củ Chi"], "color": "#ef4444"},
    {"id": "14", "name": "Miền Đông - 3/2 - Miền Tây", "price": "6.000đ", "time": "04:00 - 20:30", "stops": ["Miền Đông", "3/2", "Hồng Bàng", "Kinh Dương Vương", "Miền Tây"], "color": "#3b82f6"},
    {"id": "15", "name": "Chợ Phú Định - Đầm Sen", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Phú Định", "Hậu Giang", "Lũy Bán Bích", "Đầm Sen"], "color": "#10b981"},
    {"id": "16", "name": "Chợ Lớn - Bến xe Tân Phú", "price": "6.000đ", "time": "05:15 - 19:15", "stops": ["Chợ Lớn", "Hồng Bàng", "Lũy Bán Bích", "Tân Phú"], "color": "#8b5cf6"},
    {"id": "18", "name": "Bến Thành - Chợ Hiệp Thành", "price": "6.000đ", "time": "04:50 - 20:30", "stops": ["Bến Thành", "Hai Bà Trưng", "Quang Trung", "Hiệp Thành"], "color": "#ec4899"},
    {"id": "19", "name": "Bến Thành - KCX Linh Trung - ĐHQG", "price": "7.000đ", "time": "05:00 - 20:15", "stops": ["Bến Thành", "Hàng Xanh", "XLHN", "KCX Linh Trung", "ĐHQG"], "color": "#ef4444"},
    {"id": "20", "name": "Bến Thành - Nhà Bè", "price": "6.000đ", "time": "04:20 - 21:00", "stops": ["Bến Thành", "Quận 4", "Huỳnh Tấn Phát", "Nhà Bè"], "color": "#10b981"},
    {"id": "22", "name": "Bến xe Quận 8 - KCN Lê Minh Xuân", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Q8", "Tỉnh lộ 10", "Lê Minh Xuân"], "color": "#10b981"},
    {"id": "23", "name": "Chợ Lớn - Ngã 3 Giồng - Cầu Lớn", "price": "6.000đ", "time": "05:00 - 19:30", "stops": ["Chợ Lớn", "Phan Văn Hớn", "Nguyễn Văn Bứa", "Cầu Lớn"], "color": "#8b5cf6"},
    {"id": "24", "name": "Bến xe Miền Đông - Hóc Môn", "price": "6.000đ", "time": "04:00 - 20:30", "stops": ["Miền Đông", "Bạch Đằng", "Lê Quang Định", "Hóc Môn"], "color": "#10b981"},
    {"id": "25", "name": "Bến xe Quận 8 - KDC Vĩnh Lộc A", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Q8", "Hương lộ 80", "Vĩnh Lộc A"], "color": "#10b981"},
    {"id": "27", "name": "Bến Thành - Âu Cơ - An Sương", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Bến Thành", "Âu Cơ", "Trường Chinh", "An Sương"], "color": "#10b981"},
    {"id": "28", "name": "Bến Thành - Chợ Xuân Thới Thượng", "price": "6.000đ", "time": "05:15 - 19:15", "stops": ["Bến Thành", "CMT8", "Lê Minh Xuân", "Xuân Thới Thượng"], "color": "#10b981"},
    {"id": "29", "name": "Phà Cát Lái - Chợ Nông Sản Thủ Đức", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Cát Lái", "Nguyễn Thị Định", "Lê Văn Việt", "Chợ Đầu Mối"], "color": "#3b82f6"},
    {"id": "30", "name": "Chợ Tân Hương - ĐH Quốc Tế", "price": "7.000đ", "time": "05:00 - 18:30", "stops": ["Tân Hương", "Suối Tiên", "ĐH Quốc Tế"], "color": "#10b981"},

    # --- NHÓM 2: LIÊN KẾT ĐÔNG TÂY & KHU VỰC (31 - 60) ---
    {"id": "31", "name": "KDC Tân Quy - KDC Bình Lợi", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Tân Quy", "Tôn Đức Thắng", "Nơ Trang Long", "Bình Lợi"], "color": "#8b5cf6"},
    {"id": "32", "name": "BX Miền Tây - BX Ngã 4 Ga", "price": "6.000đ", "time": "04:00 - 19:30", "stops": ["Miền Tây", "Lũy Bán Bích", "Phan Huy Ích", "Ngã 4 Ga"], "color": "#10b981"},
    {"id": "33", "name": "BX An Sương - ĐH Quốc Gia", "price": "7.000đ", "time": "04:30 - 21:00", "stops": ["An Sương", "QL1A", "Suối Tiên", "ĐHQG"], "color": "#ef4444"},
    {"id": "34", "name": "Bến Thành - ĐH Công Nghệ Sài Gòn", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Bến Thành", "Quận 8", "Phạm Hùng", "STU"], "color": "#10b981"},
    {"id": "36", "name": "Bến Thành - Thới An", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Bến Thành", "Hai Bà Trưng", "Phan Văn Trị", "Thới An"], "color": "#10b981"},
    {"id": "38", "name": "KDC Tân Quy - Đầm Sen", "price": "6.000đ", "time": "05:15 - 19:00", "stops": ["Tân Quy", "Nguyễn Thị Minh Khai", "Lãnh Binh Thăng", "Đầm Sen"], "color": "#10b981"},
    {"id": "39", "name": "Bến Thành - Võ Văn Kiệt - BX Miền Tây", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Bến Thành", "Võ Văn Kiệt", "Miền Tây"], "color": "#3b82f6"},
    {"id": "41", "name": "BX Miền Tây - Ngã 4 Bốn Xã - An Sương", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Miền Tây", "Hương lộ 2", "An Sương"], "color": "#10b981"},
    {"id": "43", "name": "BX Miền Đông - Phà Cát Lái", "price": "6.000đ", "time": "05:25 - 19:00", "stops": ["Miền Đông", "Hàng Xanh", "Trần Não", "Cát Lái"], "color": "#10b981"},
    {"id": "44", "name": "Cảng Quận 4 - Bình Quới", "price": "6.000đ", "time": "05:15 - 19:30", "stops": ["Cảng Q4", "Tôn Đức Thắng", "Bạch Đằng", "Bình Quới"], "color": "#f59e0b"},
    {"id": "45", "name": "BX Quận 8 - Bến Thành - Chợ Lớn", "price": "6.000đ", "time": "05:30 - 19:30", "stops": ["Q8", "Bến Thành", "Trần Hưng Đạo", "Chợ Lớn"], "color": "#8b5cf6"},
    {"id": "46", "name": "Cảng Quận 4 - Bến Mễ Cốc", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Cảng Q4", "Bến Thành", "Trần Hưng Đạo", "Mễ Cốc"], "color": "#10b981"},
    {"id": "47", "name": "Chợ Lớn - QL50 - Hưng Long", "price": "6.000đ", "time": "05:10 - 19:10", "stops": ["Chợ Lớn", "QL50", "Hưng Long"], "color": "#ef4444"},
    {"id": "48", "name": "Siêu thị SMart - Chợ Hiệp Thành", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Siêu thị SMart", "Phan Văn Trị", "Hiệp Thành"], "color": "#10b981"},
    {"id": "50", "name": "ĐH Bách Khoa - ĐH Quốc Gia", "price": "7.000đ", "time": "05:00 - 18:00", "stops": ["ĐH Bách Khoa", "Điện Biên Phủ", "XLHN", "ĐHQG"], "color": "#3b82f6"},
    {"id": "51", "name": "BX Miền Đông - Bình Hưng Hòa", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Miền Đông", "Phan Đăng Lưu", "Bà Chiểu", "Bình Hưng Hòa"], "color": "#10b981"},
    {"id": "52", "name": "Bến Thành - ĐH Quốc Tế", "price": "7.000đ", "time": "05:30 - 17:30", "stops": ["Bến Thành", "Hàng Xanh", "ĐH Quốc Tế"], "color": "#3b82f6"},
    {"id": "53", "name": "Lê Hồng Phong - ĐH Quốc Gia", "price": "7.000đ", "time": "05:00 - 18:30", "stops": ["Lê Hồng Phong", "Phạm Văn Đồng", "KCX Linh Trung", "ĐHQG"], "color": "#10b981"},
    {"id": "54", "name": "BX Miền Đông - Chợ Lớn", "price": "6.000đ", "time": "04:00 - 19:30", "stops": ["Miền Đông", "Đinh Tiên Hoàng", "3/2", "Chợ Lớn"], "color": "#10b981"},
    {"id": "55", "name": "CV Phần mềm Quang Trung - Khu CNC", "price": "7.000đ", "time": "05:00 - 19:00", "stops": ["Quang Trung", "Tô Ký", "XLHN", "Khu CNC"], "color": "#10b981"},
    {"id": "56", "name": "Chợ Lớn - ĐH Giao thông Vận tải", "price": "6.000đ", "time": "05:00 - 20:30", "stops": ["Chợ Lớn", "Nguyễn Văn Cừ", "Trần Hưng Đạo", "ĐH GTVT"], "color": "#10b981"},
    {"id": "57", "name": "Chợ Phước Bình - THPT Trường Chinh", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Phước Bình", "Đỗ Xuân Hợp", "Lê Văn Việt", "Trường Chinh"], "color": "#10b981"},
    {"id": "58", "name": "BX Ngã 4 Ga - KCN Tân Bình", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Ngã 4 Ga", "Quang Trung", "Âu Cơ", "KCN Tân Bình"], "color": "#10b981"},
    {"id": "59", "name": "BX Quận 8 - BX Ngã 4 Ga", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Q8", "Phạm Hùng", "Nguyễn Thái Sơn", "Ngã 4 Ga"], "color": "#10b981"},
    {"id": "60", "name": "BX An Sương - KCN Vĩnh Lộc", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["An Sương", "QL1A", "KCN Vĩnh Lộc"], "color": "#10b981"},

    # --- NHÓM 3: LIÊN TỈNH ĐỒNG NAI, BÌNH DƯƠNG, LONG AN (60-x, 61-x, 62-x) ---
    {"id": "60-1", "name": "BX Miền Tây - BX Biên Hòa", "price": "12.000đ", "time": "04:45 - 18:30", "stops": ["Miền Tây", "KCN Tân Bình", "An Sương", "Suối Tiên", "Biên Hòa"], "color": "#ef4444"},
    {"id": "60-2", "name": "ĐH Nông Lâm - Phú Túc", "price": "15.000đ", "time": "05:00 - 18:00", "stops": ["Nông Lâm", "QL1A", "Trảng Bom", "Phú Túc"], "color": "#ef4444"},
    {"id": "60-3", "name": "BX Miền Đông - KCN Nhơn Trạch", "price": "15.000đ", "time": "05:00 - 18:00", "stops": ["Miền Đông", "XLHN", "Nhơn Trạch"], "color": "#ef4444"},
    {"id": "60-5", "name": "BX An Sương - BX Biên Hòa", "price": "12.000đ", "time": "05:00 - 18:00", "stops": ["An Sương", "QL1A", "Thủ Đức", "Biên Hòa"], "color": "#ef4444"},
    {"id": "60-7", "name": "BX Miền Đông Mới - BX Biên Hòa", "price": "8.000đ", "time": "05:00 - 18:30", "stops": ["BXMĐ Mới", "Ngã 3 Vũng Tàu", "Biên Hòa"], "color": "#ef4444"},
    {"id": "61-1", "name": "Thủ Đức - Dĩ An", "price": "8.000đ", "time": "05:00 - 18:30", "stops": ["Thủ Đức", "QL1K", "Dĩ An"], "color": "#ef4444"},
    {"id": "61-3", "name": "BX An Sương - Thủ Dầu Một", "price": "12.000đ", "time": "05:00 - 18:00", "stops": ["An Sương", "QL13", "Thủ Dầu Một"], "color": "#ef4444"},
    {"id": "61-4", "name": "Bến Dược - Dầu Tiếng", "price": "10.000đ", "time": "05:30 - 17:30", "stops": ["Bến Dược", "Dầu Tiếng"], "color": "#ef4444"},
    {"id": "61-6", "name": "Bến Thành - KDL Đại Nam", "price": "20.000đ", "time": "05:00 - 18:00", "stops": ["Bến Thành", "Hàng Xanh", "QL13", "Đại Nam"], "color": "#f59e0b"},
    {"id": "61-7", "name": "Bến đò Bình Mỹ - BX Bình Dương", "price": "10.000đ", "time": "05:00 - 18:00", "stops": ["Bình Mỹ", "Cầu Phú Cường", "Bình Dương"], "color": "#ef4444"},
    {"id": "61-8", "name": "BX Miền Tây - KDL Đại Nam", "price": "20.000đ", "time": "05:00 - 18:00", "stops": ["Miền Tây", "An Sương", "Đại Nam"], "color": "#f59e0b"},
    {"id": "62-1", "name": "BX Chợ Lớn - Tân Trụ", "price": "12.000đ", "time": "05:00 - 18:00", "stops": ["Chợ Lớn", "QL1A", "Tân Trụ"], "color": "#ef4444"},
    {"id": "62-2", "name": "BX Chợ Lớn - Ngã 3 Tân Lân", "price": "12.000đ", "time": "05:00 - 18:30", "stops": ["Chợ Lớn", "QL50", "Tân Lân"], "color": "#ef4444"},
    {"id": "62-5", "name": "BX An Sương - Hậu Nghĩa", "price": "15.000đ", "time": "05:00 - 17:00", "stops": ["An Sương", "QL22", "Hậu Nghĩa"], "color": "#ef4444"},
    {"id": "62-6", "name": "BX Chợ Lớn - Hậu Nghĩa", "price": "15.000đ", "time": "05:00 - 17:00", "stops": ["Chợ Lớn", "Tỉnh lộ 10", "Hậu Nghĩa"], "color": "#ef4444"},
    {"id": "62-7", "name": "BX Chợ Lớn - Đức Huệ", "price": "15.000đ", "time": "05:00 - 17:00", "stops": ["Chợ Lớn", "Tỉnh lộ 10", "Đức Huệ"], "color": "#ef4444"},
    {"id": "62-8", "name": "BX Chợ Lớn - Tân An", "price": "12.000đ", "time": "05:00 - 18:30", "stops": ["Chợ Lớn", "QL1A", "Tân An"], "color": "#ef4444"},
    {"id": "62-9", "name": "BX Quận 8 - Gò Công", "price": "15.000đ", "time": "05:00 - 18:00", "stops": ["Q8", "QL50", "Cầu Mỹ Lợi", "Gò Công"], "color": "#ef4444"},
    {"id": "62-10", "name": "BX Chợ Lớn - Thanh Vĩnh Đông", "price": "15.000đ", "time": "05:00 - 17:00", "stops": ["Chợ Lớn", "Thanh Vĩnh Đông"], "color": "#ef4444"},
    {"id": "62-11", "name": "BX Quận 8 - Tân Tập", "price": "15.000đ", "time": "05:00 - 17:00", "stops": ["Q8", "Tân Tập"], "color": "#ef4444"},

    # --- NHÓM 4: TUYẾN 64-99 (NỘI THÀNH & CẦN GIỜ) ---
    {"id": "64", "name": "BX Miền Đông - Đầm Sen", "price": "6.000đ", "time": "05:30 - 19:00", "stops": ["Miền Đông", "Lũy Bán Bích", "Đầm Sen"], "color": "#10b981"},
    {"id": "65", "name": "Bến Thành - CMT8 - An Sương", "price": "6.000đ", "time": "05:00 - 20:30", "stops": ["Bến Thành", "CMT8", "Bảy Hiền", "An Sương"], "color": "#ef4444"},
    {"id": "66", "name": "BX Chợ Lớn - BX An Sương", "price": "6.000đ", "time": "04:50 - 20:00", "stops": ["Chợ Lớn", "An Dương Vương", "Trường Chinh", "An Sương"], "color": "#10b981"},
    {"id": "68", "name": "BX Chợ Lớn - ĐH Tài chính Marketing", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Chợ Lớn", "Trần Xuân Soạn", "UFM"], "color": "#3b82f6"},
    {"id": "69", "name": "Bến Thành - KDC Tân Quy", "price": "6.000đ", "time": "05:15 - 19:30", "stops": ["Bến Thành", "Nguyễn Thị Thập", "Tân Quy"], "color": "#10b981"},
    {"id": "70", "name": "Tân Quy - Bến Súc", "price": "10.000đ", "time": "05:00 - 18:30", "stops": ["Tân Quy", "Tỉnh lộ 15", "Bến Súc"], "color": "#ef4444"},
    {"id": "71", "name": "BX An Sương - Phật Cô Đơn", "price": "6.000đ", "time": "05:20 - 18:30", "stops": ["An Sương", "Vĩnh Lộc", "Phật Cô Đơn"], "color": "#8b5cf6"},
    {"id": "72", "name": "CV 23/9 - Hiệp Phước", "price": "7.000đ", "time": "04:40 - 18:30", "stops": ["CV 23/9", "Nguyễn Hữu Thọ", "Hiệp Phước"], "color": "#10b981"},
    {"id": "73", "name": "Chợ Bình Chánh - KCN Lê Minh Xuân", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Bình Chánh", "KCN Lê Minh Xuân"], "color": "#10b981"},
    {"id": "74", "name": "BX An Sương - BX Củ Chi", "price": "7.000đ", "time": "04:40 - 20:30", "stops": ["An Sương", "QL22", "Củ Chi"], "color": "#ef4444"},
    {"id": "75", "name": "Bến Thành - Cần Giờ", "price": "20.000đ", "time": "07:30 - 16:30", "stops": ["Bến Thành", "Rừng Sác", "Cần Giờ"], "color": "#3b82f6"},
    {"id": "76", "name": "Long Phước - Suối Tiên - Đền Hùng", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Long Phước", "Suối Tiên", "Đền Hùng"], "color": "#10b981"},
    {"id": "77", "name": "Đồng Đen - Cần Giờ", "price": "20.000đ", "time": "07:00 - 16:00", "stops": ["Đồng Đen", "Lý Thường Kiệt", "Phà Bình Khánh", "Cần Giờ"], "color": "#3b82f6"},
    {"id": "78", "name": "Thới An - Hóc Môn", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Thới An", "Lê Văn Khương", "Hóc Môn"], "color": "#10b981"},
    {"id": "79", "name": "BX Củ Chi - Đền Bến Dược", "price": "6.000đ", "time": "05:30 - 17:30", "stops": ["Củ Chi", "Tỉnh lộ 15", "Bến Dược"], "color": "#ef4444"},
    {"id": "81", "name": "BX Chợ Lớn - Lê Minh Xuân", "price": "6.000đ", "time": "04:30 - 19:30", "stops": ["Chợ Lớn", "Tỉnh lộ 10", "Lê Minh Xuân"], "color": "#10b981"},
    {"id": "84", "name": "BX Chợ Lớn - Tân Túc", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Chợ Lớn", "QL1A", "Tân Túc"], "color": "#10b981"},
    {"id": "86", "name": "Bến Thành - ĐH Tôn Đức Thắng", "price": "6.000đ", "time": "05:30 - 18:30", "stops": ["Bến Thành", "Nguyễn Hữu Thọ", "TDTU"], "color": "#10b981"},
    {"id": "87", "name": "BX Củ Chi - An Nhơn Tây", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Củ Chi", "Tỉnh lộ 7", "An Nhơn Tây"], "color": "#10b981"},
    {"id": "88", "name": "Bến Thành - Chợ Long Phước", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Bến Thành", "Đỗ Xuân Hợp", "Long Phước"], "color": "#10b981"},
    {"id": "89", "name": "ĐH Nông Lâm - Bến tàu Hiệp Bình Chánh", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Nông Lâm", "Kha Vạn Cân", "Bến tàu HBC"], "color": "#10b981"},
    {"id": "90", "name": "Phà Bình Khánh - Cần Thạnh", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Bình Khánh", "Rừng Sác", "Cần Thạnh"], "color": "#10b981"},
    {"id": "91", "name": "BX Miền Tây - Chợ Nông Sản Thủ Đức", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Miền Tây", "QL1A", "Chợ Đầu Mối"], "color": "#10b981"},
    {"id": "93", "name": "Bến Thành - ĐH Nông Lâm", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Bến Thành", "Hàng Xanh", "Nông Lâm"], "color": "#10b981"},
    {"id": "94", "name": "BX Chợ Lớn - BX Củ Chi", "price": "10.000đ", "time": "04:45 - 20:30", "stops": ["Chợ Lớn", "Trường Chinh", "Củ Chi"], "color": "#ef4444"},
    {"id": "99", "name": "Chợ Thạnh Mỹ Lợi - ĐH Quốc Gia", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Thạnh Mỹ Lợi", "Lê Văn Việt", "ĐHQG"], "color": "#10b981"},

    # --- NHÓM 5: TUYẾN 100+ & CITY TOUR & HỌC SINH (HS) ---
    {"id": "100", "name": "BX Củ Chi - Cầu Tân Thái", "price": "6.000đ", "time": "05:00 - 19:10", "stops": ["Củ Chi", "Tỉnh lộ 7", "Cầu Tân Thái"], "color": "#10b981"},
    {"id": "101", "name": "BX Chợ Lớn - Chợ Tân Nhựt", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Chợ Lớn", "Tên Lửa", "Tân Nhựt"], "color": "#10b981"},
    {"id": "102", "name": "Bến Thành - BX Miền Tây", "price": "7.000đ", "time": "05:00 - 19:00", "stops": ["Bến Thành", "Nguyễn Văn Linh", "Miền Tây"], "color": "#10b981"},
    {"id": "103", "name": "BX Chợ Lớn - BX Ngã 4 Ga", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Chợ Lớn", "Lý Thường Kiệt", "Ngã 4 Ga"], "color": "#10b981"},
    {"id": "104", "name": "BX An Sương - ĐH Nông Lâm", "price": "6.000đ", "time": "04:40 - 20:00", "stops": ["An Sương", "Quang Trung", "Nông Lâm"], "color": "#10b981"},
    {"id": "107", "name": "BX Củ Chi - Bố Heo", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Củ Chi", "Hương lộ 2", "Bố Heo"], "color": "#10b981"},
    {"id": "109", "name": "Sân bay TSN - Bến Thành", "price": "15.000đ", "time": "05:30 - 23:00", "stops": ["Sân bay TSN", "Nam Kỳ Khởi Nghĩa", "Bến Thành"], "color": "#f59e0b"},
    {"id": "110", "name": "Hiệp Phước - Phước Lộc", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Hiệp Phước", "Nhà Bè", "Phước Lộc"], "color": "#10b981"},
    {"id": "122", "name": "BX An Sương - Tân Quy", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["An Sương", "Tỉnh lộ 8", "Tân Quy"], "color": "#10b981"},
    {"id": "126", "name": "BX Củ Chi - Bình Mỹ", "price": "6.000đ", "time": "05:00 - 18:30", "stops": ["Củ Chi", "Tỉnh lộ 8", "Bình Mỹ"], "color": "#10b981"},
    {"id": "127", "name": "An Thới Đông - Ngã 3 Bà Xán", "price": "6.000đ", "time": "05:30 - 18:00", "stops": ["An Thới Đông", "Cần Giờ", "Bà Xán"], "color": "#10b981"},
    {"id": "128", "name": "Tân Điền - An Nghĩa", "price": "6.000đ", "time": "05:30 - 18:00", "stops": ["Tân Điền", "Cần Giờ", "An Nghĩa"], "color": "#10b981"},
    {"id": "139", "name": "BX Miền Tây - KDC Phú Mỹ", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Miền Tây", "Hồng Bàng", "Phú Mỹ"], "color": "#10b981"},
    {"id": "140", "name": "Bến Thành - KDC Phú Lợi", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Bến Thành", "Phạm Thế Hiển", "Phú Lợi"], "color": "#10b981"},
    {"id": "141", "name": "KDL BCR - KCX Linh Trung 2", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["BCR", "Lò Lu", "Linh Trung 2"], "color": "#10b981"},
    {"id": "144", "name": "BX Miền Tây - Đầm Sen", "price": "6.000đ", "time": "05:30 - 18:30", "stops": ["Miền Tây", "Đầm Sen"], "color": "#10b981"},
    {"id": "145", "name": "BX Chợ Lớn - Chợ Hiệp Thành", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Chợ Lớn", "Hiệp Thành"], "color": "#10b981"},
    {"id": "146", "name": "BX Miền Đông - Chợ Hiệp Thành", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Miền Đông", "Phan Văn Trị", "Hiệp Thành"], "color": "#10b981"},
    {"id": "148", "name": "BX Miền Tây - Gò Vấp", "price": "6.000đ", "time": "05:00 - 19:00", "stops": ["Miền Tây", "Lũy Bán Bích", "Gò Vấp"], "color": "#10b981"},
    {"id": "150", "name": "BX Chợ Lớn - Tân Vạn", "price": "6.000đ", "time": "04:30 - 21:00", "stops": ["Chợ Lớn", "Điện Biên Phủ", "Tân Vạn"], "color": "#ef4444"},
    {"id": "151", "name": "BX Miền Tây - BX An Sương", "price": "6.000đ", "time": "04:30 - 20:30", "stops": ["Miền Tây", "QL1A", "An Sương"], "color": "#10b981"},
    {"id": "152", "name": "KDC Trung Sơn - Sân bay TSN", "price": "5.000đ", "time": "05:15 - 19:00", "stops": ["Trung Sơn", "Bến Thành", "Sân bay TSN"], "color": "#34d399"},
    # Tuyến xe điện VinBus (153-163 & D4)
    {"id": "D4", "name": "VinBus: Vinhomes GP - Bến Thành", "price": "7.000đ", "time": "05:00 - 22:00", "stops": ["Vinhomes GP", "Bến Thành"], "color": "#10b981"},
    {"id": "153", "name": "Bến tàu Bình An - Đường Liên Phường", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Bến tàu Bình An", "Liên Phường"], "color": "#34d399"},
    {"id": "154", "name": "Thạnh Mỹ Lợi - Masteri An Phú", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Thạnh Mỹ Lợi", "Masteri An Phú"], "color": "#34d399"},
    {"id": "155", "name": "Bến Thành - Nhà hát Thành phố", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Bến Thành", "Nhà hát TP"], "color": "#34d399"},
    {"id": "156", "name": "Bến Thành - Ga Hòa Hưng", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Bến Thành", "Ga Sài Gòn"], "color": "#34d399"},
    {"id": "157", "name": "BX Văn Thánh - Chung cư Đức Khải", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Văn Thánh", "Đức Khải"], "color": "#34d399"},
    {"id": "158", "name": "BX Văn Thánh - Cư xá Thanh Đa", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Văn Thánh", "Thanh Đa"], "color": "#34d399"},
    {"id": "159", "name": "Chung cư Ngô Tất Tố - Ngã 4 Hàng Xanh", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Ngô Tất Tố", "Hàng Xanh"], "color": "#34d399"},
    {"id": "160", "name": "Ga Văn Thánh - Vinhomes Central Park", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Văn Thánh", "Vinhomes CP"], "color": "#34d399"},
    {"id": "161", "name": "BX Văn Thánh - BX Ngã 4 Ga", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Văn Thánh", "Ngã 4 Ga"], "color": "#34d399"},
    {"id": "162", "name": "Chung cư Man Thiện - THCS Hoa Lư", "price": "6.000đ", "time": "05:00 - 20:00", "stops": ["Man Thiện", "Hoa Lư"], "color": "#34d399"},
    # City Tour & Học sinh
    {"id": "DL01", "name": "City Tour: Sài Gòn - Gia Định", "price": "150.000đ", "time": "09:00 - 22:00", "stops": ["Nhà thờ Đức Bà", "Bưu điện TP", "Dinh Độc Lập"], "color": "#f59e0b"},
    {"id": "DL02", "name": "City Tour: Sài Gòn - Chợ Lớn", "price": "150.000đ", "time": "09:00 - 18:00", "stops": ["Bến Thành", "Chợ Lớn"], "color": "#f59e0b"},
    {"id": "HS01", "name": "Học sinh: Hà Quang Vóc - THCS Bình Khánh", "price": "Miễn phí", "time": "Giờ học", "stops": ["Hà Quang Vóc", "THCS Bình Khánh"], "color": "#ec4899"},
    {"id": "HS02", "name": "Học sinh: Bà Xán - THCS Bình Khánh", "price": "Miễn phí", "time": "Giờ học", "stops": ["Bà Xán", "THCS Bình Khánh"], "color": "#ec4899"},
]

def get_full_system_instruction():
    """Hàm này ghép nối dữ liệu xe buýt vào prompt để AI học"""
    data_context = "\n\nDỮ LIỆU CÁC TUYẾN XE BUÝT HIỆN CÓ:\n"
    for bus in BUS_DATA:
        data_context += f"- Mã {bus['id']} ({bus['name']}): Giá {bus['price']}, Giờ {bus['time']}, Đi qua: {', '.join(bus['stops'])}\n"
    
    return BOT_PERSONA + data_context
