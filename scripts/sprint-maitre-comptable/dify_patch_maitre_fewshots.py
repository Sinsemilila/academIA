"""P1.3 — Inject 8 few-shots Lyster compta dans system prompt Maître Comptable.

Pattern API automation S57/S58 (login console + cookies session + draft update + publish).
"""
import sys, json
sys.path.insert(0, "/tmp")
from dify_helper import login, call

APP_ID = "4ce8ffe2-0cdf-4fa8-aab4-478e5dd8ac1c"
NEW_SYSTEM_PATH = "/tmp/maitre_augmented_system.txt"


def main():
    new_system = open(NEW_SYSTEM_PATH).read()
    print(f"New system prompt: {len(new_system)} chars")

    auth = login()

    # 1. Fetch draft
    code, draft = call(auth, "GET", f"/apps/{APP_ID}/workflows/draft")
    assert code == 200, f"draft fetch fail {code}: {draft}"
    graph = draft["graph"]
    hash_ = draft.get("hash")
    features = draft.get("features", {})
    env_vars = draft.get("environment_variables", [])
    conv_vars = draft.get("conversation_variables", [])
    print(f"Draft loaded — hash={hash_[:12] if hash_ else None}, nodes={len(graph['nodes'])}")

    # 2. Patch LLM node prompt[0]
    patched = False
    for n in graph["nodes"]:
        if n["id"] == "llm_maitre":
            old = n["data"]["prompt_template"][0]["text"]
            n["data"]["prompt_template"][0]["text"] = new_system
            print(f"Patched llm_maitre system prompt: {len(old)} → {len(new_system)} chars")
            patched = True
            break
    assert patched, "llm_maitre node not found"

    # 3. POST draft update
    body = {
        "graph": graph,
        "features": features,
        "environment_variables": env_vars,
        "conversation_variables": conv_vars,
        "hash": hash_,
    }
    code, resp = call(auth, "POST", f"/apps/{APP_ID}/workflows/draft", body=body)
    print(f"Draft update: status={code}")
    if code != 200:
        print(json.dumps(resp, indent=2)[:600])
        return 1
    print(f"  new hash={resp.get('hash', '?')[:12]}")

    # 4. Publish
    code, resp = call(auth, "POST", f"/apps/{APP_ID}/workflows/publish", body={})
    print(f"Publish: status={code}")
    if code not in (200, 201):
        print(json.dumps(resp, indent=2)[:600])
        return 1
    print(f"  published workflow id: {resp.get('id', '?')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
