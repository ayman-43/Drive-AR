"""
Experiment agent: owns web research only. Never sees the report, never
writes prose -- it searches, then extracts facts strictly grounded in what
it actually retrieved, and writes them to a structured file. This mirrors
experiment.md's boundary: it owns data collection, nothing else.
"""
import json
import os

import httpx
from anthropic import AsyncAnthropic

TAVILY_URL = "https://api.tavily.com/search"

EXTRACT_SYSTEM_PROMPT = """You are the EXPERIMENT AGENT in a three-agent research pipeline \
(Master / Experiment / Writing). You never write a report and never talk to the other \
agents -- the only thing you produce is a list of structured facts.

Hard rules:
- Every fact must be grounded ONLY in the search results you were given below. Do not add \
anything from your own prior knowledge, even if you believe it's true.
- If the search results don't clearly support a fact, leave it out. Fewer correct facts beat \
more unverifiable ones.
- Give every fact a short unique id in the form "<subtask>-1", "<subtask>-2", etc.
- Output ONLY a JSON object matching this schema, no prose, no markdown fences:
{"facts": [{"id": "...", "claim": "...", "source_name": "...", "source_url": "..."}]}
"""


async def research_subtask(run_id: str, subtask: str, query: str, store) -> dict:
    store.log(run_id, "experiment", f"{subtask}: searching -> \"{query}\"")

    api_key = os.environ.get("TAVILY_API_KEY", "")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(TAVILY_URL, json={
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 6,
            "include_answer": False,
        })
        resp.raise_for_status()
        search = resp.json()

    results = search.get("results", [])
    store.log(run_id, "experiment", f"{subtask}: {len(results)} sources retrieved, extracting grounded facts")

    snippets = "\n\n".join(
        f"[{i+1}] {r.get('title', '')} ({r.get('url', '')})\n{r.get('content', '')[:1500]}"
        for i, r in enumerate(results)
    )

    client = AsyncAnthropic()
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    message = await client.messages.create(
        model=model,
        max_tokens=2000,
        system=EXTRACT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Sub-task name: {subtask}\n"
                f"Research question for this sub-task: {query}\n\n"
                f"Search results:\n{snippets}\n\n"
                f"Extract grounded facts as JSON now."
            ),
        }],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    data = json.loads(text)

    # backfill source_url from the matching search result if the model omitted it
    url_by_title = {r.get("title", ""): r.get("url", "") for r in results}
    for fact in data.get("facts", []):
        if not fact.get("source_url"):
            fact["source_url"] = url_by_title.get(fact.get("source_name", ""), "")

    data["subtask"] = subtask
    store.write_result(run_id, subtask, data)
    store.log(run_id, "experiment", f"{subtask}: wrote {len(data.get('facts', []))} sourced facts")
    return data
