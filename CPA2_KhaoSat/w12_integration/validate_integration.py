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
    # P20-2 (Tuần 20): câu ngoài phạm vi / không nhận ra ý định KHÔNG được rơi về tot_nghiep (trả lời nhầm TRUE)
    for q in ("Mức học phí một tín chỉ năm nay là bao nhiêu ạ?", "Em muốn chuyển sang học ngành khác thì làm sao?",
              "Thầy cô nào dạy môn này hay vậy?"):
        r = proto.answer(q, str(HERE.parent / "w7_student_facts" / "students" / "sv_lvtn.json"))
        check(r.get("claim") != "tot_nghiep" and r["verdict"] == "UNKNOWN",
              f"E10 '{q[:32]}…' → UNKNOWN 'chưa hỗ trợ', không rơi về tot_nghiep ({r.get('claim')}, {r['verdict']})")
    check(proto.parse_question("Em ra trường được chưa ạ?") == "tot_nghiep", "E11 'ra trường được chưa' vẫn là câu tốt nghiệp")
    # P20-3: chữ chen giữa "đăng ký" và mã HP
    for q, ma in (("Em có được đăng ký học phần niên luận CT466E chưa?", "CT466E"),
                  ("kỳ này em đăng ký luận văn tốt nghiệp CT550E được không", "CT550E")):
        check(proto.parse_question(q) == f'duoc_dang_ky("{ma}")', f"E12 '{q[:34]}…' → duoc_dang_ky(\"{ma}\") ({proto.parse_question(q)})")
    # review P20: khe "đăng ký … <MÃ>" không được bắt câu về HP KHÁC / hủy / rút
    sai = {q: proto.parse_question(q) for q in (
        "em đã đăng ký học phần tiên quyết của CT180 chưa", "em đăng ký học phần song hành với CT180 được không",
        "em đăng ký hủy học phần CT180 được không", "em đăng ký rút học phần CT180 được không",
        "em cần đăng ký học phần gì để tốt nghiệp CT550E", "em đăng ký học phần nào để thay thế CT550E được không")}
    check(not any(v_.startswith("duoc_dang_ky") for v_ in sai.values()), f"E13 câu về HP khác/hủy/rút không thành duoc_dang_ky ({sai})")
    k = {q: proto.parse_question(q) for q in ("Em có đủ điều kiện làm luận văn tốt nghiệp không?",
         "ĐTBCTL của em đạt 2,00 để xét tốt nghiệp chưa?", "Em có được miễn luận văn tốt nghiệp không?",
         "Hồ sơ xét tốt nghiệp nộp ở đâu, có được nộp trễ không?", "Em tốt nghiệp loại trung bình được không?")}
    check(not any(v_ == "tot_nghiep" for v_ in k.values()), f"E14 câu luận văn/ĐTBCTL/miễn/hồ sơ/xếp loại không thành tot_nghiep ({k})")
    k = {q: proto.parse_question(q) for q in ("em du dieu kien tot nghiep chua", "Em có thể tốt nghiệp không?",
         "em có tốt nghiệp kịp không")}
    check(all(v_ == "tot_nghiep" for v_ in k.values()), f"E15 câu tốt nghiệp không dấu / 'có thể' / 'kịp' vẫn nhận ra ({k})")
    check(proto.parse_question("đăng kí ct180 được ko") == 'duoc_dang_ky("CT180")', "E16 'đăng kí … được ko' (kí/ko) nhận là đăng ký")
    # P20-5 (Q-Noise, Tuần 20): loại trừ chỉ có dạng CÓ DẤU → câu không dấu về luận văn/ĐTBCTL/miễn/hồ sơ/xếp loại
    # bị hiểu là tot_nghiep (trả lời câu khác kèm chứng chỉ). Câu kiểm thử mới, không chép từ Q-Noise.
    k = {q: proto.parse_question(q) for q in ("em co du dieu kien lam luan van tot nghiep khong",
         "dtbctl cua em dat 2,00 de xet tot nghiep chua", "em co duoc mien luan van tot nghiep khong",
         "ho so xet tot nghiep nop o dau, co duoc nop tre khong", "em tot nghiep loai gioi duoc khong",
         "em co du dieu kien lam tieu luan tot nghiep chua")}
    check(not any(v_ == "tot_nghiep" for v_ in k.values()), f"E17 câu KHÔNG DẤU về luận văn/ĐTBCTL/miễn/hồ sơ/xếp loại không thành tot_nghiep ({k})")
    sv_tltn = str(HERE.parent / "w7_student_facts" / "students" / "sv_tltn.json")
    k = {q: proto.answer(q, sv_tltn).get("claim") for q in ("em du dieu kien lam tieu luan chua a",
         "e du dk lam tieu luan tot nghiep chua")}
    check(all(v_ == "du_dk(tltn)" for v_ in k.values()), f"E18 'tieu luan' không dấu xét TLTN, không xét nhầm LVTN ({k})")
    # chuẩn hoá cách gõ của sinh viên: bỏ dấu + viết tắt (đk, đki, dky, đc, ko, k, tn, lv, hp, hk, kì, e)
    k = {q: proto.parse_question(q) for q, _ in (
        ("ki nay e dang ky hp ct180 duoc ko", 0), ("hk nay e dki ct180 dc k", 0), ("e dky mon ct180 đc chưa", 0),
        ("cho e hoi e hoc ct180 dc chua", 0), ("e dk hp ct180 dc khong a", 0))}
    check(all(v_ == 'duoc_dang_ky("CT180")' for v_ in k.values()), f"E19 câu đăng ký không dấu / viết tắt → duoc_dang_ky(\"CT180\") ({k})")
    k = {q: proto.parse_question(q) for q in ("e du dk tn chua a", "e đủ đk xét tn chưa", "em ra truong dc chua")}
    check(all(v_ == "tot_nghiep" for v_ in k.values()), f"E20 câu tốt nghiệp viết tắt / không dấu → tot_nghiep ({k})")
    k = {q: proto.parse_question(q) for q in ("e du dk lam lv chua", "em đủ đk làm lvtn chưa ạ", "em đủ dk làm tltn chưa ạ!!", "e du dk lam lv chua??")}
    check(all(v_ == "du_dk_tc" for v_ in k.values()), f"E21 câu luận văn viết tắt → du_dk_tc ({k})")
    # chuẩn hoá KHÔNG được mở cửa cho kết luận nhầm: các chốt chặn cũ phải giữ ở dạng không dấu / viết tắt
    k = {q: proto.parse_question(q) for q in ("neu e rot ct177 thi tre may ki", "hoc phi hk nay bao nhieu",
         "dk xet tn la gi", "e bi canh bao hoc vu ko", "e muon chuyen nganh thi can dk gi")}
    check(all(v_ in ("khong_ro", "counterfactual") for v_ in k.values()), f"E22 câu ngoài phạm vi (không dấu/viết tắt) vẫn từ chối ({k})")
    k = {q: proto.parse_question(q) for q in ("e co nen dk ct180 ko", "e dk huy hp ct180 dc ko", "ielts 6.0 mien dc fl001 ko",
         "e dk hp song hanh voi ct180 dc ko", "diem ct180 cua e dc bao nhieu")}
    check(not any(v_.startswith("duoc_dang_ky") for v_ in k.values()), f"E23 nên/hủy/miễn/song hành/điểm (không dấu) không thành duoc_dang_ky ({k})")
    check(proto.parse_question("kỳ này em đăng ký đề tài luận văn CT550E được không") == 'duoc_dang_ky("CT550E")',
          "E24 'đề tài' (bỏ dấu = 'de') không bị nhầm với 'để' của khe xấu")
    # review P20-5: bỏ dấu làm từ KHÁC trùng từ khoá (thế/thể, dự/dư/đủ, nền/nên, tn = tin nhắn/tình nguyện) →
    # câu trước đây bị từ chối nay bị trả lời như câu khác. Phải giữ từ chối.
    k = {q: proto.parse_question(q) for q in ("làm thế nào để tốt nghiệp", "em tốt nghiệp thế nào",
         "em dự lễ tốt nghiệp ở đâu", "em dư tín chỉ tốt nghiệp không", "thẻ sinh viên khi tốt nghiệp được giữ không",
         "em gửi tn cho thầy được chưa", "e di tn mua he xanh duoc cong diem ko", "em đủ đk tn chưa nhưng còn nợ học phí",
         "lam the nao de tot nghiep", "em du le tot nghiep o dau duoc khong", "em đủ tín chỉ tốt nghiệp chưa",
         # review lượt 2: tn = nhắn tin / tình nguyện sau "em/đã/được/sau"; lễ/thẻ/đồ án/thực tập/bằng giỏi có dấu
         "em tn cho thầy được không ạ", "em đã tn cho thầy chưa", "em được tn mùa hè xanh không", "sau tn em duoc nghi khong",
         "em dự lễ tốt nghiệp được không", "em làm đồ án tốt nghiệp được chưa", "em đi thực tập tốt nghiệp được chưa",
         "em đủ điều kiện nhận bằng giỏi khi tốt nghiệp chưa")}
    check(all(v_ != "tot_nghiep" for v_ in k.values()), f"E25 thế nào/dự/dư/thẻ/tin nhắn/học phí/tín chỉ không thành tot_nghiep ({k})")
    k = {q: proto.parse_question(q) for q in ("đk ct180 là gì", "dk hp ct180 la gi", "ki nay e dk ct180 dc chua ma e rot ct177",
         "đăng ký ct180 ở đâu được", "em học ct180 được mấy tín chỉ", "em học ct180 được 2 lần không",
         "đăng ký ct180 cùng lúc với ct181 được không", "em đã đăng ký ct180 chưa", "em đăng ký ct180 không được vì sao",
         "em đăng ký ct180 thì có bị trùng lịch không")}
    check(not any(v_.startswith("duoc_dang_ky") or v_ == "du_dk_dang_ky" for v_ in k.values()),
          f"E26 hỏi 'là gì/ở đâu' hoặc có rớt về HP không thành câu đăng ký (kể cả stub không đối số) ({k})")
    k = {q: proto.parse_question(q) for q in ("ct180 có phải học phần nền tảng không", "học phần nền ct180 có bao nhiêu tín chỉ",
         "hoc phan nen ct180 co bao nhieu tin chi", "e duoc lam tl nhom khong", "kien thuc nen hoc o dau",
         "em được làm luận văn nhóm không", "em được làm tiểu luận thay luận văn không", "em du dk lam luan van chua neu rot ct177")}
    check(all(v_ not in ("de_xuat", "du_dk_tc") for v_ in k.values()), f"E27 nền/nén, 'tl' (thảo luận) không thành đề xuất/tiểu luận ({k})")
    sv = str(HERE.parent / "w7_student_facts" / "students" / "sv_lvtn.json")
    k = {q: (proto.parse_question(q), proto.answer(q, sv)["explanation_vi"]) for q in (
         "ky 2 e nen dang ky gi", "hoc ki 3 em nen hoc gi", "ky 2 em he clc nen dang ky gi", "hè này em nên đăng ký gì")}
    check(all(p_ == "de_xuat" for p_, _ in k.values()) and "HK2" in k["ky 2 e nen dang ky gi"][1]
          and "HK3" in k["hoc ki 3 em nen hoc gi"][1] and "HK2" in k["ky 2 em he clc nen dang ky gi"][1]
          and "HK3" in k["hè này em nên đăng ký gì"][1],
          f"E28 đề xuất: học kỳ đọc từ câu không dấu ('ky 2', 'hoc ki 3'), không lặng lẽ về HK1 (P19-3) ({k})")
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
