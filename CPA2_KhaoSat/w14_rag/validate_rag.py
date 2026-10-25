"""
validate_rag.py — kiểm chứng RAG grounding (CPA2, Tuần 14)

  A. Corpus      : mọi quy tắc R-Formal có passage; mọi asp có passage; passage trỏ đúng điều
  B. Truy hồi    : Recall@1, Recall@5, MRR trên rag_queries.json (dev hoặc test); nhầm văn bản
  C. Grounding   : certificate của Prototype v1 (Tuần 12) — mỗi bước có passage, passage cùng
                   văn bản + điều với quy tắc nguồn trong R-Formal
  D. Hậu kiểm    : trích passage ngoài nguồn của certificate → bị chặn

Chạy: python validate_rag.py            (dev — dùng khi tinh chỉnh)
      python validate_rag.py --test     (test — chỉ để báo cáo)
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "w12_integration"))

from retriever import Retriever, kiem_trich_dan
import build_corpus
import prototype

QUERIES = HERE / "rag_queries.json"
STUDENTS = ROOT / "w7_student_facts" / "students"

ok_all = True        # cổng: A, C, D — tiêu chí tuần "truy hồi đúng nguồn" cho KẾT LUẬN
muc_tieu_dat = True  # B: truy hồi tự do — báo cáo theo mục tiêu, không chặn


def check(cond, msg, cong=True):
    global ok_all, muc_tieu_dat
    print(f"  [{'OK' if cond else ('FAIL' if cong else 'CHƯA ĐẠT')}] {msg}")
    if cong:
        ok_all = ok_all and cond
    else:
        muc_tieu_dat = muc_tieu_dat and cond
    return cond


def phan_A(r):
    print("A. CORPUS")
    cat = json.loads(build_corpus.CATALOG.read_text(encoding="utf-8"))
    rules = {x["id"] for x in cat["rules"]}
    co_passage = set(r.by_rule)
    check(rules <= co_passage, f"mọi quy tắc R-Formal ({len(rules)}) có passage (thiếu: {sorted(rules - co_passage)})")
    asp = {x["asp"] for x in cat["rules"] if x.get("asp")}
    check(asp <= set(r.by_asp), f"mọi asp ({len(asp)}) có passage (thiếu: {sorted(asp - set(r.by_asp))})")
    lech = [x["id"] for x in cat["rules"]
            if r.by_rule[x["id"]]["van_ban"] != x["van_ban"]
            or str(r.by_rule[x["id"]]["dieu"]) != str(x["dieu"] if x["dieu"] is not None else "PL1")]
    check(not lech, f"passage của mỗi quy tắc cùng văn bản + điều với bản ghi R-Formal (lệch: {lech})")
    # trang 20 QĐ3266 (OCR trắng — Điều 32 k4 → Điều 35) chép tay từ PDF gốc: passage lấy từ bản chép, có tiêu đề
    tr20 = [d for d in r.docs if d.get("van_ban") == "qd3266" and (str(d.get("dieu")) in ("33", "34", "35")
            or d["id"] in ("qd3266:D32:K4", "qd3266:D32:K5", "qd3266:D32:K6"))]
    check(tr20 and all(d.get("nguon") == "chep_tay" for d in tr20),
          f"passage QĐ3266 Điều 32 k4 → Điều 35 lấy từ bản chép tay trang 20 ({sorted((d['id'], d.get('nguon')) for d in tr20)})")
    td = {d["id"]: d["tieu_de"] for d in tr20}
    check(td.get("qd3266:D33:K1") == "Xử lý sinh viên quá hạn thời gian học tập"
          and td.get("qd3266:D34:K2") == "Bằng tốt nghiệp và hạng tốt nghiệp",
          f"tiêu đề Điều 33, 34 theo PDF gốc ({td.get('qd3266:D33:K1')!r}, {td.get('qd3266:D34:K2')!r})")
    check({"qd3266:D32:K4", "qd3266:D33:K3", "qd3266:D33:K4"} <= {d["id"] for d in r.docs},
          "có passage Điều 32 k4 và Điều 33 k3, k4 (trước đây mất cùng trang OCR trắng)")
    trich = [d["id"] for d in r.docs if d.get("nguon") == "trich_r_formal"]
    print(f"     ghi nhận: {len(trich)} passage dựng từ trích R-Formal vì OCR hỏng/trắng: {trich}")


def phan_B(r, split):
    print(f"B. TRUY HỒI — tập {split}")
    qs = [q for q in json.loads(QUERIES.read_text(encoding="utf-8"))["queries"] if q["split"] == split]
    muc = json.loads(QUERIES.read_text(encoding="utf-8"))["meta"]["muc_tieu"]
    h1 = h5 = mrr = nham_vb = 0
    truot = []
    theo_loai = {}
    for q in qs:
        kq = [p["id"] for p, _ in r.search(q["q"], k=10)]
        rank = next((i for i, pid in enumerate(kq) if pid in q["gold"]), None)
        h1 += rank == 0
        h5 += rank is not None and rank < 5
        mrr += 1 / (rank + 1) if rank is not None else 0
        vb_gold = {g.split(":")[0] for g in q["gold"]}
        nham_vb += kq[0].split(":")[0] not in vb_gold
        t = theo_loai.setdefault(q["loai"], [0, 0])
        t[0] += rank == 0
        t[1] += 1
        if rank != 0:
            truot.append(f"{q['id']} [{q['loai']}] hạng {'>10' if rank is None else rank + 1}: {q['q']} → top1 {kq[0]}")
    n = len(qs)
    print(f"     Recall@1 = {h1}/{n} = {h1/n:.2f} · Recall@5 = {h5}/{n} = {h5/n:.2f} · MRR = {mrr/n:.3f} · "
          f"top-1 sai văn bản = {nham_vb}/{n}")
    print("     Recall@1 theo loại: " + ", ".join(f"{k} {a}/{b}" for k, (a, b) in sorted(theo_loai.items())))
    for s in truot:
        print("       · " + s)
    check(h1 / n >= muc["recall_at_1"], f"mục tiêu Recall@1 ≥ {muc['recall_at_1']}", cong=False)
    check(h5 / n >= muc["recall_at_5"], f"mục tiêu Recall@5 ≥ {muc['recall_at_5']}", cong=False)


def phan_C(r):
    print("C. GROUNDING CERTIFICATE (Prototype v1)")
    cat = {x["asp"]: x for x in json.loads(build_corpus.CATALOG.read_text(encoding="utf-8"))["rules"] if x.get("asp")}
    for sv in ("sv_lvtn", "sv_tron_ngoai_ngu", "sv_mien_ielts"):
        res = prototype.answer("em đủ điều kiện tốt nghiệp chưa?", str(STUDENTS / f"{sv}.json"))
        cert = r.ground_certificate(res["certificate"])
        steps = cert["proof"]["steps"]
        check(steps and not cert["grounding"]["khong_nguon"],
              f"{sv} ({res['verdict']}): {len(steps)} bước, mọi bước có passage nguồn")
        sai = [s["rule_id"] for s in steps
               if r.by_id[s["passage_id"]]["van_ban"] != cat[s["rule_id"]]["van_ban"]
               or str(r.by_id[s["passage_id"]]["dieu"]) != str(cat[s["rule_id"]]["dieu"] or "PL1")]
        check(not sai, f"{sv}: passage của từng bước cùng văn bản + điều với quy tắc (lệch: {sai})")
    return cert


def phan_D(r, cert):
    print("D. HẬU KIỂM TRÍCH DẪN")
    hop_le = [t["passage_id"] for t in r.trich_dan(cert)]
    ok, _ = kiem_trich_dan(cert, hop_le)
    check(ok and hop_le, f"trích từ nguồn certificate ({len(hop_le)} passage) → cho qua")
    # passage có thật trong corpus, rất giống câu hỏi, nhưng KHÔNG phải nguồn của chứng minh
    la = r.search("Sinh viên được đăng ký học tối đa bao nhiêu tín chỉ", k=1)[0][0]["id"]
    assert la not in cert["grounding"]["passages"]
    ok, sai = kiem_trich_dan(cert, hop_le + [la])
    check(not ok and sai == [la], f"chèn passage truy hồi được nhưng ngoài chứng minh ({la}) → chặn")
    ok, sai = kiem_trich_dan(cert, ["qd3266:D99:K1"])
    check(not ok, "passage không tồn tại → chặn")


def main():
    from retriever import chuan_hoa
    check('cảnh báo học tập' in chuan_hoa('e bị cbhv lần 1'), 'viết tắt CBHV của survey train được mở rộng cho truy hồi')
    check('đăng ký' in chuan_hoa('dk học phần'), 'viết tắt dk được mở rộng cho truy hồi')
    split = "test" if "--test" in sys.argv else "dev"
    build_corpus.build()
    print()
    r = Retriever()
    phan_A(r)
    phan_B(r, split)
    cert = phan_C(r)
    phan_D(r, cert)
    print("\nKẾT LUẬN:", "ĐẠT — mọi kết luận có passage nguồn đúng điều/khoản, hậu kiểm chặn trích sai"
          if ok_all else "CHƯA ĐẠT")
    print("Truy hồi tự do:", "đạt mục tiêu" if muc_tieu_dat else "CHƯA đạt mục tiêu Recall (xem mục B)")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
