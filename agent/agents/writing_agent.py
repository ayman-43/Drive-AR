"""
Writing agent: owns the report only. Reads structured fact files -- never
conversation, never a number relayed second-hand -- and drafts a report
where every factual sentence cites the exact fact id backing it.
Mirrors writing.md's boundary: it never runs research, only writes.
"""
import os

from anthropic import AsyncAnthropic

SYSTEM_PROMPT = """You are the WRITING AGENT in a three-agent research pipeline \
(Master / Experiment / Writing). You never did any research yourself -- you are only \
allowed to state a fact if you cite the exact id of a fact given to you below.

Hard rules:
- Every factual sentence (a number, a claim, a feature, a limitation) must end with an \
inline citation tag in square brackets referencing the exact fact id it came from, e.g. \
"X costs $20/month [pricing-3]." Combine multiple ids if needed: "...[pricing-3][features-1]".
- Never cite an id that isn't in the facts given to you.
- Never state a number or claim that isn't backed by one of these ids. Reasoning/transition \
sentences and the final recommendation's logic don't need a citation -- only factual claims do.
- Write in clean markdown: a title, a short intro, one section per sub-task, and a final \
recommendation section. Keep it tight -- do not pad.
"""


async def write_report(run_id: str, question: str, all_results: dict, store) -> str:
    store.log(run_id, "writing", "reading results/*.json only, drafting report")

    facts_block = ""
    for subtask, data in all_results.items():
        facts_block += f"\n## {subtask}\n"
        for f in data.get("facts", []):
            facts_block += f"- [{f['id']}] {f['claim']} (source: {f.get('source_name','')}, {f.get('source_url','')})\n"

    client = AsyncAnthropic()
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
    message = await client.messages.create(
        model=model,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Research question: {question}\n\n"
                f"Available sourced facts (grouped by sub-task):\n{facts_block}\n\n"
                f"Write the report now."
            ),
        }],
    )
    report_text = message.content[0].text.strip()
    store.write_report(run_id, report_text)
    store.log(run_id, "writing", f"report drafted, {len(report_text.split())} words")
    return report_text
