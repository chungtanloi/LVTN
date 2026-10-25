"""ho_so.py — kiểm hồ sơ sinh viên TRƯỚC khi vào solver.

  1. đúng student_fact_schema (w7), kèm kiểm CHẶT hơn schema: số nguyên thật (5.0 không phải số nguyên), khoảng giá trị, hữu hạn
     (NaN / Infinity), định danh (mã học phần, ma_hp, mục khong_tinh_tich_luy) chỉ gồm chữ-số-gạch dưới ≤ 20 ký tự   → loi_dau_vao
     Định danh được ghép vào chương trình ASP: mã như  X"). xac_nhan_ky_luat_sach. %  có thể tiêm dữ kiện giả / `#include` đọc file / làm
     solver nổ tổ hợp. Loader (w7) cũng đã chặn; đây là lớp phòng thủ thứ hai và cho người dùng thông báo lỗi rõ.
  2. chỉ hỗ trợ CNTT K49 (ngành cntt, khoá K49, ctdt cntt_k49)                                                       → khong_ho_tro_ho_so
  3. khoá bản ghi == mã học phần; tín chỉ khớp CTĐT K49; ≤ max_grades học phần; ≤ max_mau_thuan bản ghi tự mâu thuẫn  → loi_dau_vao
  4. mã đúng dạng nhưng ngoài CTĐT (bảng điểm thật có TC025–027, CC004…) → CẢNH BÁO, không chặn (KB bỏ qua mã lạ)
Không phản hồi lại giá trị đầu vào: thông báo chỉ nêu vị trí, loại lỗi, và các đoạn đã làm sạch/cắt ngắn. Trả hồ sơ CHUẨN HOÁ: bản sao, chỉ
giữ trường có trong schema (trừ `meta`). Hồ sơ tự mâu thuẫn ít (điểm chữ ≠ điểm số…) không bị chặn: loader mở nhánh, solver trả UNKNOWN
kèm `mau_thuan` + câu hỏi bổ sung.
"""
import json
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import jsonschema

from .cau_hinh import CauHinh
from .dich_vu import nap_duong_dan

PHAM_VI = {"major": "cntt", "cohort": "K49", "ctdt": "cntt_k49"}
MO_TA_PHAM_VI = "Hiện chỉ hỗ trợ ngành CNTT, khoá K49 (CTĐT cntt_k49)"
_MA = re.compile(r"[A-Za-z0-9_]{1,20}\Z")
_SV_ID = re.compile(r"sv_[a-z0-9_]{1,60}\Z")
SO_NGUYEN = {"da_hoc_nam2": (0, 100), "tc_cong_nhan": (0, 400), "tc_diem_f": (0, 400)}
# Trần danh sách: mỗi mục là một dòng ASP (exemptions → duoc_mien, certificates → chung_chi, khong_tinh_tich_luy) và có thể mở thêm nhánh
# → đầu vào không giới hạn là cách ép solver / bộ nhớ (review bảo mật vòng 2). Khớp với trần ở loader (lớp phòng thủ thứ hai).
TRAN_DANH_SACH = {"exemptions": 50, "certificates": 20, "khong_tinh_tich_luy": 100}
_TEN_BIET = set()          # tên trường CỦA SCHEMA (không phải do người dùng đặt) → được nêu nguyên văn trong đường dẫn lỗi
MAX_DO_SAU = 12


@dataclass
class KetQua:
    ho_so: dict = field(default_factory=dict)
    loi: list = field(default_factory=list)            # [{"duong_dan", "thong_bao"}]
    canh_bao: list = field(default_factory=list)       # [str]
    khong_ho_tro: str | None = None


@lru_cache(maxsize=2)
def _nap(goc):
    schema = json.loads((goc / "w7_student_facts" / "student_fact_schema.json").read_text(encoding="utf-8"))
    _TEN_BIET.update(_ten_trong_schema(schema))
    ct = json.loads((goc / "w6_curriculum" / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))
    return jsonschema.Draft7Validator(schema), set(schema["properties"]) - {"meta"}, {h["ma"]: h["tin_chi"] for h in ct["hoc_phan"]}


def _ten_trong_schema(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "properties" and isinstance(v, dict):
                yield from (t for t in v if isinstance(t, str))
            yield from _ten_trong_schema(v)
    elif isinstance(x, list):
        for v in x:
            yield from _ten_trong_schema(v)


def nap_ten_schema(goc):
    nap_duong_dan(goc)
    _nap(Path(goc))


def _cat(x, n=24):
    t = re.sub(r"[^\w .,;:()+\-]", "?", str(x))
    return t[:n] + ("…" if len(t) > n else "")


def _seg(x):
    s = str(x)
    return s if s in _TEN_BIET or re.fullmatch(r"[A-Za-z0-9_]{1,20}", s) else "[khoá]"


def _so_nguyen(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _duyet(x, duong, kq, sau=0):
    """Số không hữu hạn và lồng quá sâu ở BẤT KỲ đâu trong hồ sơ."""
    if sau > MAX_DO_SAU:
        kq.loi.append({"duong_dan": duong, "thong_bao": "hồ sơ lồng quá sâu"})
        return False
    if isinstance(x, float) and not math.isfinite(x):
        kq.loi.append({"duong_dan": duong, "thong_bao": "số không hữu hạn (NaN / Infinity)"})
    elif isinstance(x, dict):
        for k, v in x.items():
            if not _duyet(v, f"{duong}.{_seg(k)}" if duong else _seg(k), kq, sau + 1):
                return False
    elif isinstance(x, list):
        for i, v in enumerate(x[:1000]):
            if not _duyet(v, f"{duong}.{i}", kq, sau + 1):
                return False
    return True


def kiem_tra(j, cfg=None):
    cfg = cfg or CauHinh()
    kq = KetQua()
    if not isinstance(j, dict):
        kq.loi.append({"duong_dan": "", "thong_bao": "hồ sơ phải là một đối tượng JSON"})
        return kq
    nap_duong_dan(cfg.cpa2_root)
    validator, truong_hop_le, tin_chi = _nap(cfg.cpa2_root)         # trước _duyet: nạp tên trường schema cho _seg
    if not _duyet(j, "", kq) or kq.loi:
        return kq
    for e in sorted(validator.iter_errors(j), key=lambda e: list(map(str, e.absolute_path)))[:20]:
        # thông báo của jsonschema có thể kèm GIÁ TRỊ đầu vào → chỉ nêu loại lỗi, hoặc TÊN trường thiếu
        tb = (e.message if e.validator == "required" and re.fullmatch(r"'[a-z_0-9]+' is a required property", e.message) else
              f"không hợp lệ theo schema ({e.validator})" + (f": {e.validator_value}" if e.validator in ("maximum", "minimum", "type", "pattern", "enum")
                                                              and isinstance(e.validator_value, (int, float, str, list)) and len(str(e.validator_value)) < 80 else ""))
        kq.loi.append({"duong_dan": ".".join(_seg(x) for x in e.absolute_path), "thong_bao": tb})
    if kq.loi:
        return kq
    # --- kiểm chặt hơn schema
    if not _SV_ID.match(j["student_id"]):
        kq.loi.append({"duong_dan": "student_id", "thong_bao": "student_id sai dạng (sv_ + chữ thường, số, _)"})
    if len(str(j.get("ctdt", ""))) > 40:
        kq.loi.append({"duong_dan": "ctdt", "thong_bao": "ctdt quá dài"})
    for k, (lo, hi) in SO_NGUYEN.items():
        v = j.get(k)
        if v is not None and not (_so_nguyen(v) and lo <= v <= hi):
            kq.loi.append({"duong_dan": k, "thong_bao": f"{k} phải là số nguyên trong [{lo}, {hi}]"})
    for ten, tran in TRAN_DANH_SACH.items():
        if len(j.get(ten) or []) > tran:
            kq.loi.append({"duong_dan": ten, "thong_bao": f"quá nhiều mục ({len(j[ten])} > {tran})"})
    if kq.loi:
        return kq
    for i, c in enumerate(j.get("certificates", [])):
        d = c["diem"]
        if not (0 <= d <= 100000) or (c.get("bac") is not None and not _so_nguyen(c["bac"])):
            kq.loi.append({"duong_dan": f"certificates.{i}", "thong_bao": "điểm chứng chỉ ngoài [0, 100000] hoặc bậc không phải số nguyên"})
    for i, e in enumerate(j.get("exemptions", [])):
        if not _MA.match(e["ma_hp"]):
            kq.loi.append({"duong_dan": f"exemptions.{i}.ma_hp", "thong_bao": "mã học phần sai dạng (chỉ chữ, số, _; tối đa 20 ký tự)"})
    for i, c in enumerate(j.get("khong_tinh_tich_luy", [])):
        if not _MA.match(c):
            kq.loi.append({"duong_dan": f"khong_tinh_tich_luy.{i}", "thong_bao": "mã học phần sai dạng (chỉ chữ, số, _; tối đa 20 ký tự)"})
    gs = j["grades"]
    if len(gs) > cfg.max_grades:
        kq.loi.append({"duong_dan": "grades", "thong_bao": f"quá nhiều học phần ({len(gs)} > {cfg.max_grades})"})
        return kq
    for khoa, g in gs.items():
        if not _MA.match(khoa):
            kq.loi.append({"duong_dan": "grades.[khoá]", "thong_bao": "mã học phần sai dạng (chỉ chữ, số, _; tối đa 20 ký tự)"})
            continue
        if not _MA.match(str(g.get("code", ""))) or g["code"] != khoa:
            kq.loi.append({"duong_dan": f"grades.{khoa}.code", "thong_bao": "khoá bản ghi khác mã học phần (hoặc mã sai dạng)"})
        for tr, lo, hi in (("credits", 1, 15), ("thang10", 0, 100)):
            v = g.get(tr)
            if v is not None and not (_so_nguyen(v) and lo <= v <= hi):
                kq.loi.append({"duong_dan": f"grades.{khoa}.{tr}", "thong_bao": f"{tr} phải là số nguyên trong [{lo}, {hi}]"})
    if kq.loi:
        return kq
    # --- phạm vi (chỉ sau khi hồ sơ đã đúng dạng)
    sai = [f"{k}={_cat(j.get(k) if j.get(k) is not None else ('cntt_k49' if k == 'ctdt' else None))!r}" for k, v in PHAM_VI.items()
           if (j.get(k) if j.get(k) is not None else ("cntt_k49" if k == "ctdt" else None)) != v]
    if sai:
        kq.khong_ho_tro = f"{MO_TA_PHAM_VI}; hồ sơ này có " + ", ".join(sai)
        return kq
    for khoa, g in gs.items():
        if khoa not in tin_chi:
            kq.canh_bao.append(f"mã {khoa} không có trong CTĐT CNTT K49 — bỏ qua khi xét")
        elif g.get("credits") is not None and g["credits"] != tin_chi[khoa]:
            kq.loi.append({"duong_dan": f"grades.{khoa}.credits",
                           "thong_bao": f"số tín chỉ {khoa} = {g['credits']} khác CTĐT K49 = {tin_chi[khoa]} (tín chỉ không khớp)"})
    if kq.loi:
        return kq
    import loader as LD
    n_mt = sum(1 for ma, g in gs.items() if LD._loi_ban_ghi(ma, g))
    if n_mt > cfg.max_mau_thuan:
        # mỗi bản ghi tự mâu thuẫn mở 4 nhánh (F/D/A/điểm ghi) → thời gian solver tăng ~×4,5 mỗi bản ghi (đo: 1 → 0,3s; 4 → 21s; 6 → > 100s)
        kq.loi.append({"duong_dan": "grades", "thong_bao": f"{n_mt} bản ghi điểm tự mâu thuẫn (điểm chữ ≠ điểm số, trạng thái…); "
                                                          f"tối đa {cfg.max_mau_thuan} — hãy sửa hồ sơ trước khi hỏi"})
        return kq
    la = sorted(set(j) - truong_hop_le - {"meta"})
    if la:
        kq.canh_bao.append("trường không thuộc schema bị bỏ qua: " + ", ".join(_cat(x, 20) for x in la[:10]))
    kq.ho_so = {k: json.loads(json.dumps(v)) for k, v in j.items() if k in truong_hop_le}
    return kq
