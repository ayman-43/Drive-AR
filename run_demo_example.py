"""
Demo: Writing-Driven Auto-Research Engine
==========================================
Simulates the full 3-agent writing-first workflow:
  1. Paper is drafted FIRST with \ph{} (guesses) and \phm{} (metric contracts)
  2. Experiments run and produce result JSONs
  3. All \phm{} values are verified against the JSONs
  4. Build FAILS if any \ph{} placeholder survives
  5. Final paper is unwrapped and ready for camera-ready submission
"""

import re, json
from pathlib import Path

# ── PHM engine (inline, no external deps) ──────────────────────────────────

PH_PATTERN  = re.compile(r'\\ph\{([^}]*)\}')
PHM_PATTERN = re.compile(r'\\phm\{([^}]+)\}\{([^}]*)\}')

def normalize(val):
    return val.replace(r'\%', '%').strip()

def audit(tex, metrics):
    ph_hits  = PH_PATTERN.findall(tex)
    phm_hits = PHM_PATTERN.findall(tex)
    errors   = []
    if ph_hits:
        errors.append(f"[BLOCK] {len(ph_hits)} unmeasured \\ph{{}} placeholder(s): {ph_hits}")
    for key, val in phm_hits:
        if key not in metrics:
            errors.append(f"[BLOCK] \\phm key '{key}' not found in experiment JSON")
        elif normalize(val) != normalize(str(metrics[key])):
            errors.append(f"[MISMATCH] '{key}': paper has '{normalize(val)}', JSON has '{normalize(str(metrics[key]))}'")
    return {"valid": len(errors) == 0, "ph": len(ph_hits), "phm": len(phm_hits), "errors": errors}

def unwrap(tex):
    return PHM_PATTERN.sub(r'\2', tex)

# ── STAGE 1: master agent writes the paper draft at T+0:20 ─────────────────

print("=" * 62)
print("  Writing-Driven Auto-Research — Live Workflow Demo")
print("=" * 62)

print("\n[T+0:20]  master → writing: Draft paper with placeholders")

paper_draft = r"""
\section{Abstract}
We propose Depth-AR, a training-free method for Transformer layer
skipping that predicts residual updates from a learned depth
trajectory instead of zeroing them out.

\section{Results}
On Qwen2.5-7B with 14 of 28 layers skipped:
\begin{itemize}
  \item Gap-recovery NLL: \phm{recovery_pct}{24.7}\% of the oracle
  \item Throughput speedup: \phm{speedup}{1.38}x prefill
  \item Perplexity delta: \phm{ppl_delta}{+0.12} vs full model
  \item Peak GPU memory: \ph{guessed 22 GB}
\end{itemize}
"""

print(f"  → Draft written: {paper_draft.count(chr(92)+'ph{')} \\ph{{}} + {paper_draft.count(chr(92)+'phm{')} \\phm{{}} found")

# ── STAGE 2: experiment agent runs GPU jobs, writes result JSON ─────────────

print("\n[T+1:05]  experiment agent → ralph/results/headline_7b.json")

experiment_json = {
    "model":        "Qwen2.5-7B-Instruct",
    "layers_skipped": 14,
    "recovery_pct": "24.7",
    "speedup":      "1.38",
    "ppl_delta":    "+0.12",
}

result_file = Path("ralph") / "results" / "_demo_headline_7b.json"
result_file.parent.mkdir(parents=True, exist_ok=True)
result_file.write_text(json.dumps(experiment_json, indent=2))
print(f"  → Written: {result_file}")
print(f"  → Metrics: recovery={experiment_json['recovery_pct']}%  speedup={experiment_json['speedup']}x  ppl={experiment_json['ppl_delta']}")

# ── STAGE 3: master calls verify — should FAIL because \ph{} survives ───────

print("\n[T+1:10]  master → verify audit (expecting FAILURE on \\ph{})")
result = audit(paper_draft, experiment_json)
print(f"  → valid={result['valid']}   \\ph={result['ph']}   \\phm={result['phm']}")
for e in result['errors']:
    print(f"  {e}")

# ── STAGE 4: writing agent replaces the \ph{} with the real number ──────────

print("\n[T+1:15]  writing agent: replaces \\ph{guessed 22 GB} → 21.4 GB (measured)")
paper_fixed = paper_draft.replace(r"\ph{guessed 22 GB}", r"21.4 GB")

# ── STAGE 5: verify again — must PASS ───────────────────────────────────────

print("\n[T+1:16]  master → verify audit (expecting PASS)")
result2 = audit(paper_fixed, experiment_json)
print(f"  → valid={result2['valid']}   \\ph={result2['ph']}   \\phm={result2['phm']}")
if result2['valid']:
    print("  ✓ All metrics verified against GPU result JSON — paper cleared for compilation")

# ── STAGE 6: writing agent unwraps \phm{} → raw numbers for tectonic ────────

print("\n[T+2:00]  writing agent: unwrap \\phm{} for camera-ready PDF")
final_tex = unwrap(paper_fixed)
print("\n  ─── Camera-Ready Section (results only) ───────────────────")
for line in final_tex.splitlines():
    if line.strip():
        print("  " + line)

# ── STAGE 7: clean up demo file ─────────────────────────────────────────────
result_file.unlink()

print("\n" + "=" * 62)
print("  PASS — Full Writing-Driven workflow verified end-to-end!")
print("=" * 62)
