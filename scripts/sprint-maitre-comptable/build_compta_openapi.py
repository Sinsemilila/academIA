"""Build clean OpenAPI spec for Dify Custom Tool import — 5 compta tools.

Renames operationIds to short tool names and enriches descriptions for
LLM function-calling efficacy.
"""
import json

src = json.load(open("/tmp/full_openapi.json"))
schemas_src = src["components"]["schemas"]

# Tool descriptions (LLM-facing; what triggers the call)
TOOL_META = {
    "lookup_pcg": {
        "summary": "Vérifier numéro de compte PCG",
        "description": (
            "Vérifie qu'un numéro de compte PCG existe (Plan Comptable Général ANC v2026) "
            "et retourne son libellé + classe + suggestions si non trouvé. "
            "À APPELER OBLIGATOIREMENT avant d'affirmer 'le compte X est Y' à Marie. "
            "Évite les hallucinations sur les numéros de compte (~200 comptes principaux indexés)."
        ),
    },
    "verify_partie_double": {
        "summary": "Vérifier équilibre débit=crédit d'une écriture",
        "description": (
            "Vérifie sum(débits) == sum(crédits) sur une écriture comptable proposée par Marie. "
            "Tolérance flottant 0.01€. À APPELER SYSTÉMATIQUEMENT quand Marie propose une écriture "
            "(plusieurs lignes débit/crédit). Retourne valid: bool + somme_debits + somme_credits."
        ),
    },
    "verify_calcul_tva": {
        "summary": "Vérifier calcul TVA (HT, taux, TVA, TTC)",
        "description": (
            "Vérifie un calcul TVA selon les taux FR (0% / 2.1% / 5.5% livres-alimentaire / "
            "10% restauration-transport / 20% standard). À APPELER OBLIGATOIREMENT avant de "
            "valider un montant TVA ou TTC. Retourne expected_tva, expected_ttc, valid: bool."
        ),
    },
    "verify_compte_classe": {
        "summary": "Vérifier classe PCG d'un compte",
        "description": (
            "Vérifie qu'un compte PCG appartient bien à une classe attendue (1=capitaux, "
            "2=immo, 3=stocks, 4=tiers, 5=financiers, 6=charges, 7=produits). Utile pour "
            "détecter erreurs de classe (ex: Marie utilise 6xx alors qu'elle veut 7xx)."
        ),
    },
    "lookup_studi_module": {
        "summary": "Identifier module Studi probable d'une question",
        "description": (
            "Heuristique mapping concept compta → module Studi BC1.X / BC2.X / BC3.X "
            "(RNCP41653). Utile pour rappeler à Marie le module Studi correspondant à sa "
            "question (ex: TVA → BC1.4, paie → BC2.2)."
        ),
    },
}

# Map endpoint path → short tool name
PATH_TO_TOOL = {f"/internal/compta/tools/{name}": name for name in TOOL_META}

paths_out = {}
for path, tool_name in PATH_TO_TOOL.items():
    src_op = src["paths"][path]["post"]
    new_op = {
        "operationId": tool_name,
        "summary": TOOL_META[tool_name]["summary"],
        "description": TOOL_META[tool_name]["description"],
        "requestBody": src_op["requestBody"],
        "responses": {
            "200": {
                "description": "Success",
                "content": {"application/json": {"schema": {"type": "object"}}},
            }
        },
    }
    paths_out[path] = {"post": new_op}

# Resolve refs reachable from request bodies
import re
needed = set()
seen = set()
to_walk = list(json.dumps(paths_out).encode())
walk_str = json.dumps(paths_out)
for m in re.findall(r"#/components/schemas/(\w+)", walk_str):
    needed.add(m)
while needed - seen:
    for name in list(needed - seen):
        seen.add(name)
        s = schemas_src.get(name)
        if s is None:
            continue
        for m in re.findall(r"#/components/schemas/(\w+)", json.dumps(s)):
            needed.add(m)

components_out = {"schemas": {n: schemas_src[n] for n in sorted(seen) if n in schemas_src}}

spec_out = {
    "openapi": "3.1.0",
    "info": {
        "title": "AcademIA Compta Tools",
        "version": "1.0.0",
        "description": "Outils déterministes pour Maître Comptable (no auth, internal network).",
    },
    "servers": [{"url": "http://academie-api:8000"}],
    "paths": paths_out,
    "components": components_out,
}

out = json.dumps(spec_out, ensure_ascii=False, indent=2)
open("/tmp/compta_openapi.json", "w").write(out)
print(f"Wrote /tmp/compta_openapi.json — {len(out)} bytes")
print(f"Operations: {sorted(PATH_TO_TOOL.values())}")
print(f"Schemas inlined: {sorted(seen)}")
