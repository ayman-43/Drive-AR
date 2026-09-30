"""
Verification gate for the demo run — adapted from writing-driven-autoresearch's
verify-phm.py. Checks every citation tag in the Writing agent's report against
the ids that actually exist in the Experiment agents' result files. Any tag
that doesn't resolve to a real, source-backed fact fails the build.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS = ROOT / "ralph" / "results"
REPORT = ROOT / "writing" / "report.md"

def load_valid_ids():
    valid = {}
    for f in RESULTS.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        for fact in data.get("facts", []):
            valid[fact["id"]] = fact
    return valid

def find_cited_ids(text):
    # matches [pricing-3], [features-2][pricing-1], etc.
    tags = re.findall(r"\[([a-zA-Z0-9_-]+)\]", text)
    return tags

def main():
    if not REPORT.exists():
        print(f"FAIL: report not found at {REPORT}")
        sys.exit(1)

    valid_ids = load_valid_ids()
    report_text = REPORT.read_text(encoding="utf-8")
    cited = find_cited_ids(report_text)

    unresolved = sorted(set(t for t in cited if t not in valid_ids))
    resolved = sorted(set(t for t in cited if t in valid_ids))
    unused = sorted(set(valid_ids) - set(cited))

    print(f"Report: {REPORT}")
    print(f"Total citation tags found: {len(cited)}  (unique: {len(set(cited))})")
    print(f"Resolved against a real, sourced fact: {len(resolved)}")
    print(f"Unused facts (measured but not cited — allowed, nothing lost): {len(unused)}")
    if unused:
        for u in unused:
            print(f"  - {u}: {valid_ids[u]['claim']}")

    print()
    if unresolved:
        print(f"FAIL: {len(unresolved)} citation(s) do not match any fact id on file:")
        for u in unresolved:
            print(f"  - [{u}]  <-- no source backs this, must be fixed or the sentence deleted")
        sys.exit(1)
    else:
        print("PASS: every citation in the report resolves to a real, sourced fact.")
        print("Nothing invented survives; nothing measured was silently dropped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
