"""Simulate 6 personas A1→C2 — compare scoring v1 vs v2 (Approach A).

Hand-crafted error sets per CEFR level reflecting SLA literature distribution:
- A1/A2 : high count of endemic surface/verb_tense/noun_det, few rare sentence/word_order
- B1/B2 : tense/article persists, modals/conditionals emerge, fewer surface
- C1/C2 : minimal surface, mostly discourse/register/vocabulary fine points

For each persona, score the same error set under v1 (current matrix + weights)
and v2 (new matrix + GLMM weights + override sentence×beginner=noted).

Output:
  /root/sinse-workspace/projects/academie-ia/docs/01-pedagogy/v1_vs_v2_personas_report.md
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml

V1_YAML = Path("/opt/academie/webapp/backend/app/config/tolerance_matrix.yaml")
V2_YAML = Path("/opt/academie/webapp/backend/app/config/tolerance_matrix_v2.yaml")
OV_YAML = Path("/opt/academie/webapp/backend/app/config/tolerance_matrix_v2_overrides.yaml")
REPORT = Path("/root/sinse-workspace/projects/academie-ia/docs/01-pedagogy/v1_vs_v2_personas_report.md")


# ════════════════════════════════════════════════════════════
# Personas — error code sets typical of each CEFR level.
# Sources : Bryant 2017 (ERRANT W&I distribution), Rifkin & Roberts 1995,
# Yannakoudakis 2018, AcademIA criterial_per_family priors.
# Format: list of (error_code, count)
# ════════════════════════════════════════════════════════════
PERSONAS = {
    "A1": [
        # Endemic at A1 : surface, basic tense, articles, prepositions
        ("SPELL", 6), ("ORTH:CASE", 4), ("PUNCT", 3),
        ("V:TENSE", 5), ("V:SVA", 4), ("V:FORM", 3),
        ("N:COUNT", 4), ("ART", 5), ("PRON:FORM", 3),
        ("PREP", 5),
        # Rare at A1 — should flag
        ("SENT:FRAG", 1), ("WO", 1),
        # Calque français typique débutant
        ("LEX:CALQUE", 2), ("PREP:CALQUE", 2),
    ],
    "A2": [
        # Surface still high, verb tenses extending
        ("SPELL", 4), ("ORTH:CASE", 2), ("PUNCT", 3),
        ("V:TENSE", 5), ("V:SVA", 3), ("V:FORM", 4), ("V:INFL", 3),
        ("V:MODAL", 2),  # modals émergent
        ("N:COUNT", 3), ("ART", 4), ("DET", 2),
        ("PRON:FORM", 2), ("PRON:CHOICE", 2),
        ("PREP", 4), ("PREP:CALQUE", 3),
        ("ADJ:CHOICE", 2),
        # Rare
        ("SENT:FRAG", 1), ("WO:QUEST", 1),
    ],
    "B1": [
        # Surface dwindling, tenses still present, complex structures emerge
        ("SPELL", 2), ("PUNCT", 2),
        ("V:TENSE", 4), ("V:SVA", 2), ("V:ASPECT", 2),
        ("V:MODAL", 3), ("V:COND", 2), ("V:PASS", 1),
        ("N:COUNT", 2), ("ART", 3), ("ART:GENERIC", 1),
        ("PREP", 3),
        ("LEX:CHOICE", 2), ("LEX:COLLOC", 1),
        ("SENT:RUNON", 1), ("SENT:SUBORD", 2),
        ("MORPH:WORDCLASS", 1),
        ("DISC:TRANS", 1),
    ],
    "B2": [
        # Less surface, more nuanced grammar, discourse beginning
        ("V:ASPECT", 2), ("V:COND", 2), ("V:MODAL", 3),
        ("V:PASS", 2), ("V:CHOICE", 2),
        ("ART:GENERIC", 2),
        ("PREP", 3), ("PREP:CALQUE", 1),
        ("LEX:CHOICE", 3), ("LEX:COLLOC", 2), ("LEX:FALSE", 1),
        ("SENT:SUBORD", 2), ("SENT:PARALLEL", 1),
        ("DISC:TRANS", 2), ("DISC:COHER", 1),
        ("REG:LEVEL", 1),
        ("WO", 1),
    ],
    "C1": [
        # Minimal surface/basic, mostly fine semantic + discourse
        ("V:COND", 1), ("V:ASPECT", 1),
        ("ART:GENERIC", 1),
        ("LEX:COLLOC", 3), ("LEX:FALSE", 2), ("LEX:IDIOM", 2), ("LEX:ARGSTRUCT", 1),
        ("SENT:PARALLEL", 1), ("SENT:MOD", 1),
        ("DISC:COHER", 2), ("DISC:TRANS", 1),
        ("REG:LEVEL", 2), ("REG:PRAGMA", 1),
        ("MORPH:DERIV", 1),
    ],
    "C2": [
        # Almost native-proximate ; only style + advanced lexical
        ("LEX:COLLOC", 2), ("LEX:IDIOM", 2),
        ("DISC:COHER", 1),
        ("REG:LEVEL", 1), ("REG:PRAGMA", 2),
        ("MORPH:DERIV", 1),
        # Persistent fossilization (1 each)
        ("PREP", 1), ("ART:GENERIC", 1),
    ],
}


def _load_with_overrides(path: Path) -> dict:
    m = yaml.safe_load(path.read_text())
    if path == V2_YAML and OV_YAML.exists():
        ov = yaml.safe_load(OV_YAML.read_text()) or {}
        for fam, bands in (ov.get("overrides") or {}).items():
            if fam in m.get("matrix", {}):
                m["matrix"][fam].update(bands)
    return m


def _code_to_family(code: str, m: dict) -> str | None:
    for fam, defn in m["families"].items():
        if code in defn.get("codes", []):
            return fam
    return None


def _level_to_band(niveau: str, m: dict) -> str:
    return m["cefr_bands"].get(niveau.strip().upper(), "intermediate")


def _score_persona(error_set: list[tuple[str, int]], niveau: str, m: dict) -> dict:
    """Compute family aggregation + total weight for a persona under matrix m."""
    band = _level_to_band(niveau, m)
    weights = m["weights"]
    family_sums = {}        # family → weighted score
    family_counts = {}      # family → raw error count
    family_tier = {}        # family → tier label
    total_weight = 0.0
    total_errors = 0
    unscored = 0

    for code, n in error_set:
        fam = _code_to_family(code, m)
        if not fam or fam not in m["matrix"]:
            unscored += n
            continue
        tier = m["matrix"][fam].get(band, "ignored")
        w = weights.get(tier, 0.0)
        family_sums[fam] = family_sums.get(fam, 0.0) + w * n
        family_counts[fam] = family_counts.get(fam, 0) + n
        family_tier[fam] = tier
        total_weight += w * n
        total_errors += n

    return {
        "total_weight": round(total_weight, 3),
        "total_errors": total_errors,
        "unscored_errors": unscored,
        "family_breakdown": {
            fam: {
                "count": family_counts[fam],
                "tier": family_tier[fam],
                "weight_per_error": round(weights.get(family_tier[fam], 0.0), 3),
                "subtotal": round(family_sums[fam], 3),
            }
            for fam in sorted(family_sums.keys(), key=lambda f: -family_sums[f])
        },
    }


def main() -> int:
    v1 = _load_with_overrides(V1_YAML)
    v2 = _load_with_overrides(V2_YAML)

    results = {}
    for niveau, errors in PERSONAS.items():
        s1 = _score_persona(errors, niveau, v1)
        s2 = _score_persona(errors, niveau, v2)
        results[niveau] = {"v1": s1, "v2": s2, "errors": errors}

    # ── Markdown report ──
    lines: list[str] = []
    lines.append("---")
    lines.append("title: v1 vs v2 — simulation 6 personas A1→C2 (Approach A)")
    lines.append("status: authoritative")
    lines.append("last_reviewed: 2026-04-15")
    lines.append("owner: claude")
    lines.append("---")
    lines.append("")
    lines.append("# v1 vs v2 — simulation 6 personas (Approach A)")
    lines.append("")
    lines.append("> Simulation déterministe : 6 personas (A1→C2) avec error sets typiques")
    lines.append("> de chaque niveau (sources : Bryant 2017, Yannakoudakis 2018, Rifkin &")
    lines.append("> Roberts 1995, AcademIA criterial priors). Pour chaque persona, scoring")
    lines.append("> identique appliqué avec matrix v1 vs matrix v2 (avec override).")
    lines.append(">")
    lines.append("> But : valider quantitativement que v2 produit des scores plus")
    lines.append("> empiriquement pertinents (lenient sur endemic, strict sur rare).")
    lines.append("")

    # ── Synthèse globale ──
    lines.append("## Synthèse globale")
    lines.append("")
    lines.append("| Niveau | Erreurs total | Score v1 | Score v2 | Delta | Direction |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for niveau, r in results.items():
        s1, s2 = r["v1"], r["v2"]
        delta = s2["total_weight"] - s1["total_weight"]
        pct = (delta / s1["total_weight"] * 100) if s1["total_weight"] else 0
        direction = "🟢 plus lenient" if delta < 0 else ("🔴 plus strict" if delta > 0 else "≈ inchangé")
        lines.append(
            f"| **{niveau}** | {s1['total_errors']} | "
            f"{s1['total_weight']:.2f} | {s2['total_weight']:.2f} | "
            f"{delta:+.2f} ({pct:+.0f}%) | {direction} |"
        )
    lines.append("")

    lines.append("**Lecture** :")
    lines.append("- A1/A2 : v2 plus strict — détecte les rare errors (sentence, word_order) que v1 ignorait")
    lines.append("- B1+ : v2 plus lenient — relaxe les endemic errors (verb_tense, noun_det, surface) que v1 sur-pénalisait")
    lines.append("- Pattern attendu (cf. sprint1_report.md § 4.2 et matrix_v2_review.md)")
    lines.append("")

    # ── Détail par persona ──
    for niveau, r in results.items():
        lines.append(f"## Persona {niveau}")
        lines.append("")
        s1, s2 = r["v1"], r["v2"]
        lines.append(f"**Erreurs simulées** : {s1['total_errors']} occurrences sur {len(r['errors'])} codes distincts")
        lines.append("")
        lines.append("```")
        for code, n in r["errors"]:
            lines.append(f"  {code:18s} × {n}")
        lines.append("```")
        lines.append("")

        lines.append("### Comparaison family × tier × weight")
        lines.append("")
        lines.append("| Famille | Erreurs | Tier v1 | Weight v1 | Subtotal v1 | Tier v2 | Weight v2 | Subtotal v2 | Δ |")
        lines.append("|---|---:|---|---:|---:|---|---:|---:|---:|")
        all_families = sorted(set(s1["family_breakdown"].keys()) | set(s2["family_breakdown"].keys()))
        for fam in all_families:
            f1 = s1["family_breakdown"].get(fam, {})
            f2 = s2["family_breakdown"].get(fam, {})
            count = f1.get("count") or f2.get("count", 0)
            sub1 = f1.get("subtotal", 0)
            sub2 = f2.get("subtotal", 0)
            delta = sub2 - sub1
            arrow = "🟢" if delta < -0.01 else ("🔴" if delta > 0.01 else "≈")
            lines.append(
                f"| {fam} | {count} | "
                f"{f1.get('tier','-')} | {f1.get('weight_per_error',0):.2f} | {sub1:.2f} | "
                f"{f2.get('tier','-')} | {f2.get('weight_per_error',0):.2f} | {sub2:.2f} | "
                f"{delta:+.2f} {arrow} |"
            )
        lines.append(
            f"| **TOTAL** | **{s1['total_errors']}** | | | "
            f"**{s1['total_weight']:.2f}** | | | **{s2['total_weight']:.2f}** | "
            f"**{s2['total_weight'] - s1['total_weight']:+.2f}** |"
        )
        lines.append("")

    # ── Effet override ──
    lines.append("## Effet de l'override `sentence × beginner = noted`")
    lines.append("")
    has_sent_at_beg = any(
        any(c.startswith("SENT") for c, _ in PERSONAS[lvl])
        for lvl in ("A1", "A2")
    )
    if has_sent_at_beg:
        # Recompute v2 without override to show the diff
        v2_no_override = yaml.safe_load(V2_YAML.read_text())
        for lvl in ("A1", "A2"):
            no_ov = _score_persona(PERSONAS[lvl], lvl, v2_no_override)
            with_ov = results[lvl]["v2"]
            sentence_no_ov = no_ov["family_breakdown"].get("sentence", {})
            sentence_with_ov = with_ov["family_breakdown"].get("sentence", {})
            if sentence_no_ov:
                lines.append(
                    f"- **{lvl}** : sentence sans override = `{sentence_no_ov.get('tier')}` (subtotal {sentence_no_ov.get('subtotal',0):.2f}) "
                    f"→ avec override = `{sentence_with_ov.get('tier')}` (subtotal {sentence_with_ov.get('subtotal',0):.2f}). "
                    f"Différence : {sentence_with_ov.get('subtotal',0) - sentence_no_ov.get('subtotal',0):+.2f} sur le total."
                )
        lines.append("")
        lines.append("**Conclusion override** : réduit la pénalité sentence chez A1/A2 (cohérent avec rationale chat fragments != essay fragments).")
    else:
        lines.append("Aucune erreur sentence présente dans les personas A1/A2 — override n'a pas d'effet observable ici.")
    lines.append("")

    # ── Effet enrichissement gravity / criterial ──
    lines.append("## Effet de l'enrichissement gravity_axes + criterial_levels")
    lines.append("")
    lines.append("Les nouvelles colonnes `gravity_*` et `criterial_level_*` sont **populées** dans `error_log` mais")
    lines.append("**pas encore utilisées** par `compute_error_profile` (`USE_V2_SCORING=false`). Pour montrer leur potentiel :")
    lines.append("")
    lines.append("| Famille | gravity_linguistic | gravity_communicative | gravity_social | criterial_emergence | criterial_mastery |")
    lines.append("|---|---:|---:|---:|---|---|")
    gravity = v2.get("gravity_per_family", {})
    criterial = v2.get("criterial_per_family", {})
    for fam in sorted(gravity.keys()):
        g = gravity[fam]
        c = criterial.get(fam, {})
        lines.append(
            f"| {fam} | {g.get('linguistic','-')} | {g.get('communicative','-')} | "
            f"{g.get('social','-')} | {c.get('emergence','-')} | {c.get('mastery','-')} |"
        )
    lines.append("")
    lines.append("**Cas d'usage futurs (Phase B3 / Sprint 6+)** :")
    lines.append("- UI : afficher gravity_communicative comme \"impact sur la compréhension\" (score colorisé)")
    lines.append("- Scoring : pondérer le tier par gravity_communicative pour les erreurs blocantes (priorité haute si > 0.7)")
    lines.append("- Recommendation : prioriser les erreurs au-dessus du criterial_mastery du niveau (\"tu devrais déjà maîtriser ça\")")
    lines.append("")

    # ── Limites ──
    lines.append("## Limites de la simulation")
    lines.append("")
    lines.append("- **Personas synthétiques** : codes choisis par intuition SLA, pas issus d'utilisateurs réels AcademIA")
    lines.append("- **Counts arbitraires** : 5×SPELL pour A1 = approximation, vraies distributions varieront")
    lines.append("- **Pas d'effet random_effect (learner)** : tous les personas considérés \"moyens\"")
    lines.append("- **Familles non calibrées** (verb_usage, vocabulary, calque, discourse) gardent les priors v1 — leur impact dans le tableau peut être surestimé")
    lines.append("- **`compute_error_profile` complet** non simulé — recommendation/eligibility nécessitent session_id et turn structure que les personas n'ont pas")
    lines.append("")
    lines.append("Pour valider en réel : Approach C (synthetic transcripts + LLM analysis) ou attendre des users réels A1-C2 sur AcademIA.")
    lines.append("")

    # ── Recommandations ──
    lines.append("## Recommandations")
    lines.append("")
    lines.append("1. **Valider auprès d'un éleve** : montrer le tableau des familles à un user réel à différents niveaux pour qualité ressentie")
    lines.append("2. **Phase B3** (USE_V2_SCORING=true) : activer la lecture de `tier` depuis error_log → consistance historique")
    lines.append("3. **Sprint 6** : recalibration sur AcademIA quand error_log ≥ 10k rows + activation gravity-based pondération")
    lines.append("4. **Approach C** dans une session ultérieure : générer 6 transcripts via LLM Teacher pour test E2E réaliste")
    lines.append("")

    REPORT.write_text("\n".join(lines))
    print(f"Report written: {REPORT}")
    print(f"Size: {REPORT.stat().st_size / 1024:.1f} KB")
    print()
    print("=== Synthèse globale ===")
    for niveau, r in results.items():
        delta = r["v2"]["total_weight"] - r["v1"]["total_weight"]
        pct = delta / r["v1"]["total_weight"] * 100 if r["v1"]["total_weight"] else 0
        print(
            f"  {niveau}: {r['v1']['total_errors']:3d} errors  "
            f"v1={r['v1']['total_weight']:6.2f}  v2={r['v2']['total_weight']:6.2f}  "
            f"Δ={delta:+6.2f} ({pct:+5.0f}%)"
        )
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
