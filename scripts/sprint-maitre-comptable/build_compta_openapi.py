"""Build clean OpenAPI spec for Dify Custom Tool import — 5 compta tools.

Renames operationIds to short tool names and enriches descriptions for
LLM function-calling efficacy.
"""
import json

src = json.load(open("/tmp/full_openapi.json"))
schemas_src = src["components"]["schemas"]

# Tool descriptions (LLM-facing). S59 hardened :
# - Imperative rules in caps to discourage tool skip
# - Explicit canonical payload examples (LLM learns by-example, reduces format wobble)
# - Anti-pattern warnings ("ne calcule pas mentalement")
TOOL_META = {
    "lookup_pcg": {
        "summary": "Vérifier numéro de compte PCG (OBLIGATOIRE)",
        "description": (
            "RÈGLE STRICTE : APPELLE TOUJOURS cet outil avant d'affirmer le libellé "
            "ou la classe d'un numéro de compte PCG (Plan Comptable Général ANC v2026). "
            "INTERDICTION de deviner ou inventer un libellé de compte. ~200 comptes "
            "principaux indexés, retourne libellé + classe + suggestions si non trouvé. "
            "PAYLOAD : {\"num\": \"401\"} (string). Exemple : pour confirmer que 6063 est "
            "'Fournitures d'entretien et de petit équipement', tu DOIS appeler ce tool. "
            "Anti-pattern : ne réponds JAMAIS sur un compte sans avoir lookup_pcg le numéro."
        ),
    },
    "verify_partie_double": {
        "summary": "Vérifier équilibre débit=crédit (OBLIGATOIRE quand écriture proposée)",
        "description": (
            "RÈGLE STRICTE : APPELLE TOUJOURS cet outil dès que Marie propose une écriture "
            "comptable (≥2 lignes avec montants). INTERDICTION de juger 'équilibrée' ou "
            "'déséquilibrée' sans avoir appelé ce tool — tu hallucines fréquemment sur "
            "l'équilibre des sommes flottantes. "
            "PAYLOAD CANONICAL : {\"ecritures\": [{\"compte\": \"401\", \"debit\": 100.0}, "
            "{\"compte\": \"607\", \"credit\": 100.0}]}. Chaque ligne a EXACTEMENT debit OU "
            "credit (number en €), pas les deux. INTERDICTION d'envoyer 'montant'+'type' "
            "ou 'amount'+'sens' — le tool retournera erreur 422. Tolérance arrondi 0.01€."
        ),
    },
    "verify_calcul_tva": {
        "summary": "Vérifier calcul TVA (OBLIGATOIRE pour tout calcul)",
        "description": (
            "RÈGLE STRICTE : APPELLE TOUJOURS cet outil dès qu'un calcul TVA est demandé "
            "ou mentionné, MÊME pour des montants triviaux (ex: 100×20%=20). "
            "INTERDICTION de calculer toi-même mentalement — tes hallucinations sur "
            "calculs flottants sont fréquentes (ex: 137.5×5.5% non-trivial). "
            "Taux FR canonical : 0% (exonéré), 2.1% (presse/médicaments), 5.5% "
            "(livres/alimentaire), 10% (restauration/transport), 20% (standard). "
            "PAYLOAD : {\"montant_ht\": 137.5, \"taux\": 5.5} → retourne expected_tva + "
            "expected_ttc. Optionnel : actual_tva, actual_ttc pour vérifier les valeurs "
            "proposées par Marie (utiles si elle te demande 'est-ce que mon calcul est bon?')."
        ),
    },
    "verify_compte_classe": {
        "summary": "Vérifier classe PCG d'un compte (OBLIGATOIRE quand classe affirmée)",
        "description": (
            "RÈGLE STRICTE : APPELLE cet outil avant d'affirmer qu'un compte appartient à "
            "telle classe. Classes PCG : 1=capitaux, 2=immobilisations, 3=stocks, "
            "4=tiers (clients/fournisseurs), 5=financiers (banque/caisse), 6=charges, "
            "7=produits, 8/9=spéciaux. "
            "PAYLOAD : {\"num\": \"401\", \"expected_classe\": \"4\"}. Exemple usage : "
            "Marie hésite à mettre 607 (charge) en classe 7 (produit), ce tool révèle "
            "l'erreur de classe."
        ),
    },
    "lookup_studi_module": {
        "summary": "Identifier module Studi pour une question",
        "description": (
            "Mapping concept compta → module Studi BC1.X / BC2.X / BC3.X (RNCP41653). "
            "À appeler quand tu veux pointer Marie vers la bonne section de sa formation "
            "Studi (ex: question TVA → BC1.4 'TVA mécanisme'). Mapping heuristique, "
            "confidence 'medium' ou 'low'. PAYLOAD : {\"query\": \"TVA déductible\"}. "
            "Pas obligatoire mais améliore l'expérience pédagogique."
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
