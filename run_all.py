"""
run_all.py — Run all Writing-Driven Auto-Research tools in one go
Usage: python run_all.py
"""
import subprocess, sys, os

env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

steps = [
    ("Demo (3-agent workflow)",  ["python", "run_demo_example.py"]),
    ("PHM Verifier",             ["python", "verify-phm.py", "--ledger"]),
    ("Writing Audit",            ["python", "writing_audit.py"]),
]

for title, cmd in steps:
    print(f"\n{'='*60}")
    print(f"  ▶  {title}")
    print(f"{'='*60}")
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        print(f"\n  [FAILED] {title} exited with code {r.returncode}")
        sys.exit(r.returncode)

print("\n" + "="*60)
print("  ✓  All checks passed!")
print("="*60)
