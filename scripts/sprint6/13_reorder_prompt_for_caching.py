#!/usr/bin/env python3
"""Phase C — reorder llm_session prompt for OpenAI auto-caching.

MINIMAL-INTERVENTION VERSION : move ONLY the top volatile chunk (learner_profile
block + plan_prefix placeholder + MODE QUIZ gate) to the BOTTOM of the prompt.
Everything else stays in place.

Rationale : the top chunk is what breaks caching from byte 1. Relocating it
lifts the cacheable prefix from 5 tokens (0.1%) to ~1000 tokens (~20%) —
200× improvement, with zero semantic risk. A deeper reorder (targeting 75%
cacheable) is deferred to a follow-up iteration after validating this step.

Anchor : persona line identified by `{{#code_turn_check.lang_target_prof#}}`
(language-agnostic placeholder present in both Teacher EN + Maestro ES).

Patches Teacher EN + Maestro ES, published + draft versions. Idempotent via
`CACHE_REORDER_v1` marker. Backups to /tmp/prompt-reorder-backup-*.json.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

MARKER = "<!-- CACHE_REORDER_v1 : everything above === CONTEXTE DE CE TOUR === is STABLE (cacheable prefix) ; below is per-turn VOLATILE. Do NOT inject per-turn placeholders above that marker or OpenAI prompt caching breaks. -->"

PERSONA_ANCHOR = "{{#code_turn_check.lang_target_prof#}}"

TARGETS = [
    ("006cba2d-08b0-449c-91ed-0dda79d414ce", "Teacher EN published"),
    ("ed0d1c91-8c9a-48ad-9c3a-063981f8da87", "Teacher EN draft"),
    ("d3df0ef0-a28f-4850-9396-d4d1cf6c0e21", "Maestro ES published"),
    ("69fc4cf7-8835-44ce-925a-09099af67bc1", "Maestro ES draft"),
]


def psql_q(sql: str) -> str:
    return subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
         "-d", "academie_db", "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.rstrip("\n")


def psql_exec(sql: str) -> None:
    subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
         "-d", "academie_db", "-v", "ON_ERROR_STOP=1"],
        input=sql, text=True, check=True,
    )


def reorder(template: str) -> tuple[str, bool]:
    """Minimal transform : relocate top volatile chunk (everything before the
    persona line) to the bottom. Returns (new_template, changed).

    Idempotent — returns unchanged if MARKER already present.
    """
    if "CACHE_REORDER_v1" in template:
        return template, False

    # Find the persona line by its anchor placeholder
    persona_idx = template.find(PERSONA_ANCHOR)
    if persona_idx == -1:
        raise RuntimeError("persona anchor not found in template")

    # Walk back to start of that line
    line_start = template.rfind("\n", 0, persona_idx)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1  # skip the \n

    top_chunk = template[:line_start].rstrip()
    main_body = template[line_start:].rstrip()

    # Detect whether top_chunk is actually the "volatile header" we want to move.
    # Sanity check : must contain learner_profile_summary placeholder.
    if "{{#code_turn_check.learner_profile_summary#}}" not in top_chunk:
        raise RuntimeError(
            "top chunk does not contain learner_profile_summary — abort"
        )

    # Rewrite the MODE QUIZ gate so the directives point to the NEW location
    # of the doctrine (above, not below, since we've moved the top chunk to
    # the end). Touches 2 sub-strings per language :
    #   - "Ignore TOUT ce qui suit" → point to context section
    #   - "=== SINON : SESSION NORMALE ===" → point upward to doctrine
    top_chunk_patched = top_chunk
    for old, new in [
        # French (Teacher EN prompt uses French meta-directives)
        ("Ignore TOUT ce qui suit",
         "Ignore le reste du CONTEXTE DE CE TOUR"),
        ("=== SINON : SESSION NORMALE (Sprint 3 Lyster v2) ===",
         "=== SINON : appliquer la doctrine Sprint 3 Lyster v2 énoncée ci-dessus ==="),
        # Spanish (Maestro ES) — two variants observed
        ("Ignora TODO lo que sigue",
         "Ignora el resto del CONTEXTO DE ESTE TURNO"),
        ("Ignora TODO lo que viene después",
         "Ignora el resto del CONTEXTO DE ESTE TURNO"),
        ("=== SI NO : SESIÓN NORMAL (Sprint 3 Lyster v2) ===",
         "=== SI NO : aplicar la doctrina Sprint 3 Lyster v2 anunciada arriba ==="),
    ]:
        top_chunk_patched = top_chunk_patched.replace(old, new)

    new_template = (
        MARKER + "\n\n"
        + main_body + "\n\n"
        + "=== CONTEXTE DE CE TOUR ===\n"
        + top_chunk_patched + "\n"
        + "=== FIN CONTEXTE DE CE TOUR ==="
    )
    return new_template, True


def patch_workflow(wf_id: str, label: str, dry_run: bool) -> dict:
    stats: dict = {"label": label, "workflow_id": wf_id, "patched": False}

    graph_str = psql_q(f"SELECT graph FROM workflows WHERE id='{wf_id}';")
    if not graph_str:
        stats["error"] = "workflow not found"
        return stats

    graph = json.loads(graph_str)
    nodes = graph.get("nodes", [])

    session_node = None
    for n in nodes:
        d = n.get("data", {})
        if d.get("type") == "llm" and re.search(r"session", d.get("title", ""), re.I):
            session_node = n
            break
    if not session_node:
        stats["error"] = "llm_session node not found"
        return stats

    tpl_list = session_node["data"].get("prompt_template", [])
    if not tpl_list or not tpl_list[0].get("text"):
        stats["error"] = "empty prompt_template"
        return stats

    old_text = tpl_list[0]["text"]
    try:
        new_text, changed = reorder(old_text)
    except RuntimeError as e:
        stats["error"] = str(e)
        return stats

    stats["old_chars"] = len(old_text)
    stats["new_chars"] = len(new_text)
    stats["changed"] = changed

    if not changed:
        stats["note"] = "already patched (marker present) — skipped"
        return stats

    if dry_run:
        stats["note"] = "dry-run ; no write"
        return stats

    ts = int(time.time())
    backup = Path(f"/tmp/prompt-reorder-backup-{ts}-{wf_id[:8]}.json")
    backup.write_text(json.dumps(
        {"workflow_id": wf_id, "label": label, "old_text": old_text},
        ensure_ascii=False, indent=2,
    ))
    stats["backup"] = str(backup)

    tpl_list[0]["text"] = new_text
    session_node["data"]["prompt_template"] = tpl_list
    graph["nodes"] = nodes

    new_graph_str = json.dumps(graph, ensure_ascii=False).replace("'", "''")
    psql_exec(
        f"UPDATE workflows SET graph='{new_graph_str}'::jsonb, "
        f"updated_at=NOW() WHERE id='{wf_id}';"
    )
    stats["patched"] = True
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="filter TARGETS by substring")
    args = ap.parse_args()

    results = []
    for wf_id, label in TARGETS:
        if args.only and args.only.lower() not in label.lower():
            continue
        print(f"\n── {label} ({wf_id}) ──")
        st = patch_workflow(wf_id, label, dry_run=args.dry_run)
        results.append(st)
        for k, v in st.items():
            if k == "backup":
                print(f"  {k}: {v}")
            else:
                print(f"  {k}: {v}")

    patched = sum(1 for s in results if s.get("patched"))
    skipped = sum(1 for s in results if (s.get("note") or "").startswith("already"))
    errors = sum(1 for s in results if s.get("error"))
    print(f"\n━━━ Summary ━━━")
    print(f"  patched={patched}  skipped={skipped}  errors={errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
