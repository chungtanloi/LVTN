"""
build_curriculum.py — Curriculum KB v1 (CPA², Tuần 6)

NGUỒN DUY NHẤT của khung CTĐT ngành Công nghệ thông tin, Khoá 49.
Sinh ra hai sản phẩm phái sinh — KHÔNG sửa tay:
    curriculum_cntt_k49.json   bản chép có cấu trúc, mỗi dòng có con trỏ nguồn
    curriculum_cntt_k49.lp     dữ kiện ASP cho clingo

Nguồn: Chương trình đào tạo trình độ đại học ngành Công nghệ thông tin (7480201),
       ban hành theo QĐ 2423/QĐ-ĐHCT ngày 05/6/2023.
       File: LVTN/NiênLuan/ctdt/K49/69_7480201_CongNgheThongTin.pdf, mục 6 "Khung CTĐT".
       Trang 3 (dòng 1–41) CÓ lớp văn bản; trang 4 (dòng 42–78) là ẢNH QUÉT, chép tay
       trên ảnh 200 dpi. Đối chiếu tự động: xem doi_chieu_nguon.py.

Chạy:  python3 build_curriculum.py
Mã thoát 0 = sinh xong và mọi kiểm tra nội tại đạt; 1 = bảng chép có lỗi.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent

META = {
    "ctdt": "cntt_k49",
    "ten": "Kỹ sư Công nghệ thông tin — Khoá 49",
    "nganh_ma": "7480201",
    "van_ban": "qd2423_ctdt",
    "van_ban_ten": "QĐ 2423/QĐ-ĐHCT ngày 05/6/2023 — CTĐT ngành Công nghệ thông tin",
    "file_pdf": "LVTN/NiênLuan/ctdt/K49/69_7480201_CongNgheThongTin.pdf",
    "thoi_gian_dao_tao_nam": 4.5,
    "danh_hieu": "ky_su",
    # dòng "Cộng" của từng khối — chép RIÊNG khỏi các dòng học phần để kiểm tra chéo
    "khoi_khai_bao": {
        "dai_cuong":    {"tong": 56, "bat_buoc": 41, "tu_chon": 15, "trang": 3},
        "co_so_nganh":  {"tong": 46, "bat_buoc": 46, "tu_chon": 0,  "trang": 4},
        "chuyen_nganh": {"tong": 59, "bat_buoc": 38, "tu_chon": 21, "trang": 4},
    },
    "tong_khai_bao": {"tong": 161, "bat_buoc": 125, "tu_chon": 36},
}

# -----------------------------------------------------------------------------
# NHÓM TỰ CHỌN — đọc từ cột "Tự chọn" (ô gộp dọc) của bảng
#   kieu = "tin_chi"   : tích lũy ≥ min TC trong nhóm
#   kieu = "mot_nhanh" : tích lũy ≥ min TC trong ĐÚNG MỘT nhánh (ô ghi "A hoặc B")
# -----------------------------------------------------------------------------
NHOM = {
    "g_gdtc": {
        "khoi": "dai_cuong", "kieu": "tin_chi", "min": 3,
        "o_nguon": "dòng 5, cột Tự chọn ghi '3'; cột Số TC ghi '1+1+1'",
    },
    "g_ngoai_ngu": {
        "khoi": "dai_cuong", "kieu": "mot_nhanh", "min": 10,
        "nhanh": {
            "av": ["XH023", "XH024", "XH025", "XH031", "XH032", "XH033"],
            "pv": ["FL001", "FL002", "FL003", "FL007", "FL008", "FL009"],
        },
        "o_nguon": "dòng 6–17, ô gộp cột Tự chọn ghi '10 AV hoặc PV'",
    },
    "g_xa_hoi": {
        "khoi": "dai_cuong", "kieu": "tin_chi", "min": 2,
        "o_nguon": "dòng 24–30, ô gộp cột Tự chọn ghi '2'",
    },
    "g_chuyen_nganh": {
        "khoi": "chuyen_nganh", "kieu": "mot_nhanh", "min": 6,
        "nhanh": {
            "cn1": ["CT211", "CT297"],
            "cn2": ["CT449", "CT484"],
            "cn3": ["CT522", "CT279"],
        },
        "o_nguon": "dòng 62–67, cột Bắt buộc ghi CN1/CN2/CN3, ô gộp Tự chọn ghi '6 CN1 hoặc CN2 hoặc CN3'",
    },
    "g_tot_nghiep": {
        "khoi": "chuyen_nganh", "kieu": "tin_chi", "min": 15,
        "o_nguon": "dòng 70–78, ô gộp cột Tự chọn ghi '15' — GỒM CẢ CT550E (LVTN) và CT501E (TLTN)",
    },
}

# -----------------------------------------------------------------------------
# DÒNG HỌC PHẦN
#   (tt, mã, tên, TC, cột, LT, TH, tiên quyết, song hành, HK, sao)
#   cột  : "BB" = số ở cột Bắt buộc; hoặc mã nhóm ở NHOM
#   tiên quyết: list mã học phần, hoặc ">=N" (ngưỡng tín chỉ tích lũy — loại T4b)
#   HK   : "I,II,III" ... ; None = "Bố trí theo nhóm ngành"
#   sao  : True nếu tên có (*) = học phần điều kiện
# -----------------------------------------------------------------------------
D, C, N = "dai_cuong", "co_so_nganh", "chuyen_nganh"
ROWS = [
    # ---- Khối kiến thức Giáo dục đại cương (trang 3) -------------------------
    (1,  "QP010E", "Giáo dục quốc phòng và An ninh 1", 2, "BB", 37, 8,  [], [], None, True),
    (2,  "QP011E", "Giáo dục quốc phòng và An ninh 2", 2, "BB", 22, 8,  [], [], None, True),
    (3,  "QP012",  "Giáo dục quốc phòng và An ninh 3", 2, "BB", 24, 21, [], [], None, True),
    (4,  "QP013",  "Giáo dục quốc phòng và An ninh 4", 2, "BB", 4,  56, [], [], None, True),
    (5,  "TC100",  "Giáo dục thể chất 1+2+3",          3, "g_gdtc", 0, 90, [], [], "I,II,III", True),
    (6,  "XH023",  "Anh văn căn bản 1",     4, "g_ngoai_ngu", 60, 0, [], [],        "I,II,III", True),
    (7,  "XH024",  "Anh văn căn bản 2",     3, "g_ngoai_ngu", 45, 0, [], ["XH023"], "I,II,III", True),
    (8,  "XH025",  "Anh văn căn bản 3",     3, "g_ngoai_ngu", 45, 0, [], ["XH024"], "I,II,III", True),
    (9,  "XH031",  "Anh văn tăng cường 1",  4, "g_ngoai_ngu", 60, 0, [], ["XH025"], "I,II,III", True),
    (10, "XH032",  "Anh văn tăng cường 2",  3, "g_ngoai_ngu", 45, 0, [], ["XH031"], "I,II,III", True),
    (11, "XH033",  "Anh văn tăng cường 3",  3, "g_ngoai_ngu", 45, 0, [], ["XH032"], "I,II,III", True),
    (12, "FL001",  "Pháp văn căn bản 1",    4, "g_ngoai_ngu", 60, 0, [], [],        "I,II,III", True),
    (13, "FL002",  "Pháp văn căn bản 2",    3, "g_ngoai_ngu", 45, 0, [], ["FL001"], "I,II,III", True),
    (14, "FL003",  "Pháp văn căn bản 3",    3, "g_ngoai_ngu", 45, 0, [], ["FL002"], "I,II,III", True),
    (15, "FL007",  "Pháp văn tăng cường 1", 4, "g_ngoai_ngu", 60, 0, [], ["FL003"], "I,II,III", True),
    (16, "FL008",  "Pháp văn tăng cường 2", 3, "g_ngoai_ngu", 45, 0, [], ["FL007"], "I,II,III", True),
    (17, "FL009",  "Pháp văn tăng cường 3", 3, "g_ngoai_ngu", 45, 0, [], ["FL008"], "I,II,III", True),
    (18, "ML014",  "Triết học Mác - Lênin",             3, "BB", 45, 0, [],        [], "I,II,III", False),
    (19, "ML016",  "Kinh tế chính trị Mác - Lênin",     2, "BB", 30, 0, ["ML014"], [], "I,II,III", False),
    (20, "ML018",  "Chủ nghĩa xã hội khoa học",         2, "BB", 30, 0, ["ML016"], [], "I,II,III", False),
    (21, "ML019",  "Lịch sử Đảng Cộng sản Việt Nam",    2, "BB", 30, 0, ["ML018"], [], "I,II,III", False),
    (22, "ML021",  "Tư tưởng Hồ Chí Minh",              2, "BB", 30, 0, ["ML019"], [], "I,II,III", False),
    (23, "KL001E", "Pháp luật đại cương",               2, "BB", 30, 0, [],        [], "I,II,III", False),
    (24, "ML007",  "Logic học đại cương",               2, "g_xa_hoi", 30, 0,  [], [], "I,II,III", False),
    (25, "XH028",  "Xã hội học đại cương",              2, "g_xa_hoi", 30, 0,  [], [], "I,II,III", False),
    (26, "XH011",  "Cơ sở văn hóa Việt Nam",            2, "g_xa_hoi", 30, 0,  [], [], "I,II,III", False),
    (27, "XH012",  "Tiếng Việt thực hành",              2, "g_xa_hoi", 30, 0,  [], [], "I,II,III", False),
    (28, "XH014",  "Văn bản và lưu trữ học đại cương",  2, "g_xa_hoi", 30, 0,  [], [], "I,II,III", False),
    (29, "KN001E", "Kỹ năng mềm",                       2, "g_xa_hoi", 20, 20, [], [], "I,II,III", False),
    (30, "KN002E", "Đổi mới sáng tạo và khởi nghiệp",   2, "g_xa_hoi", 20, 20, [], [], "I,II,III", False),
    (31, "TN001",  "Vi - Tích phân A1",                 3, "BB", 45, 0,  [],        [], "I,II,III", False),
    (32, "TN002",  "Vi - Tích phân A2",                 4, "BB", 60, 0,  ["TN001"], [], "I,II,III", False),
    (33, "TN010",  "Xác suất thống kê",                 3, "BB", 45, 0,  [],        [], "I,II,III", False),
    (34, "TN012",  "Đại số tuyến tính và Hình học",     4, "BB", 60, 0,  [],        [], "I,II,III", False),
    (35, "CT100",  "Kỹ năng học đại học",               2, "BB", 20, 20, [],        [], "I,II,III", False),
    (36, "CT200",  "Nền tảng công nghệ thông tin",      4, "BB", 30, 60, [],        [], "I,II,III", False),
    # ---- Khối kiến thức cơ sở ngành (dòng 37–41 trang 3; 42–51 trang 4) -------
    (37, "CT101",  "Lập trình căn bản A",               4, "BB", 30, 60, [],        [],        "I,II", False),
    (38, "CT177",  "Cấu trúc dữ liệu",                  3, "BB", 30, 30, ["CT101"], [],        "I,II", False),
    (39, "CT174",  "Phân tích và thiết kế thuật toán",  3, "BB", 30, 30, ["CT177"], [],        "I,II", False),
    (40, "CT172",  "Toán rời rạc",                      4, "BB", 60, 0,  [],        [],        "I,II", False),
    (41, "CT175",  "Lý thuyết đồ thị",                  3, "BB", 30, 30, ["CT177"], [],        "I,II", False),
    (42, "CT190",  "Nhập môn trí tuệ nhân tạo",         2, "BB", 20, 20, [],        [],        "I,II", False),
    (43, "CT180",  "Cơ sở dữ liệu",                     3, "BB", 30, 30, ["CT177"], [],        "I,II", False),
    (44, "CT182",  "Ngôn ngữ mô hình hóa",              3, "BB", 30, 30, ["CT176"], ["CT180"], "I,II", False),
    (45, "CT296",  "Phân tích và thiết kế hệ thống thông tin", 3, "BB", 30, 30, ["CT180"], [], "I,II", False),
    (46, "CT173",  "Kiến trúc máy tính",                3, "BB", 45, 0,  [],        [],        "I,II", False),
    (47, "CT178",  "Nguyên lý hệ điều hành",            3, "BB", 30, 30, ["CT173"], [],        "I,II", False),
    (48, "CT112",  "Mạng máy tính",                     3, "BB", 30, 30, ["CT178"], [],        "I,II", False),
    (49, "CT176",  "Lập trình hướng đối tượng",         3, "BB", 30, 30, ["CT101"], [],        "I,II", False),
    (50, "CT179",  "Quản trị hệ thống",                 3, "BB", 30, 30, [],        [],        "I,II", False),
    (51, "CT188",  "Nhập môn lập trình web",            3, "BB", 30, 30, [],        [],        "I,II", False),
    # ---- Khối kiến thức chuyên ngành (trang 4) --------------------------------
    (52, "CT271E", "Niên luận cơ sở - CNTT",            3, "BB", 0,  90, ["CT174", "CT176"], [], "I,II", False),
    (53, "CT273",  "Giao diện người - máy",             3, "BB", 30, 30, [],        [], "I,II", False),
    (54, "CT294",  "Máy học ứng dụng",                  3, "BB", 30, 30, [],        [], "I,II", False),
    (55, "CT202",  "Nguyên lý máy học",                 3, "BB", 30, 30, [],        [], "I,II", False),
    (56, "CT467",  "Quản trị dữ liệu",                  3, "BB", 30, 30, ["CT180"], [], "I,II", False),
    (57, "CT293",  "Mạng và truyền thông dữ liệu",      3, "BB", 30, 30, ["CT112"], [], "I,II", False),
    (58, "CT275",  "Công nghệ Web",                     3, "BB", 30, 30, ["CT188"], [], "I,II", False),
    (59, "CT300",  "Phát triển phần mềm",               3, "BB", 30, 30, ["CT176"], [], "I,II", False),
    (60, "CT223",  "Quản lý dự án phần mềm",            3, "BB", 30, 30, [],        [], "I,II", False),
    (61, "CT222",  "An toàn hệ thống",                  3, "BB", 30, 30, [],        [], "I,II", False),
    (62, "CT211",  "An ninh mạng",                      3, "g_chuyen_nganh", 30, 30, [], [], "I,II", False),
    (63, "CT297",  "Pháp y máy tính",                   3, "g_chuyen_nganh", 30, 30, [], [], "I,II", False),
    (64, "CT449",  "Phát triển ứng dụng Web",           3, "g_chuyen_nganh", 30, 30, [], [], "I,II", False),
    (65, "CT484",  "Phát triển ứng dụng di động",       3, "g_chuyen_nganh", 30, 30, [], [], "I,II", False),
    (66, "CT522",  "Nền tảng về internet vạn vật",      3, "g_chuyen_nganh", 30, 30, [], [], "I,II", False),
    (67, "CT279",  "Blockchain",                        3, "g_chuyen_nganh", 30, 30, [], [], "I,II", False),
    (68, "CT466E", "Niên luận - CNTT",                  3, "BB", 0, 90,  ">=80",  [], "I,II", False),
    (69, "CT518E", "Thực tập doanh nghiệp - CNTT",      5, "BB", 0, 150, ">=125", [], "III",  False),
    (70, "CT550E", "Luận văn tốt nghiệp - CNTT",        15, "g_tot_nghiep", 0, 450, ">=120", [], "I,II", False),
    (71, "CT501E", "Tiểu luận tốt nghiệp - CNTT",       6,  "g_tot_nghiep", 0, 180, ">=120", [], "I,II", False),
    (72, "CT478",  "Trung tâm dữ liệu",                 3, "g_tot_nghiep", 30, 30, [], [], "I,II", False),
    (73, "CT283",  "Hệ thống chịu lỗi",                 3, "g_tot_nghiep", 30, 30, [], [], "I,II", False),
    (74, "CT233",  "Điện toán đám mây",                 3, "g_tot_nghiep", 30, 30, [], [], "I,II", False),
    (75, "CT482",  "Xử lý dữ liệu lớn",                 3, "g_tot_nghiep", 30, 30, [], [], "I,II", False),
    (76, "CT210",  "Thị giác máy tính",                 3, "g_tot_nghiep", 30, 30, [], [], "I,II", False),
    (77, "CT219",  "Xử lý ngôn ngữ tự nhiên",           3, "g_tot_nghiep", 30, 30, [], [], "I,II", False),
    (78, "CT312",  "Khai khoáng dữ liệu",               3, "g_tot_nghiep", 30, 30, [], [], "I,II", False),
]


def khoi_of(tt):
    return D if tt <= 36 else (C if tt <= 51 else N)


def loai_dieu_kien(ma):
    """(*) → loại học phần điều kiện theo QĐ3266 Điều 7 k.6"""
    if ma.startswith("QP"):
        return "gdqp"
    if ma.startswith("TC1"):
        return "gdtc"
    if ma.startswith(("XH02", "XH03", "FL")):
        return "ngoai_ngu_cb"
    return None


def ngon_ngu(ma):
    """Ngôn ngữ của HP ngoại ngữ căn bản — QĐ5339 Đ3 k5: điểm a Anh văn, điểm b Pháp văn"""
    if ma.startswith(("XH02", "XH03")):
        return "anh"
    if ma.startswith("FL"):
        return "phap"
    return None


HK_MAP = {"I": 1, "II": 2, "III": 3}


# =============================================================================
# KIỂM TRA NỘI TẠI CỦA BẢN CHÉP — chạy TRƯỚC khi sinh bất cứ thứ gì
# =============================================================================
def kiem_tra(rows):
    loi = []
    ma_set = [r[1] for r in rows]
    if len(ma_set) != len(set(ma_set)):
        loi.append("mã học phần trùng")
    if [r[0] for r in rows] != list(range(1, 79)):
        loi.append("số thứ tự không liền 1..78")
    ma = set(ma_set)
    for r in rows:
        tt, m, _, tc, cot, lt, th, tq, sh, hk, sao = r
        if cot != "BB" and cot not in NHOM:
            loi.append(f"dòng {tt}: cột '{cot}' không phải BB hay nhóm đã khai báo")
        for p in (tq if isinstance(tq, list) else []) + sh:
            if p not in ma:
                loi.append(f"dòng {tt}: {m} tham chiếu {p} không có trong CTĐT")
        if sao and not loai_dieu_kien(m):
            loi.append(f"dòng {tt}: {m} có (*) nhưng không xác định được loại điều kiện")
        # quy ước ĐHCT: 1 TC = 15 tiết LT = 30 tiết TH (kiểm tra mềm, không áp cho
        # QP, GDTC, niên luận, thực tập, LVTN — những dòng có quy đổi riêng)
        if not sao and lt + th / 2 != tc * 15 and m not in ("CT271E", "CT466E", "CT518E",
                                                            "CT550E", "CT501E"):
            loi.append(f"dòng {tt}: {m} {tc} TC nhưng LT={lt}, TH={th} (≠ {tc}×15 giờ quy đổi)")
    # nhánh của nhóm "mot_nhanh" phải trùng đúng tập dòng có cột = nhóm đó
    for g, spec in NHOM.items():
        dong = {r[1] for r in rows if r[4] == g}
        if spec["kieu"] == "mot_nhanh":
            nh = set().union(*map(set, spec["nhanh"].values()))
            if nh != dong:
                loi.append(f"{g}: nhánh {sorted(nh)} ≠ dòng {sorted(dong)}")
        if not dong:
            loi.append(f"{g}: nhóm rỗng")
    # tổng theo khối phải khớp dòng "Cộng" chép riêng
    for k, kb in META["khoi_khai_bao"].items():
        bb = sum(r[3] for r in rows if khoi_of(r[0]) == k and r[4] == "BB")
        tcn = sum(s["min"] for s in NHOM.values() if s["khoi"] == k)
        if (bb, tcn, bb + tcn) != (kb["bat_buoc"], kb["tu_chon"], kb["tong"]):
            loi.append(f"khối {k}: tính được BB={bb}, TC={tcn}, tổng={bb+tcn}; "
                       f"dòng Cộng ghi {kb}")
    t = META["tong_khai_bao"]
    s_kb = {x: sum(v[x] for v in META["khoi_khai_bao"].values())
            for x in ("tong", "bat_buoc", "tu_chon")}
    if s_kb != t:
        loi.append(f"ba dòng Cộng {s_kb} không khớp dòng Tổng cộng {t}")
    # đồ thị tiên quyết + song hành phải là DAG
    ke = {r[1]: (r[7] if isinstance(r[7], list) else []) + r[8] for r in rows}
    trang_thai = {}

    def dfs(u, path):
        trang_thai[u] = 1
        for v in ke[u]:
            if trang_thai.get(v) == 1:
                loi.append("chu trình: " + " → ".join(path + [v]))
            elif v not in trang_thai:
                dfs(v, path + [v])
        trang_thai[u] = 2
    for u in ke:
        if u not in trang_thai:
            dfs(u, [u])
    return loi


def q(s):
    return '"' + s.replace('"', '\\"') + '"'


def sinh_lp(rows):
    L = []
    w = L.append
    w("%" * 79)
    w("%% curriculum_cntt_k49.lp — SINH TỰ ĐỘNG bởi build_curriculum.py. KHÔNG SỬA TAY.")
    w(f"%% Nguồn: {META['van_ban_ten']}")
    w(f"%%        {META['file_pdf']} — mục 6, trang 3–4")
    w("%% Dùng kèm: curriculum_schema.lp (ngữ nghĩa nhóm, độc lập ngành/khoá)")
    w("%" * 79)
    w("")
    w(f"ctdt({META['ctdt']}).  nganh_ma({q(META['nganh_ma'])}).  danh_hieu({META['danh_hieu']}).")
    w(f"van_ban_ctdt({META['van_ban']}).")
    w("")
    w("%% --- Thời gian đào tạo 4,5 năm → QĐ3266 Điều 5: tối đa 9 năm (18 nửa năm) ---")
    w("thiet_ke_nam2(9).")
    w("khoa_tu_k45. khoa_tu_k47. khoa_den_k49.")
    w("")
    w("%% --- Dòng 'Cộng' của CTĐT, chép riêng để kiểm tra chéo với từng dòng ---------")
    t = META["tong_khai_bao"]
    w(f"tc_toi_thieu_ctdt({t['tong']}).  tc_bat_buoc_ctdt({t['bat_buoc']}).  "
      f"tc_tu_chon_ctdt({t['tu_chon']}).")
    for k, kb in META["khoi_khai_bao"].items():
        w(f"khoi({k}, {kb['tong']}, {kb['bat_buoc']}, {kb['tu_chon']}).")
    w("")
    w("%% --- Nhóm tự chọn ----------------------------------------------------------")
    for g, s in NHOM.items():
        w(f"nhom({g}).  nhom_kieu({g},{s['kieu']}).  nhom_min_tc({g},{s['min']}).  "
          f"nhom_khoi({g},{s['khoi']}).")
        if s["kieu"] == "mot_nhanh":
            for b, lst in s["nhanh"].items():
                w(f"nhanh({g},{b}).  " + " ".join(f"thuoc_nhanh({g},{b},{q(c)})." for c in lst))
    w("")
    w("%% --- Học phần: course/2, ten/2, thuoc_khoi/2, ctdt_src/3 --------------------")
    for r in rows:
        tt, m, ten, tc, cot, lt, th, tq, sh, hk, sao = r
        k = khoi_of(tt)
        trang = 3 if tt <= 41 else 4
        parts = [f"course({q(m)},{tc}).", f"ten({q(m)},{q(ten)}).",
                 f"thuoc_khoi({q(m)},{k}).", f"ctdt_src({q(m)},{trang},{tt})."]
        if cot == "BB":
            parts.append(f"bat_buoc({q(m)}).")
        elif NHOM[cot]["kieu"] == "tin_chi":
            parts.append(f"thuoc_nhom({cot},{q(m)}).")
        if sao:
            parts.append(f"loai_hp({q(m)},{loai_dieu_kien(m)}).")
            if ngon_ngu(m):
                parts.append(f"ngon_ngu_hp({q(m)},{ngon_ngu(m)}).")
        if isinstance(tq, list):
            parts += [f"tien_quyet({q(m)},{q(p)})." for p in tq]
        else:
            parts.append(f"tien_quyet_tc({q(m)},{int(tq[2:])}).")
        parts += [f"song_hanh({q(m)},{q(p)})." for p in sh]
        if hk:
            parts += [f"mo_hk({q(m)},{HK_MAP[x]})." for x in hk.split(",")]
        else:
            parts.append(f"mo_hk_bo_tri_rieng({q(m)}).")
        w(" ".join(parts))
    w("")
    w("%% --- Hình thức cuối khoá (QĐ3266 Điều 31) -----------------------------------")
    w('hinh_thuc_cuoi_khoa("CT550E", luan_van).  hinh_thuc_cuoi_khoa("CT501E", tieu_luan).')
    w("")
    w("%% --- TÊN GỌI TƯƠNG THÍCH với ctdt_cntt_k49.lp của Tuần 5 (ca C34–C36) --------")
    w("chon_cn(B)          :- dat_nhanh(g_chuyen_nganh,B).")
    w("dat_nhom_cn         :- dat_nhom(g_chuyen_nganh).")
    w("nhieu_hon_mot_cn    :- dat_nhanh(g_chuyen_nganh,B1), dat_nhanh(g_chuyen_nganh,B2), B1 != B2.")
    w('du_dk_tin_chi_lam_lvtn :- du_dk_tc("CT550E").')
    w('chi_mo_hk(C,K)      :- mo_hk(C,K), not mo_hk(C,K2) : mo_hk(C,K2), K2 != K.')
    return "\n".join(L) + "\n"


def sinh_json(rows):
    out = {"meta": META, "nhom": NHOM, "hoc_phan": []}
    for r in rows:
        tt, m, ten, tc, cot, lt, th, tq, sh, hk, sao = r
        out["hoc_phan"].append({
            "tt": tt, "ma": m, "ten": ten, "tin_chi": tc, "khoi": khoi_of(tt),
            "cot": cot, "lt": lt, "th": th,
            "tien_quyet": tq if isinstance(tq, list) else [],
            "tien_quyet_tc": None if isinstance(tq, list) else int(tq[2:]),
            "song_hanh": sh, "hk": hk.split(",") if hk else None,
            "dieu_kien": loai_dieu_kien(m) if sao else None,
            "trang": 3 if tt <= 41 else 4,
            "nguon_trang": "lớp văn bản" if tt <= 41 else "ảnh quét — chép tay",
        })
    return out


def main():
    loi = kiem_tra(ROWS)
    if loi:
        print("BẢN CHÉP CÓ LỖI — không sinh file:")
        for x in loi:
            print("  ·", x)
        return 1
    (HERE / "curriculum_cntt_k49.lp").write_text(sinh_lp(ROWS), encoding="utf-8")
    (HERE / "curriculum_cntt_k49.json").write_text(
        json.dumps(sinh_json(ROWS), ensure_ascii=False, indent=1), encoding="utf-8")
    nbb = sum(1 for r in ROWS if r[4] == "BB")
    print(f"OK — 78 dòng, {nbb} học phần bắt buộc, {len(NHOM)} nhóm tự chọn; "
          f"ba khối cộng đúng 56/46/59 = 161 TC.")
    print("Đã sinh: curriculum_cntt_k49.lp, curriculum_cntt_k49.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
