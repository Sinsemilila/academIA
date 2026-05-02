"""P1.1 — Wire 5 compta tools into Maître Comptable Dify chatflow.

Replaces basic LLM node `llm_maitre` with Agent node `agent_compta` (strategy:
function_calling) wired to the 5 custom api tools registered under provider
`compta_tools` (lookup_pcg, verify_partie_double, verify_calcul_tva,
verify_compte_classe, lookup_studi_module).

Prerequisites (already done):
- compta_tools API tool provider registered (POST /tool-provider/api/add)
- langgenius/agent plugin installed (POST /plugin/install/marketplace)

Pipeline: start → knowledge_compta → agent_compta → answer_main
"""
import sys, json
sys.path.insert(0, "/tmp")
from dify_helper import login, call

APP_ID = "4ce8ffe2-0cdf-4fa8-aab4-478e5dd8ac1c"
SYSTEM_PROMPT_PATH = "/opt/academie/scripts/sprint-maitre-comptable/maitre_augmented_system.txt"
TOOLS_META_PATH = "/tmp/compta_tools_meta.json"
PROVIDER_NAME = "compta_tools"  # human-readable, used to fetch provider UUID at runtime

def get_provider_uuid(auth) -> str:
    """Resolve compta_tools provider name → UUID."""
    code, resp = call(auth, "GET", "/workspaces/current/tool-providers")
    assert code == 200, f"tool-providers fetch failed: {code}"
    for p in resp:
        if p.get("name") == PROVIDER_NAME and p.get("type") == "api":
            return p["id"]
    raise RuntimeError(f"provider '{PROVIDER_NAME}' (type=api) not found")


def build_tool_selectors(meta: dict, provider_uuid: str) -> list[dict]:
    """Build agent_parameters[tools].value entries (array[tools] format).

    Each entry follows the shape consumed by AgentNode runtime_support
    (cf core/workflow/nodes/agent/runtime_support.py L80-110): per-tool dict
    with type/provider_name/tool_name/parameters where each parameter is
    auto=1 (LLM-filled at function-calling runtime).
    """
    out = []
    for tool_name, info in meta.items():
        params_dict = {}
        for p in info["parameters"]:
            # auto=1 (OPEN) → LLM provides at runtime via function calling
            params_dict[p["name"]] = {"auto": 1, "value": None}
        out.append({
            "enabled": True,
            "type": "api",
            "provider_name": provider_uuid,
            "tool_name": tool_name,
            "parameters": params_dict,
            "settings": {},
            "credential_id": None,
            "plugin_unique_identifier": None,
            "extra": {"description": info["description"]},
        })
    return out


def build_agent_node(system_prompt: str, tool_selectors: list[dict], position: dict) -> dict:
    """Build agent node data block."""
    return {
        "id": "agent_compta",
        "position": position,
        "type": "custom",
        "data": {
            "type": "agent",
            "title": "Maître Comptable Agent",
            "desc": "Function-calling agent with 5 deterministic compta tools.",
            "agent_strategy_provider_name": "langgenius/agent/agent",
            "agent_strategy_name": "ReAct",
            "agent_strategy_label": "ReAct",
            "tool_node_version": "2",
            "agent_parameters": {
                "model": {
                    "type": "constant",
                    "value": {
                        "provider": "langgenius/openai_api_compatible/openai_api_compatible",
                        "model": "gpt-4o-mini",
                        "model_type": "llm",
                        "mode": "chat",
                        "completion_params": {"temperature": 0.5, "max_tokens": 2048},
                    },
                },
                "tools": {"type": "constant", "value": tool_selectors},
                "instruction": {"type": "constant", "value": system_prompt},
                "query": {"type": "constant", "value": "{{#sys.query#}}"},
                "context": {
                    "type": "variable",
                    "value": ["knowledge_compta", "result"],
                },
                "maximum_iterations": {"type": "constant", "value": 5},
            },
            "memory": {
                "role_prefix": {"user": "", "assistant": ""},
                "window": {"enabled": True, "size": 10},
            },
        },
    }


def main():
    system_prompt = open(SYSTEM_PROMPT_PATH).read()
    tools_meta = json.load(open(TOOLS_META_PATH))
    print(f"system prompt: {len(system_prompt)} chars")
    print(f"tools to wire: {list(tools_meta.keys())}")

    auth = login()

    # 1. Fetch draft
    code, draft = call(auth, "GET", f"/apps/{APP_ID}/workflows/draft")
    assert code == 200, f"draft fetch fail {code}"
    graph = draft["graph"]
    hash_ = draft.get("hash")
    features = draft.get("features", {})
    env_vars = draft.get("environment_variables", [])
    conv_vars = draft.get("conversation_variables", [])

    # 2. Find position from existing llm_maitre or agent_compta (idempotent)
    pos = None
    for n in graph["nodes"]:
        if n["id"] in ("llm_maitre", "agent_compta"):
            pos = n.get("position", {"x": 604, "y": 221})
            break
    if not pos:
        pos = {"x": 604, "y": 221}

    # 3. Build new agent node
    provider_uuid = get_provider_uuid(auth)
    print(f"compta_tools provider UUID: {provider_uuid}")
    selectors = build_tool_selectors(tools_meta, provider_uuid)
    agent_node = build_agent_node(system_prompt, selectors, pos)

    # 4. Replace nodes: drop llm_maitre + agent_compta, append fresh agent_compta
    graph["nodes"] = [n for n in graph["nodes"] if n["id"] not in ("llm_maitre", "agent_compta")]
    graph["nodes"].append(agent_node)

    # 5. Re-wire edges: knowledge_compta → agent_compta → answer_main
    new_edges = []
    for e in graph.get("edges", []):
        src, tgt = e.get("source"), e.get("target")
        if src == "llm_maitre":
            e = {**e, "source": "agent_compta"}
            # Update id/handle if present
            if "id" in e:
                e["id"] = e["id"].replace("llm_maitre", "agent_compta")
        if tgt == "llm_maitre":
            e = {**e, "target": "agent_compta"}
            if "id" in e:
                e["id"] = e["id"].replace("llm_maitre", "agent_compta")
        new_edges.append(e)
    graph["edges"] = new_edges

    # 6. Update answer_main reference to agent output
    for n in graph["nodes"]:
        if n["id"] == "answer_main":
            old = n["data"].get("answer", "")
            n["data"]["answer"] = old.replace("{{#llm_maitre.text#}}", "{{#agent_compta.text#}}")
            print(f"answer_main updated: '{old}' → '{n['data']['answer']}'")

    # 7. Save draft
    body = {
        "graph": graph,
        "features": features,
        "environment_variables": env_vars,
        "conversation_variables": conv_vars,
        "hash": hash_,
    }
    code, resp = call(auth, "POST", f"/apps/{APP_ID}/workflows/draft", body=body)
    print(f"\nDraft update: status={code}")
    if code != 200:
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:1000])
        return 1
    print(f"  new hash={resp.get('hash', '?')[:12]}")

    # 8. Publish
    code, resp = call(auth, "POST", f"/apps/{APP_ID}/workflows/publish", body={})
    print(f"Publish: status={code}")
    if code not in (200, 201):
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:600])
        return 1
    print(f"  published id: {resp.get('id', '?')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
