#!/usr/bin/env python3
r"""
writing_audit.py — Native Python port of writing-audit.sh
Usage:
    python writing_audit.py            # audit only
    python writing_audit.py --final    # also FAIL if any \ph{} survives
"""

import re, sys, subprocess
from pathlib import Path

ROOT    = Path(__file__).parent / "writing"
FINAL   = "--final" in sys.argv
fails   = 0

def ok(msg):  print(f"  \033[32m ok \033[0m {msg}")
def fail(msg): global fails; fails += 1; print(f"  \033[31mFAIL\033[0m {msg}")
def warn(msg): print(f"  \033[33mwarn\033[0m {msg}")

print("=== writing audit ===")

if not ROOT.exists():
    print(f"  [skip] writing/ directory not found at {ROOT}")
    print("  (This is a reference run — no live paper to audit.)")
    print()
    print("  Sections audited in a real sprint:")
    print("  1. Build log — 0 undefined citations/references")
    print(r"  2. No STAND/N-gram/speculative-decoding leftovers")
    print(r"  3. No bare \cite{} — all must use \citep/\citet")
    print(r"  4. All cross-refs use \Cref (no hand-typed Figure~\ref)")
    print(r"  5. Method name always via \mname macro")
    print("  6. No overclaims: SOTA, lossless, first-ever")
    print("  6b. No false hardware claims (A100/V100/H100)")
    print(r"  7. PDF is anonymous; no visible filler/placeholder")
    print("  8. No tokens/secrets in repo")
    print(r"  9. \ph{} count (must be 0 at --final); \phm{} verified")
    print("  9b. verify-phm.py passes")
    print("  10. Working tree clean, pushed to origin")
    sys.exit(0)

tex_files = list(ROOT.rglob("*.tex"))
all_tex   = "\n".join(f.read_text(errors="replace") for f in tex_files)

# ── 1. Undefined citations/references ───────────────────────────────────────
log_path = ROOT.parent / "writing-build" / "main.log"
if log_path.exists():
    log = log_path.read_text(errors="replace")
    u = len(re.findall(r"undefined (citation|reference)", log, re.I))
    if u == 0: ok("0 undefined citations/references")
    else:      fail(f"{u} undefined citation/reference warnings")
else:
    warn("no build log — run build-writing.sh first")

# ── 2. STAND/N-gram leftovers ────────────────────────────────────────────────
STAND = re.compile(r'\b(stand|n-gram|ngram|speculative|drafting|gumbel)\b', re.I)
hits = [(f.name, ln+1, l.strip()) for f in tex_files
        for ln, l in enumerate(f.read_text(errors="replace").splitlines())
        if STAND.search(l) and not l.strip().startswith('%')]
if not hits: ok("no STAND/N-gram/speculative-decoding leftovers")
else:
    fail(f"STAND/N-gram leftovers in {len(hits)} line(s):")
    for name, ln, l in hits[:5]: print(f"       {name}:{ln}: {l}")

# ── 3. Bare \cite{} ──────────────────────────────────────────────────────────
bare = len(re.findall(r'\\cite\{', all_tex))
if bare == 0: ok(r"no bare \cite{} (all \citep/\citet)")
else:         fail(f"{bare} bare \\cite{{}}")

# ── 4. Hand-typed Figure~\ref ────────────────────────────────────────────────
if re.search(r'(Figure|Table|Section)~\\ref', all_tex):
    fail(r"hand-typed Figure~\ref found — use \Cref")
else:
    ok(r"all cross-refs use \Cref")

# ── 5. Literal method name ───────────────────────────────────────────────────
lit = [l.strip() for l in all_tex.splitlines()
       if 'Depth-AR' in l and 'mname' not in l and not l.strip().startswith('%')]
if not lit: ok(r"\mname used everywhere (no literal method name)")
else:       warn(f"literal 'Depth-AR' found in {len(lit)} line(s) (should be \\mname)")

# ── 6. Overclaims ────────────────────────────────────────────────────────────
OC = re.compile(r'state[- ]of[- ]the[- ]art|SOTA|lossless|first (activation|linear|ever)|outperforms all', re.I)
oc = [l.strip() for l in all_tex.splitlines() if OC.search(l)]
if not oc: ok("no SOTA/lossless/first-ever claims")
else:      fail(f"forbidden claim in {len(oc)} line(s): {oc[:2]}")

# ── 6b. False hardware claims ────────────────────────────────────────────────
HW = re.compile(r'\b(a100|v100|h100)\b', re.I)
hw = [l.strip() for l in all_tex.splitlines() if HW.search(l)]
if not hw: ok("no false hardware claims (A100/V100/H100)")
else:      fail(f"false hardware claim in {len(hw)} line(s)")

# ── 7. Visible filler ────────────────────────────────────────────────────────
FILL = re.compile(r'placeholder|lipsum|lorem|TODO|AUTHORERR', re.I)
filler = [l.strip() for l in all_tex.splitlines()
          if FILL.search(l) and not l.strip().startswith('%')]
if not filler: ok("no visible filler/placeholder/AUTHORERR")
else:          fail(f"filler found in {len(filler)} line(s)")

# ── 8. No secrets ────────────────────────────────────────────────────────────
# Only scan tex + ralph JSON, never the audit scripts themselves
scan_files = tex_files + list((Path(".") / "ralph").rglob("*.json") if (Path(".") / "ralph").exists() else [])
s_hits = [f for f in scan_files if 'olp_' in f.read_text(errors="replace")]
if not s_hits: ok("no tokens in repo")
else:          fail(f"TOKEN found in: {[str(f) for f in s_hits]}")

# ── 9. \ph{} and \phm{} counts ──────────────────────────────────────────────
ph  = len(re.findall(r'\\ph\{',  all_tex))
phm = len(re.findall(r'\\phm\{', all_tex))
if FINAL:
    if ph == 0: ok(r"0 surviving \ph{} — no unevidenced numbers")
    else:       fail(fr"{ph} \ph{{}} still wrapped — land the real number or DELETE THE SENTENCE")
    if phm > 0: warn(fr"{phm} \phm{{}} still wrapped — UNWRAP them (keep the value)")
    else:       ok(r"0 surviving \phm{}")
else:
    ok(fr"{ph} \ph{{}} unevidenced + {phm} \phm{{}} measured (see ralph/PH-LEDGER.md)")

# ── 9b. verify-phm.py ───────────────────────────────────────────────────────
vp = Path("verify-phm.py")
if vp.exists():
    r = subprocess.run([sys.executable, str(vp)], capture_output=True, text=True)
    line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    if r.returncode == 0: ok(line)
    else:                 fail(r"\phm{} verification failed:\n" + r.stdout)

# ── 10. Git status ───────────────────────────────────────────────────────────
try:
    dirty = subprocess.run(["git","status","--porcelain"], capture_output=True, text=True).stdout.strip()
    if not dirty: ok("working tree clean")
    else:         warn("uncommitted changes")
    ahead = subprocess.run(["git","log","origin/main..HEAD","--oneline"],
                           capture_output=True, text=True).stdout.strip()
    if not ahead: ok("pushed to origin")
    else:         warn("unpushed commits")
except Exception:
    warn("git not available")

print(f"=== {'PASS' if fails == 0 else str(fails) + ' FAILURE(S)'} ===")
sys.exit(fails)
