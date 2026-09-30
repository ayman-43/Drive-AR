"""
The integrity gate. Adapted from writing-driven-autoresearch's verify-phm.py:
every citation tag [id] in the report must resolve to a fact id that actually
exists in one of the Experiment agent's result files. Nothing invented ships;
nothing measured is silently dropped.
"""
import re


def verify_report(report_text: str, all_results: dict) -> dict:
    valid_ids = {}
    for subtask, data in all_results.items():
        for fact in data.get("facts", []):
            valid_ids[fact["id"]] = fact

    cited = re.findall(r"\[([a-zA-Z0-9_-]+)\]", report_text)
    unique_cited = sorted(set(cited))
    resolved = [i for i in unique_cited if i in valid_ids]
    unresolved = [i for i in unique_cited if i not in valid_ids]
    unused = [i for i in valid_ids if i not in unique_cited]

    return {
        "pass": len(unresolved) == 0,
        "citation_tags_total": len(cited),
        "unique_ids_cited": len(unique_cited),
        "resolved": len(resolved),
        "unresolved": unresolved,
        "unused": unused,
    }
