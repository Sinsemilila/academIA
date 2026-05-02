"""S59 — Push hardened OpenAPI spec to Dify Custom Tool provider 'compta_tools'.

Updates the existing provider IN PLACE via /workspaces/current/tool-provider/api/update
(preserves UUID 855f3981-d9e8-4dd3-b0ce-f69a8c20645a, agent_compta tool refs intact).

Hardened changes (vs S58/S59 initial registration) :
- TOOL_META descriptions now include imperative rules ("OBLIGATOIRE",
  "INTERDICTION de calculer toi-même") + canonical payload examples.
- EcritureLineModel schema reflects extra='forbid' + non-zero validator
  (additionalProperties: false → Dify advertises this in tool schema → LLM
  knows to send only canonical {compte, debit | credit}).

Validation order :
1. /api/schema (parse-only) on new spec — must status 200
2. /api/update push — original_provider preserves provider id + tools
3. /api/tools list — must show 5 tools w/ updated descriptions
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/tmp")
from dify_helper import call, login

PROVIDER_NAME = "compta_tools"
SPEC_PATH = Path("/opt/academie/scripts/sprint-maitre-comptable/compta_openapi.json")


def main() -> int:
    schema_str = SPEC_PATH.read_text()
    print(f"Spec: {len(schema_str)} bytes from {SPEC_PATH}")

    auth = login()

    # 1. Validate schema parse-only
    code, resp = call(
        auth,
        "POST",
        "/workspaces/current/tool-provider/api/schema",
        body={"schema": schema_str},
    )
    print(f"schema validate: {code}")
    if code != 200:
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:600])
        return 1

    parsed = resp.get("parameters_schema", [])
    print(f"  parsed {len(parsed)} operations")
    for op in parsed:
        op_id = op.get("operation_id")
        summary_short = (op.get("summary") or "")[:60]
        print(f"    - {op_id}: {summary_short}")

    # 2. Update provider in place
    payload = {
        "original_provider": PROVIDER_NAME,
        "provider": PROVIDER_NAME,
        "credentials": {"auth_type": "none"},
        "schema_type": "openapi",
        "schema": schema_str,
        "icon": {"content": "🧮", "background": "#FFEAD5"},
        "privacy_policy": "",
        "labels": ["compta", "marie"],
        "custom_disclaimer": "",
    }
    code, resp = call(auth, "POST", "/workspaces/current/tool-provider/api/update", body=payload)
    print(f"\n/api/update: {code}")
    if code != 200:
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:600])
        return 1
    print(f"  result: {resp.get('result')}")

    # 3. Confirm tools list
    code, resp = call(
        auth,
        "GET",
        f"/workspaces/current/tool-provider/api/tools?provider={PROVIDER_NAME}",
    )
    print(f"\n/api/tools list: {code}")
    if code == 200 and isinstance(resp, list):
        for t in resp:
            print(f"  - {t.get('name')}")
        if len(resp) != 5:
            print(f"  ⚠️ expected 5 tools, got {len(resp)}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
