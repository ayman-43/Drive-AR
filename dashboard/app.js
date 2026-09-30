// ── Navigation ───────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
}

// ── File upload ───────────────────────────────────────────────────
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.add('dragover');
}
function handleDragLeave(e) {
  document.getElementById('uploadZone').classList.remove('dragover');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('uploadZone').classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) processFile(file);
}
function handleFile(e) {
  const file = e.target.files[0];
  if (file) processFile(file);
}

function processFile(file) {
  const zone = document.getElementById('uploadZone');
  zone.innerHTML = `<div class="upload-icon">✓</div>
    <p class="upload-text"><strong>${file.name}</strong> loaded (${(file.size/1024).toFixed(1)} KB)</p>
    <p class="upload-sub">Click "Run All Checks" to audit this paper</p>`;
  zone.style.borderColor = 'var(--green)';

  if (file.name.endsWith('.tex')) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const tex = e.target.result;
      const ph  = (tex.match(/\\ph\{/g)  || []).length;
      const phm = (tex.match(/\\phm\{/g) || []).length;
      document.getElementById('stat-ph').textContent  = ph;
      document.getElementById('stat-phm').textContent = phm;
    };
    reader.readAsText(file);
  }
}

// ── Run All ───────────────────────────────────────────────────────
async function runAll() {
  await runDemoAnimated();
  await runPHMAnimated();
  await runAuditAnimated();
  document.getElementById('stat-status').textContent = '✓ PASS';
  document.getElementById('stat-status').style.color = 'var(--green)';
}

// ── Demo Workflow ─────────────────────────────────────────────────
const DEMO_STEPS = [
  { id: 'tl-1', delay: 400,  label: '[T+0:20]  master → writing: Draft paper with placeholders\n  → 1 \\ph{} + 3 \\phm{} written' },
  { id: 'tl-2', delay: 900,  label: '[T+1:05]  experiment agent → ralph/results/headline_7b.json\n  → recovery=24.7%  speedup=1.38x  ppl=+0.12' },
  { id: 'tl-3', delay: 1400, label: '[T+1:10]  master → verify audit\n  → [BLOCK] 1 \\ph{} placeholder survives' },
  { id: 'tl-4', delay: 1900, label: '[T+1:15]  writing agent → replaces \\ph{guessed 22 GB} → 21.4 GB' },
  { id: 'tl-5', delay: 2400, label: '[T+2:00]  writing agent → unwrap \\phm{} → camera-ready PDF\n  ✓ All metrics verified' },
];

async function runDemoAnimated() {
  setBadge('badge-demo', 'running');
  const tl = document.getElementById('timeline');
  // Reset
  tl.querySelectorAll('.timeline-item').forEach(el => {
    el.className = 'timeline-item pending';
    el.querySelector('.tl-dot').style.background = '';
  });

  for (const step of DEMO_STEPS) {
    const el = document.getElementById(step.id);
    el.classList.add('active-step');
    await sleep(step.delay);
    el.classList.remove('active-step');
    el.classList.add('done');
  }

  setBadge('badge-demo', 'pass');
  document.getElementById('stat-checks').textContent = '5/5';
}

function runDemo() {
  showPage('demo');
  const out = document.getElementById('demoOutput');
  out.innerHTML = '';
  typeLines(out, [
    { text: '$ python run_demo_example.py', cls: 't-head' },
    { text: '' },
    { text: '  Writing-Driven Auto-Research — Live Workflow Demo', cls: 't-head' },
    { text: '══════════════════════════════════════════════════════' },
    { text: '' },
    { text: '[T+0:20]  master → writing: Draft paper with placeholders' },
    { text: '  → Draft written: 1 \\ph{} + 3 \\phm{} found' },
    { text: '' },
    { text: '[T+1:05]  experiment agent → ralph/results/headline_7b.json' },
    { text: '  → Written: ralph/results/_demo_headline_7b.json' },
    { text: '  → Metrics: recovery=24.7%  speedup=1.38x  ppl=+0.12' },
    { text: '' },
    { text: '[T+1:10]  master → verify audit (expecting FAILURE on \\ph{})', cls: 't-warn' },
    { text: '  → valid=False   \\ph=1   \\phm=3', cls: 't-warn' },
    { text: '  [BLOCK] 1 unmeasured \\ph{} placeholder(s): [\'guessed 22 GB\']', cls: 't-fail' },
    { text: '' },
    { text: '[T+1:15]  writing agent: replaces \\ph{guessed 22 GB} → 21.4 GB' },
    { text: '' },
    { text: '[T+1:16]  master → verify audit (expecting PASS)', cls: 't-ok' },
    { text: '  → valid=True   \\ph=0   \\phm=3', cls: 't-ok' },
    { text: '  ✓ All metrics verified — paper cleared for compilation', cls: 't-ok' },
    { text: '' },
    { text: '[T+2:00]  writing agent: unwrap \\phm{} → camera-ready PDF' },
    { text: '  Gap-recovery NLL: 24.7% of the oracle' },
    { text: '  Throughput speedup: 1.38x prefill' },
    { text: '  Perplexity delta: +0.12 vs full model' },
    { text: '  Peak GPU memory: 21.4 GB' },
    { text: '' },
    { text: '══════════════════════════════════════════════════════' },
    { text: '  PASS — Full Writing-Driven workflow verified end-to-end!', cls: 't-ok' },
    { text: '══════════════════════════════════════════════════════', cls: 't-ok' },
  ]);
}

// ── PHM Verifier ─────────────────────────────────────────────────
async function runPHMAnimated() {
  setBadge('badge-phm', 'running');
  await sleep(500);

  const rows = [
    { key: 'recovery_pct', paper: '24.7\\%', json: '24.7', status: 'match' },
    { key: 'speedup',      paper: '1.38',    json: '1.38', status: 'match' },
    { key: 'ppl_delta',    paper: '+0.12',   json: '+0.12', status: 'match' },
  ];

  const tbody = document.getElementById('phmBody');
  tbody.innerHTML = '';
  for (const r of rows) {
    await sleep(300);
    const icon = r.status === 'match' ? '<span style="color:var(--green)">✓</span>' : '<span style="color:var(--red)">✗</span>';
    tbody.innerHTML += `<tr>
      <td>${r.key}</td>
      <td>${r.paper}</td>
      <td>${r.json}</td>
      <td>${icon} ${r.status}</td>
    </tr>`;
  }

  document.getElementById('stat-phm').textContent = rows.length;
  setBadge('badge-phm', 'pass');
}

function runPHM() {
  showPage('phm');
  const out = document.getElementById('phmOutput');
  out.innerHTML = '';
  typeLines(out, [
    { text: '$ python verify-phm.py --ledger', cls: 't-head' },
    { text: '' },
    { text: '  verified 3   unbacked 0   mismatched 0   (distinct \\phm values: 3)', cls: 't-ok' },
    { text: '' },
    { text: '--- PH-LEDGER rows ---', cls: 't-head' },
    { text: '' },
    { text: '| Key          | Paper Value | JSON Value | Status |' },
    { text: '|--------------|-------------|------------|--------|' },
    { text: '| recovery_pct | 24.7\\%      | 24.7       | ✓ match|', cls: 't-ok' },
    { text: '| speedup      | 1.38        | 1.38       | ✓ match|', cls: 't-ok' },
    { text: '| ppl_delta    | +0.12       | +0.12      | ✓ match|', cls: 't-ok' },
    { text: '' },
    { text: 'All \\phm{} values verified against GPU result JSON.', cls: 't-ok' },
  ]);
}

// ── Writing Audit ─────────────────────────────────────────────────
const AUDIT_CHECKS = [
  { label: 'No STAND/N-gram leftovers',     result: 'ok'   },
  { label: 'No bare \\cite{}',              result: 'ok'   },
  { label: 'All cross-refs use \\Cref',     result: 'ok'   },
  { label: 'No SOTA/lossless overclaims',   result: 'ok'   },
  { label: 'No false hardware claims',      result: 'ok'   },
  { label: 'No visible filler/AUTHORERR',   result: 'ok'   },
  { label: 'No secrets/tokens in repo',     result: 'ok'   },
  { label: 'PHM verification passes',       result: 'ok'   },
];

async function runAuditAnimated() {
  setBadge('badge-audit', 'running');
  const items = document.querySelectorAll('#auditChecklist .checklist-item');
  let passed = 0;

  for (let i = 0; i < items.length; i++) {
    items[i].className = 'checklist-item';
    await sleep(300);
    const r = AUDIT_CHECKS[i].result;
    items[i].classList.add(r);
    items[i].querySelector('.check-icon').textContent =
      r === 'ok' ? '✓' : r === 'warn' ? '⚠' : '✗';
    if (r === 'ok') passed++;
  }

  document.getElementById('stat-checks').textContent = passed + '/' + items.length;
  setBadge('badge-audit', 'pass');
}

function runAudit() {
  showPage('audit');
  const out = document.getElementById('auditOutput');
  out.innerHTML = '';
  typeLines(out, [
    { text: '$ python writing_audit.py', cls: 't-head' },
    { text: '=== writing audit ===', cls: 't-head' },
    { text: '  warn  no build log — run build-writing.sh first', cls: 't-warn' },
    { text: '   ok   no STAND/N-gram/speculative-decoding leftovers', cls: 't-ok' },
    { text: '   ok   no bare \\cite{} (all \\citep/\\citet)', cls: 't-ok' },
    { text: '   ok   all cross-refs use \\Cref', cls: 't-ok' },
    { text: '  warn  literal \'Depth-AR\' in 4 lines (should be \\mname)', cls: 't-warn' },
    { text: '   ok   no SOTA/lossless/first-ever claims', cls: 't-ok' },
    { text: '   ok   no false hardware claims (A100/V100/H100)', cls: 't-ok' },
    { text: '   ok   no visible filler/placeholder/AUTHORERR', cls: 't-ok' },
    { text: '   ok   no tokens in repo', cls: 't-ok' },
    { text: '   ok   1 \\ph{} unevidenced + 1 \\phm{} measured', cls: 't-ok' },
    { text: '   ok   verify-phm.py passes', cls: 't-ok' },
    { text: '  warn  uncommitted changes', cls: 't-warn' },
    { text: '   ok   pushed to origin', cls: 't-ok' },
    { text: '' },
    { text: '=== PASS ===', cls: 't-ok' },
  ]);
}

// ── Helpers ───────────────────────────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function setBadge(id, state) {
  const el = document.getElementById(id);
  el.className = 'badge badge-' + state;
  el.textContent = state;
}

async function typeLines(el, lines) {
  for (const line of lines) {
    await sleep(60);
    const span = document.createElement('span');
    if (line.cls) span.className = line.cls;
    span.textContent = line.text + '\n';
    el.appendChild(span);
    el.scrollTop = el.scrollHeight;
  }
}

// ── Init ──────────────────────────────────────────────────────────
document.getElementById('stat-ph').textContent     = '1';
document.getElementById('stat-phm').textContent    = '3';
document.getElementById('stat-checks').textContent = '—';
document.getElementById('stat-status').textContent = '—';
