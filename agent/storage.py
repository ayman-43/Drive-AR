"""
File-based shared state for a run, modeled directly on ralph/ from
writing-driven-autoresearch: a status file, an append-only decision log,
one result file per sub-task, and the final report. Kept as plain files
on purpose -- it's the same "files, never chat" contract the source
repo uses, and it means a run survives a server restart.
"""
import asyncio
import json
import time
import uuid
from pathlib import Path

RUNS_DIR = Path(__file__).parent / "runs"
RUNS_DIR.mkdir(exist_ok=True)


class RunStore:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def _dir(self, run_id: str) -> Path:
        d = RUNS_DIR / run_id
        (d / "results").mkdir(parents=True, exist_ok=True)
        return d

    def create_run(self, question: str) -> str:
        run_id = uuid.uuid4().hex[:12]
        d = self._dir(run_id)
        self._write_json(d / "status.json", {
            "run_id": run_id,
            "question": question,
            "phase": "starting",
            "created_at": time.time(),
        })
        (d / "decisions.jsonl").touch()
        return run_id

    def set_status(self, run_id: str, **fields):
        d = self._dir(run_id)
        status = self._read_json(d / "status.json", {})
        status.update(fields)
        self._write_json(d / "status.json", status)
        self._publish(run_id, {"type": "status", **status})

    def get_status(self, run_id: str) -> dict:
        return self._read_json(self._dir(run_id) / "status.json", {})

    def log(self, run_id: str, who: str, text: str):
        entry = {"ts": time.time(), "who": who, "text": text}
        d = self._dir(run_id)
        with open(d / "decisions.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        self._publish(run_id, {"type": "decision", **entry})

    def get_decisions(self, run_id: str) -> list[dict]:
        path = self._dir(run_id) / "decisions.jsonl"
        if not path.exists():
            return []
        out = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def write_result(self, run_id: str, subtask: str, data: dict):
        path = self._dir(run_id) / "results" / f"{subtask}.json"
        self._write_json(path, data)
        self._publish(run_id, {"type": "result", "subtask": subtask, "facts": len(data.get("facts", []))})

    def read_all_results(self, run_id: str) -> dict:
        d = self._dir(run_id) / "results"
        out = {}
        for p in d.glob("*.json"):
            out[p.stem] = self._read_json(p, {})
        return out

    def write_report(self, run_id: str, text: str):
        (self._dir(run_id) / "report.md").write_text(text, encoding="utf-8")

    def get_report(self, run_id: str) -> str | None:
        p = self._dir(run_id) / "report.md"
        return p.read_text(encoding="utf-8") if p.exists() else None

    def write_verify(self, run_id: str, result: dict):
        self._write_json(self._dir(run_id) / "verify.json", result)
        self._publish(run_id, {"type": "verify", **result})

    def get_verify(self, run_id: str) -> dict | None:
        p = self._dir(run_id) / "verify.json"
        return self._read_json(p, None) if p.exists() else None

    # ---- pub/sub for live SSE ----
    def subscribe(self, run_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(run_id, []).append(q)
        return q

    def unsubscribe(self, run_id: str, q: asyncio.Queue):
        subs = self._subscribers.get(run_id, [])
        if q in subs:
            subs.remove(q)

    def _publish(self, run_id: str, event: dict):
        for q in self._subscribers.get(run_id, []):
            q.put_nowait(event)

    @staticmethod
    def _write_json(path: Path, data):
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path, default):
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))


store = RunStore()
