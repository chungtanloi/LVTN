"""
kb.py — Tri thức nền dùng chung cho 3 prototype solver (Tuần 4, giai đoạn Khảo sát CPA²).
Dữ liệu lấy từ NiênLuan/core/constants.py và academiq_ctdt_mysql.sql (CTĐT CNTT, ĐHCT).
Đây là bản THU NHỎ có chủ đích: đủ để đo tính khả thi của solver, không phải KB đầy đủ.

ĐÍNH CHÍNH TUẦN 6 (đối chiếu với khung CTĐT CNTT K49 thật — xem ERRATA_Tuan6.md):
  · CT466E là NIÊN LUẬN 3 TC (tiên quyết ≥80 TC), không phải luận văn. Luận văn là
    CT550E 15 TC (≥120 TC) — và nó nằm trong NHÓM TỰ CHỌN 15 TC, không phải bắt buộc.
  · K49 dùng mã CT172, CT190 (không có hậu tố E).
  · Nhóm "10 chọn 2" không tồn tại. Các HP CT203E, CT280, CT282E, CT299, CT291, CT295
    không có trong CTĐT CNTT K49. Nhóm dưới đây dùng 7 HP tự chọn 3 TC THẬT của nhóm
    tốt nghiệp, giữ dạng đếm-môn "chọn 2" chỉ để prototype chạy được — cấu trúc thật
    (nhóm đếm tín chỉ, nhóm một-nhánh CN1/CN2/CN3) nằm ở w6_curriculum/.
  · Tiên quyết: bỏ các cạnh không có trong CTĐT K49 (CT294←CT190E, CT312←CT180, …);
    CT182 có tiên quyết CT176 và SONG HÀNH CT180 (không phải tiên quyết kép);
    CT271E ← CT174, CT176.
  · WARNING_TERM_GPA 1,20 → 1,00 (0,80 ở HK đầu khoá) theo QĐ3266 Điều 18 k.2 đ.a.
"""

# --- Học phần: mã -> (tên, số tín chỉ, loại) -----------------------------------
COURSES = {
    "CT101":  ("Lập trình căn bản A", 4, "required"),
    "CT172":  ("Toán rời rạc", 4, "required"),
    "CT173":  ("Kiến trúc máy tính", 3, "required"),
    "CT176":  ("Lập trình hướng đối tượng", 3, "required"),
    "CT177":  ("Cấu trúc dữ liệu", 3, "required"),
    "CT178":  ("Nguyên lý hệ điều hành", 3, "required"),
    "CT180":  ("Cơ sở dữ liệu", 3, "required"),
    "CT112":  ("Mạng máy tính", 3, "required"),
    "CT174":  ("Phân tích và thiết kế thuật toán", 3, "required"),
    "CT175":  ("Lý thuyết đồ thị", 3, "required"),
    "CT182":  ("Ngôn ngữ mô hình hóa", 3, "required"),
    "CT296":  ("Phân tích và thiết kế HTTT", 3, "required"),
    "CT190":  ("Nhập môn trí tuệ nhân tạo", 2, "required"),
    "CT294":  ("Máy học ứng dụng", 3, "required"),
    "CT271E": ("Niên luận cơ sở - CNTT", 3, "required"),
    "CT466E": ("Niên luận - CNTT", 3, "required"),
    "CT550E": ("Luận văn tốt nghiệp - CNTT", 15, "thesis"),
    "TN001":  ("Vi - Tích phân A1", 3, "required"),
    "TN002":  ("Vi - Tích phân A2", 4, "required"),
    "TN010":  ("Xác suất thống kê", 3, "required"),
    # nhóm tự chọn (N-of-M) — 7 HP 3 TC THẬT của nhóm tốt nghiệp 15 TC (CTĐT dòng 72–78)
    "CT478":  ("Trung tâm dữ liệu", 3, "elective"),
    "CT283":  ("Hệ thống chịu lỗi", 3, "elective"),
    "CT233":  ("Điện toán đám mây", 3, "elective"),
    "CT482":  ("Xử lý dữ liệu lớn", 3, "elective"),
    "CT210":  ("Thị giác máy tính", 3, "elective"),
    "CT219":  ("Xử lý ngôn ngữ tự nhiên", 3, "elective"),
    "CT312":  ("Khai khoáng dữ liệu", 3, "elective"),
}

CREDITS = {c: v[1] for c, v in COURSES.items()}
THESIS = "CT550E"   # Tuần 4 ghi nhầm CT466E

# --- Tiên quyết (nguồn: core/constants.py PREREQS) ------------------------------
PREREQS = {             # đúng theo cột "Học phần tiên quyết" của CTĐT K49
    "CT177":  ["CT101"],
    "CT174":  ["CT177"],
    "CT175":  ["CT177"],
    "CT176":  ["CT101"],
    "CT180":  ["CT177"],
    "CT182":  ["CT176"],          # CT180 là SONG HÀNH, không phải tiên quyết
    "CT296":  ["CT180"],
    "CT178":  ["CT173"],
    "CT112":  ["CT178"],
    "CT271E": ["CT174", "CT176"],
}

# --- Nhóm tự chọn N-of-M --------------------------------------------------------
ELECTIVE_GROUPS = {
    # tên nhóm: (danh sách môn, số môn tối thiểu phải đạt) — ĐƠN GIẢN HOÁ, xem đầu file
    "TC_TOT_NGHIEP_RUT_GON": (
        ["CT478", "CT283", "CT233", "CT482", "CT210", "CT219", "CT312"],
        2,
    ),
}

# --- Tham số quy chế (QĐ3266 — bản THU NHỎ, cần đối chiếu lại toàn văn) ----------
GRADE_POINTS = {"A": 4.0, "B+": 3.5, "B": 3.0, "C+": 2.5,
                "C": 2.0, "D+": 1.5, "D": 1.0, "F": 0.0}
PASSING_GRADES = {"A", "B+", "B", "C+", "C", "D+", "D"}

MAX_CREDITS_PER_TERM = 20      # trần tín chỉ mỗi HK chính
MIN_CREDITS_TO_GRADUATE = 120  # rút gọn cho instance thử nghiệm
MIN_CGPA_TO_GRADUATE = 2.00
WARNING_TERM_GPA = 1.00        # QĐ3266 Đ.18 k.2 đ.a (0,80 ở HK đầu khoá) — Tuần 4 ghi nhầm 1,20

# --- Hồ sơ sinh viên thử nghiệm -------------------------------------------------
# Trạng thái mỗi học phần: passed / failed / exempted / substituted / unknown
STUDENT_A = {   # đủ điều kiện — dùng kiểm tra nhánh TRUE
    "id": "SV-A",
    "records": {
        "CT101": "A", "CT177": "A", "CT176": "A", "CT180": "B",
        "CT172": "B+", "CT173": "C+", "CT178": "B", "CT112": "B",
        "CT174": "B", "CT175": "B+", "CT182": "C+", "CT296": "B",
        "CT190": "A", "CT294": "B+", "CT271E": "A", "CT466E": "A",
        "TN001": "A", "TN002": "A", "TN010": "A",
        "CT312": "B", "CT219": "B+",
    },
    "extra_credits_passed": 68,   # khối đại cương/khác đã đạt, không mô hình chi tiết
    "exemptions": {},
    "substitutions": {},
    "unknown": [],
}

STUDENT_B = {   # thiếu dữ liệu 2 môn tự chọn — dùng kiểm tra nhánh UNKNOWN
    "id": "SV-B",
    "records": {
        "CT101": "A", "CT177": "B+", "CT176": "B", "CT180": "B",
        "CT172": "B", "CT173": "C", "CT178": "C+", "CT112": "C+",
        "CT174": "C+", "CT175": "B", "CT182": "C", "CT296": "C+",
        "CT190": "B", "CT294": "C+", "CT271E": "B", "CT466E": "B",
        "TN001": "B", "TN002": "C+", "TN010": "B",
    },
    "extra_credits_passed": 62,
    "exemptions": {},
    "substitutions": {},
    "unknown": ["CT312", "CT219"],   # điểm chưa cập nhật
}

STUDENT_C = {   # rớt CT177 — dùng cho truy vấn phản thực (lập kế hoạch)
    "id": "SV-C",
    "records": {
        "CT101": "B", "CT177": "F", "CT173": "B", "CT190": "B",
        "TN001": "B", "TN002": "C+",
    },
    "extra_credits_passed": 30,
    "exemptions": {"TN010": "CHUNG_CHI_TUONG_DUONG"},
    "substitutions": {},
    "unknown": [],
}
