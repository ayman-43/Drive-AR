import asyncio
import json

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from orchestrator import run_pipeline
from storage import store

app = FastAPI(title="ResearchOps Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    question: str


@app.post("/api/run")
async def start_run(req: RunRequest):
    run_id = store.create_run(req.question)
    asyncio.create_task(run_pipeline(run_id, req.question, store))
    return {"run_id": run_id}


@app.get("/api/run/{run_id}/status")
async def get_status(run_id: str):
    status = store.get_status(run_id)
    if not status:
        raise HTTPException(404, "run not found")
    return status


@app.get("/api/run/{run_id}/decisions")
async def get_decisions(run_id: str):
    return store.get_decisions(run_id)


@app.get("/api/run/{run_id}/results")
async def get_results(run_id: str):
    return store.read_all_results(run_id)


@app.get("/api/run/{run_id}/report")
async def get_report(run_id: str):
    report = store.get_report(run_id)
    verify = store.get_verify(run_id)
    if report is None:
        raise HTTPException(202, "not ready yet")
    return {"report": report, "verify": verify}


@app.get("/api/run/{run_id}/events")
async def events(run_id: str):
    async def gen():
        q = store.subscribe(run_id)
        try:
            # replay what already happened, so a client connecting late still sees history
            for d in store.get_decisions(run_id):
                yield f"data: {json.dumps({'type': 'decision', **d})}\n\n"
            status = store.get_status(run_id)
            if status:
                yield f"data: {json.dumps({'type': 'status', **status})}\n\n"
            while True:
                event = await asyncio.wait_for(q.get(), timeout=15)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") == "status" and event.get("phase") in ("done", "failed"):
                    break
        except asyncio.TimeoutError:
            yield ": keep-alive\n\n"
        finally:
            store.unsubscribe(run_id, q)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/health")
async def health():
    return {"ok": True}
