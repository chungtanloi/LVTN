"""
probe_z3.py — Thử nghiệm Z3 (SMT) cho 3 tác vụ lõi của CPA².
T1: xét tốt nghiệp theo NGỮ NGHĨA BA TRỊ bằng suy diễn logic (entailment), không phải if-else.
T2: nhóm tự chọn N-of-M.
T3: lập kế hoạch tối thiểu số học kỳ (phản thực) — Z3 Optimize.

Ý tưởng ba trị (điểm mấu chốt của đề tài):
  KB = ràng buộc từ quy chế + CTĐT + dữ kiện đã biết của sinh viên.
  Dữ kiện CHƯA BIẾT để làm biến tự do.
    - KB ∧ ¬Grad  UNSAT  →  Grad ĐÚNG   trong mọi thế giới khả dĩ
    - KB ∧  Grad  UNSAT  →  Grad SAI    trong mọi thế giới khả dĩ
    - cả hai SAT               →  KHÔNG ĐỦ DỮ LIỆU (và ta chỉ ra đúng dữ kiện còn thiếu)
"""
import time
from z3 import (Bool, Real, And, Or, Not, Implies, Sum, If, Solver, Optimize,
                sat, unsat, Int, is_true)

import kb


# ---------------------------------------------------------------------------
# T1 + T2 — xét tốt nghiệp ba trị (đã bao gồm ràng buộc N-of-M)
# ---------------------------------------------------------------------------
def build_graduation_model(student):
    known = student["records"]
    unknown = set(student["unknown"])
    exempted = set(student["exemptions"])
    all_courses = set(kb.COURSES)

    passed = {c: Bool(f"passed_{c}") for c in all_courses}
    point = {c: Real(f"pt_{c}") for c in all_courses}

    s_constraints = []

    for c in all_courses:
        # miền giá trị điểm
        s_constraints.append(And(point[c] >= 0, point[c] <= 4))
        # đạt  <->  điểm >= 1.0 (từ D trở lên, theo GRADE_MAP)
        s_constraints.append(passed[c] == (point[c] >= 1.0))

        if c in known:                       # dữ kiện chắc chắn
            s_constraints.append(point[c] == kb.GRADE_POINTS[known[c]])
        elif c in exempted:                  # miễn: tính đạt, KHÔNG tính vào CGPA
            s_constraints.append(passed[c])
        elif c in unknown:                   # để tự do -> nguồn của UNKNOWN
            pass
        else:                                # chưa học
            s_constraints.append(Not(passed[c]))

    # --- Điều kiện A: mọi học phần bắt buộc phải đạt
    required = [c for c, v in kb.COURSES.items() if v[2] in ("required", "thesis")]
    cond_required = And(*[passed[c] for c in required if c != kb.THESIS])

    # --- Điều kiện B: nhóm tự chọn N-of-M
    nofm = []
    for _, (members, n) in kb.ELECTIVE_GROUPS.items():
        nofm.append(Sum([If(passed[c], 1, 0) for c in members]) >= n)
    cond_elective = And(*nofm)

    # --- Điều kiện C: tổng tín chỉ tích luỹ
    earned = Sum([If(passed[c], kb.CREDITS[c], 0) for c in all_courses]) \
             + student["extra_credits_passed"]
    cond_credits = earned >= kb.MIN_CREDITS_TO_GRADUATE

    # --- Điều kiện D: CGPA >= 2.00  (môn miễn không tính vào CGPA)
    gpa_pool = [c for c in all_courses if c not in exempted]
    num = Sum([If(passed[c], point[c] * kb.CREDITS[c], 0) for c in gpa_pool])
    den = Sum([If(passed[c], kb.CREDITS[c], 0) for c in gpa_pool])
    cond_cgpa = num >= kb.MIN_CGPA_TO_GRADUATE * den      # tránh chia

    grad = And(cond_required, cond_elective, cond_credits, cond_cgpa)
    parts = {"required": cond_required, "elective_n_of_m": cond_elective,
             "credits": cond_credits, "cgpa": cond_cgpa}
    return s_constraints, grad, parts


def three_valued_graduation(student):
    kbc, grad, parts = build_graduation_model(student)

    s1 = Solver(); s1.add(kbc); s1.add(Not(grad))
    r1 = s1.check()                       # UNSAT -> chắc chắn ĐÚNG
    s2 = Solver(); s2.add(kbc); s2.add(grad)
    r2 = s2.check()                       # UNSAT -> chắc chắn SAI

    if r1 == unsat:
        verdict = "TRUE"
    elif r2 == unsat:
        verdict = "FALSE"
    else:
        verdict = "UNKNOWN"

    # điều kiện con nào tự nó đã hỏng (dùng làm phản ví dụ / giải thích)
    broken = []
    for name, cond in parts.items():
        s = Solver(); s.add(kbc); s.add(cond)
        if s.check() == unsat:
            broken.append(name)

    return verdict, broken


# ---------------------------------------------------------------------------
# T3 — phản thực: số học kỳ tối thiểu còn lại để tốt nghiệp
# ---------------------------------------------------------------------------
def min_semesters(student, horizon=8):
    known = student["records"]
    exempted = set(student["exemptions"])
    all_courses = list(kb.COURSES)
    # môn còn phải học: chưa đạt và chưa miễn
    done = {c for c, g in known.items() if g in kb.PASSING_GRADES} | exempted
    todo = [c for c in all_courses if c not in done]

    opt = Optimize()
    # term[c] in 1..horizon nếu phải học; môn đã đạt -> term = 0
    term = {c: Int(f"t_{c}") for c in all_courses}
    for c in all_courses:
        if c in done:
            opt.add(term[c] == 0)
        else:
            opt.add(term[c] >= 1, term[c] <= horizon)

    # take[c]: có xếp học phần c vào kế hoạch hay không
    take = {c: Bool(f"take_{c}") for c in all_courses}
    for c in all_courses:
        if c in done:
            opt.add(Not(take[c]))
        elif kb.COURSES[c][2] != "elective":
            opt.add(take[c])          # môn bắt buộc: luôn phải học

    # trần tín chỉ mỗi học kỳ — chỉ tính học phần THỰC SỰ được xếp
    for k in range(1, horizon + 1):
        opt.add(Sum([If(And(take[c], term[c] == k), kb.CREDITS[c], 0) for c in todo])
                <= kb.MAX_CREDITS_PER_TERM)

    # tiên quyết chỉ ràng buộc khi cả hai môn đều được xếp
    for c, ps in kb.PREREQS.items():
        for p in ps:
            if c in all_courses and p in all_courses and c in todo:
                opt.add(Implies(And(take[c], take[p]), term[p] < term[c]))

    # phải đủ nhóm N-of-M
    for _, (members, n) in kb.ELECTIVE_GROUPS.items():
        already = sum(1 for m in members if m in done)
        opt.add(Sum([If(take[m], 1, 0) for m in members]) >= max(0, n - already))

    last = Int("last_term")
    for c in todo:
        opt.add(Implies(take[c], last >= term[c]))
    opt.add(last >= 0)
    opt.minimize(last)                                    # mục tiêu 1: ít học kỳ nhất
    elective_pool = [c for c in todo if kb.COURSES[c][2] == "elective"]
    opt.minimize(Sum([If(take[c], 1, 0) for c in elective_pool]))  # mục tiêu 2: ít môn thừa
    ok = opt.check()
    if ok != sat:
        return None, None
    m = opt.model()
    plan = {}
    for c in todo:
        if is_true(m.eval(take[c], model_completion=True)):
            k = m.eval(term[c], model_completion=True).as_long()
            plan.setdefault(k, []).append(c)
    return m.eval(last).as_long(), plan


if __name__ == "__main__":
    print("=== Z3 / SMT ===")
    for st in (kb.STUDENT_A, kb.STUDENT_B, kb.STUDENT_C):
        t0 = time.perf_counter()
        v, broken = three_valued_graduation(st)
        dt = (time.perf_counter() - t0) * 1000
        print(f"[T1+T2] {st['id']}: tot_nghiep = {v:<8} "
              f"dieu_kien_hong={broken or '-'}  ({dt:.1f} ms)")
        if v == "UNKNOWN":
            print(f"         du kien con thieu: {st['unknown']}")

    t0 = time.perf_counter()
    n, plan = min_semesters(kb.STUDENT_C)
    dt = (time.perf_counter() - t0) * 1000
    print(f"[T3] SV-C so hoc ky toi thieu = {n}  ({dt:.1f} ms)")
    for k in sorted(plan):
        print(f"     HK{k}: {sorted(plan[k])}")
