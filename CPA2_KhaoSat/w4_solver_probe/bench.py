"""
bench.py — Đo và ĐỐI CHIẾU CHÉO ba solver trên cùng bài toán.
Mục đích của Tuần 4: lấy số liệu để chọn solver, và kiểm chứng rằng
ba cài đặt độc lập cho CÙNG một đáp án (dấu hiệu mô hình hoá không sai).
"""
import statistics
import time

import kb
import probe_z3
import probe_clingo
import probe_cpsat


def timeit(fn, repeat=5):
    ts = []
    out = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        out = fn()
        ts.append((time.perf_counter() - t0) * 1000)
    return out, statistics.median(ts)


def main():
    print("=" * 74)
    print("T1+T2 — XET TOT NGHIEP BA TRI (TRUE / FALSE / UNKNOWN)")
    print("=" * 74)
    print(f"{'Ho so':<8} {'Z3':<10} {'ms':>8}   {'clingo':<10} {'ms':>8}   {'khop?':>6}")
    for st in (kb.STUDENT_A, kb.STUDENT_B, kb.STUDENT_C):
        (vz, _), tz = timeit(lambda s=st: probe_z3.three_valued_graduation(s))
        (vc, _, _), tc = timeit(lambda s=st: probe_clingo.three_valued_graduation(s))
        print(f"{st['id']:<8} {vz:<10} {tz:8.1f}   {vc:<10} {tc:8.1f}   "
              f"{'OK' if vz == vc else 'LECH':>6}")

    print()
    print("=" * 74)
    print("T3 — SO HOC KY TOI THIEU (truy van phan thuc, ho so SV-C)")
    print("=" * 74)
    (nz, pz), tz = timeit(lambda: probe_z3.min_semesters(kb.STUDENT_C), repeat=3)
    (nc, pc), tc = timeit(lambda: probe_clingo.min_semesters(kb.STUDENT_C), repeat=3)
    (np_, pp, _), tp = timeit(lambda: probe_cpsat.min_semesters(kb.STUDENT_C), repeat=3)
    print(f"{'Z3 Optimize':<16} k = {nz}   {tz:9.1f} ms")
    print(f"{'clingo (ASP)':<16} k = {nc}   {tc:9.1f} ms")
    print(f"{'CP-SAT':<16} k = {np_}   {tp:9.1f} ms")
    agree = (nz == nc == np_)
    print(f"\nDoi chieu cheo ba solver: {'TRUNG KHOP' if agree else 'KHONG TRUNG KHOP'}"
          f"  (k = {nz})")
    print(f"So hoc phan trong ke hoach: Z3={sum(len(v) for v in pz.values())}, "
          f"clingo={sum(len(v) for v in pc.values())}, "
          f"CP-SAT={sum(len(v) for v in pp.values())}")


if __name__ == "__main__":
    main()
