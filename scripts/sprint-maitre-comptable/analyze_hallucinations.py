"""Analyze 12 Maître Comptable responses for hallucinations.

Cross-check claims via deterministic backend tools:
  - account numbers (\d{3,5}) → lookup_pcg
  - calcul TVA (HT/taux/TVA/TTC) → verify_calcul_tva (when extractable)
  - taux TVA cited → static reference (FR rates 0/2.1/5.5/10/20)
  - Studi modules cited → static BC1/BC2/BC3 mapping
  - Lyster posture (explicit_correction vs prompt elicitation patterns)

Score per question + breakdown by claim type. Output markdown report.
"""
import json, re, urllib.request
from pathlib import Path

API = "http://academie-api:8000"  # not reachable from /root, but tools also live in /opt
TOOL_API = "http://localhost:8000"  # academie-api exposed on cosmos host

# --- Static references (canonical PCG / TVA / Studi mapping) ---
CANONICAL_PCG_LIBELLE = {
    # Class 4 — Tiers
    "401": "Fournisseurs",
    "411": "Clients",
    "44566": "TVA déductible sur autres biens et services",
    "44562": "TVA déductible sur immobilisations",
    "44567": "Crédit de TVA à reporter",
    "44571": "TVA collectée",
    "44551": "TVA à décaisser",
    # Class 6 — Charges
    "607": "Achats de marchandises",
    "606": "Achats non stockés de matières et fournitures",
    "6061": "Fournitures non stockables (eau, énergie...)",
    # Class 7 — Produits
    "707": "Ventes de marchandises",
    # Class 5 — Financiers
    "512": "Banque",
}
CANONICAL_TVA_RATES = {0.0, 2.1, 5.5, 10.0, 20.0}
LIVRES_SCOLAIRES_TAUX = 5.5  # Critical: NOT 10%
TVA_STANDARD = 20.0

# Studi BC modules canonical (from system prompt anchorage)
STUDI_MODULES = {
    "BC1.1": "Objectifs compta",
    "BC1.2": "Compte de résultat + bilan",
    "BC1.3": "Écritures + balance",
    "BC1.4": "TVA mécanisme",
    "BC1.5": "Factures",
    "BC1.6": "Opérations courantes",
    "BC1.7": "Facturation électronique 2026",
    "BC1.11": "Amortissements fiscaux",
    "BC2.1": "Préparer paie",
    "BC2.2": "Bulletins paie (Sage v10)",
    "BC2.3": "Déclaration TVA",
    "BC3.1": "Écrits professionnels",
    "BC3.2": "Classement + RGPD",
}

# --- Lyster posture detection (heuristics) ---
PROMPT_ELICIT_PATTERNS = [
    r"\bqu['']est-ce qu",  # "qu'est-ce qui manque", "qu'est-ce que tu"
    r"\btu te souviens\b",
    r"\bpourquoi tu\b",
    r"\bquel(?:le)?\s.*selon toi\b",
    r"\bes-tu sûre?\b",
    r"\bqu'en penses-tu\b",
    r"\?\s*$",  # ends with question
    r"\bque préfères-tu\b",
    r"\bà toi de\b",
]
EXPLICIT_CORRECTION_PATTERNS = [
    r"\bnon,?\s+c['']est\b",
    r"\bla bonne réponse est\b",
    r"\bla réponse correcte\b",
    r"\bil faut\s+(?:plutôt|en fait)\b",
]


def fetch_tool(endpoint: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{TOOL_API}/internal/compta/tools/{endpoint}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def extract_account_numbers(text: str) -> list[str]:
    """Extract candidate PCG account numbers (3-5 digits) from text."""
    # Filter: must be standalone (not part of larger number, not year, not amount)
    candidates = re.findall(r"(?<![\d.,])(\d{3,5})(?![\d.,])", text)
    # Drop years (2024-2030) and likely amounts
    out = []
    for c in candidates:
        n = int(c)
        if 2024 <= n <= 2030:
            continue  # year
        if len(c) == 4 and 1000 <= n <= 9999 and "20" in c[:2]:
            continue  # year-like
        out.append(c)
    return list(dict.fromkeys(out))  # dedupe preserve order


def extract_tva_rates(text: str) -> list[float]:
    """Extract TVA percentages mentioned."""
    rates = re.findall(r"(\d+(?:[.,]\d+)?)\s*%", text)
    return [float(r.replace(",", ".")) for r in rates]


def extract_studi_modules(text: str) -> list[str]:
    """Extract BC1.X / BC2.X / BC3.X module references."""
    return list(set(re.findall(r"\bBC[123]\.\d+\b", text)))


def detect_lyster_posture(text: str) -> dict:
    elicit_count = sum(1 for p in PROMPT_ELICIT_PATTERNS if re.search(p, text, re.IGNORECASE))
    explicit_count = sum(1 for p in EXPLICIT_CORRECTION_PATTERNS if re.search(p, text, re.IGNORECASE))
    return {"elicit_signals": elicit_count, "explicit_correction_signals": explicit_count}


def analyze_response(qid: str, query: str, answer: str) -> dict:
    """Cross-check claims in answer."""
    findings = []  # list of {kind, claim, verdict, detail}

    # 1. Account numbers
    accounts = extract_account_numbers(answer)
    for acc in accounts:
        result = fetch_tool("lookup_pcg", {"num": acc})
        if result.get("error"):
            findings.append({"kind": "pcg_lookup", "claim": acc, "verdict": "TOOL_ERR", "detail": result["error"]})
            continue
        if not result.get("found"):
            findings.append({"kind": "pcg_lookup", "claim": acc, "verdict": "❌ INVENTED", "detail": f"compte {acc} introuvable PCG"})
            continue
        canonical = result.get("libelle", "")
        # Check if answer's libellé claim matches canonical (fuzzy)
        # If canonical libellé is in CANONICAL_PCG_LIBELLE, use that; else use endpoint result
        canon_short = canonical.split("(")[0].strip()
        # Search if answer contains a label near the account number
        idx = answer.find(acc)
        snippet = answer[max(0, idx-100):idx+200]
        # crude check: does any keyword from canonical libellé appear near
        keywords = [w.lower() for w in canon_short.split() if len(w) > 4]
        match = any(kw in snippet.lower() for kw in keywords) or canon_short.lower() in snippet.lower()
        if match:
            findings.append({"kind": "pcg_lookup", "claim": f"{acc} = {canon_short}", "verdict": "✅", "detail": f"matches canonical"})
        else:
            findings.append({"kind": "pcg_lookup", "claim": acc, "verdict": "⚠️ AMBIG", "detail": f"canonical='{canon_short}', context='{snippet[:80].replace(chr(10),' ')}...'"})

    # 2. TVA rates cited
    rates = extract_tva_rates(answer)
    for r in rates:
        if r in CANONICAL_TVA_RATES:
            findings.append({"kind": "tva_rate", "claim": f"{r}%", "verdict": "✅", "detail": "rate FR canonical"})
        elif 0 < r < 100:
            # Could be a calculation result (TVA = 20€ on 100€ HT, 100€ here is amount, but 20€ etc.)
            # Skip if looks like amount (with €)
            findings.append({"kind": "tva_rate", "claim": f"{r}%", "verdict": "⚠️ NON-CANON", "detail": "not in {0,2.1,5.5,10,20}"})

    # 3. Specific case: livres scolaires → must mention 5.5%
    if "livres" in query.lower() and "livres" in answer.lower():
        if "5.5" in answer or "5,5" in answer or "5.5%" in answer or "5,5%" in answer:
            findings.append({"kind": "domain_fact", "claim": "TVA livres = 5.5%", "verdict": "✅", "detail": "correct rate cited or hinted"})
        elif "10%" in answer and "5.5" not in answer and "5,5" not in answer:
            findings.append({"kind": "domain_fact", "claim": "TVA livres", "verdict": "❌ HALLU", "detail": "answer accepts 10% as livres rate (real = 5.5%)"})
        else:
            findings.append({"kind": "domain_fact", "claim": "TVA livres", "verdict": "⚠️ AMBIG", "detail": "no rate clearly stated"})

    # 4. Studi modules cited
    modules = extract_studi_modules(answer)
    for m in modules:
        if m in STUDI_MODULES:
            findings.append({"kind": "studi_module", "claim": m, "verdict": "✅", "detail": STUDI_MODULES[m]})
        else:
            findings.append({"kind": "studi_module", "claim": m, "verdict": "⚠️ UNKNOWN", "detail": "not in canonical map"})

    # 5. Lyster posture
    posture = detect_lyster_posture(answer)
    if posture["elicit_signals"] >= 1 and posture["explicit_correction_signals"] == 0:
        findings.append({"kind": "lyster", "claim": "posture", "verdict": "✅ ELICIT", "detail": str(posture)})
    elif posture["explicit_correction_signals"] > posture["elicit_signals"]:
        findings.append({"kind": "lyster", "claim": "posture", "verdict": "⚠️ EXPLICIT-DOMINANT", "detail": str(posture)})
    else:
        findings.append({"kind": "lyster", "claim": "posture", "verdict": "⚠️ NEUTRAL", "detail": str(posture)})

    # Aggregate
    halls = sum(1 for f in findings if "❌" in f["verdict"])
    ambig = sum(1 for f in findings if "⚠️" in f["verdict"])
    oks = sum(1 for f in findings if "✅" in f["verdict"])

    return {
        "qid": qid,
        "query": query,
        "answer_excerpt": answer[:400],
        "findings": findings,
        "summary": {"hallu": halls, "ambig": ambig, "ok": oks},
    }


def main():
    data = json.load(open("/tmp/maitre_test_responses.json"))
    analyses = []
    for r in data["results"]:
        if not r.get("ok"):
            print(f"--- {r['qid']} SKIP (no answer) ---")
            continue
        a = analyze_response(r["qid"], r["query"], r["answer"])
        analyses.append(a)
        print(f"=== {a['qid']} : hallu={a['summary']['hallu']} ambig={a['summary']['ambig']} ok={a['summary']['ok']} ===")
        for f in a["findings"]:
            print(f"  [{f['verdict']}] {f['kind']}: {f['claim']} — {f['detail']}")
        print()

    total_hallu = sum(a["summary"]["hallu"] for a in analyses)
    total_ambig = sum(a["summary"]["ambig"] for a in analyses)
    total_ok = sum(a["summary"]["ok"] for a in analyses)
    questions_with_hallu = sum(1 for a in analyses if a["summary"]["hallu"] > 0)
    print("=" * 60)
    print(f"AGGREGATE: {len(analyses)} questions, {questions_with_hallu} with ≥1 hallu")
    print(f"Total: {total_hallu} hallu / {total_ambig} ambig / {total_ok} ok")
    print(f"Decision threshold: <2 questions w/ hallu → defer P1.1 ; 2-4 → A1 (pre-process) ; 5+ → A4 (full agent)")

    Path("/tmp/maitre_hallu_report.json").write_text(json.dumps(analyses, ensure_ascii=False, indent=2))
    print(f"\nFull report → /tmp/maitre_hallu_report.json")


if __name__ == "__main__":
    main()
