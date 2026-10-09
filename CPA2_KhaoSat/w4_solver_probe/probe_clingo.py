"""
probe_clingo.py — Thử nghiệm ASP (clingo) cho cùng 3 tác vụ.
Điểm mạnh riêng của ASP: ba trị có sẵn trong ngữ nghĩa suy diễn
  - cautious consequences (đúng trong MỌI answer set)  -> TRUE
  - brave    consequences (đúng trong ÍT NHẤT MỘT set) -> có thể đúng
  - không nằm trong brave                              -> FALSE
  - nằm trong brave nhưng không trong cautious         -> UNKNOWN
Không cần gọi solver hai lần với công thức phủ định như SMT.
"""
import time
import clingo

import kb


def facts_for(student):
    known = student["records"]
    unknown = set(student["unknown"])
    exempted = set(student["exemptions"])
    lines = []

    for c, (_, cr, kind) in kb.COURSES.items():
        lines.append(f'course("{c}",{cr}).')
        if kind in ("required", "thesis") and c != kb.THESIS:
            lines.append(f'required("{c}").')
        if kind == "thesis":
            lines.append(f'must_take("{c}").')

    for _, (members, n) in kb.ELECTIVE_GROUPS.items():
        for m in members:
            lines.append(f'in_group(g1,"{m}").')
        lines.append(f"group_min(g1,{n}).")

    for c, g in known.items():
        pts10 = int(round(kb.GRADE_POINTS[g] * 10))
        lines.append(f'grade("{c}",{pts10}).')
    for c in exempted:
        lines.append(f'exempted("{c}").')
    for c in unknown:
        lines.append(f'unknown_course("{c}").')

    lines.append(f'extra_credits({student["extra_credits_passed"]}).')
    lines.append(f"min_credits({kb.MIN_CREDITS_TO_GRADUATE}).")
    lines.append(f"min_cgpa10({int(kb.MIN_CGPA_TO_GRADUATE * 10)}).")
    return "\n".join(lines)


PROGRAM = """
% --- dữ kiện chưa biết: sinh mọi thế giới khả dĩ -------------------------------
possible_grade(0;10;15;20;25;30;35;40).
1 { grade(C,P) : possible_grade(P) } 1 :- unknown_course(C).

% --- đạt học phần ---------------------------------------------------------------
passed(C) :- grade(C,P), P >= 10.
passed(C) :- exempted(C).

% --- điều kiện A: mọi học phần bắt buộc đều đạt ----------------------------------
missing_required(C) :- required(C), not passed(C).
cond_required :- not missing_required(_).

% --- điều kiện B: nhóm tự chọn N-of-M --------------------------------------------
group_ok(G) :- group_min(G,N), #count{ C : in_group(G,C), passed(C) } >= N.
cond_elective :- group_ok(G) : group_min(G,_).

% --- điều kiện C: tổng tín chỉ ---------------------------------------------------
earned(T) :- T = #sum{ CR,C : course(C,CR), passed(C) }.
cond_credits :- earned(T), extra_credits(E), min_credits(M), T + E >= M.

% --- điều kiện D: CGPA (nhân 10 để dùng số nguyên; môn miễn không tính) ----------
gpa_num(N) :- N = #sum{ P*CR,C : course(C,CR), grade(C,P), passed(C), not exempted(C) }.
gpa_den(D) :- D = #sum{ CR,C   : course(C,CR), passed(C), not exempted(C) }.
cond_cgpa :- gpa_num(N), gpa_den(D), min_cgpa10(M), N*10 >= M*D.

% --- kết luận --------------------------------------------------------------------
graduate :- cond_required, cond_elective, cond_credits, cond_cgpa.

#show graduate/0.
#show cond_required/0.
#show cond_elective/0.
#show cond_credits/0.
#show cond_cgpa/0.
#show missing_required/1.
"""


def three_valued_graduation(student):
    def consequences(mode):
        ctl = clingo.Control(["--enum-mode=" + mode, "--models=0"])
        ctl.add("base", [], facts_for(student) + PROGRAM)
        ctl.ground([("base", [])])
        out = set()
        with ctl.solve(yield_=True) as handle:
            for model in handle:
                out = {str(a) for a in model.symbols(shown=True)}
        return out

    cautious = consequences("cautious")   # đúng trong MỌI answer set
    brave = consequences("brave")         # đúng trong ÍT NHẤT một answer set

    if "graduate" in cautious:
        verdict = "TRUE"
    elif "graduate" not in brave:
        verdict = "FALSE"
    else:
        verdict = "UNKNOWN"

    broken = [c for c in ("cond_required", "cond_elective", "cond_credits", "cond_cgpa")
              if c not in brave]
    missing = sorted(a for a in cautious if a.startswith("missing_required"))
    return verdict, broken, missing


# ---------------------------------------------------------------------------
# T3 — số học kỳ tối thiểu (ASP + tối ưu)
# ---------------------------------------------------------------------------
PLAN_PROGRAM = """
term(1..H) :- horizon(H).
done(C) :- grade(C,P), P >= 10.
done(C) :- exempted(C).
todo(C) :- course(C,_), not done(C).

% chọn học phần đưa vào kế hoạch
take(C) :- todo(C), required(C).
take(C) :- todo(C), must_take(C).
{ take(C) } :- todo(C), in_group(_,C).
sat_group(C) :- done(C).
sat_group(C) :- take(C).
:- group_min(G,N), #count{ C : in_group(G,C), sat_group(C) } < N.

% xếp mỗi học phần được chọn vào đúng một học kỳ
1 { at(C,K) : term(K) } 1 :- take(C).

% tiên quyết
:- at(C,K1), prereq(C,P), take(P), at(P,K2), K2 >= K1.
:- at(C,_), prereq(C,P), not done(P), not take(P).

% trần tín chỉ
:- term(K), #sum{ CR,C : at(C,K), course(C,CR) } > MAX, max_credits(MAX).

used(K) :- at(_,K).
later(K) :- used(K1), term(K), K1 > K.
maxt(K)  :- used(K), not later(K).
#minimize { K@2 : maxt(K) }.
#minimize { 1@1,C : take(C), in_group(_,C) }.
#show at/2.
"""


def min_semesters(student, horizon=8):
    lines = [facts_for(student),
             f"horizon({horizon}).",
             f"max_credits({kb.MAX_CREDITS_PER_TERM})."]
    for c, ps in kb.PREREQS.items():
        for p in ps:
            if c in kb.COURSES and p in kb.COURSES:
                lines.append(f'prereq("{c}","{p}").')

    # Tuần 6: optN liệt kê MỌI kế hoạch tối ưu — với bộ dữ liệu thật (nhiều HP tự chọn
    # hoán vị được) số kế hoạch tối ưu bùng nổ và lệnh chạy > 2 phút. Chỉ cần CHỨNG
    # MINH tối ưu, nên dùng --opt-mode=opt.
    ctl = clingo.Control(["--models=0", "--opt-mode=opt", "--warn=none"])
    ctl.add("base", [], "\n".join(lines) + PLAN_PROGRAM)
    ctl.ground([("base", [])])
    best = None
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            if True:   # opt: mô hình sau cùng là mô hình tối ưu
                best = [str(a) for a in model.symbols(shown=True)]
    plan = {}
    for a in best or []:
        inner = a[len("at("):-1]
        code, k = inner.split(",")
        plan.setdefault(int(k), []).append(code.strip('"'))
    return (max(plan) if plan else 0), plan


if __name__ == "__main__":
    print("=== clingo / ASP ===")
    for st in (kb.STUDENT_A, kb.STUDENT_B, kb.STUDENT_C):
        t0 = time.perf_counter()
        v, broken, missing = three_valued_graduation(st)
        dt = (time.perf_counter() - t0) * 1000
        print(f"[T1+T2] {st['id']}: tot_nghiep = {v:<8} "
              f"dieu_kien_hong={broken or '-'}  ({dt:.1f} ms)")
        if missing:
            print(f"         {len(missing)} mon bat buoc chua dat")

    t0 = time.perf_counter()
    n, plan = min_semesters(kb.STUDENT_C)
    dt = (time.perf_counter() - t0) * 1000
    print(f"[T3] SV-C so hoc ky toi thieu = {n}  ({dt:.1f} ms)")
    for k in sorted(plan):
        print(f"     HK{k}: {sorted(plan[k])}")
