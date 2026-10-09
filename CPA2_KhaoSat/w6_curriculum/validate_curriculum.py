"""
validate_curriculum.py — kiểm chứng Curriculum KB v1 (CPA², Tuần 6)
Tiêu chí hoàn thành của Tuần 6: "Solver đọc được curriculum".

  S. CẤU TRÚC — KB tự nhất quán; đột biến một con số làm KB vô nghiệm
  P. SOLVER ĐỌC ĐƯỢC CURRICULUM — ba cài đặt ĐỘC LẬP phải cho cùng đáp án:
       (1) clingo trên KB .lp   (2) OR-Tools CP-SAT trên JSON   (3) liệt kê thuần Python
     cho hai câu hỏi: số TC tối thiểu để hoàn thành CTĐT, và số kế hoạch tối thiểu khác nhau
  I. TÍCH HỢP VỚI R-FORMAL (QĐ3266 + QĐ5339) — kết luận học vụ trên CTĐT THẬT,
     gồm hồi quy cho ba lỗi L1–L3 phát hiện ở tuần này, và một ca ba trị (UNKNOWN)
  G. ĐỒ THỊ TIÊN QUYẾT — số liệu mô tả dùng cho luận văn (không phải kiểm tra đạt/trượt)

Chạy:  pip install clingo ortools     (ortools chỉ cần cho P2; thiếu thì P2 báo BỎ QUA)
       python3 build_curriculum.py && python3 validate_curriculum.py
Mã thoát: 0 đạt · 1 có lỗi · 2 đạt nhưng có phần bị bỏ qua.
"""
import itertools
import json
import re
import sys
from pathlib import Path

import clingo

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
SCHEMA = HERE / "curriculum_schema.lp"
FACTS = HERE / "curriculum_cntt_k49.lp"
PLAN = HERE / "kiem_tra_cau_truc.lp"
RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]
KB = json.loads((HERE / "curriculum_cntt_k49.json").read_text(encoding="utf-8"))

errors, skipped = [], []
OK, FAIL = "  [OK]  ", "  [FAIL]"


def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note:
        print("          ↳ " + note)
    if not cond:
        errors.append(msg)
    return cond


def txt(p):
    return p.read_text(encoding="utf-8")


def models(program, args=("--warn=none",), n=1):
    ctl = clingo.Control(list(args) + [f"--models={n}"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    out = []
    with ctl.solve(yield_=True) as h:
        for m in h:
            out.append({str(a) for a in m.symbols(atoms=True)})
    return out


def kb_program(extra="", rules=True):
    files = (RULES if rules else []) + [SCHEMA, FACTS]
    return "\n".join(txt(f) for f in files) + "\n" + extra


def solve_one(extra):
    ms = models(kb_program(extra), args=("--warn=none",))
    return ms[0] if ms else None


# =============================================================================
# S. CẤU TRÚC
# =============================================================================
def section_s():
    print("\nS. CẤU TRÚC KB")
    hp = KB["hoc_phan"]
    check(len(hp) == 78, f"S1 đủ 78 dòng học phần (có {len(hp)})")
    check(bool(models(kb_program(rules=False))), "S2 KB tự nhất quán: schema + dữ kiện có answer set",
          "các ràng buộc nội tại (dòng Cộng = tổng các dòng; không HP nào vừa BB vừa tự chọn) đều thoả")
    # đột biến: đổi 1 TC của một học phần bắt buộc → phải vô nghiệm
    bad = txt(FACTS).replace('course("CT177",3)', 'course("CT177",4)')
    check(not models("\n".join([txt(SCHEMA), bad])),
          "S3 đột biến CT177: 3→4 TC làm KB VÔ NGHIỆM (không im lặng cho số sai)")
    bad2 = txt(FACTS).replace("nhom_min_tc(g_tot_nghiep,15)", "nhom_min_tc(g_tot_nghiep,12)")
    check(not models("\n".join([txt(SCHEMA), bad2])),
          "S4 đột biến nhóm tốt nghiệp 15→12 TC làm KB VÔ NGHIỆM")
    # mọi why/2 của schema trỏ tới RuleId đã có rule_src/5 trong R-Formal
    src = set(re.findall(r"rule_src\((\w+),", "".join(txt(f) for f in RULES)))
    ids = set(re.findall(r"why\([^:]*?,\s*(r_\w+)\)", txt(SCHEMA)))
    check(ids <= src, f"S5 con trỏ nguồn của schema ({sorted(ids)}) đều có trong R-Formal",
          "Curriculum KB không đẻ RuleId mới; con số/thành viên nhóm mang nguồn qua ctdt_src/3")
    n_src = len(re.findall(r"ctdt_src\(", txt(FACTS)))
    check(n_src == 78, f"S6 mọi học phần có ctdt_src(mã, trang, dòng) ({n_src}/78)")


# =============================================================================
# P. SOLVER ĐỌC ĐƯỢC CURRICULUM — ba cài đặt độc lập
# =============================================================================
def clingo_min_and_count():
    base = "\n".join([txt(SCHEMA), txt(FACTS), txt(PLAN)])
    ctl = clingo.Control(["--warn=none", "--opt-mode=opt"])
    ctl.add("base", [], base + "\n#minimize{ CR,C : hoc(C), course(C,CR) }.")
    ctl.ground([("base", [])])
    best = None
    with ctl.solve(yield_=True) as h:
        for m in h:
            best = m.cost[0]
    ctl2 = clingo.Control(["--warn=none", "--models=0", "--project"])
    ctl2.add("base", [], base + f"\n:- tong_tc(T), T != {best}.")
    ctl2.ground([("base", [])])
    cnt = 0
    with ctl2.solve(yield_=True) as h:
        for _ in h:
            cnt += 1
    return best, cnt


def _closure_in(c, byma):
    h = byma[c]
    return h["tien_quyet"] + h["song_hanh"]


def python_min_and_count():
    """Liệt kê thuần Python — không dùng solver, không đọc file .lp."""
    byma = {h["ma"]: h for h in KB["hoc_phan"]}
    bb = [h for h in KB["hoc_phan"] if h["cot"] == "BB"]
    total_bb = sum(h["tin_chi"] for h in bb)
    tong_min, so_cach = total_bb, 1
    for g, spec in KB["nhom"].items():
        mem = [h["ma"] for h in KB["hoc_phan"] if h["cot"] == g]
        # tính độc lập giữa các nhóm: mọi tham chiếu của thành viên phải nằm trong nhóm
        for c in mem:
            for p in _closure_in(c, byma):
                assert byma[p]["cot"] in (g, "BB"), f"tham chiếu chéo nhóm {c}->{p}"
        best, cnt = None, 0
        for k in range(len(mem) + 1):
            for S in itertools.combinations(mem, k):
                S = set(S)
                if any(p not in S and byma[p]["cot"] == g
                       for c in S for p in _closure_in(c, byma)):
                    continue                       # không đóng dưới tiên quyết/song hành
                if spec["kieu"] == "tin_chi":
                    ok = sum(byma[c]["tin_chi"] for c in S) >= spec["min"]
                else:
                    ok = any(sum(byma[c]["tin_chi"] for c in S & set(lst)) >= spec["min"]
                             for lst in spec["nhanh"].values())
                if not ok:
                    continue
                tc = sum(byma[c]["tin_chi"] for c in S)
                if best is None or tc < best:
                    best, cnt = tc, 1
                elif tc == best:
                    cnt += 1
        tong_min += best
        so_cach *= cnt
    return tong_min, so_cach


def cpsat_min_and_count():
    hp = KB["hoc_phan"]
    byma = {h["ma"]: h for h in hp}

    def build():
        m = cp_model.CpModel()
        x = {h["ma"]: m.NewBoolVar(h["ma"]) for h in hp}
        for h in hp:
            if h["cot"] == "BB":
                m.Add(x[h["ma"]] == 1)
            for p in h["tien_quyet"] + h["song_hanh"]:
                m.AddImplication(x[h["ma"]], x[p])
        for g, spec in KB["nhom"].items():
            mem = [h["ma"] for h in hp if h["cot"] == g]
            if spec["kieu"] == "tin_chi":
                m.Add(sum(byma[c]["tin_chi"] * x[c] for c in mem) >= spec["min"])
            else:
                ys = []
                for b, lst in spec["nhanh"].items():
                    y = m.NewBoolVar(f"{g}_{b}")
                    m.Add(sum(byma[c]["tin_chi"] * x[c] for c in lst) >= spec["min"]).OnlyEnforceIf(y)
                    ys.append(y)
                m.AddBoolOr(ys)
        tong = sum(h["tin_chi"] * x[h["ma"]] for h in hp)
        for h in hp:
            if h["tien_quyet_tc"]:
                m.Add(tong - h["tin_chi"] >= h["tien_quyet_tc"]).OnlyEnforceIf(x[h["ma"]])
        return m, x, tong

    m, x, tong = build()
    m.Minimize(tong)
    s = cp_model.CpSolver()
    st = s.Solve(m)
    best = int(s.ObjectiveValue())
    m2, x2, tong2 = build()
    m2.Add(tong2 == best)

    class Cnt(cp_model.CpSolverSolutionCallback):
        def __init__(self, xs):
            super().__init__()
            self.xs, self.seen = xs, set()

        def on_solution_callback(self):
            self.seen.add(frozenset(c for c, v in self.xs.items() if self.Value(v)))

    s2 = cp_model.CpSolver()
    s2.parameters.enumerate_all_solutions = True
    cb = Cnt(x2)
    s2.Solve(m2, cb)
    return best, len(cb.seen), s.StatusName(st)


def section_p():
    print("\nP. SOLVER ĐỌC ĐƯỢC CURRICULUM — đối chiếu chéo ba cài đặt độc lập")
    c_min, c_cnt = clingo_min_and_count()
    p_min, p_cnt = python_min_and_count()
    tong = KB["meta"]["tong_khai_bao"]["tong"]
    check(c_min == tong, f"P1 clingo: số TC tối thiểu hoàn thành CTĐT = {c_min} (CTĐT ghi {tong})",
          "con số được TÍNH từ 78 dòng + 5 nhóm + tiên quyết/song hành, không chép từ dòng Tổng cộng")
    if cp_model is None:
        print("  [BỎ QUA] P2 — thiếu ortools")
        skipped.append("P2")
        k_min = k_cnt = None
    else:
        k_min, k_cnt, st = cpsat_min_and_count()
        check(k_min == c_min, f"P2 CP-SAT (đọc JSON, không đọc .lp): tối thiểu = {k_min} [{st}]")
    check(p_min == c_min, f"P3 liệt kê thuần Python: tối thiểu = {p_min}")
    counts = {"clingo": c_cnt, "python": p_cnt}
    if k_cnt is not None:
        counts["cp-sat"] = k_cnt
    check(len(set(counts.values())) == 1,
          f"P4 số kế hoạch tối thiểu khác nhau trùng khớp: {counts}",
          "= 2 (ngoại ngữ: AV/PV, buộc từ căn bản 1 do chuỗi song hành) × 7 (nhóm xã hội) "
          "× 3 (CN1/CN2/CN3) × 57 (nhóm 15 TC: LVTN | TLTN+3 HP | 5 HP)")
    return counts


# =============================================================================
# I. TÍCH HỢP VỚI R-FORMAL
# =============================================================================
BB = [h["ma"] for h in KB["hoc_phan"] if h["cot"] == "BB"]


def sv(chon, diem=80, bo=(), them=""):
    """Hồ sơ tổng hợp: đạt mọi HP bắt buộc (trừ `bo`) + các HP tự chọn trong `chon`."""
    ds = [c for c in BB if c not in bo] + list(chon)
    return "\n".join(f'g10("{c}",{diem}).' for c in ds) + "\n" + them


CHUAN = ["TC100", "XH023", "XH024", "XH025", "ML007", "CT449", "CT484"]
KY_LUAT = "xac_nhan_ky_luat_sach.\n"


def tri_tri(atom, extra):
    """Ba trị bằng cautious/brave trên mọi answer set (Tuần 4, mục 2)."""
    ms = models(kb_program(extra), n=0)
    ms = [m for m in ms]
    if not ms:
        return "UNSAT"
    co = [atom in m for m in ms]
    return "TRUE" if all(co) else ("FALSE" if not any(co) else "UNKNOWN")


def tri_tri_ton_tai(atom, extra):
    """Ba trị khi SV còn QUYỀN CHỌN (CQ-06): ∀ thế giới dữ kiện ∃ cách chọn.
    Thế giới = tập điểm g10/2; các answer set cùng thế giới khác nhau ở lựa chọn."""
    ms = models(kb_program(extra), n=0)
    if not ms:
        return "UNSAT"
    the_gioi = {}
    for m in ms:
        k = frozenset(a for a in m if a.startswith("g10("))
        the_gioi[k] = the_gioi.get(k, False) or (atom in m)
    v = list(the_gioi.values())
    return "TRUE" if all(v) else ("FALSE" if not any(v) else "UNKNOWN")


def section_i():
    print("\nI. TÍCH HỢP VỚI R-FORMAL (QĐ3266 + QĐ5339) TRÊN CTĐT THẬT")
    T = []

    def t(name, extra, yes=(), no=(), note=""):
        m = solve_one(extra)
        if m is None:
            check(False, name + " — VÔ NGHIỆM", note)
            return
        miss = [a for a in yes if a not in m] + [a for a in no if a in m]
        check(not miss, name + (f"   (lệch: {miss})" if miss else ""), note)
        T.append(name)

    t("I1 SV đủ: AV căn bản 1–3, CN2, LVTN 15 TC → tot_nghiep",
      sv(CHUAN + ["CT550E"], them=KY_LUAT), yes=["tot_nghiep", "tc_tich_luy(161)"],
      note="HỒI QUY L1: R-Formal v1.4 cho FALSE vì đòi đạt cả 12 HP ngoại ngữ (40 TC)")
    t("I2 SV đủ theo hình thức TLTN 6 TC + 3 HP tự chọn → tot_nghiep",
      sv(CHUAN + ["CT501E", "CT478", "CT283", "CT233"], them=KY_LUAT), yes=["tot_nghiep"])
    t("I3 SV không làm LVTN/TLTN, học 5 HP tự chọn 3 TC → tot_nghiep",
      sv(CHUAN + ["CT478", "CT283", "CT233", "CT482", "CT210"], them=KY_LUAT),
      yes=["tot_nghiep"], note="QĐ3266 Đ.31 k.3 (R-F05) hiện hình đúng trong ô gộp '15' của CTĐT")
    t("I4 Đủ 164 TC nhưng THIẾU nhóm 15 TC tốt nghiệp → KHÔNG tốt nghiệp",
      sv(CHUAN + ["CT211", "CT297", "CT522", "CT279", "XH028", "XH011", "XH012", "XH014",
                  "KN001E", "KN002E"], them=KY_LUAT),
      yes=["dk_tin_chi", "thieu_nhom(g_tot_nghiep,15)"], no=["dk_tu_chon", "tot_nghiep"],
      note="HỒI QUY L2 (dương tính giả): v1.4 bỏ qua mọi nhóm đếm tín chỉ → dk_tu_chon đúng rỗng")
    t("I5 Trộn ngoại ngữ: AV 4 TC + PV 7 TC = 11 TC → nhóm ngoại ngữ CHƯA đạt",
      sv(["TC100", "XH023", "FL001", "FL002", "ML007", "CT449", "CT484", "CT550E"], them=KY_LUAT),
      yes=["thieu_nhom(g_ngoai_ngu,3)"], no=["dk_hp_dieu_kien", "tot_nghiep"],
      note="ô '10 AV hoặc PV' là nhóm MỘT NHÁNH: tín chỉ không cộng dồn qua hai ngoại ngữ (CQ-02)")
    t("I6 Mới 30 TC → CT550E CHƯA được đăng ký, thiếu 90 TC",
      'g10(x,80). course(x,30).', yes=['thieu_tc("CT550E",90)'], no=['du_dk_dang_ky("CT550E")'],
      note="HỒI QUY L3: v1.4 kết luận du_dk_dang_ky(\"CT550E\") vì chỉ xét tiên quyết học phần")
    t("I7 Song hành: XH024 xếp HK1, XH023 xếp HK2 → vi phạm",
      "xep_hk(\"XH024\",1). xep_hk(\"XH023\",2).", yes=['vi_pham_song_hanh("XH024","XH023")'])
    t("I8 CT182: tiên quyết CT176, SONG HÀNH CT180 → đạt CT176 là đủ để đăng ký",
      'g10("CT176",70).', yes=['du_dk_dang_ky("CT182")'],
      note="CT180 ở cột song hành, không phải tiên quyết — học cùng kỳ được")
    t("I9 Hai HP chéo cặp (CT211 của CN1 + CT449 của CN2) → nhóm chuyên ngành CHƯA đạt",
      'g10("CT211",80). g10("CT449",80).', no=["dat_nhom(g_chuyen_nganh)"],
      yes=["thieu_nhom(g_chuyen_nganh,3)"])
    thieu_nn = sv(["TC100", "ML007", "CT449", "CT484", "CT550E"],
                  them=KY_LUAT + "da_hoc_nam2(19).")
    t("I10a Quá hạn, chỉ thiếu nhóm điều kiện (ngoại ngữ), cách đọc CHẶT → KHÔNG được quay lại",
      thieu_nn, yes=["tc_dk_ctdt(21)", "tc_tich_luy(151)"], no=["duoc_quay_lai(3)", "dk_tin_chi"],
      note="PHÁT HIỆN (CQ-05): 161 TC gồm 21 TC điều kiện → thiếu HP điều kiện là thiếu luôn TC ở "
           "đ.a, nên Đ.33 k.2 không kích hoạt được trừ khi SV học dư tự chọn để bù đúng số TC điều kiện thiếu")
    t("I10b Cùng hồ sơ, chính sách tc_khong_gom_dk → được quay lại trong 3 năm",
      thieu_nn + "chinh_sach_bat(tc_khong_gom_dk).",
      yes=["duoc_quay_lai(3)", "dk_tin_chi", "dien_giai(cq05)"],
      note="CHỈ để phân tích độ nhạy: CQ-05 đã đóng theo cách đọc chặt (I10a); kết luận mang cờ dien_giai(cq05)")
    t("I11 Học phần (*) không vào ĐTBCTL: AV điểm 4,0 không kéo ĐTBCTL xuống dưới 2,00",
      sv(["TC100", "ML007", "CT449", "CT484", "CT550E"], diem=60,
         them='g10("XH023",40). g10("XH024",40). g10("XH025",40).' + KY_LUAT),
      yes=["dk_dtbctl", "dk_hp_dieu_kien"])

    # --- CQ-06: SV chọn học phần tự chọn để tích lũy khi xét tốt nghiệp -------------
    tb = sv(CHUAN + ["CT550E"], diem=55, them=KY_LUAT + 'g10("CT478",45).')   # C=2,0 ; dư CT478 điểm D
    t("I15 Học dư CT478 điểm D, tính tất cả → ĐTBCTL < 2,00, KHÔNG tốt nghiệp",
      tb, yes=["tc_tich_luy(164)"], no=["dk_dtbctl", "tot_nghiep"],
      note="cách tính của v1.4 (mọi HP đạt đều vào tích lũy) phạt SV vì học thêm")
    t("I16 Cùng hồ sơ, SV chọn KHÔNG tính CT478 → ĐTBCTL = 2,00, tốt nghiệp",
      tb + 'khong_tinh_tich_luy("CT478").',
      yes=["tc_tich_luy(161)", "dk_dtbctl", "tot_nghiep", "dien_giai(cq06)", 'passed("CT478")'],
      note="CQ-06: HP không chọn vẫn 'đã đạt' (thỏa tiên quyết) nhưng ra khỏi TC tích lũy, ĐTBCTL và nhóm")
    t("I17 Loại CT550E — HP duy nhất phủ nhóm tốt nghiệp → thiếu nhóm, KHÔNG tốt nghiệp",
      sv(CHUAN + ["CT550E"], them=KY_LUAT + 'khong_tinh_tich_luy("CT550E").'),
      yes=["thieu_nhom(g_tot_nghiep,15)"], no=["tot_nghiep"],
      note="quyền chọn không phải miễn phí: hệ thống vẫn xét lại mọi điều kiện trên tập đã chọn")
    check(solve_one(sv(CHUAN + ["CT550E"], them='khong_tinh_tich_luy("CT177").')) is None,
          "I18 Loại một HP BẮT BUỘC (CT177) khỏi tích lũy → VÔ NGHIỆM",
          "chỉ HP thuộc nhóm tự chọn mới được SV chọn bỏ")
    t("I19 Làm CẢ LVTN và TLTN → vẫn tốt nghiệp, kèm khuyến nghị (không phải vi phạm)",
      sv(CHUAN + ["CT550E", "CT501E"], them=KY_LUAT),
      yes=["tot_nghiep", "tc_tich_luy(167)", "khuyen_nghi(khong_lam_ca_lvtn_tltn)"],
      note="CQ-06: không có quy định cấm làm cả hai; 'không nên' là khuyến nghị cho nhánh Recommendation")
    # ∀ thế giới ∃ lựa chọn
    ab = sv(CHUAN + ["CT550E"], diem=55,
            them=KY_LUAT + '{ g10("CT478",80); g10("CT478",45) } = 1.')
    v_all = tri_tri("tot_nghiep", ab)
    v_chon = tri_tri_ton_tai("tot_nghiep", ab + "che_do(sv_chon_tich_luy).")
    v_sai = tri_tri("tot_nghiep", ab + "che_do(sv_chon_tich_luy).")
    check((v_all, v_chon, v_sai) == ("UNKNOWN", "TRUE", "UNKNOWN"),
          f"I20 Chưa rõ điểm HP dư CT478: tính-tất-cả = {v_all}; có quyền chọn (∀∃) = {v_chon}",
          "đúng là TRUE: điểm nào thì SV cũng bỏ được CT478. Cautious ngây thơ trên toàn bộ "
          f"answer set cho {v_sai} — SAI lượng từ; phải nhóm theo thế giới dữ kiện rồi mới ∃ trên lựa chọn")

    # ba trị
    unk = sv(CHUAN, them=KY_LUAT + '{ g10("CT550E",80); g10("CT550E",30) } = 1.')
    v = tri_tri("tot_nghiep", unk)
    check(v == "UNKNOWN", f"I12 Chưa có điểm LVTN → tot_nghiep = {v} (mong đợi UNKNOWN)",
          "ba trị là HỆ QUẢ của mô hình (cautious/brave), không phải nhánh if do người viết")
    v2 = tri_tri("tot_nghiep", sv(CHUAN + ["CT550E"], them=KY_LUAT))
    check(v2 == "TRUE", f"I13 Đủ dữ kiện → tot_nghiep = {v2}")
    v3 = tri_tri("tot_nghiep", sv(CHUAN + ["CT550E"]))
    check(v3 == "FALSE", f"I14 Thiếu xác nhận kỷ luật → tot_nghiep = {v3}",
          "đúng thiết kế R-F03: trục kỷ luật là dữ kiện ngoài phạm vi, không bao giờ tự suy ra")


# =============================================================================
# G. ĐỒ THỊ TIÊN QUYẾT — số liệu mô tả
# =============================================================================
def section_g():
    print("\nG. ĐỒ THỊ TIÊN QUYẾT (mô tả)")
    hp = {h["ma"]: h for h in KB["hoc_phan"]}
    tq = sum(len(h["tien_quyet"]) for h in hp.values())
    sh = sum(len(h["song_hanh"]) for h in hp.values())
    t4b = [(h["ma"], h["tien_quyet_tc"]) for h in hp.values() if h["tien_quyet_tc"]]
    memo = {}

    def depth(c):
        if c not in memo:
            memo[c] = 1 + max([depth(p) for p in hp[c]["tien_quyet"]], default=0)
        return memo[c]
    d = max(depth(c) for c in hp)
    chain = [c for c in hp if depth(c) == d]
    print(f"  · {tq} cạnh tiên quyết học phần (T4a), {sh} cạnh song hành, "
          f"{len(t4b)} ngưỡng tín chỉ (T4b): {t4b}")
    print(f"  · chuỗi tiên quyết (T4a) dài nhất: {d} học phần — kết thúc ở {sorted(chain)}")
    goc = sorted(c for c in hp if hp[c]["cot"] == "BB" and not hp[c]["tien_quyet"]
                 and any(c in h["tien_quyet"] for h in hp.values()))
    print(f"  · học phần gốc có kế thừa: {goc}")
    print(f"  · chỉ mở HK III: {[c for c in hp if hp[c]['hk'] == ['III']]}")


def main():
    print("=" * 78)
    print("VALIDATE CURRICULUM KB v1 — CTĐT CNTT K49 (" + KB["meta"]["van_ban_ten"] + ")")
    print("=" * 78)
    section_s()
    section_p()
    section_i()
    section_g()
    print("\n" + "=" * 78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors:
            print("  ·", e)
        return 1
    print("KẾT LUẬN: ĐẠT" + (f" (bỏ qua: {skipped})" if skipped else "") + ".")
    return 2 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
