"""
validate_parser.py — kiểm chứng Semantic Parser Tuần 13 (CPA2)

Tiêu chí: "Parse ≥80% test nội bộ"

Chạy:  python validate_parser.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parser import run_tests

def main():
    print("="*78)
    print("VALIDATE SEMANTIC PARSER — Tuần 13 (CPA2)")
    print("Q tiếng Việt → formal query (intent + claim + params)")
    print("="*78)
    acc = run_tests()
    print("\n"+"="*78)
    if acc >= 0.8:
        print(f"KẾT LUẬN: ĐẠT — {acc:.0%} ≥ 80%")
        print("="*78)
        return 0
    print(f"KẾT LUẬN: CHƯA ĐẠT — {acc:.0%} < 80%")
    print("="*78)
    return 1

if __name__=="__main__": sys.exit(main())
