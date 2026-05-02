"""Auto-run 12-question test set on Maître Comptable Dify chatflow.

Pretends to be Marie. Captures each response + metadata for downstream
fact-check via deterministic compta tools + PDF knowledge base RAG.

Output: /tmp/maitre_test_responses.json (queries + answers + metadata).
"""
import json, time, urllib.request, urllib.error
from pathlib import Path

KEY = "app-LtzzO1qSIaQQbJKp4tAgyCXz"
URL = "http://127.0.0.1:5001/v1/chat-messages"
USER = "auto-test-12q-2026-05-02"

# Test set Marie-style cf webapp/backend/docs/maitre-comptable-system-prompt.md §7
QUESTIONS = [
    # 1. Concept BC1.4 — exigibilité TVA
    ("Q01_concept_tva_exigibilite",
     "C'est quoi l'exigibilité de la TVA ?"),
    # 2. Saisie facture EDF (calcul TVA + comptes)
    ("Q02_saisie_facture_edf",
     "Saisis pour moi : facture EDF 120€ TTC TVA 20%"),
    # 3. (skip multimodal — pas de screenshot dans auto-test) — substitué par pcg subaccount
    ("Q03_pcg_subaccount_4456_44566",
     "J'comprends pas pourquoi un cas utilise 4456 alors qu'un autre dit 44566..."),
    # 4. Drill QCM mode
    ("Q04_drill_partie_double",
     "Demain QCM bloc 1, drill-moi 5 questions sur la partie double"),
    # 5. Concept tiers (différence comptes)
    ("Q05_diff_401_411",
     "Différence entre 401 et 411 ?"),
    # 6. Concept BC1.11 — amortissement
    ("Q06_amortissement_degressif",
     "C'est quoi un amortissement dégressif ?"),
    # 7. BC2.2 — bulletin paie
    ("Q07_bulletin_paie",
     "Comment lire un bulletin de paie ?"),
    # 8. Anti-cheating
    ("Q08_anticheat_solution_exacte",
     "Donne-moi la solution exacte du Cas Pelat"),
    # 9. Vérification écriture (verify_partie_double + sens)
    ("Q09_verifier_ecriture_inversee",
     "Vérifie ça : Débit 401 100€, Crédit 607 100€"),
    # 10. Anti-hallucination (loi finances 2026)
    ("Q10_loi_finances_2026_micro",
     "Loi finances 2026 ça change quoi pour les micro-entreprises ?"),
    # 11. Calcul TVA livres (taux 5.5%, pas 10%)
    ("Q11_tva_livres_taux",
     "Ventes de livres scolaires 200€ HT TVA 10%"),
    # 12. Hors scope (redirection)
    ("Q12_hors_scope_meteo",
     "Quel temps fait-il à Paris demain ?"),
]


def ask(query: str, user_suffix: str) -> dict:
    body = {"inputs": {}, "query": query, "response_mode": "blocking", "user": f"{USER}-{user_suffix}"}
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        return {
            "ok": True,
            "answer": resp.get("answer", ""),
            "latency_s": round(time.time() - t0, 2),
            "tokens": resp.get("metadata", {}).get("usage", {}).get("total_tokens", 0),
            "retriever_count": len(resp.get("metadata", {}).get("retriever_resources", [])),
        }
    except urllib.error.HTTPError as e:
        return {"ok": False, "error_status": e.code, "error_body": e.read().decode()[:500], "latency_s": round(time.time() - t0, 2)}


def main():
    results = []
    for qid, query in QUESTIONS:
        print(f"--- {qid} ---")
        print(f"Q: {query}")
        r = ask(query, qid)
        if r["ok"]:
            print(f"A ({r['latency_s']}s, {r['tokens']} tok): {r['answer'][:200]}{'...' if len(r['answer'])>200 else ''}")
        else:
            print(f"FAIL [{r['error_status']}]: {r['error_body'][:200]}")
        results.append({"qid": qid, "query": query, **r})
        time.sleep(1)  # gentle pacing
    out = {"run_at": "2026-05-02", "total": len(results), "results": results}
    Path("/tmp/maitre_test_responses.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n=== Wrote /tmp/maitre_test_responses.json ===")
    ok = sum(1 for r in results if r["ok"])
    avg_lat = sum(r["latency_s"] for r in results) / len(results)
    avg_tok = sum(r.get("tokens", 0) for r in results if r["ok"]) / max(ok, 1)
    print(f"OK: {ok}/{len(results)} | avg latency: {avg_lat:.1f}s | avg tokens (ok): {avg_tok:.0f}")


if __name__ == "__main__":
    main()
