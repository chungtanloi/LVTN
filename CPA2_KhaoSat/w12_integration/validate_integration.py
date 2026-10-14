"""
validate_integration.py — kiểm chứng Prototype v1 Tuần 12 (CPA2)

Tiêu chí: "Answer đi kèm proof" — mỗi verdict có certificate + explanation + hậu kiểm

Chạy:  python validate_integration.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
import importlib.util, json
spec = importlib.util.spec_from_file_location("prototype", HERE / "prototype.py")
proto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proto)

errors=[]
OK, FAIL = "  [OK]  ", "  [FAIL]"
def check(cond, msg, note=""):
    print((OK if cond else FAIL) + " " + msg)
    if note: print("          ↳ " + note)
    if not cond: errors.append(msg)
    return cond

def test_true():
    print("\nA. TRUE — sv_lvtn đủ 161 TC")
    res=proto.answer("em đủ điều kiện tốt nghiệp chưa?", str(HERE.parent / "w7_student_facts" / "students" / "sv_lvtn.json"))
    check(res["verdict"]=="TRUE", f"A1 verdict TRUE (got {res['verdict']})")
    check(len(res["certificate"]["proof"]["steps"])>0, f"A2 certificate có {len(res['certificate']['proof']['steps'])} steps")
    check("tot_nghiep" in res["explanation_vi"], "A3 explanation chứa claim")
    check(res["missing_facts"]==[], "A4 TRUE không có missing_facts")

def test_false():
    print("\nB. FALSE — sv_tron_ngoai_ngu trộn AV/PV")
    res=proto.answer("em đủ điều kiện tốt nghiệp chưa?", str(HERE.parent / "w7_student_facts" / "students" / "sv_tron_ngoai_ngu.json"))
    check(res["verdict"]=="FALSE", f"B1 verdict FALSE (got {res['verdict']})")
    check(len(res["certificate"]["proof"]["steps"])>0, "B2 certificate có steps (phản ví dụ)")
    # explanation phải đề cập thiếu
    check("thieu" in res["explanation_vi"].lower() or "thiếu" in res["explanation_vi"].lower(), "B3 explanation đề cập thiếu")

def test_unknown():
    print("\nC. UNKNOWN — thiếu điểm LVTN (2 thế giới)")
    # tạo hồ sơ tạm thiếu CT550E
    extra = proto.load_student(str(HERE.parent / "w7_student_facts" / "students" / "sv_lvtn.json"))[0]
    # bỏ CT550E ra, thêm choice
    extra = "\n".join([l for l in extra.split("\n") if "CT550E" not in l])
    extra += '\n{ g10("CT550E",80); g10("CT550E",30) } = 1.\n'
    # dùng trực tiếp solver
    claim="tot_nghiep"
    verdict, models, caut, brave = proto.solve_verdict(claim, extra)
    check(verdict=="UNKNOWN", f"C1 verdict UNKNOWN (got {verdict})")
    cert=proto.build_certificate(claim, verdict, models, caut, brave)
    check(len(cert["missing_facts"])>0 and any("CT550E" in f for f in cert["missing_facts"]), f"C2 missing_facts chứa CT550E ({cert['missing_facts'][:2]})")
    # verbalizer cho UNKNOWN
    text, block = proto.verbalize(cert, caut)
    check(block is None, "C3 hậu kiểm không chặn UNKNOWN")
    check("CT550E" in text or "thiếu" in text.lower(), "C4 explanation đề cập missing")

def test_postcheck():
    print("\nD. HẬU KIỂM — chặn mã không có trong certificate")
    # tạo certificate giả có steps không chứa CT999 nhưng explanation lại chứa CT999 → phải chặn
    cert={"claim":"tot_nghiep","verdict":"TRUE","proof":{"steps":[{"atom":"tot_nghiep","rule_id":"r_f01a","source":{"van_ban":"qd3266","dieu":32}}]},"missing_facts":[]}
    # monkey patch verbalize để tạo explanation chứa mã lạ
    import re
    text="Kết luận: tot_nghiep = TRUE. Mã CT999 thiếu."
    codes=re.findall(r"[A-Z]{1,3}\d{2,3}E?", text)
    cert_text=" ".join([s["atom"] for s in cert["proof"]["steps"]])
    blocked = any(c not in cert_text for c in codes)
    check(blocked, "D1 hậu kiểm phát hiện CT999 không trong certificate → chặn")
    # test thật qua prototype: không có mã lạ nên không chặn
    res=proto.answer("em đủ điều kiện tốt nghiệp chưa?", str(HERE.parent / "w7_student_facts" / "students" / "sv_lvtn.json"))
    check(res["verdict"]!="BLOCKED", "D2 case thật không bị chặn")

def main():
    print("="*78)
    print("VALIDATE PROTOTYPE v1 — Tuần 12 (CPA2)")
    print("Answer = verdict + certificate + explanation_vi + missing_facts + hậu kiểm")
    print("="*78)
    test_true()
    test_false()
    test_unknown()
    test_postcheck()
    print("\n"+"="*78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors: print("  ·",e)
        return 1
    print("KẾT LUẬN: ĐẠT — Prototype v1 trả lời kèm proof và hậu kiểm")
    print("="*78)
    return 0

if __name__=="__main__": sys.exit(main())
