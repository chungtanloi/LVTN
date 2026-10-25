"""
validate_api.py — kiểm chứng dịch vụ Python (FastAPI) bọc lõi CPA² cho website (Mốc 1). Không cần mạng, không cần khoá thật.

  A. Sức khoẻ + xác thực: /health mở; /v1/* cần X-API-Key; server chưa cấu hình khoá → 503 (đóng, không mở)
  B. Hồ sơ vào: kiểm schema + phạm vi CNTT K49 + tín chỉ; K51/ngành khác → khong_ho_tro_ho_so; không nhận đường dẫn file
  C. /v1/advice trùng với CLI (prototype.answer + grounded_answer) trên ma trận hồ sơ × câu hỏi: TRUE, FALSE, UNKNOWN,
     đã hoàn thành, ngoài phạm vi, phản thực tế, hồ sơ mâu thuẫn; lỗi kỹ thuật KHÔNG thành kết luận học vụ
  D. /v1/lookup, /v1/recommendations trùng với mô-đun gốc
  E. /v1/ocr: ảnh tổng hợp → hồ sơ NHÁP (chưa xác minh) + báo cáo; giới hạn số file / kích thước / không phải ảnh
  F. Giới hạn body (413, kể cả chunked), không log nội dung hồ sơ, không trộn dữ liệu giữa các yêu cầu song song
  G. Phiên bản KB
  H. Hồ sơ độc hại: tiêm ASP (mã học phần, khong_tinh_tich_luy, ma_hp, số, chứng chỉ), NaN/Infinity, quá nhiều mâu thuẫn, UNSAT
  I. Hình dạng phản hồi thống nhất, xác thực trước parse, Cache-Control, không phản hồi lại dữ liệu người dùng
  J. Bể tiến trình: hết giờ → giết, quá tải → 503, tiến trình chết, lõi thật trong tiến trình con
  K. Review bảo mật vòng 2: trần danh sách, ngoại lệ chưa bắt, dọn bể khi khởi động hỏng, tiến trình rảnh chết, bể OCR riêng,
     UNSAT nhất quán ở /v1/recommendations, tên trường thật không bị che, khoá trùng, tiến trình cháu mồ côi, giới hạn RAM, biến môi trường

Chạy (cần fastapi + httpx; xem requirements-dev.txt):  python validate_api.py [--nhanh]     (--nhanh bỏ OCR ảnh)
"""
import copy, json, logging, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
CPA2 = Path(os.environ.get("CPA2_ROOT") or HERE.parent.parent / "CPA2_KhaoSat")
sys.path.insert(0, str(HERE))
for d in ("w12_integration", "w14_rag", "w19_recommendation", "w15_ocr", "w7_student_facts"):
    sys.path.insert(0, str(CPA2 / d))

from fastapi.testclient import TestClient

from cpa2_api import cau_hinh, ho_so as HS
from cpa2_api.main import tao_app

KHOA = "khoa-thu-nghiem-123"
HS_DIR = CPA2 / "w7_student_facts" / "students"
ok_all = True


def check(cond, msg):
    global ok_all
    print(f"  [{'OK' if cond else 'FAIL'}] {msg}")
    ok_all = ok_all and bool(cond)
    return cond


def ho_so(ten):
    return json.loads((HS_DIR / f"{ten}.json").read_text(encoding="utf-8"))


def may_khach(**kw):
    kw.setdefault("so_worker", 0)            # 0 = chạy trong tiến trình (nhanh, mock được); phần J kiểm bể tiến trình thật
    cfg = cau_hinh.CauHinh(api_key=KHOA, **kw)
    return TestClient(tao_app(cfg)), cfg


H = {"X-API-Key": KHOA}


def phan_A():
    print("A. SỨC KHOẺ + XÁC THỰC")
    c, _ = may_khach()
    r = c.get("/health")
    check(r.status_code == 200 and r.json()["trang_thai"] == "ok" and "kb" in r.json(), f"/health mở, không cần khoá ({r.status_code})")
    body = {"ho_so": ho_so("sv_lvtn"), "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}
    for hd, mong in (({}, 401), ({"X-API-Key": "sai"}, 401), ({"X-API-Key": ""}, 401), (H, 200)):
        r = c.post("/v1/advice", json=body, headers=hd)
        check(r.status_code == mong, f"/v1/advice với khoá {hd or 'không có'} → {r.status_code} (mong {mong})")
    check(c.post("/v1/advice", json=body).json().get("trang_thai") == "khong_xac_thuc", "401 có trang_thai khong_xac_thuc (không lộ chi tiết)")
    c2 = TestClient(tao_app(cau_hinh.CauHinh(api_key=None, so_worker=0)))
    r = c2.post("/v1/advice", json=body, headers=H)
    check(r.status_code == 503 and r.json()["trang_thai"] == "loi_he_thong", f"server chưa đặt khoá → 503, không mở công khai ({r.status_code})")
    check(c2.get("/health").status_code == 200, "/health vẫn trả lời khi chưa đặt khoá (để Render kiểm sức khoẻ)")
    for path in ("/v1/lookup", "/v1/recommendations", "/v1/ocr"):
        check(c.post(path).status_code == 401, f"{path} cần khoá")


def phan_B():
    print("B. HỒ SƠ VÀO")
    base = ho_so("sv_lvtn")
    r = HS.kiem_tra(base)
    check(not r.loi and r.khong_ho_tro is None, f"sv_lvtn hợp lệ ({r.loi[:1]}, {r.khong_ho_tro})")
    for ten, sua, mong in [("K51", {"cohort": "K51"}, "K49"), ("ngành khmt", {"major": "khmt"}, "CNTT"),
                           ("ctdt khác", {"ctdt": "cntt_k51"}, "cntt_k49")]:
        j = {**copy.deepcopy(base), **sua}
        r = HS.kiem_tra(j)
        check(r.khong_ho_tro and mong in r.khong_ho_tro, f"{ten} → khong_ho_tro nêu phạm vi ({r.khong_ho_tro})")
    j = copy.deepcopy(base); j.pop("grades")
    r = HS.kiem_tra(j)
    check(r.loi and "grades" in json.dumps(r.loi, ensure_ascii=False), f"thiếu grades → loi_dau_vao ({r.loi[:1]})")
    j = copy.deepcopy(base); j["grades"]["CT177"]["thang10"] = 150
    r = HS.kiem_tra(j)
    check(r.loi and "CT177" in json.dumps(r.loi, ensure_ascii=False), f"điểm 150 → loi_dau_vao nêu CT177 ({r.loi[:1]})")
    j = copy.deepcopy(base); j["grades"]["CT177"]["credits"] = 5
    r = HS.kiem_tra(j)
    check(r.loi and "CT177" in json.dumps(r.loi, ensure_ascii=False) and "tín chỉ" in json.dumps(r.loi, ensure_ascii=False),
          f"tín chỉ không khớp CTĐT → loi_dau_vao ({r.loi[:1]})")
    j = copy.deepcopy(base); j["grades"]["ZZ999"] = {"code": "ZZ999", "credits": 3, "thang10": 80, "letter": "B+", "status": "passed"}
    r = HS.kiem_tra(j)
    check(not r.loi and any("ZZ999" in x for x in r.canh_bao), f"mã ngoài CTĐT → cảnh báo, không chặn ({r.canh_bao[:1]})")
    j = copy.deepcopy(base); j["grades"]["CT178"]["code"] = "CT179"
    r = HS.kiem_tra(j)
    check(r.loi and "CT178" in json.dumps(r.loi, ensure_ascii=False), f"khoá bản ghi ≠ mã học phần → loi_dau_vao ({r.loi[:1]})")
    j = copy.deepcopy(base)
    for i in range(450):
        j["grades"][f"XX{i:03d}"] = {"code": f"XX{i:03d}", "credits": 1, "thang10": 50, "letter": "D+", "status": "passed"}
    check(HS.kiem_tra(j).loi, "hơn 400 học phần → loi_dau_vao (chặn hồ sơ phình to)")
    j = {**copy.deepcopy(base), "mat_khau": "bi-mat", "student_path": "/etc/passwd"}
    r = HS.kiem_tra(j)
    check("mat_khau" not in r.ho_so and "student_path" not in r.ho_so and r.canh_bao,
          f"trường lạ bị loại khỏi hồ sơ chuẩn hoá (không chuyển tiếp), có cảnh báo ({sorted(r.ho_so)[:3]}…)")
    check(HS.kiem_tra("không phải dict").loi and HS.kiem_tra(None).loi, "đầu vào không phải đối tượng → loi_dau_vao")
    goc = json.dumps(base, sort_keys=True)
    HS.kiem_tra(base)
    check(json.dumps(base, sort_keys=True) == goc, "kiem_tra không sửa hồ sơ của nơi gọi")
    c, _ = may_khach()
    r = c.post("/v1/advice", json={"ho_so": "/etc/passwd", "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H)
    check(r.status_code == 422, f"ho_so là chuỗi (đường dẫn) → 422, không đọc file ({r.status_code})")
    r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "x", "student_path": "/etc/passwd"}, headers=H)
    check(r.status_code == 422, f"trường thừa student_path → 422 (extra=forbid) ({r.status_code})")
    r = c.post("/v1/advice", json={"ho_so": {**base, "cohort": "K51"}, "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H)
    j = r.json()
    check(r.status_code == 200 and j["trang_thai"] == "khong_ho_tro_ho_so" and j["ket_luan"] is None,
          f"K51 qua API → khong_ho_tro_ho_so, ket_luan null ({j.get('trang_thai')}, {j.get('ket_luan')})")
    r = c.post("/v1/advice", json={"ho_so": {"student_id": "sv_x"}, "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H)
    j = r.json()
    check(r.status_code == 200 and j["trang_thai"] == "loi_dau_vao" and j["ket_luan"] is None and j["chi_tiet"],
          f"hồ sơ sai schema qua API → loi_dau_vao kèm chi_tiet ({j.get('trang_thai')})")
    for q in ("", "x" * 501):
        check(c.post("/v1/advice", json={"ho_so": base, "cau_hoi": q}, headers=H).status_code == 422, f"câu hỏi độ dài {len(q)} → 422")


MA_TRAN = [("sv_lvtn", "em đủ điều kiện tốt nghiệp chưa?"), ("sv_tron_ngoai_ngu", "em đủ điều kiện tốt nghiệp chưa?"),
           ("sv_5hp", "em đủ điều kiện tốt nghiệp chưa?"), ("sv_lvtn", "Em đăng ký CT180 được không?"),
           ("sv_lvtn", "Nếu tốt nghiệp, em xếp hạng gì?"), ("sv_lvtn", "Em có đủ điều kiện làm luận văn không?"),
           ("sv_tltn", "Em có đủ điều kiện làm tiểu luận không?"), ("sv_lvtn", "kỳ này em nên đăng ký môn gì?"),
           ("sv_lvtn", "em còn thiếu môn gì"), ("sv_tron_ngoai_ngu", "em còn thiếu môn gì"),
           ("sv_tron_ngoai_ngu", "em còn thiếu bao nhiêu tín chỉ"), ("sv_mien_ielts", "chứng chỉ ielts của em miễn được môn nào"),
           ("sv_lvtn", "Học phí kỳ này bao nhiêu?"),
           ("sv_lvtn", "Nếu em rớt CT177 thì trễ mấy kỳ?")]


def phan_C():
    print("C. /v1/advice TRÙNG CLI")
    import prototype, grounded_answer
    c, _ = may_khach()
    tap = set()
    for ten, hoi in MA_TRAN:
        j = ho_so(ten)
        f = HS_DIR / f"{ten}.json"
        cli = prototype.answer(hoi, str(f))
        gr = grounded_answer.tra_loi(hoi, str(f))
        r = c.post("/v1/advice", json={"ho_so": j, "cau_hoi": hoi}, headers=H)
        a = r.json()
        v = cli["verdict"]
        mong_kl = None if a["trang_thai"] != "ok" else v
        # claim KHÔNG đối số (thieu_bat_buoc, thieu_nhom, du_dk_xin_mien) không bao giờ có trong answer set → CLI luôn trả FALSE sai (P18-1);
        # API chỉ cho 'ok' với claim thuộc danh sách cho phép, còn lại là ngoai_pham_vi, KHÔNG phải kết luận FALSE
        pham_vi = cli.get("claim") in ("khong_ro", "counterfactual", "thieu_bat_buoc", "thieu_nhom", "du_dk_xin_mien")
        dung = (r.status_code == 200 and a["claim"] == cli.get("claim") and a["ket_luan"] == (None if pham_vi else v)
                and a["trang_thai"] == ("ngoai_pham_vi" if pham_vi else "ok")
                and (pham_vi or (a["loi_giai"] == cli["explanation_vi"] and a["du_kien_thieu"] == cli.get("missing_facts", [])
                                 and [p["passage_id"] for p in a["nguon"]] == [p["passage_id"] for p in gr.get("nguon", [])]))
                and (not pham_vi or (a["chung_chi"] is None and a["nguon"] == [] and a["du_kien_thieu"] == [])))
        check(dung, f"{ten} · {hoi[:36]} → {a.get('trang_thai')}/{a.get('ket_luan')} (CLI {v}, claim {cli.get('claim')})")
        tap.add((a["trang_thai"], a["ket_luan"]))
        check(bool(a["phien_ban_kb"]) and a["canh_bao"] == [] and (pham_vi or a["chung_chi"] is not None),
              f"  · có phien_ban_kb, canh_bao rỗng; có chung_chi khi có kết luận ({ten})")
    check({("ok", "TRUE"), ("ok", "FALSE"), ("ok", "UNKNOWN"), ("ok", "DA_HOAN_THANH"), ("ngoai_pham_vi", None)} <= tap,
          f"ma trận phủ TRUE / FALSE / UNKNOWN / DA_HOAN_THANH / ngoài phạm vi ({sorted(map(str, tap))})")
    # thiếu dữ kiện → UNKNOWN kèm câu hỏi bổ sung
    j = ho_so("sv_lvtn"); j["xac_nhan_ky_luat_sach"] = None
    a = c.post("/v1/advice", json={"ho_so": j, "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H).json()
    check(a["ket_luan"] == "UNKNOWN" and "xac_nhan_ky_luat_sach" in a["du_kien_thieu"] and a["can_bo_sung"],
          f"thiếu xác nhận kỷ luật → UNKNOWN + câu hỏi bổ sung ({a['ket_luan']}, {a['du_kien_thieu']})")
    # hồ sơ mâu thuẫn (chữ B nhưng điểm 3,0)
    j = ho_so("sv_lvtn"); j["grades"]["CT177"]["thang10"] = 30
    a = c.post("/v1/advice", json={"ho_so": j, "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H).json()
    check(a["trang_thai"] == "ok" and a["ket_luan"] == "UNKNOWN" and a["mau_thuan"] and 'g10("CT177")' in a["du_kien_thieu"],
          f"hồ sơ mâu thuẫn → UNKNOWN, liệt kê mâu thuẫn, hỏi lại điểm CT177 ({a['mau_thuan'][:1]})")
    # lỗi kỹ thuật / hậu kiểm không thành kết luận học vụ
    orig = prototype.answer
    try:
        prototype.answer = lambda q, s: {"verdict": "BLOCKED", "explanation_vi": "HẬU KIỂM CHẶN: mã CT999", "missing_facts": [],
                                         "certificate": {"claim": "x", "proof": {"steps": []}}}
        a = c.post("/v1/advice", json={"ho_so": ho_so("sv_lvtn"), "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H).json()
        check(a["trang_thai"] == "hau_kiem_chan" and a["ket_luan"] is None and a["chung_chi"] is None and a["nguon"] == []
              and "CT999" not in json.dumps(a, ensure_ascii=False) and "HẬU KIỂM" not in a["loi_giai"],
              f"BLOCKED → hau_kiem_chan, ket_luan null, KHÔNG mang chứng chỉ / nguồn / nội dung bị chặn ({a['trang_thai']}, {a['ket_luan']})")
        prototype.answer = lambda q, s: {"verdict": "UNSAT", "explanation_vi": "mâu thuẫn", "missing_facts": [], "claim": "tot_nghiep",
                                         "certificate": {"claim": "tot_nghiep", "proof": {"steps": []}}}
        a = c.post("/v1/advice", json={"ho_so": ho_so("sv_lvtn"), "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H).json()
        check(a["trang_thai"] == "ho_so_mau_thuan" and a["ket_luan"] == "MAU_THUAN", f"UNSAT → ho_so_mau_thuan / MAU_THUAN ({a['trang_thai']}, {a['ket_luan']})")

        def hong(q, s):
            raise RuntimeError("clingo nổ: chứa CT180 và điểm 9.5")
        prototype.answer = hong
        r = c.post("/v1/advice", json={"ho_so": ho_so("sv_lvtn"), "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H)
        a = r.json()
        check(r.status_code == 500 and a["trang_thai"] == "loi_he_thong" and a["ket_luan"] is None and "CT180" not in json.dumps(a, ensure_ascii=False),
              f"ngoại lệ trong lõi → 500 loi_he_thong, ket_luan null, KHÔNG lộ nội dung ngoại lệ ({r.status_code})")
    finally:
        prototype.answer = orig


def phan_D():
    print("D. /v1/lookup · /v1/recommendations")
    from retriever import Retriever
    import recommendation
    c, _ = may_khach()
    q = "điều kiện tốt nghiệp"
    r = c.post("/v1/lookup", json={"truy_van": q, "k": 3}, headers=H)
    a = r.json()
    gốc = Retriever().search(q, k=3)
    check(r.status_code == 200 and a["trang_thai"] == "ok" and [p["id"] for p in a["ket_qua"]] == [p["id"] for p, _ in gốc]
          and all({"id", "dia_chi", "trang", "noi_dung", "van_ban"} <= set(p) for p in a["ket_qua"]),
          f"lookup trùng Retriever.search ({[p['id'] for p in a.get('ket_qua', [])]})")
    for body in ({"truy_van": "", "k": 3}, {"truy_van": "x", "k": 0}, {"truy_van": "x", "k": 11}, {"truy_van": "x" * 301, "k": 3}):
        check(c.post("/v1/lookup", json=body, headers=H).status_code == 422, f"lookup {str(body)[:40]} → 422")
    j = ho_so("sv_lvtn")
    for m in ("CT178", "CT179", "CT180", "CT182"):       # chưa học 4 HP → có đề xuất thật (hồ sơ mẫu đều rỗng vì đã đủ / còn thiếu quá nhiều)
        j["grades"].pop(m)
    for hk in (1, 2, 3):
        g = recommendation.de_xuat(copy.deepcopy(j), hk)
        a = c.post("/v1/recommendations", json={"ho_so": j, "hoc_ky": hk}, headers=H).json()
        check(a["trang_thai"] == "ok" and [x["ma"] for x in a["dang_ky"]] == [x["ma"] for x in g["dang_ky"]] and a["tong_tc"] == g["tong_tc"]
              and [x["ma"] or x["ly_do"] for x in a["can_xac_minh"]] == [x["ma"] or x["ly_do"] for x in g["can_xac_minh"]],
              f"recommendations HK{hk} trùng w19 ({a.get('tong_tc')} TC, {len(a.get('dang_ky', []))} HP)")
    a1 = c.post("/v1/recommendations", json={"ho_so": j, "hoc_ky": 1}, headers=H).json()
    check(len(a1["dang_ky"]) == 4 and a1["tong_tc"] == 12 and all(x["chung_chi"] for x in a1["dang_ky"]),
          f"HK1: 4 học phần / 12 TC, mỗi học phần kèm chung_chi ({[x['ma'] for x in a1['dang_ky']]})")
    for hk in (0, 4, "1"):
        check(c.post("/v1/recommendations", json={"ho_so": j, "hoc_ky": hk}, headers=H).status_code == 422, f"hoc_ky={hk!r} → 422")
    a = c.post("/v1/recommendations", json={"ho_so": {**j, "cohort": "K51"}, "hoc_ky": 1}, headers=H).json()
    check(a["trang_thai"] == "khong_ho_tro_ho_so" and a["dang_ky"] == [], f"K51 → khong_ho_tro_ho_so ({a['trang_thai']})")


def anh_png(ten):
    import io
    import render_transcript as RT
    out = []
    for im in RT.render(ho_so(ten), bien_the="sach"):
        b = io.BytesIO()
        im.save(b, "PNG")
        out.append(b.getvalue())
    return out


def phan_E(nhanh):
    print("E. /v1/ocr")
    c, _ = may_khach(max_files_ocr=3, max_bytes_file=200_000, max_body_ocr=2_000_000)
    r = c.post("/v1/ocr", files=[("anh", ("a.png", b"day khong phai anh", "image/png"))], headers=H)
    a = r.json()
    check(r.status_code == 200 and a["trang_thai"] == "loi_dau_vao" and a["ho_so_nhap"] is None, f"file không phải ảnh → loi_dau_vao ({a.get('trang_thai')})")
    r = c.post("/v1/ocr", files=[("anh", (f"{i}.png", b"x", "image/png")) for i in range(4)], headers=H)
    check(r.json()["trang_thai"] == "loi_dau_vao", "4 file > giới hạn 3 → loi_dau_vao")
    r = c.post("/v1/ocr", files=[("anh", ("a.png", b"x" * 300_000, "image/png"))], headers=H)
    check(r.json()["trang_thai"] == "loi_dau_vao", "file 300 KB > giới hạn 200 KB → loi_dau_vao")
    r = c.post("/v1/ocr", headers=H)
    check(r.status_code == 422, f"không có file → 422 ({r.status_code})")
    from PIL import Image
    import io
    b = io.BytesIO()
    Image.new("L", (9000, 9000), 255).save(b, "PNG")
    c2, _ = may_khach(max_bytes_file=5_000_000, max_pixels=25_000_000)
    r = c2.post("/v1/ocr", files=[("anh", ("lon.png", b.getvalue(), "image/png"))], headers=H)
    check(r.json()["trang_thai"] == "loi_dau_vao", f"ảnh 81 triệu điểm ảnh > giới hạn 25 triệu → loi_dau_vao, không giải nén ({r.json()['trang_thai']})")
    if nhanh:
        print("  (bỏ OCR ảnh thật do --nhanh)")
        return
    import jsonschema
    import ocr_transcript as O
    from PIL import Image
    trang = anh_png("sv_mien_ielts")
    c, _ = may_khach()
    r = c.post("/v1/ocr", files=[("anh", (f"t{i}.png", b, "image/png")) for i, b in enumerate(trang)], headers=H)
    a = r.json()
    sch = json.loads((CPA2 / "w7_student_facts" / "student_fact_schema.json").read_text(encoding="utf-8"))
    hs = a.get("ho_so_nhap") or {}
    ds = [Image.open(__import__("io").BytesIO(b)) for b in trang]
    doc = O.doc_bang_diem(ds)
    hs_goc, _, bc = O.sang_ho_so(doc, khai_bao={})
    check(r.status_code == 200 and a["trang_thai"] == "ok" and not list(jsonschema.Draft202012Validator(sch).iter_errors(hs)),
          f"{len(trang)} trang ảnh → hồ sơ NHÁP hợp lệ schema ({a.get('trang_thai')}, {len(hs.get('grades', {}))} học phần)")
    check(a["da_xac_minh"] is False and hs.get("meta", {}).get("nguon") == "ocr" and set(hs.get("grades", {})) == set(hs_goc["grades"]),
          "đánh dấu da_xac_minh=false, nguon=ocr; cùng tập học phần với pipeline trực tiếp")
    check(all(g.get("confidence") is not None for g in hs.get("grades", {}).values()), "mỗi học phần có confidence")
    check({"khong_chac", "hoc_ky_lech", "can_hoi", "khai_bao_thieu", "can_xac_nhan", "ngoai_ctdt"} <= set(a["bao_cao"]),
          f"báo cáo OCR đủ trường ({sorted(a['bao_cao'])})")
    check("ket_luan" in a and a["ket_luan"] is None, "OCR KHÔNG đưa ra kết luận học vụ: ket_luan = null (chỉ nháp để rà soát)")


def phan_F():
    print("F. GIỚI HẠN BODY · LOG · SONG SONG")
    c, _ = may_khach(max_body_json=20_000)
    big = {"ho_so": ho_so("sv_lvtn"), "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?", "rac": "x" * 30_000}
    r = c.post("/v1/advice", json=big, headers=H)
    check(r.status_code == 413 and r.json()["trang_thai"] == "loi_dau_vao", f"body JSON 30 KB > 20 KB → 413 ({r.status_code})")

    def chunks():
        for _ in range(40):
            yield b"x" * 1000
    r = c.post("/v1/advice", content=chunks(), headers={**H, "Content-Type": "application/json"})
    check(r.status_code == 413, f"body chunked (không Content-Length) vượt giới hạn → 413 ({r.status_code})")
    c, _ = may_khach()
    ghi = []

    class Bat(logging.Handler):
        def emit(self, rec):
            ghi.append(rec.getMessage())
    h = Bat()
    lg = logging.getLogger()
    lg.addHandler(h)
    old = lg.level
    lg.setLevel(logging.DEBUG)
    try:
        j = ho_so("sv_lvtn")
        c.post("/v1/advice", json={"ho_so": j, "cau_hoi": "Em đăng ký CT180 được không? Em là sv_lvtn"}, headers=H)
        c.post("/v1/lookup", json={"truy_van": "bí mật xyz", "k": 2}, headers=H)
        c.post("/v1/advice", json={"ho_so": j, "cau_hoi": "x"}, headers={"X-API-Key": "sai-khoa"})
    finally:
        lg.removeHandler(h)
        lg.setLevel(old)
    toan = "\n".join(ghi)
    check(ghi and not any(k in toan for k in ("CT180", "CT1", "thang10", "sv_lvtn", "bí mật", KHOA, "sai-khoa", "ielts")),
          f"log chỉ có thông tin vận hành, không có hồ sơ / câu hỏi / khoá ({len(ghi)} dòng)")
    cac = [("sv_lvtn", "em đủ điều kiện tốt nghiệp chưa?", "TRUE"), ("sv_tron_ngoai_ngu", "em đủ điều kiện tốt nghiệp chưa?", "FALSE")] * 6

    def goi(x):
        ten, q, mong = x
        kh = TestClient(c.app)
        return kh.post("/v1/advice", json={"ho_so": ho_so(ten), "cau_hoi": q}, headers=H).json()["ket_luan"] == mong
    with ThreadPoolExecutor(6) as ex:
        kq = list(ex.map(goi, cac))
    check(all(kq), f"12 yêu cầu song song xen kẽ hai hồ sơ: kết quả không bị trộn ({sum(kq)}/12)")


def phan_G():
    print("G. PHIÊN BẢN KB")
    c, _ = may_khach()
    h1 = c.get("/health").json()["kb"]
    h2 = c.get("/health").json()["kb"]
    check(h1 == h2 and h1["r_formal"].startswith("v1.") and len(h1["sha256"]) == 12, f"phiên bản KB ổn định, có R-Formal và hash ngắn ({h1})")
    a = c.post("/v1/advice", json={"ho_so": ho_so("sv_lvtn"), "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H).json()
    check(a["phien_ban_kb"] == h1, "kết quả tư vấn gắn đúng phiên bản KB đã dùng")
    import re
    lp = (CPA2 / "w5_rformal" / "qd3266_r_formal_v1.lp").read_text(encoding="utf-8")
    m = re.search(r"R-Formal v1 \(v(\d+\.\d+)", lp)
    check(m and h1["r_formal"] == "v" + m.group(1), f"r_formal đọc đúng từ đầu file .lp ({h1['r_formal']} vs v{m and m.group(1)})")


def phan_H():
    print("H. HỒ SƠ ĐỘC HẠI (review bảo mật)")
    c, _ = may_khach()
    base = ho_so("sv_lvtn")
    base["xac_nhan_ky_luat_sach"] = None            # thật thà: UNKNOWN (thiếu xác nhận kỷ luật)
    q = "em đủ điều kiện tốt nghiệp chưa?"
    goc = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": q}, headers=H).json()
    check(goc["ket_luan"] == "UNKNOWN", f"đối chứng: hồ sơ thật thà → UNKNOWN ({goc['ket_luan']})")
    xau = 'X"). xac_nhan_ky_luat_sach. khai_bao(ky_luat). %'
    ca = []
    j = copy.deepcopy(base); j["grades"][xau] = {"code": xau, "credits": 3, "thang10": 80, "letter": "B+", "status": "passed"}
    ca.append(("khoá grades + code", j))
    j = copy.deepcopy(base); j["khong_tinh_tich_luy"] = [xau]
    ca.append(("khong_tinh_tich_luy[]", j))
    j = copy.deepcopy(base); j["exemptions"] = [{"ma_hp": xau, "chung_chi_ref": None, "quyet_dinh": True}]
    ca.append(("exemptions[].ma_hp", j))
    j = copy.deepcopy(base); j["grades"]['X"). #include "/etc/hostname". %'] = {"code": 'X"). #include "/etc/hostname". %', "credits": 1}
    ca.append(("#include đọc file", j))
    j = copy.deepcopy(base); j["grades"]['X"). b(1..20000). c(X,Y):-b(X),b(Y),X<Y,Y<X+3. %'] = {"code": 'X"). b(1..20000). c(X,Y):-b(X),b(Y),X<Y,Y<X+3. %', "credits": 1}
    ca.append(("bùng nổ grounding", j))
    for ten, j in ca:
        t = __import__("time").time()
        r = c.post("/v1/advice", json={"ho_so": j, "cau_hoi": q}, headers=H)
        a = r.json()
        check(r.status_code == 200 and a["trang_thai"] == "loi_dau_vao" and a["ket_luan"] is None and __import__("time").time() - t < 3
              and "xac_nhan" not in json.dumps(a, ensure_ascii=False) and "#include" not in json.dumps(a, ensure_ascii=False),
              f"{ten} → loi_dau_vao (không tới solver, không phản hồi lại chuỗi độc) ({r.status_code}, {a.get('trang_thai')})")
    # số / kiểu
    for ten, sua in [("da_hoc_nam2 = 5.0", {"da_hoc_nam2": 5.0}), ("da_hoc_nam2 chuỗi", {"da_hoc_nam2": "5). xac_nhan_ky_luat_sach. %"}),
                     ("da_hoc_nam2 khổng lồ", {"da_hoc_nam2": 10 ** 22}), ("tc_cong_nhan = 10**22", {"tc_cong_nhan": 10 ** 22}),
                     ("tc_cong_nhan âm", {"tc_cong_nhan": -3}), ("tc_diem_f = 4.5", {"tc_diem_f": 4.5}),
                     ("chứng chỉ NaN", {"certificates": [{"loai": "ielts", "diem": float("nan")}]}),
                     ("chứng chỉ Infinity", {"certificates": [{"loai": "ielts", "diem": float("inf")}]}),
                     ("chứng chỉ 1e300", {"certificates": [{"loai": "ielts", "diem": 1e300}]}),
                     ("student_id xuống dòng", {"student_id": "sv_a\n"}), ("ctdt 120 KB", {"ctdt": "x" * 120_000})]:
        j = {**copy.deepcopy(base), **sua}
        body = json.dumps({"ho_so": j, "cau_hoi": q}, allow_nan=True)
        r = c.post("/v1/advice", content=body, headers={**H, "Content-Type": "application/json"})
        a = r.json()
        check(r.status_code in (200, 413) and a["trang_thai"] in ("loi_dau_vao", "khong_ho_tro_ho_so") and a["ket_luan"] is None and len(r.content) < 3000,
              f"{ten} → {a.get('trang_thai')} ({r.status_code}, phản hồi {len(r.content)} byte)")
    # quá nhiều bản ghi tự mâu thuẫn → chi phí tổ hợp (mỗi bản ghi mở 4 nhánh): chặn ở cổng vào
    j = copy.deepcopy(base)
    for m in ("CT177", "CT174", "CT172", "CT175", "CT190", "CT101"):
        j["grades"][m].update(thang10=90, letter="F", status="passed")
    r = c.post("/v1/advice", json={"ho_so": j, "cau_hoi": q}, headers=H)
    a = r.json()
    check(a["trang_thai"] == "loi_dau_vao" and "mâu thuẫn" in json.dumps(a, ensure_ascii=False), f"6 bản ghi tự mâu thuẫn → loi_dau_vao, không để solver nổ tổ hợp ({a['trang_thai']})")
    j = copy.deepcopy(base)
    j["grades"]["CT177"].update(thang10=30)
    a = c.post("/v1/advice", json={"ho_so": j, "cau_hoi": q}, headers=H).json()
    check(a["trang_thai"] == "ok" and a["mau_thuan"], "1 bản ghi mâu thuẫn vẫn được xử lý (UNKNOWN + hỏi lại) — chỉ chặn khi quá nhiều")
    # UNSAT thật qua luồng chính (trước đây: KeyError → 500)
    j = copy.deepcopy(base); j["khong_tinh_tich_luy"] = ["CT177"]
    r = c.post("/v1/advice", json={"ho_so": j, "cau_hoi": q}, headers=H)
    a = r.json()
    check(r.status_code == 200 and a["trang_thai"] == "ho_so_mau_thuan" and a["ket_luan"] == "MAU_THUAN" and a["chung_chi"] is None,
          f"hồ sơ làm solver vô nghiệm (loại HP bắt buộc khỏi tích lũy) → ho_so_mau_thuan / MAU_THUAN ({r.status_code}, {a['trang_thai']})")


def phan_I():
    print("I. HÌNH DẠNG PHẢN HỒI · TIÊU ĐỀ · THỨ TỰ XÁC THỰC")
    c, cfg = may_khach(max_body_json=50_000)
    base = ho_so("sv_lvtn")
    khoa = {"Content-Type": "application/json"}
    phan_hoi = {
        "401": c.post("/v1/lookup", json={"truy_van": "x"}),
        "422": c.post("/v1/lookup", json={"truy_van": ""}, headers=H),
        "422 trường thừa": c.post("/v1/lookup", json={"truy_van": "x", "BI_MAT_ABC": 1}, headers=H),
        "400 JSON hỏng": c.post("/v1/lookup", content=b"{khong phai json", headers={**H, **khoa}),
        "400 UTF-8 hỏng": c.post("/v1/lookup", content=b'{"truy_van": "\xff\xfe"}', headers={**H, **khoa}),
        "400 lồng sâu": c.post("/v1/lookup", content=b"[" * 40_000 + b"]" * 40_000, headers={**H, **khoa}),
        "400 số 5000 chữ số": c.post("/v1/lookup", content=b'{"truy_van": "x", "k": ' + b"9" * 5000 + b"}", headers={**H, **khoa}),
        "413": c.post("/v1/lookup", json={"truy_van": "x" * 60_000}, headers=H),
        "404": c.get("/khong-co", headers=H), "405": c.get("/v1/advice", headers=H),
        "loi_dau_vao advice": c.post("/v1/advice", json={"ho_so": {"student_id": "sv_x"}, "cau_hoi": "x"}, headers=H),
        "khong_ho_tro advice": c.post("/v1/advice", json={"ho_so": {**base, "cohort": "K51"}, "cau_hoi": "x"}, headers=H),
        "khong_ho_tro recs": c.post("/v1/recommendations", json={"ho_so": {**base, "cohort": "K51"}, "hoc_ky": 1}, headers=H),
        "loi_dau_vao recs": c.post("/v1/recommendations", json={"ho_so": {"student_id": "sv_x"}, "hoc_ky": 1}, headers=H),
        "loi_dau_vao ocr": c.post("/v1/ocr", files=[("anh", ("a.png", b"khong phai anh", "image/png"))], headers=H),
    }
    c503 = TestClient(tao_app(cau_hinh.CauHinh(api_key=None, so_worker=0)))
    phan_hoi["503"] = c503.post("/v1/lookup", json={"truy_van": "x"}, headers=H)
    loi = []
    for ten, r in phan_hoi.items():
        try:
            j = r.json()
        except ValueError:
            loi.append((ten, "không phải JSON"))
            continue
        if not ({"trang_thai", "ket_luan", "thong_bao", "chi_tiet"} <= set(j) and j["ket_luan"] is None and isinstance(j["chi_tiet"], list)
                and isinstance(j["thong_bao"], str) and "detail" not in j):
            loi.append((ten, sorted(j)))
    check(not loi, f"MỌI phản hồi không-ok có đủ trang_thai/ket_luan(null)/thong_bao/chi_tiet(list), không có 'detail' của framework ({loi[:3]})")
    kq = {ten: (r.status_code, r.json().get("trang_thai")) for ten, r in phan_hoi.items()}
    check(kq["401"] == (401, "khong_xac_thuc") and kq["422"][0] == 422 and kq["413"] == (413, "loi_dau_vao") and kq["503"] == (503, "loi_he_thong")
          and all(kq[k][1] == "loi_dau_vao" for k in ("400 JSON hỏng", "400 UTF-8 hỏng", "400 lồng sâu", "400 số 5000 chữ số", "404", "405")),
          f"mã HTTP + trang_thai đúng cho từng loại lỗi ({kq})")
    check(all(r.status_code != 500 for r in phan_hoi.values()), "không đầu vào hỏng nào gây 500")
    # xác thực TRƯỚC khi đọc / parse body
    r = c.post("/v1/advice", content=b"{khong phai json", headers=khoa)
    check(r.status_code == 401, f"JSON hỏng + KHÔNG có khoá → 401 (xác thực trước parse), không phải 422/400 ({r.status_code})")
    r = c.post("/v1/advice", content=b"x" * 60_000, headers=khoa)
    check(r.status_code == 401, f"body lớn + không khoá → 401, không đọc body ({r.status_code})")
    # không phản hồi lại dữ liệu người dùng
    check("BI_MAT_ABC" not in phan_hoi["422 trường thừa"].text, "422 không phản hồi lại tên trường thừa do người dùng đặt")
    a = c.post("/v1/advice", json={"ho_so": {**base, "ctdt": "x" * 20_000}, "cau_hoi": "x"}, headers=H)
    check(len(a.content) < 1500, f"khong_ho_tro_ho_so không phản hồi lại giá trị dài ({len(a.content)} byte)")
    # hình dạng thành công thống nhất: luôn có trang_thai + ket_luan
    ok = [c.post("/v1/lookup", json={"truy_van": "tốt nghiệp"}, headers=H), c.post("/v1/recommendations", json={"ho_so": base, "hoc_ky": 1}, headers=H),
          c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H), c.get("/health")]
    check(all("trang_thai" in r.json() for r in ok) and all("ket_luan" in r.json() for r in ok[:3]),
          "phản hồi thành công của lookup / recommendations / advice đều có trang_thai + ket_luan (lookup, recommendations: null)")
    check(ok[0].json()["ket_luan"] is None and ok[1].json()["ket_luan"] is None, "lookup / recommendations KHÔNG mang ket_luan học vụ")
    # tiêu đề an toàn
    for ten, r in list(phan_hoi.items()) + [("advice ok", ok[2]), ("health", ok[3])]:
        h = r.headers
        if h.get("cache-control") != "no-store" or h.get("x-content-type-options") != "nosniff":
            check(False, f"{ten}: thiếu Cache-Control: no-store / X-Content-Type-Options: nosniff ({dict(h)})")
            break
    else:
        check(True, "mọi phản hồi (kể cả lỗi) có Cache-Control: no-store + X-Content-Type-Options: nosniff")
    # log: có bộ ghi riêng ở INFO (dưới uvicorn root không có handler nên trước đây dòng INFO bị nuốt)
    lg = logging.getLogger("cpa2_api")
    check(lg.level == logging.INFO and lg.handlers, f"logger cpa2_api có handler + mức INFO (dòng vận hành không bị nuốt dưới uvicorn) ({lg.level}, {len(lg.handlers)})")


def anh_cat_dut():
    import io
    from PIL import Image
    b = io.BytesIO()
    im = Image.new("L", (1200, 1200))
    im.putdata([(x * 7) % 256 for x in range(1200 * 1200)])
    im.save(b, "PNG")
    return b.getvalue()[:-4000]                      # cắt đuôi: header đọc được, giải nén thì lỗi


def phan_E2():
    print("E2. OCR — ảnh hỏng / khai báo sai kiểu")
    import io
    from PIL import Image
    c, _ = may_khach(max_pixels_tong=3_000_000)
    r = c.post("/v1/ocr", files=[("anh", ("c.png", anh_cat_dut(), "image/png"))], headers=H)
    check(r.status_code == 200 and r.json()["trang_thai"] == "loi_dau_vao", f"ảnh PNG bị cắt dở → loi_dau_vao (không 500) ({r.status_code}, {r.json().get('trang_thai')})")
    b = io.BytesIO()
    Image.new("L", (1500, 1500), 255).save(b, "PNG")
    r = c.post("/v1/ocr", files=[("anh", (f"{i}.png", b.getvalue(), "image/png")) for i in range(2)], headers=H)
    check(r.json()["trang_thai"] == "loi_dau_vao" and "tổng" in json.dumps(r.json(), ensure_ascii=False), "tổng điểm ảnh của yêu cầu (4,5 triệu) vượt trần 3 triệu → loi_dau_vao")
    b2 = io.BytesIO()
    Image.new("L", (300, 300), 255).save(b2, "PNG")
    for kb in ('{"dtbchk_khai_bao": "abc"}', '{"da_hoc_nam2": "5"}', '{"xac_nhan_ky_luat_sach": "yes"}', '{"khong_tinh_tich_luy": 5}',
               '{"tc_cong_nhan": {"a": 1}}', '{"da_hoc_nam2": NaN}', "[1]", "{khong json"):
        r = c.post("/v1/ocr", files=[("anh", ("a.png", b2.getvalue(), "image/png"))], data={"khai_bao": kb}, headers=H)
        check(r.status_code == 200 and r.json()["trang_thai"] == "loi_dau_vao", f"khai_bao {kb[:34]} → loi_dau_vao ({r.status_code}, {r.json().get('trang_thai')})")
    r = c.post("/v1/ocr", files=[("anh", ("a.png", b2.getvalue(), "image/png"))], data={"khai_bao": '{"da_hoc_nam2": 6, "la": 1}'}, headers=H)
    j = r.json()
    check(j["trang_thai"] == "ok" and j["ho_so_nhap"].get("da_hoc_nam2") == 6 and any("la" in x for x in j["canh_bao"]),
          f"khai_bao hợp lệ được nhận, khoá lạ bị bỏ + cảnh báo ({j['trang_thai']})")


def phan_J():
    print("J. BỂ TIẾN TRÌNH: HẾT GIỜ · QUÁ TẢI · TIẾN TRÌNH CHẾT")
    import time
    kh = "gia_lap_tien_trinh:tao"
    c, cfg = may_khach(so_worker=1, khoi_tao_worker=kh, timeout_advice=1.5, cho_hang_doi=0.4, timeout_lookup=1.5)
    body = lambda q: {"ho_so": ho_so("sv_lvtn"), "cau_hoi": q}      # noqa: E731
    try:
        t = time.time()
        r = c.post("/v1/advice", json=body("ngu:30"), headers=H)
        a = r.json()
        check(r.status_code == 504 and a["trang_thai"] == "het_gio" and a["ket_luan"] is None and time.time() - t < 8,
              f"yêu cầu treo → 504 het_gio sau ~{time.time() - t:.1f}s (tiến trình bị giết), ket_luan null")
        bk = c.app.state.backend
        check(bk.cho_san_sang(30), "tiến trình bị giết được dựng lại ở nền")
        r = c.post("/v1/advice", json=body("binh thuong"), headers=H)
        check(r.status_code == 200 and r.json()["trang_thai"] == "ok", f"sau hết giờ, tiến trình mới phục vụ được yêu cầu tiếp ({r.status_code})")
        r = c.post("/v1/advice", json=body("chet"), headers=H)
        a = r.json()
        check(r.status_code == 500 and a["trang_thai"] == "loi_he_thong" and a["ket_luan"] is None, f"tiến trình chết giữa chừng → 500 loi_he_thong ({r.status_code})")
        check(bk.cho_san_sang(30), "tiến trình chết được dựng lại ở nền")
        r = c.post("/v1/advice", json=body("binh thuong"), headers=H)
        check(r.status_code == 200, f"tiến trình chết được thay mới ({r.status_code})")
        r = c.post("/v1/advice", json=body("loi"), headers=H)
        a = r.json()
        check(r.status_code == 500 and "BI_MAT_TRONG_NGOAI_LE" not in r.text, f"ngoại lệ trong tiến trình con → 500, KHÔNG lộ nội dung ngoại lệ ({r.status_code})")
        # quá tải: một tiến trình đang bận → yêu cầu thứ hai chờ tối đa cho_hang_doi rồi 503 qua_tai
        c.app.state.cfg.timeout_advice = 6.0
        kq = {}
        th = __import__("threading").Thread(target=lambda: kq.update(a=c.post("/v1/advice", json=body("ngu:3"), headers=H)))
        th.start()
        time.sleep(0.8)
        t = time.time()
        r = c.post("/v1/lookup", json={"truy_van": "x"}, headers=H)
        check(r.status_code == 503 and r.json()["trang_thai"] == "qua_tai" and time.time() - t < 3, f"bể bận → 503 qua_tai sau ≤ cho_hang_doi ({r.status_code}, {time.time() - t:.1f}s)")
        th.join()
        check(kq["a"].status_code == 200, "yêu cầu đang chạy vẫn hoàn tất bình thường")
    finally:
        c.app.state.backend.dong()
    # đường thật: lõi CPA² chạy trong tiến trình con (nhập module, pickle hồ sơ/kết quả, KB trong tiến trình con)
    c, cfg = may_khach(so_worker=1)
    try:
        a = c.post("/v1/advice", json={"ho_so": ho_so("sv_lvtn"), "cau_hoi": "em đủ điều kiện tốt nghiệp chưa?"}, headers=H).json()
        l = c.post("/v1/lookup", json={"truy_van": "điều kiện tốt nghiệp", "k": 2}, headers=H).json()
        rc = c.post("/v1/recommendations", json={"ho_so": ho_so("sv_lvtn"), "hoc_ky": 1}, headers=H).json()
        check(a["trang_thai"] == "ok" and a["ket_luan"] == "TRUE" and a["nguon"] and len(l["ket_qua"]) == 2 and rc["trang_thai"] == "ok",
              f"lõi thật trong tiến trình con: advice TRUE + nguồn, lookup, recommendations ({a['trang_thai']}/{a['ket_luan']})")
    finally:
        c.app.state.backend.dong()


def thu(ten, ham):
    """Chạy một nhóm kiểm tra; ngoại lệ không dừng cả bộ mà ghi thành FAIL (để thấy hết các lỗi cùng lúc)."""
    try:
        ham()
    except Exception as e:  # noqa: BLE001
        check(False, f"{ten}: ngoại lệ {type(e).__name__}: {str(e)[:120]}")


def phan_K():
    import time
    import multiprocessing
    print("K. REVIEW BẢO MẬT VÒNG 2")
    base = ho_so("sv_lvtn")
    q = "em đủ điều kiện tốt nghiệp chưa?"

    def k1():
        check(cau_hinh.CauHinh(api_key=KHOA).max_mau_thuan == 2, "trần bản ghi tự mâu thuẫn mặc định = 2 (4 bản ghi ≈ 21s)")
        for ten, sua in (("exemptions 60 mục", {"exemptions": [{"ma_hp": f"X{i}", "chung_chi_ref": None, "quyet_dinh": True} for i in range(60)]}),
                         ("certificates 25 mục", {"certificates": [{"loai": "ielts", "diem": 6.0} for _ in range(25)]}),
                         ("khong_tinh_tich_luy 150 mục", {"khong_tinh_tich_luy": [f"X{i}" for i in range(150)]})):
            r = HS.kiem_tra({**copy.deepcopy(base), **sua})
            check(r.loi and not r.ho_so, f"{ten} → loi_dau_vao (mỗi mục là một dòng ASP / một lần mở nhánh) ({[x['duong_dan'] for x in r.loi][:2]})")
        j = copy.deepcopy(base)
        for m in ("CT177", "CT174", "CT172"):
            j["grades"][m].update(thang10=90, letter="F", status="passed")
        r = HS.kiem_tra(j)
        check(r.loi and "mâu thuẫn" in json.dumps(r.loi, ensure_ascii=False), "3 bản ghi tự mâu thuẫn → loi_dau_vao (trần 2)")
    thu("K1", k1)

    def k2():
        from cpa2_api import dich_vu
        check(dich_vu.an_toan({"a": float("nan"), "b": [float("inf"), 1.5, float("-inf")]}) == {"a": None, "b": [None, 1.5, None]},
              "an_toan đổi NaN / ±Infinity thành null (JSON hợp lệ)")
        goc = HS.kiem_tra
        HS.kiem_tra = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("BI_MAT_TRONG_NGOAI_LE"))
        try:
            cfg = cau_hinh.CauHinh(api_key=KHOA, so_worker=0)
            c = TestClient(tao_app(cfg), raise_server_exceptions=False)
            r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": q}, headers=H)
            a = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            check(r.status_code == 500 and a.get("trang_thai") == "loi_he_thong" and a.get("ket_luan") is None and a.get("thong_bao") and "chi_tiet" in a
                  and r.headers.get("cache-control") == "no-store" and "BI_MAT" not in r.text,
                  f"ngoại lệ chưa bắt trong endpoint → 500 cùng hình dạng + no-store, không lộ nội dung ({r.status_code}, {r.headers.get('content-type')})")
        finally:
            HS.kiem_tra = goc
    thu("K2", k2)

    def k3():
        # khởi động hỏng: không để lại tiến trình con mồ côi, lần gọi sau không cộng dồn
        c, _ = may_khach(so_worker=2, khoi_tao_worker="cpa2_api.khong_co_module:x")
        r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": q}, headers=H)
        check(r.status_code == 500 and r.json()["trang_thai"] == "loi_he_thong", f"bể không khởi động được → 500 loi_he_thong ({r.status_code})")
        bk = c.app.state.backend
        han = time.time() + 5
        while time.time() < han and multiprocessing.active_children():
            time.sleep(0.1)
        check(not multiprocessing.active_children() and bk.ds == [] and not bk.da_khoi_dong,
              f"khởi động hỏng → dọn sạch tiến trình con ({len(multiprocessing.active_children())} còn sống, ds={len(bk.ds)})")
        h = c.get("/health")
        check(h.status_code == 503 and h.json()["trang_thai"] == "loi_he_thong", f"khởi động hỏng → /health 503 (bể chưa từng chạy được nhưng cũng không khoẻ) ({h.status_code})")
        bk.dong()
        # /health và yêu cầu khác không bị chặn bởi khoá trong lúc bể khởi động chậm
        os.environ["GIA_KHOI_NGU"] = "4"
        try:
            c2, _ = may_khach(so_worker=1, khoi_tao_worker="gia_lap_tien_trinh:tao", cho_hang_doi=1.0)
            th = threading.Thread(target=lambda: c2.post("/v1/advice", json={"ho_so": base, "cau_hoi": "x"}, headers=H))
            th.start()
            time.sleep(1.0)
            t = time.time()
            h = c2.get("/health")
            check(h.status_code == 200 and time.time() - t < 1.0, f"/health không bị chặn khi bể đang khởi động chậm ({time.time() - t:.2f}s)")
            t = time.time()
            r = c2.post("/v1/lookup", json={"truy_van": "x"}, headers=H)
            check(r.status_code == 503 and r.json()["trang_thai"] == "qua_tai" and time.time() - t < 3,
                  f"yêu cầu đến trong lúc khởi động chờ ≤ cho_hang_doi rồi qua_tai ({r.status_code}, {time.time() - t:.1f}s)")
            th.join()
            c2.app.state.backend.dong()
        finally:
            os.environ.pop("GIA_KHOI_NGU", None)
    thu("K3a", k3)

    def k4():
        kh = "gia_lap_tien_trinh:tao"
        c, cfg = may_khach(so_worker=1, khoi_tao_worker=kh, timeout_advice=3.0, cho_hang_doi=1.0)
        bk = c.app.state.backend
        try:
            body = lambda qq: {"ho_so": base, "cau_hoi": qq}        # noqa: E731
            check(c.post("/v1/advice", json=body("x"), headers=H).status_code == 200, "làm nóng bể")
            h = c.get("/health").json()
            check(h.get("bo_xu_ly", {}).get("san_sang") == 1 and h["bo_xu_ly"].get("tong") == 1, f"/health nêu tình trạng bể ({h.get('bo_xu_ly')})")
            bk.ranh.queue[0].proc.kill()                           # tiến trình RẢNH chết (OOM killer, v.v.)
            time.sleep(0.5)
            r = c.post("/v1/advice", json=body("x"), headers=H)
            check(r.status_code == 200 and r.json()["trang_thai"] == "ok", f"tiến trình rảnh đã chết → yêu cầu vẫn được phục vụ (thay thế trong suốt) ({r.status_code})")
            # không dựng lại được → bể rỗng → /health 503 (để nền tảng khởi động lại container)
            from cpa2_api import tien_trinh as TT
            goc, goc_lui = TT._Worker.khoi_dong, TT.LUI_BUOC_HOI_SINH
            TT.LUI_BUOC_HOI_SINH = (0.0, 0.3)                      # mặc định ~31s: rút ngắn để test
            TT._Worker.khoi_dong = lambda self: (_ for _ in ()).throw(OSError("het tai nguyen"))
            try:
                c.post("/v1/advice", json=body("chet"), headers=H)
                han = time.time() + 15
                while time.time() < han and c.get("/health").status_code == 200:
                    time.sleep(0.2)
                r = c.get("/health")
                check(r.status_code == 503 and r.json()["trang_thai"] == "loi_he_thong", f"mọi tiến trình mất và không dựng lại được → /health 503 ({r.status_code})")
            finally:
                TT._Worker.khoi_dong = goc
                TT.LUI_BUOC_HOI_SINH = goc_lui
        finally:
            bk.dong()
    thu("K3b", k4)

    def k5():
        # bể OCR riêng: OCR chậm không làm nghẽn advice
        os.environ["GIA_OCR_NGU"] = "4"
        try:
            c, cfg = may_khach(so_worker=1, so_worker_ocr=1, khoi_tao_worker="gia_lap_tien_trinh:tao", timeout_advice=3.0, cho_hang_doi=0.5, timeout_ocr=20.0)
            anh = anh_png("sv_lvtn")[:1]
            try:
                c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "x"}, headers=H)                    # làm nóng bể advice
                kq = {}
                th = threading.Thread(target=lambda: kq.update(r=c.post("/v1/ocr", files=[("anh", ("a.png", anh[0], "image/png"))], headers=H)))
                th.start()
                time.sleep(1.5)
                t = time.time()
                r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "x"}, headers=H)
                check(r.status_code == 200 and time.time() - t < 2, f"OCR đang chạy (4s) không chặn advice ({r.status_code}, {time.time() - t:.1f}s)")
                th.join()
                check(kq["r"].status_code == 200 and kq["r"].json()["trang_thai"] == "ok", "OCR vẫn hoàn tất")
            finally:
                for b in {id(c.app.state.backend): c.app.state.backend, id(getattr(c.app.state, "backend_ocr", None)): getattr(c.app.state, "backend_ocr", None)}.values():
                    if b is not None:
                        b.dong()
        finally:
            os.environ.pop("GIA_OCR_NGU", None)
    thu("K4", k5)

    def k6():
        c, _ = may_khach()
        j = copy.deepcopy(base); j["khong_tinh_tich_luy"] = ["CT177"]
        for ten, pt, body in (("recommendations", "/v1/recommendations", {"ho_so": j, "hoc_ky": 1}),
                              ("advice đề xuất", "/v1/advice", {"ho_so": j, "cau_hoi": "kỳ này em nên đăng ký môn gì?"})):
            a = c.post(pt, json=body, headers=H).json()
            check(a["trang_thai"] == "ho_so_mau_thuan" and a["ket_luan"] == "MAU_THUAN" and a.get("thong_bao"),
                  f"UNSAT nhất quán ở {ten} → ho_so_mau_thuan / MAU_THUAN, có thong_bao ({a['trang_thai']}/{a['ket_luan']})")
        a = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "học phí kỳ này bao nhiêu?"}, headers=H).json()
        check(a["trang_thai"] == "ngoai_pham_vi" and a.get("thong_bao"), f"ngoai_pham_vi có thong_bao khác rỗng ({a['trang_thai']})")
    thu("K5", k6)

    def k7():
        j = copy.deepcopy(base); j["xac_nhan_ky_luat_sach"] = "co"; j["student_id"] = "sv_a\n"
        r = HS.kiem_tra(j)
        duong = {x["duong_dan"] for x in r.loi}
        check("xac_nhan_ky_luat_sach" in duong, f"đường dẫn lỗi giữ tên trường THẬT dài > 20 ký tự ({sorted(duong)})")
        c, _ = may_khach()
        a = c.post("/v1/advice", json={"ho_so": {**base, "xac_nhan_ky_luat_sach": "co"}, "cau_hoi": q}, headers=H).json()
        check(any(x["duong_dan"] == "xac_nhan_ky_luat_sach" for x in a["chi_tiet"]), "…và ở phản hồi HTTP")
        j = copy.deepcopy(base); j["x" * 30] = 1
        a = c.post("/v1/advice", json={"ho_so": {**base, "x" * 30: 1}, "cau_hoi": q}, headers=H).json()
        check("x" * 30 not in json.dumps(a, ensure_ascii=False), "tên trường LẠ do người dùng đặt vẫn không được phản hồi lại")
    thu("K6", k7)

    def k8():
        c, _ = may_khach()
        r = c.post("/v1/advice/", json={"ho_so": base, "cau_hoi": q}, headers=H, follow_redirects=False)
        check(r.status_code == 404 and r.json()["trang_thai"] == "loi_dau_vao", f"đường dẫn có '/' thừa → 404 cùng hình dạng, không chuyển hướng ({r.status_code})")
        check(c.head("/health").status_code == 200, "HEAD /health → 200 (bộ kiểm tra sức khoẻ của nền tảng)")
        r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": q}, headers=[("X-API-Key", "sai"), ("X-API-Key", KHOA)])
        check(r.status_code == 401, f"hai tiêu đề X-API-Key: dùng cái ĐẦU TIÊN (cái sai) → 401 ({r.status_code})")
        goc = os.environ.get("CPA2_WORKERS")
        try:
            for v, mong in (("3", 3), ("0", 0), (None, 2), ("abc", ValueError), ("-1", ValueError), ("", 2), ("9999", ValueError)):
                if v is None:
                    os.environ.pop("CPA2_WORKERS", None)
                else:
                    os.environ["CPA2_WORKERS"] = v
                try:
                    kq = cau_hinh.CauHinh(api_key=KHOA).so_worker
                except ValueError:
                    kq = ValueError
                check(kq == mong, f"CPA2_WORKERS={v!r} → {mong if mong is not ValueError else 'lỗi rõ ràng lúc khởi động'} (được {kq})")
        finally:
            if goc is None:
                os.environ.pop("CPA2_WORKERS", None)
            else:
                os.environ["CPA2_WORKERS"] = goc
        dk = (HERE / "Dockerfile").read_text(encoding="utf-8")
        check(not any("--limit-concurrency" in l for l in dk.splitlines() if not l.lstrip().startswith("#")), "Dockerfile không dùng --limit-concurrency (làm /health và yêu cầu hợp lệ bị 503 khi có kết nối treo)")
        di = (HERE.parent.parent / ".dockerignore").read_text(encoding="utf-8")
        check("**/.env" in di and "**/.env.*" in di, ".dockerignore chặn .env ở mọi thư mục con")
    thu("K7", k8)

    def k9():
        kh = "gia_lap_tien_trinh:tao"
        os.environ["CPA2_API_KEY"] = "KHOA-CHA-KHONG-DUOC-LOT-SANG-CON"
        try:
            c, _ = may_khach(so_worker=1, khoi_tao_worker=kh, timeout_advice=3.0, cho_hang_doi=1.0, gioi_han_ram_mb=512)
            bk = c.app.state.backend
            try:
                a = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "env"}, headers=H).json()
                check(a.get("loi_giai") == "KHONG_CO_KHOA", f"khoá API không lọt vào môi trường tiến trình con ({a.get('loi_giai')})")
                r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "ram"}, headers=H)
                check(r.status_code == 500 and r.json()["trang_thai"] == "loi_he_thong", f"xin 900 MB khi giới hạn 512 MB → MemoryError → 500 ({r.status_code})")
                r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": "x"}, headers=H)
                check(r.status_code == 200, f"…tiến trình con vẫn dùng tiếp được sau MemoryError ({r.status_code})")
                tep = HERE / "_pid_chau.tmp"
                tep.unlink(missing_ok=True)
                r = c.post("/v1/advice", json={"ho_so": base, "cau_hoi": f"con:{tep}"}, headers=H)
                check(r.status_code == 504, f"tiến trình treo có tiến trình cháu → 504 ({r.status_code})")
                pid = int(tep.read_text()) if tep.exists() else 0
                han = time.time() + 5
                song = True
                while time.time() < han and song and pid:
                    try:
                        os.kill(pid, 0)
                        time.sleep(0.1)
                    except ProcessLookupError:
                        song = False
                check(pid and not song, f"tiến trình cháu (kiểu tesseract) bị giết cùng nhóm, không mồ côi (pid {pid}, còn sống={song})")
                if pid and song:
                    os.kill(pid, 9)
                tep.unlink(missing_ok=True)
            finally:
                bk.dong()
        finally:
            os.environ.pop("CPA2_API_KEY", None)
    thu("K8", k9)


def main():
    nhanh = "--nhanh" in sys.argv
    os.environ.pop("CPA2_API_KEY", None)
    for p in (phan_A, phan_B, phan_C, phan_D):
        p()
    phan_E(nhanh)
    phan_E2()
    phan_F()
    phan_G()
    phan_H()
    phan_I()
    phan_J()
    phan_K()
    print("\nKẾT LUẬN:", "ĐẠT — API trùng CLI, đóng khi thiếu khoá, không lộ hồ sơ, lỗi kỹ thuật không thành kết luận học vụ" if ok_all else "CHƯA ĐẠT")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
