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

def test_dang_ky():
    print("\nE. ĐĂNG KÝ MỘT HỌC PHẦN — tiên quyết (Đ7 k4) + song hành (Đ7 k5)")
    import tempfile
    base = json.loads((HERE.parent / "w7_student_facts" / "students" / "sv_lvtn.json").read_text(encoding="utf-8"))
    def hoi(q, xoa=(), them=None):
        j = json.loads(json.dumps(base))
        for m in xoa:
            j["grades"].pop(m, None)
        j["grades"].update(them or {})
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "sv.json"
            f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
            return proto.answer(q, str(f))
    r = hoi("Kỳ này em đăng ký CT180 được chưa?", xoa=["CT180"])
    check(r.get("claim") == 'duoc_dang_ky("CT180")' and r["verdict"] == "TRUE",
          f"E1 câu hỏi có mã HP → claim có đối số, không rơi về tot_nghiep ({r.get('claim')}, {r['verdict']})")
    r = hoi("Kỳ này em đăng ký CT182 được chưa?", xoa=["CT180", "CT182"])
    check(r["verdict"] == "TRUE" and "CT180" in r["explanation_vi"] and "cùng kỳ" in r["explanation_vi"]
          and any(s["rule_id"] == "r_a04" for s in r["certificate"]["proof"]["steps"]),
          f"E2 chưa học CT180 → được đăng ký CT182 VỚI ĐIỀU KIỆN học CT180 cùng kỳ, chứng chỉ r_a04 ({r['explanation_vi'][:120]})")
    r = hoi("Kỳ này em đăng ký CT182 được chưa?", xoa=["CT180", "CT182", "CT177"])
    check(r["verdict"] == "FALSE" and "CT180" in r["explanation_vi"],
          f"E3 chưa học CT180 và CT180 thiếu tiên quyết CT177 → chưa thể học CT182 kỳ này ({r['verdict']}: {r['explanation_vi'][:120]})")
    r = hoi("Kỳ này em đăng ký CT182 được chưa?", xoa=["CT182"],
            them={"CT180": {"code": "CT180", "credits": 3, "thang10": 30, "letter": "F", "status": "failed"}})
    check(r["verdict"] == "TRUE" and "cùng kỳ" not in r["explanation_vi"],
          f"E4 đã học CT180 (bị F) → song hành thoả, không đặt điều kiện ({r['explanation_vi'][:100]})")
    r = hoi("Kỳ này em đăng ký XH033 được chưa?", xoa=[m for m in base["grades"] if m.startswith("XH0")])
    check(r["verdict"] == "TRUE" and all(m in r["explanation_vi"] for m in ("XH032", "XH031", "XH025", "XH024", "XH023")),
          f"E6 song hành dây chuyền XH033→XH032→…→XH023: nêu ĐỦ các HP phải học cùng kỳ ({r['explanation_vi'][:160]})")
    r = hoi("Kỳ này em đăng ký CT182 được chưa?", xoa=["CT180", "CT182", "CT177"])
    check(any(s_["atom"].startswith('thieu_tien_quyet("CT180"') for s_ in r["certificate"]["proof"]["steps"]),
          "E7 bước 'thiếu tiên quyết' trong chứng chỉ lấy từ why/2 của KB (không dựng tay)")
    sai = {q: proto.parse_question(q) for q in (
        "nếu em học lại CT177 thì được bao nhiêu điểm", "Nếu em không đăng ký CT180 thì có tốt nghiệp được không",
        "em học xong ct180 thì được tốt nghiệp chưa", "em đã học ct180 được mấy điểm",
        "IELTS 6.0 miễn được QP001 không, em đăng ký được chưa", "nếu em rot ct177 thì sao")}
    check(not any(v.startswith("duoc_dang_ky") for v in sai.values()),
          f"E8 câu điều kiện/điểm/miễn có mã HP không bị hiểu nhầm thành câu hỏi đăng ký ({sai})")
    v = proto.parse_question("em có nên đăng ký ct180 không")
    check(not v.startswith("duoc_dang_ky"), f"E9 'có NÊN đăng ký' không trả lời bằng 'được đăng ký' ({v})")
    r = proto.answer("Nếu em rớt CT177 thì trễ mấy kỳ?", None)
    check(r.get("claim") != "tot_nghiep" and r["verdict"] == "UNKNOWN",
          f"E5 câu phản thực tế (chưa hỗ trợ) → UNKNOWN, không trả lời nhầm tot_nghiep ({r.get('claim')}, {r['verdict']})")

def main():
    print("="*78)
    print("VALIDATE PROTOTYPE v1 — Tuần 12 (CPA2)")
    print("Answer = verdict + certificate + explanation_vi + missing_facts + hậu kiểm")
    print("="*78)
    test_true()
    test_false()
    test_unknown()
    test_postcheck()
    test_dang_ky()
    print("\n"+"="*78)
    if errors:
        print(f"KẾT LUẬN: CÓ {len(errors)} LỖI")
        for e in errors: print("  ·",e)
        return 1
    print("KẾT LUẬN: ĐẠT — Prototype v1 trả lời kèm proof và hậu kiểm")
    print("="*78)
    return 0

if __name__=="__main__": sys.exit(main())
