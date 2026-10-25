"""
validate_student_facts.py — kiểm chứng Student Fact Model Tuần 7 trên Curriculum KB v1 + R-Formal v1.5
Kiểm 5 hồ sơ giả lập theo student_fact_schema.json, rồi chạy qua solver, đối chiếu tot_nghiep / thieu_nhom / tc_tich_luy.

Chạy: python validate_student_facts.py
"""
import json, sys
from pathlib import Path
import clingo
import jsonschema

HERE = Path(__file__).parent
W5 = HERE.parent / "w5_rformal"
W6 = HERE.parent / "w6_curriculum"
STUDENTS = HERE / "students"
SCHEMA = HERE / "student_fact_schema.json"

CURRICULUM = [W6 / "curriculum_schema.lp", W6 / "curriculum_cntt_k49.lp"]
RULES = [W5 / "qd3266_r_formal_v1.lp", W5 / "qd5339_r_formal_v1.lp"]

def load_facts(j):
    """Hồ sơ → dữ kiện ASP. Dùng loader chung (loader.py): rà soát mâu thuẫn + quy ước ×10 cho chứng chỉ."""
    from loader import sang_asp
    return sang_asp(j)[0]

def solve(extra):
    prog = "\n".join(p.read_text(encoding="utf-8") for p in RULES + CURRICULUM) + "\n" + extra
    ctl = clingo.Control(["--warn=none","--models=1"])
    ctl.add("base",[],prog)
    ctl.ground([("base",[])])
    out=set()
    with ctl.solve(yield_=True) as h:
        for m in h:
            out={str(a) for a in m.symbols(atoms=True)}
            break
    return out

EXPECT = {
    "sv_lvtn": (["tot_nghiep","tc_tich_luy(161)"], [], "I1 LVTN 15TC"),
    "sv_tltn": (["tot_nghiep"], [], "I2 TLTN 6+3HP"),
    "sv_5hp": (["tot_nghiep"], [], "I3 5HP thay LVTN"),
    "sv_tron_ngoai_ngu": (["thieu_nhom(g_ngoai_ngu,3)"], ["tot_nghiep"], "I5 trộn AV/PV"),
    "sv_du_hp": (["dtbctl_lt(20)"], ["tot_nghiep"], "I15 học dư CT478 điểm D — chưa chọn bỏ nên KHÔNG tốt nghiệp (ĐTBCTL <2.0)"),
    "sv_mien_ielts": (["tot_nghiep", "tc_tich_luy(161)", 'exempted_m("XH023")', 'diem_m("XH025")', "dat_nhom(g_ngoai_ngu)"],
                      ['du_dk_xin_mien("FL001")', 'mien_treo("FL001")'],
                      "QD-11 miễn 10 TC Anh văn bằng IELTS 6.0; IELTS không mở quyền xin miễn Pháp văn"),
}

def kiem_loader_chung():
    """L. Loader dùng chung (sau Tuần 17): mọi đường vào (w7, w11 certificate, w12 prototype, w16 abstention)
    sinh CÙNG một ASP từ cùng hồ sơ — kể cả rà soát hồ sơ mâu thuẫn (P17-1) và lựa chọn tích lũy (CQ-06)."""
    import importlib.util, tempfile
    def nap(ten, f):
        spec = importlib.util.spec_from_file_location(ten, HERE.parent / f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    w11 = nap("generate_certificate", "w11_proof/generate_certificate.py")
    w12 = nap("prototype", "w12_integration/prototype.py")
    ok = True
    ho_so = {n: json.loads((STUDENTS / f"{n}.json").read_text(encoding="utf-8")) for n in EXPECT}
    mt = json.loads(json.dumps(ho_so["sv_lvtn"]))
    mt["grades"]["CT177"].update(thang10=80, letter="F", status="failed")          # bản ghi tự mâu thuẫn
    ho_so["mau_thuan"] = mt
    cd = json.loads(json.dumps(ho_so["sv_du_hp"]))
    cd["che_do_sv_chon_tich_luy"] = True                                           # CQ-06
    ho_so["che_do"] = cd
    with tempfile.TemporaryDirectory() as d:
        for ten, j in ho_so.items():
            f = Path(d) / f"{ten}.json"
            f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            ra = {"w7": load_facts(j), "w11": w11.load_student(f), "w12": w12.load_student(f)[0]}
            giong = len(set(ra.values())) == 1
            if not giong:
                ok = False
            print(f"[{'OK' if giong else 'FAIL'}] L1 {ten}: w7 = w11 = w12 (cùng ASP)")
    good = '1 { g10("CT177"' in load_facts(mt)
    print(f"[{'OK' if good else 'FAIL'}] L2 w7 load_facts rà soát bản ghi mâu thuẫn (CT177 8,0 ghi F → mở)")
    # L3 chống chép lại loader: chỉ loader.py được sinh dữ kiện chứng chỉ (quy ước ×10) và khai báo kỷ luật
    dau_hieu = ("chung_chi({", "khai_bao(ky_luat).", "khai_bao(hinh_thuc).")
    chep = [str(f.relative_to(HERE.parent)) for f in sorted(HERE.parent.glob("w*/*.py"))
            if f.name != "loader.py" and not f.name.startswith("validate_")   # test viết ASP tay, không phải loader
            and any(d in f.read_text(encoding="utf-8") for d in dau_hieu)]
    print(f"[{'OK' if not chep else 'FAIL'}] L3 không file nào ngoài loader.py tự đổi hồ sơ → ASP ({chep})")
    good = good and not chep
    # L4 (R-A04 Đ7 k5): loader sinh da_hoc(C) cho mọi bản ghi có học (kể cả F, I), KHÔNG cho W (đã rút)
    hs = {"grades": {"AA001": {"code": "AA001", "thang10": 30, "letter": "F", "status": "failed"},
                     "AA002": {"code": "AA002", "thang10": None, "letter": None, "diem": "I", "status": "unknown"},
                     "AA003": {"code": "AA003", "thang10": None, "letter": "W", "diem": "W", "status": "failed"}}}
    asp4 = load_facts(hs)
    l4 = 'da_hoc("AA001").' in asp4 and 'da_hoc("AA002").' in asp4 and 'da_hoc("AA003")' not in asp4
    print(f"[{'OK' if l4 else 'FAIL'}] L4 loader: da_hoc cho bản ghi F và I, không cho W")
    good = good and l4
    # L5 (C15, Đ34 k2): khai báo hạ bậc — tc_diem_f (TC HP từng bị F, không tính học cải thiện) và kỷ luật từ mức cảnh cáo
    # cấp Trường. Có khai báo → dữ kiện + khai_bao(...) (đóng nhánh); thiếu → KB mở nhánh; khai báo sai kiểu/âm → mâu
    # thuẫn, bỏ khai báo (để nhánh mở). tc_diem_f KHÔNG tính HP điều kiện (loader không biết HP nào là điều kiện) → không
    # so với TC đang F ở loader; KB lấy giá trị LỚN HƠN giữa khai báo và TC HP không điều kiện đang F
    f5 = {"grades": {"AA001": {"code": "AA001", "credits": 4, "thang10": 30, "letter": "F", "status": "failed"}}}
    a1, m1 = __import__("loader").sang_asp({**f5, "tc_diem_f": 7, "ky_luat_canh_cao_cap_truong": True})
    a2, m2 = __import__("loader").sang_asp({**f5, "tc_diem_f": 4, "ky_luat_canh_cao_cap_truong": False})
    a3, m3 = __import__("loader").sang_asp(f5)
    a4, m4 = __import__("loader").sang_asp({**f5, "tc_diem_f": 2})
    a5, m5 = __import__("loader").sang_asp({**f5, "tc_diem_f": -1, "ky_luat_canh_cao_cap_truong": "co"})
    l5 = ("tc_diem_f(7)." in a1 and "ky_luat_canh_cao_cap_truong." in a1 and "khai_bao(ky_luat_cap_truong)." in a1
          and "tc_diem_f(4)." in a2 and "ky_luat_canh_cao_cap_truong." not in a2 and "khai_bao(ky_luat_cap_truong)." in a2
          and "tc_diem_f(" not in a3 and "khai_bao(ky_luat_cap_truong)" not in a3 and not m3
          and "tc_diem_f(2)." in a4 and not m4 and "tc_diem_f(" not in a5 and "ky_luat_cap_truong" not in a5 and len(m5) == 2)
    print(f"[{'OK' if l5 else 'FAIL'}] L5 loader: khai báo hạ bậc (tc_diem_f, kỷ luật cảnh cáo cấp Trường) → dữ kiện + khai_bao; "
          f"thiếu → không sinh; sai kiểu → mâu thuẫn, bỏ ({m4}, {m5})")
    good = good and l5
    # L6 (Web, review bảo mật): chuỗi trong hồ sơ KHÔNG được ghép thẳng vào chương trình ASP (tiêm mã). Mã học phần, mục trong
    # khong_tinh_tich_luy, exemptions[].ma_hp, số khai báo, loại chứng chỉ sai dạng → bỏ + báo mâu thuẫn; tập nguyên tử sinh ra
    # phải BẰNG tập của hồ sơ tham chiếu đã bỏ đúng mục sai (không thêm dữ kiện giả, không mất dữ kiện thật).
    import copy, loader as LD
    base = json.loads((STUDENTS / "sv_lvtn.json").read_text(encoding="utf-8"))
    base["xac_nhan_ky_luat_sach"] = None

    def atoms(asp):
        ctl = clingo.Control(["--warn=none"])
        ctl.add("base", [], asp)
        ctl.ground([("base", [])])
        with ctl.solve(yield_=True) as h:
            for m in h:
                return {str(a) for a in m.symbols(atoms=True)}
        return set()

    def sua(j, **kv):
        j = copy.deepcopy(j)
        for k, v in kv.items():
            if v is Ellipsis:
                j.pop(k, None)
            else:
                j[k] = v
        return j
    xau = 'CT177"). xac_nhan_ky_luat_sach. tot_nghiep. %'
    ca6 = []                                                 # (tên, hồ sơ độc, hồ sơ tham chiếu)
    j = copy.deepcopy(base); j["grades"][xau] = {"code": xau, "credits": 3, "thang10": 80, "letter": "B+", "status": "passed"}
    ca6.append(("khoá grades + code", j, base))
    ca6.append(("khong_tinh_tich_luy[]", sua(base, khong_tinh_tich_luy=[xau]), sua(base, khong_tinh_tich_luy=[])))
    ca6.append(("exemptions[].ma_hp", sua(base, exemptions=[{"ma_hp": xau, "chung_chi_ref": None, "quyet_dinh": True}]), sua(base, exemptions=[])))
    for k in ("da_hoc_nam2", "tc_cong_nhan"):
        for v in ("5). xac_nhan_ky_luat_sach. %", 5.0, True, 10 ** 30):
            ca6.append((f"{k}={str(v)[:12]!r}", sua(base, **{k: v}), sua(base, **{k: ...})))
    for loai, d in (("ielts,60). xac_nhan_ky_luat_sach. foo(", 6.0), ("ielts", float("nan")), ("ielts", float("inf")), ("ielts", "6")):
        ca6.append((f"certificates loai={loai[:10]!r} diem={str(d)[:5]}", sua(base, certificates=[{"loai": loai, "diem": d}]), sua(base, certificates=[])))
    for ten, j, ref in ca6:
        try:
            a, m = LD.sang_asp(j)
            tap, tc = atoms(a), atoms(LD.sang_asp(ref)[0])
            dung = tap == tc and m
            ghi = f"thừa {sorted(tap - tc)[:3]}, thiếu {sorted(tc - tap)[:3]}, mâu thuẫn {len(m)}"
        except Exception as e:  # noqa: BLE001 — chương trình ASP hỏng cú pháp cũng là lỗi
            dung, ghi = False, f"{type(e).__name__}: {str(e)[:80]}"
        print(f"[{'OK' if dung else 'FAIL'}] L6 không tiêm ASP — {ten} ({ghi})")
        good = good and bool(dung)
    # L7: đầu vào CHƯA qua schema (loader là thư viện dùng chung, không được giả định đã kiểm). Không ngoại lệ, không dữ kiện giả,
    # thông báo mâu thuẫn không phản hồi lại chuỗi thô (xuống dòng, nháy, #).
    doc = 'X\n#include "/etc/passwd"'
    ca7 = [("grades = null", sua(base, grades=None)), ("grades = danh sách", sua(base, grades=[1, 2])), ("grades = chuỗi", sua(base, grades="x")),
           ("thang10 = 10**400", sua(base, grades={**base["grades"], "CT177": {**base["grades"]["CT177"], "thang10": 10 ** 400}})),
           ("credits chuỗi + da_hoc_nam2", sua(base, da_hoc_nam2=4, grades={**base["grades"], "CT177": {**base["grades"]["CT177"], "credits": "ba"}})),
           ("credits âm / khổng lồ", sua(base, da_hoc_nam2=4, grades={**base["grades"], "CT177": {**base["grades"]["CT177"], "credits": -5}, "CT174": {**base["grades"]["CT174"], "credits": 10 ** 12}})),
           ("exemptions thiếu quyet_dinh", sua(base, exemptions=[{"ma_hp": "CT100"}])),
           ("exemptions quyet_dinh = 'no'", sua(base, exemptions=[{"ma_hp": "CT100", "chung_chi_ref": None, "quyet_dinh": "no"}])),
           ("che_do_sv_chon_tich_luy = 'false'", sua(base, che_do_sv_chon_tich_luy="false")),
           ("tc_diem_f = 10**12", sua(base, tc_diem_f=10 ** 12)),
           ("letter độc", sua(base, grades={**base["grades"], "CT177": {**base["grades"]["CT177"], "letter": doc}})),
           ("status độc", sua(base, grades={**base["grades"], "CT177": {**base["grades"]["CT177"], "status": doc, "thang10": 90, "letter": "F"}})),
           ("hinh_thuc_cuoi_khoa độc", sua(base, hinh_thuc_cuoi_khoa='lvtn"). evil. %')),
           ("ky_luat_canh_cao_cap_truong độc", sua(base, ky_luat_canh_cao_cap_truong=doc)), ("tc_diem_f độc", sua(base, tc_diem_f=doc))]
    ca7.append(("certificates diem = 10**400", sua(base, certificates=[{"loai": "ielts", "diem": 10 ** 400}])))
    for ten, j in ca7:
        try:
            a, m = LD.sang_asp(j)
            tap = atoms(a)
            msg = "\n".join(m)
            dung = ("xac_nhan_ky_luat_sach" not in tap and "tot_nghiep" not in tap and "evil" not in tap and "duoc_mien(\"CT100\")" not in tap
                    and "che_do(sv_chon_tich_luy)" not in tap and not any(c in msg for c in ('\n#', '"/', 'passwd"')) and len(msg) < 4000)
            ghi = f"mâu thuẫn {len(m)}"
        except Exception as e:  # noqa: BLE001
            dung, ghi = False, f"{type(e).__name__}: {str(e)[:80]}"
        print(f"[{'OK' if dung else 'FAIL'}] L7 loader chịu được đầu vào chưa qua schema — {ten} ({ghi})")
        good = good and bool(dung)
    # L8: trùng lặp HỢP LỆ theo schema không được làm rơi quyết định: miễn HP có hai mục (một chưa/một đã có quyết định) vẫn được miễn;
    # khong_tinh_tich_luy trùng không sinh thông báo mâu thuẫn thừa.
    j = sua(base, exemptions=[{"ma_hp": "CT101", "chung_chi_ref": None, "quyet_dinh": False}, {"ma_hp": "CT101", "chung_chi_ref": 0, "quyet_dinh": True}],
            khong_tinh_tich_luy=["TC100", "TC100"])
    a, m = LD.sang_asp(j)
    tap = atoms(a)
    dung = 'duoc_mien("CT101")' in tap and not m
    print(f"[{'OK' if dung else 'FAIL'}] L8 miễn HP trùng mục (OR quyết định), khong_tinh_tich_luy trùng không báo mâu thuẫn ({sorted(x for x in tap if 'mien' in x)}, {len(m)} mâu thuẫn)")
    good = good and dung
    return ok and good


def main():
    ok=True
    validator=jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    for name, (yes,no,note) in EXPECT.items():
        j=json.loads((STUDENTS / f"{name}.json").read_text(encoding="utf-8"))
        errs=list(validator.iter_errors(j))
        if errs:
            print(f"[FAIL] {name}: sai schema — {[e.message for e in errs[:3]]}")
            ok=False
            continue
        m=solve(load_facts(j))
        miss=[a for a in yes if a not in m]
        extra=[a for a in no if a in m]
        status="OK" if not miss and not extra else "FAIL"
        print(f"[{status}] {name}: {note}")
        if miss: print(f"  thiếu: {miss}")
        if extra: print(f"  thừa: {extra}")
        if status=="FAIL": ok=False
        # kiểm thêm hồ sơ sv_du_hp khi chọn bỏ CT478 → phải tốt nghiệp
        if name=="sv_du_hp":
            j2=dict(j); j2["khong_tinh_tich_luy"]=["CT478"]
            m2=solve(load_facts(j2))
            if "tot_nghiep" in m2 and "tc_tich_luy(161)" in m2:
                print(f"  [OK] sv_du_hp + khong_tinh_tich_luy(CT478) → tot_nghiep (CQ-06)")
            else:
                print(f"  [FAIL] sv_du_hp bỏ CT478 vẫn chưa tốt nghiệp: {sorted([x for x in m2 if 'tot_nghiep' in x or 'tc_tich' in x])}")
                ok=False
        # QD-11: XH025 mới đủ ĐK (quyet_dinh=false) → mien_treo, nhóm ngoại ngữ thiếu 3
        if name=="sv_mien_ielts":
            j2=json.loads(json.dumps(j)); j2["exemptions"][2]["quyet_dinh"]=False
            m2=solve(load_facts(j2))
            good='mien_treo("XH025")' in m2 and "thieu_nhom(g_ngoai_ngu,3)" in m2 and "tot_nghiep" not in m2
            print(f"  [{'OK' if good else 'FAIL'}] sv_mien_ielts, XH025 chưa có QĐ → mien_treo, thiếu ngoại ngữ 3 TC (QD-11)")
            ok=ok and good
    # loader: mọi loại điểm chứng chỉ (trừ ctu_abc) phải nhân 10 cho khớp nguong_cc
    f=load_facts({"grades":{}, "certificates":[{"loai":"toeic","diem":600},{"loai":"ielts","diem":5.5},{"loai":"ctu_abc","diem":3}]})
    good=all(x in f for x in ("chung_chi(toeic,6000).","chung_chi(ielts,55).","chung_chi(ctu_abc,3)."))
    print(f"[{'OK' if good else 'FAIL'}] loader quy đổi điểm chứng chỉ ×10 (TOEIC 600→6000, IELTS 5.5→55, ctu_abc giữ bậc)")
    ok=ok and good
    ok = kiem_loader_chung() and ok
    print("\nKẾT LUẬN:", f"ĐẠT {len(EXPECT)}/{len(EXPECT)} hồ sơ + loader" if ok else "CÓ LỖI")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())
