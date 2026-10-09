"""
probe_cpsat.py — Thử nghiệm OR-Tools CP-SAT cho T3 (lập kế hoạch phản thực).
CP-SAT không làm suy diễn logic/entailment, nên KHÔNG dùng cho T1 ba trị.
Ở đây chỉ đo năng lực tối ưu tổ hợp: số học kỳ tối thiểu.
"""
import time
from ortools.sat.python import cp_model

import kb


def min_semesters(student, horizon=8):
    known = student["records"]
    exempted = set(student["exemptions"])
    all_courses = list(kb.COURSES)
    done = {c for c, g in known.items() if g in kb.PASSING_GRADES} | exempted
    todo = [c for c in all_courses if c not in done]

    m = cp_model.CpModel()
    take = {c: m.NewBoolVar(f"take_{c}") for c in todo}
    term = {c: m.NewIntVar(1, horizon, f"t_{c}") for c in todo}
    at = {(c, k): m.NewBoolVar(f"at_{c}_{k}")
          for c in todo for k in range(1, horizon + 1)}

    for c in todo:
        m.Add(sum(at[c, k] for k in range(1, horizon + 1)) == 1).OnlyEnforceIf(take[c])
        m.Add(sum(at[c, k] for k in range(1, horizon + 1)) == 0).OnlyEnforceIf(take[c].Not())
        for k in range(1, horizon + 1):
            m.Add(term[c] == k).OnlyEnforceIf(at[c, k])
        if kb.COURSES[c][2] != "elective":
            m.Add(take[c] == 1)                 # bắt buộc + luận văn

    # nhóm N-of-M
    for _, (members, n) in kb.ELECTIVE_GROUPS.items():
        already = sum(1 for x in members if x in done)
        m.Add(sum(take[x] for x in members if x in todo) >= max(0, n - already))

    # tiên quyết
    for c, ps in kb.PREREQS.items():
        if c not in todo:
            continue
        for p in ps:
            if p in done:
                continue
            if p in todo:
                m.Add(take[p] == 1).OnlyEnforceIf(take[c])
                b = m.NewBoolVar(f"pr_{c}_{p}")
                m.AddBoolAnd([take[c], take[p]]).OnlyEnforceIf(b)
                m.AddBoolOr([take[c].Not(), take[p].Not()]).OnlyEnforceIf(b.Not())
                m.Add(term[p] < term[c]).OnlyEnforceIf(b)

    # trần tín chỉ mỗi học kỳ
    for k in range(1, horizon + 1):
        m.Add(sum(kb.CREDITS[c] * at[c, k] for c in todo) <= kb.MAX_CREDITS_PER_TERM)

    last = m.NewIntVar(0, horizon, "last")
    for c in todo:
        m.Add(last >= term[c]).OnlyEnforceIf(take[c])

    n_elec = sum(take[c] for c in todo if kb.COURSES[c][2] == "elective")
    m.Minimize(last * 100 + n_elec)             # từ điển hoá: học kỳ trước, môn thừa sau

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 8
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, None, status
    plan = {}
    for c in todo:
        if solver.Value(take[c]):
            plan.setdefault(solver.Value(term[c]), []).append(c)
    return solver.Value(last), plan, solver.StatusName(status)


if __name__ == "__main__":
    print("=== OR-Tools CP-SAT ===")
    t0 = time.perf_counter()
    n, plan, st = min_semesters(kb.STUDENT_C)
    dt = (time.perf_counter() - t0) * 1000
    print(f"[T3] SV-C so hoc ky toi thieu = {n}  status={st}  ({dt:.1f} ms)")
    for k in sorted(plan):
        print(f"     HK{k}: {sorted(plan[k])}")
