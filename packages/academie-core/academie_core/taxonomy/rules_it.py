"""Italian deterministic rule layer — surface + basic grammar error detection.

SKELETON — Phase 0.3. Low-recall, high-precision detectors for the most
common FR→IT transfer errors. The LLM layer (when wired) handles deep grammar.

Rules implemented:
- IT:AUX — `ho andato` calque → `sono andato` (movement verbs take essere)
- IT:ART_CONTRACT — `a il`, `di il`, `in il` → `al`, `del`, `nel` (missing contraction)
- IT:FALSE_FRIEND — classic FR→IT false friends (libreria, sensibile, fattoria)

NOT covered (LLM layer handles):
- IT:SUBJ mood triggers (penso che + subjunctive) — requires semantic context
- Clitic placement (glielo dico, ce l'ho)
- Passato prossimo vs passato remoto narrative choice
- Complex agreement chains

Shared contract with rules.py : returns `list[RuleDetection]`.
"""
from __future__ import annotations

import re

from .rules import RuleDetection


# ── IT:AUX — movement verbs take `essere`, not `avere` ──
# Covers the most frequent FR→IT transfer: FR uses `avoir` for most verbs,
# IT splits between `essere` (movement/state change) and `avere` (transitive).

_MOVEMENT_VERBS_PP = {
    # past participles commonly used with essere (masc sing form)
    "andato", "andata", "andati", "andate",
    "venuto", "venuta", "venuti", "venute",
    "arrivato", "arrivata", "arrivati", "arrivate",
    "partito", "partita", "partiti", "partite",
    "uscito", "uscita", "usciti", "uscite",
    "entrato", "entrata", "entrati", "entrate",
    "tornato", "tornata", "tornati", "tornate",
    "caduto", "caduta", "caduti", "cadute",
    "nato", "nata", "nati", "nate",
    "morto", "morta", "morti", "morte",
}

_AVERE_FORMS = {"ho", "hai", "ha", "abbiamo", "avete", "hanno"}
_ESSERE_FIX = {
    "ho": "sono",
    "hai": "sei",
    "ha": "è",
    "abbiamo": "siamo",
    "avete": "siete",
    "hanno": "sono",
}


def _detect_aux_essere_avere(text: str) -> list[RuleDetection]:
    """Detect `avere` + movement-verb past participle → should use `essere`."""
    results: list[RuleDetection] = []
    pattern = re.compile(
        r"\b(ho|hai|ha|abbiamo|avete|hanno)\s+([a-zàèéìòù]+)\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        aux, pp = m.group(1).lower(), m.group(2).lower()
        if aux in _AVERE_FORMS and pp in _MOVEMENT_VERBS_PP:
            fix_aux = _ESSERE_FIX[aux]
            results.append(RuleDetection(
                "IT:AUX",
                f"{aux} {pp}",
                f"{fix_aux} {pp}",
                f"Verbi di movimento/stato in italiano vogliono 'essere' "
                f"('{fix_aux} {pp}' invece di '{aux} {pp}').",
            ))
    return results


# ── IT:ART_CONTRACT — missing preposition-article contractions ──
# Italian contracts preposition + article obligatorily: a + il = al, di + il = del, etc.
# FR learners often write them separately because FR doesn't contract (de le → du is
# the only FR case).

_CONTRACTIONS = {
    # (prep, art): contracted form
    ("a", "il"): "al", ("a", "lo"): "allo", ("a", "la"): "alla",
    ("a", "i"): "ai", ("a", "gli"): "agli", ("a", "le"): "alle",
    ("di", "il"): "del", ("di", "lo"): "dello", ("di", "la"): "della",
    ("di", "i"): "dei", ("di", "gli"): "degli", ("di", "le"): "delle",
    ("da", "il"): "dal", ("da", "lo"): "dallo", ("da", "la"): "dalla",
    ("da", "i"): "dai", ("da", "gli"): "dagli", ("da", "le"): "dalle",
    ("in", "il"): "nel", ("in", "lo"): "nello", ("in", "la"): "nella",
    ("in", "i"): "nei", ("in", "gli"): "negli", ("in", "le"): "nelle",
    ("su", "il"): "sul", ("su", "lo"): "sullo", ("su", "la"): "sulla",
    ("su", "i"): "sui", ("su", "gli"): "sugli", ("su", "le"): "sulle",
}


def _detect_missing_contractions(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for (prep, art), fix in _CONTRACTIONS.items():
        pattern = re.compile(rf"\b{prep}\s+{art}\b", re.IGNORECASE)
        for m in pattern.finditer(text):
            original = m.group(0)
            results.append(RuleDetection(
                "IT:ART_CONTRACT",
                original,
                fix,
                f"Contrazione preposizione+articolo obbligatoria in italiano: "
                f"'{original}' → '{fix}'.",
            ))
    return results


# ── IT:FALSE_FRIEND — classic FR→IT false friends ──

_FALSE_FRIENDS_IT: dict[str, tuple[str, str]] = {
    "libreria": ("libreria = FR 'librairie' (shop) ; bibliothèque = biblioteca",
                 "libreria est un magasin, pas une bibliothèque."),
    "sensibile": ("sensibile OK (= sensible) ; 'sensé' = sensato",
                  "sensibile = émotif. 'Sensé/raisonnable' = sensato."),
    "fattoria": ("fattoria = ferme (agricultural) ; 'factory' = fabbrica",
                 "fattoria = ferme. 'Usine' = fabbrica."),
    "camera": ("camera = chambre ; 'caméra' = videocamera",
               "camera = chambre à coucher. 'Caméra' = videocamera."),
    "burro": ("burro = beurre ; 'bureau' = ufficio",
              "burro = beurre (aliment). 'Bureau' = ufficio."),
}


def _detect_false_friends_it(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for word, (fix, reason) in _FALSE_FRIENDS_IT.items():
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            results.append(RuleDetection("IT:FALSE_FRIEND", word, fix, reason))
    return results


def detect_errors_it(text: str) -> list[RuleDetection]:
    """Main entry — aggregates all IT rule-based detectors."""
    if not text or not text.strip():
        return []
    results: list[RuleDetection] = []
    results.extend(_detect_aux_essere_avere(text))
    results.extend(_detect_missing_contractions(text))
    results.extend(_detect_false_friends_it(text))
    return results
