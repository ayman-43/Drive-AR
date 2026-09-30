"""
Master agent: owns the clock and every gate/decision. Never researches,
never writes. Decomposes the question, dispatches Experiment workers in
parallel, structurally checks their output before trusting it, dispatches
Writing, then runs the verification gate before marking the run done.
"""
import asyncio
import json
import os

from anthropic import AsyncAnthropic

from agents.experiment_agent import research_subtask
from agents.writing_agent import write_report
from verify import verify_report

DECOMPOSE_SYSTEM_PROMPT = """You are the MASTER agent in a three-agent research pipeline. \
Your only job right now is to break a research question into 2-4 independent, parallel \
sub-tasks that Experiment workers can research separately (e.g. pricing, features, \
trade-offs, market size -- whatever actually fits the question). Output ONLY JSON, no prose:
{"subtasks": [{"name": "short_slug", "query": "a concrete search query for this sub-task"}]}
"""


async def decompose(question: str) -> list[dict]:
    client = AsyncAnthropic()
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    message = await client.messages.create(
        model=model,
        max_tokens=500,
        system=DECOMPOSE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Research question: {question}"}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    return json.loads(text)["subtasks"]


async def run_pipeline(run_id: str, question: str, store):
    try:
        store.set_status(run_id, phase="decomposing")
        store.log(run_id, "master", f"kickoff: \"{question}\"")

        subtasks = await decompose(question)
        store.log(run_id, "master", "decomposed into " + ", ".join(s["name"] for s in subtasks))
        store.set_status(run_id, phase="experiment", subtasks=[s["name"] for s in subtasks])

        await asyncio.gather(*[
            research_subtask(run_id, s["name"], s["query"], store) for s in subtasks
        ])

        store.log(run_id, "master", "all experiment workers reported done -- verifying files directly before trusting them")
        all_results = store.read_all_results(run_id)
        total_facts = sum(len(d.get("facts", [])) for d in all_results.values())
        bad = [f["id"] for d in all_results.values() for f in d.get("facts", []) if not f.get("source_url")]
        store.log(run_id, "master", f"{total_facts} facts collected across {len(all_results)} files, {len(bad)} missing a source url")

        store.set_status(run_id, phase="writing")
        report_text = await write_report(run_id, question, all_results, store)

        store.set_status(run_id, phase="verifying")
        result = verify_report(report_text, all_results)
        store.write_verify(run_id, result)
        verdict = "PASS" if result["pass"] else "FAIL"
        store.log(run_id, "master", f"verification gate: {verdict} -- {result['resolved']}/{result['unique_ids_cited']} citations resolved, {len(result['unresolved'])} unresolved")

        store.set_status(run_id, phase="done", verdict=verdict)
    except Exception as e:
        store.log(run_id, "master", f"RUN FAILED: {e}")
        store.set_status(run_id, phase="failed", error=str(e))
        raise
