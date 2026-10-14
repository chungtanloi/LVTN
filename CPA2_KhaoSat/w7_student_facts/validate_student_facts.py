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
    lines=[]
    for code, g in j["grades"].items():
        th = g.get("thang10")
        diem = g.get("diem")
        if diem == "M":
            lines.append(f'diem_m("{code}").')
        elif diem == "W":
            lines.append(f'diem_w("{code}").')
        elif diem == "I":
            lines.append(f'diem_i("{code}").')
        elif th is not None:
            lines.append(f'g10("{code}",{th}).')
    for c in j.get("khong_tinh_tich_luy", []):
        lines.append(f'khong_tinh_tich_luy("{c}").')
    if j.get("che_do_sv_chon_tich_luy"):
        lines.append("che_do(sv_chon_tich_luy).")
    if j.get("xac_nhan_ky_luat_sach") is True:
        lines.append("xac_nhan_ky_luat_sach.")
    elif j.get("xac_nhan_ky_luat_sach") is False:
        lines.append("khai_bao(ky_luat).")   # đã khai báo "không" → FALSE; null/thiếu → mở nhánh (Tuần 16)
    for k in ("da_hoc_nam2", "tc_cong_nhan"):
        if j.get(k) is not None:
            lines.append(f"{k}({j[k]}).")
    # certificates → chung_chi
    for cert in j.get("certificates", []):
        loai = cert["loai"]
        diem = int(cert["diem"]) if loai == "ctu_abc" else round(cert["diem"]*10)  # nguong_cc lưu điểm ×10
        lines.append(f'chung_chi({loai},{diem}).')
    for ex in j.get("exemptions", []):
        if ex["quyet_dinh"]:
            lines.append(f'duoc_mien("{ex["ma_hp"]}").')
    return "\n".join(lines)

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
    print("\nKẾT LUẬN:", f"ĐẠT {len(EXPECT)}/{len(EXPECT)} hồ sơ + loader" if ok else "CÓ LỖI")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())
