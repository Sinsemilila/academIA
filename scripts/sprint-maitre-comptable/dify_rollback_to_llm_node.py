"""Rollback agent_compta → llm_maitre after P1.1 blocker on Dify plugin daemon.

Restores the basic LLM node architecture from after P1.3 ship (e6cc842) so
Marie keeps a working chatflow. P1.1 tools wiring deferred.
"""
import sys, json
sys.path.insert(0, "/tmp")
from dify_helper import login, call

APP_ID = "4ce8ffe2-0cdf-4fa8-aab4-478e5dd8ac1c"
SYSTEM_PROMPT_PATH = "/opt/academie/scripts/sprint-maitre-comptable/maitre_augmented_system.txt"


def main():
    system_prompt = open(SYSTEM_PROMPT_PATH).read()
    auth = login()

    code, draft = call(auth, "GET", f"/apps/{APP_ID}/workflows/draft")
    assert code == 200
    graph = draft["graph"]
    hash_ = draft.get("hash")
    features = draft.get("features", {})
    env_vars = draft.get("environment_variables", [])
    conv_vars = draft.get("conversation_variables", [])

    # Find position
    pos = {"x": 604, "y": 221}
    for n in graph["nodes"]:
        if n["id"] in ("llm_maitre", "agent_compta"):
            pos = n.get("position", pos)
            break

    # Build basic LLM node (matches state at S59 commit e6cc842)
    llm_node = {
        "id": "llm_maitre",
        "position": pos,
        "type": "custom",
        "data": {
            "type": "llm",
            "title": "Maître Comptable LLM",
            "desc": "",
            "model": {
                "provider": "langgenius/openai_api_compatible/openai_api_compatible",
                "name": "gpt-4o-mini",
                "mode": "chat",
                "completion_params": {"temperature": 0.5, "max_tokens": 2048},
            },
            "prompt_template": [
                {"role": "system", "text": system_prompt, "edition_type": "basic", "id": "sys-1"},
                {"role": "user", "text": "{{#sys.query#}}", "edition_type": "basic", "id": "usr-1"},
            ],
            "memory": {
                "role_prefix": {"user": "", "assistant": ""},
                "window": {"enabled": True, "size": 10},
            },
            "context": {
                "enabled": True,
                "variable_selector": ["knowledge_compta", "result"],
            },
            "vision": {"enabled": True, "configs": {"detail": "high"}},
            "structured_output_enabled": False,
        },
    }

    graph["nodes"] = [n for n in graph["nodes"] if n["id"] not in ("llm_maitre", "agent_compta")]
    graph["nodes"].append(llm_node)

    # Re-wire edges
    new_edges = []
    for e in graph.get("edges", []):
        src, tgt = e.get("source"), e.get("target")
        if src == "agent_compta":
            e = {**e, "source": "llm_maitre"}
            if "id" in e:
                e["id"] = e["id"].replace("agent_compta", "llm_maitre")
        if tgt == "agent_compta":
            e = {**e, "target": "llm_maitre"}
            if "id" in e:
                e["id"] = e["id"].replace("agent_compta", "llm_maitre")
        new_edges.append(e)
    graph["edges"] = new_edges

    for n in graph["nodes"]:
        if n["id"] == "answer_main":
            old = n["data"].get("answer", "")
            n["data"]["answer"] = old.replace("{{#agent_compta.text#}}", "{{#llm_maitre.text#}}")
            print(f"answer_main: '{old}' → '{n['data']['answer']}'")

    body = {
        "graph": graph,
        "features": features,
        "environment_variables": env_vars,
        "conversation_variables": conv_vars,
        "hash": hash_,
    }
    code, resp = call(auth, "POST", f"/apps/{APP_ID}/workflows/draft", body=body)
    print(f"draft update: {code} hash={resp.get('hash','?')[:12]}")
    code, resp = call(auth, "POST", f"/apps/{APP_ID}/workflows/publish", body={})
    print(f"publish: {code}")
    return 0 if code in (200, 201) else 1


if __name__ == "__main__":
    sys.exit(main())
