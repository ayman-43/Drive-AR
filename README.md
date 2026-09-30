# Drive-AR — Writing-Driven AutoResearch

> **Built for GATEWAYS 2026 – 24° Shift Hackathon**  
> *Every number in your paper, verified by code.*

A 3-agent AI pipeline that writes the research paper **first** with placeholders, runs real experiments, then **blocks submission** if any unverified claim survives.

---

## 🚀 Quick Start (Demo)

**Double-click to launch:**
```
START-DASHBOARD.bat
```
This starts the server and opens the dashboard at `http://localhost:5500` automatically.

---

## 🎯 What It Does

| Stage | Agent | Action |
|---|---|---|
| T+0:00 | **master** | Reads research idea from `DEPTH-AR-PLAN.md`, orchestrates sprint |
| T+0:20 | **writing** | Drafts paper with `\ph{guess}` placeholders |
| T+1:00 | **experiment** | Runs GPU benchmarks → saves to `ralph/results/*.json` |
| T+1:30 | **writing** | Replaces `\ph{}` with `\phm{key}{verified_value}` |
| T+2:00 | **master** | Audit passes → builds final PDF |

---

## 📄 The Two Key Macros

```latex
% ❌ Unverified guess — BLOCKS the paper if it survives to submission
\ph{guessed ~22 GB}

% ✅ Verified metric — checked against ralph/results/*.json before compiling
\phm{speedup}{1.38}
```

---

## 🖥️ Running the Tools

```bash
# Full 3-agent workflow simulation
python run_demo_example.py

# Verify \phm{} values against experiment JSONs
python verify-phm.py --ledger

# 10-point paper quality audit
python writing_audit.py

# Run everything at once
python run_all.py
```

---

## 📁 Project Structure

```
writing-driven-autoresearch/
│
├── START-DASHBOARD.bat        ← One-click demo launcher
├── run_all.py                 ← Run all checks at once
├── run_demo_example.py        ← 3-agent workflow simulation
├── verify-phm.py              ← PHM metric verifier
├── writing_audit.py           ← 10-point paper audit
│
├── master.md                  ← Master agent system prompt
├── experiment.md              ← Experiment agent system prompt
├── writing.md                 ← Writing agent system prompt
├── DEPTH-AR-PLAN.md           ← Research idea & plan (edit this for new papers)
│
├── dashboard/                 ← Web UI (served at localhost:5500)
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── sample_paper.tex       ← Test paper with \ph{} and \phm{} examples
│
├── writing/                   ← LaTeX source
│   └── main.tex
│
├── ralph/                     ← Shared agent state
│   ├── results/               ← Experiment JSON outputs
│   └── DECISIONS.md           ← Agent decision log
│
├── writing-template-reference.pdf  ← Paper BEFORE experiments (with \ph{})
└── writing-main.pdf                ← Paper AFTER verification (final output)
```

---

## 📋 Quick Demo Walkthrough

1. Double-click `START-DASHBOARD.bat`
2. Upload `dashboard/sample_paper.tex` (or your own `.tex` file)
3. Click **▶ Run Full Audit**
4. See every placeholder flagged, every metric verified
5. Download the verified paper PDF

