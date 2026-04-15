#!/usr/bin/env python3
"""
Patch code_eval_check in Teacher chatflow to handle the case where the LLM
sends [EVAL_READY] alone in a separate message.

Without fix: cleaned_text becomes "" → user sees an empty chat bubble.
With fix: fallback FR message is shown + eval_ready still triggers the diagnostic.
"""

import json
import subprocess

WORKFLOW_IDS = [
    "c52a451f-e381-46f1-a23a-077197b0fccb",  # published
    "ed0d1c91-8c9a-48ad-9c3a-063981f8da87",  # draft
]

NEW_CODE = """def main(text: str) -> dict:
    marker = "[EVAL_READY]"
    eval_ready = marker in text
    cleaned = text.replace(marker, "").strip()
    if eval_ready and not cleaned:
        cleaned = "Merci pour tes réponses ! Envoie-moi **ok** pour découvrir ton bilan de niveau."
    return {"cleaned_text": cleaned, "eval_ready": eval_ready}
"""


def load_graph(wid: str) -> dict:
    r = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-c", f"SELECT graph FROM workflows WHERE id='{wid}';"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout.strip())


def save_graph(wid: str, graph: dict) -> None:
    payload = json.dumps(graph, ensure_ascii=False).replace("'", "''")
    sql = f"UPDATE workflows SET graph = '{payload}'::json, updated_at = NOW() WHERE id = '{wid}';"
    r = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql, capture_output=True, text=True, check=True,
    )
    print(f"  [OK] {wid}: {r.stdout.strip()}")


def patch(graph: dict) -> bool:
    for node in graph.get("nodes", []):
        if node.get("id") == "code_eval_check":
            node["data"]["code"] = NEW_CODE
            return True
    return False


def main() -> None:
    for wid in WORKFLOW_IDS:
        print(f"Patching {wid} ...")
        graph = load_graph(wid)
        if not patch(graph):
            print(f"  [SKIP] code_eval_check node not found")
            continue
        save_graph(wid, graph)


if __name__ == "__main__":
    main()
