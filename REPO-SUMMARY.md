# Summary: writing-driven-autoresearch

This repo is the complete run record of a hackathon entry, not software you install or run. It took 1st place at Ralphthon @ ICML 2026 ("Auto Research" track, $10,000 in OpenAI credits) for team WooandB, Woomin Song and Byungjun Yoon of KAIST's ALIN Lab.

This summary comes from the README and the file listing; the plan, ledger, and experiment code were not opened.

## What it did

Three AI agents produced an ICML-workshop paper end to end in about 3 hours with only light human guidance. The paper is *"Depth-AR: Skipping Transformer Layers Without Dropping Their Updates"* (`writing-main.pdf`). The README says every file except itself was written by the agents.

## The core idea

The agents wrote the paper first, then made it true. A complete 4-page draft with 105 placeholder numbers existed 22 minutes in, and each experiment existed to fill a specific gap in it. Two LaTeX macros kept this honest:

| Macro | Meaning | Rule at final audit |
|---|---|---|
| `\ph{}` | Invented guess | Replace with a measured number or delete the sentence |
| `\phm{}` | Measured, backed by a result JSON key | Keep the value and unwrap the macro |

`verify-phm.py` checks every `\phm{}` against its JSON, and `writing-audit.sh` fails the build if any `\ph{}` survives.

## The three agents

Everything that crosses an agent boundary goes through a file on disk, never chat.

- **`master.md`**: owns the clock, gates and decisions; runs no experiments.
- **`experiment.md`**: owns the GPUs, models and result JSONs; never touches the paper.
- **`writing.md`**: owns the LaTeX; reads numbers directly from the JSONs.

## What's in the repo

- **Harness (the reusable part)**: the three persona files, `writing-guidelines.md`, `writing-style-guide.md`, and the build and audit scripts.
- **`DEPTH-AR-PLAN.md`**: the 1,100-line project spec, with pre-committed pivots A–F covering every outcome, including negative results.
- **`ralph/`**: the shared state, including `DECISIONS.md` (136 timestamped decisions), `PH-LEDGER.md` and 53 result JSONs.
- **`auto-research/`**: the experiment code (about 31 scripts for layer scans, predictor variants, latency and noise audits).
- **`writing/`**: the paper source and figures.
- **Infra scaffolding**: `lobroster/` (the synced worker environment), `ralphthon-icml/` (the hackathon scaffold and skills) and `alin-skills/` (the lab's herdr and Overleaf-sync skills).

## How the run went

- **The original hypothesis failed at T+0:14.** The measured effect was anti-momentum, not momentum, and the master overrode a worker's `"passed": true`.
- **The storyline shifted six times.** The final claim is that predicting a skipped layer's update pays off in proportion to the damage skipping causes; it was significant on the 7B model under aggressive skipping.
- **A late Qwen3 sweep did not replicate.** The agents kept the primary result and shipped the non-replication as a scoping caveat.
- **The paper was submitted at T+2:27, 33 minutes early.** A user-directed extension ran to T+3:47.

## Polaris Integration & Synthesis

- **`polaris/`**: Cloned repository from `https://github.com/ZJU-REAL/Polaris.git`, an autonomous research platform built on the 6-stage lifecycle (Literature → Idea → Review → Experiment → Write → Review) and the Voyage Agent Core (Navigator/Helm/Sextant).
- **`POLARIS-MIX-SYNTHESIS.md`**: Detailed comparative analysis and unified blueprint blending writing-driven auto-research with Polaris.

Suggested reading order: `POLARIS-MIX-SYNTHESIS.md`, `ralph/DECISIONS.md` at T+0:14, then `ralph/PH-LEDGER.md`, then section 0 of `master.md`.

