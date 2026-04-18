"""Spanish deterministic rule layer — surface + basic grammar error detection.

SKELETON — Sprint 5 Phase 4. Requires native-speaker linguistic review
before prod activation. Covers ONLY the most obvious FR→ES transfer errors
that can be detected with regex heuristics. The LLM layer (llm.py ES) handles
deep grammar/lexical analysis.

Rules implemented (5-10 basic):
- Missing inverted ¿ or ¡ at question/exclamation start
- Missing ñ (manana → mañana, espanol → español)
- Article before profession after "ser" (soy un médico → soy médico)
- Basic ser/estar confusion (soy cansado → estoy cansado) — heuristic only
- por/para confusion on obvious calques (para mí = FR "pour moi" OK ; gracias para → por)
- Classic false friends (embarazada, éxito, largo)
- Preposition calques (soñar de → soñar con ; pensar en correct)

NOT covered (LLM layer handles):
- Subjuntivo mood (requires semantic analysis)
- Preterito vs imperfecto (requires narrative context)
- Complex agreement chains
- Anything requiring discourse context

Shared contract with rules.py : returns `list[RuleDetection]`.
"""
from __future__ import annotations

import re

from .rules import RuleDetection

# ── Common proper nouns requiring capitalization in Spanish ──
PROPER_NOUNS_ES = {
    "español", "francés", "inglés", "japonés", "alemán", "italiano",
    "españa", "francia", "argentina", "mexico", "méxico", "madrid", "barcelona",
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
    # Days of week ARE lowercase in ES actually — removed
}
# Correction: in Spanish, days/months/languages/nationalities are LOWERCASE.
# Only city/country names are capitalized.
PROPER_NOUNS_ES = {
    "españa", "francia", "argentina", "méxico", "mexico",
    "madrid", "barcelona", "sevilla", "valencia",
    "europa", "américa", "asia", "áfrica",
}

# Classic false friends FR→ES
FALSE_FRIENDS_ES: dict[str, tuple[str, str]] = {
    # word_as_written : (correct_word, reason)
    "embarazada": ("avergonzada (si gênée)", "embarazada = enceinte ; pour 'gênée' : avergonzada"),
    "éxito": ("éxito OK, mais pas exit : salida", "éxito = succès, pas 'exit' (= salida)"),
    "largo": ("largo OK si 'long' ; pour 'large' : ancho", "largo = long ; 'large' = ancho"),
    "constipado": ("resfriado (si rhume)", "constipado = rhume/enrhumé ; 'constipé' = estreñido"),
}

# Preposition calques after specific verbs
PREP_CALQUES_ES: dict[str, tuple[str, str]] = {
    # "wrong_phrase": ("correction", "reason")
    "soñar de": ("soñar con", "soñar requires 'con' en español, pas 'de'"),
    "depender a": ("depender de", "depender requires 'de'"),
    "casarse a": ("casarse con", "casarse avec 'con' (pas 'à')"),
    "pensar de": ("pensar en (thought) / pensar de (opinion)", "pensar de = 'penser de' = avoir une opinion ; pensar en = réfléchir à"),
}

# Professions that commonly get wrong article after "ser"
PROFESSIONS_ES = {
    "médico", "doctora", "profesor", "profesora", "ingeniero", "ingeniera",
    "abogado", "abogada", "estudiante", "periodista", "arquitecto", "arquitecta",
    "cocinero", "cocinera", "enfermero", "enfermera",
}


def _detect_missing_interrog(text: str) -> list[RuleDetection]:
    """Spanish requires ¿...? and ¡...! — detect missing opening marks."""
    results: list[RuleDetection] = []
    # Sentence ending with ? without opening ¿
    for m in re.finditer(r'(?:^|[.!?]\s+)([A-Za-záéíóúÁÉÍÓÚñÑ][^.!?¿¡]{3,80}\?)', text):
        snippet = m.group(1)
        if not snippet.lstrip().startswith("¿"):
            results.append(RuleDetection(
                "PUNCT:INTERROG",
                snippet[:40],
                f"¿{snippet}",
                "Spanish questions open with ¿ (signe inversé).",
            ))
    for m in re.finditer(r'(?:^|[.!?]\s+)([A-Za-záéíóúÁÉÍÓÚñÑ][^.!?¿¡]{2,80}!)', text):
        snippet = m.group(1)
        if not snippet.lstrip().startswith("¡"):
            results.append(RuleDetection(
                "PUNCT:INTERROG",
                snippet[:40],
                f"¡{snippet}",
                "Spanish exclamations open with ¡.",
            ))
    return results


def _detect_missing_enye(text: str) -> list[RuleDetection]:
    """Detect words that should have ñ (common: espanol, manana, nino, pequeno, etc.)."""
    patterns = {
        r"\b(espanol)\b": ("español", "spelling: 'español' avec ñ"),
        r"\b(espanola)\b": ("española", "spelling: 'española' avec ñ"),
        r"\b(manana)\b": ("mañana", "spelling: 'mañana' avec ñ"),
        r"\b(nino)\b": ("niño", "spelling: 'niño' avec ñ"),
        r"\b(nina)\b": ("niña", "spelling: 'niña' avec ñ"),
        r"\b(pequeno)\b": ("pequeño", "spelling: 'pequeño' avec ñ"),
        r"\b(pequena)\b": ("pequeña", "spelling: 'pequeña' avec ñ"),
        r"\b(senor)\b": ("señor", "spelling: 'señor' avec ñ"),
        r"\b(senora)\b": ("señora", "spelling: 'señora' avec ñ"),
        r"\b(ano)\b": ("año", "spelling: 'año' (year) avec ñ — 'ano' signifie 'anus'!"),
    }
    results: list[RuleDetection] = []
    for pat, (fix, reason) in patterns.items():
        for m in re.finditer(pat, text, re.IGNORECASE):
            original = m.group(1)
            results.append(RuleDetection("ORTH:NY", original, fix, reason))
    return results


def _detect_article_before_profession(text: str) -> list[RuleDetection]:
    """Detect 'soy/eres/es un/una + profession' — should have no article after ser."""
    results: list[RuleDetection] = []
    # Match: ser_verb + un/una + profession_word
    pattern = re.compile(
        r"\b(soy|eres|es|somos|sois|son)\s+(un|una)\s+([a-záéíóúñ]+)\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        ser, article, noun = m.group(1), m.group(2), m.group(3).lower()
        if noun in PROFESSIONS_ES:
            results.append(RuleDetection(
                "ART:PROF",
                f"{ser} {article} {noun}",
                f"{ser} {noun}",
                f"Pas d'article après 'ser' + profession : '{ser} {noun}' (et non '{ser} un/una {noun}').",
            ))
    return results


def _detect_false_friends(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for word, (fix, reason) in FALSE_FRIENDS_ES.items():
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            results.append(RuleDetection("LEX:FALSE", word, fix, reason))
    return results


def _detect_prep_calques(text: str) -> list[RuleDetection]:
    results: list[RuleDetection] = []
    for phrase, (fix, reason) in PREP_CALQUES_ES.items():
        if re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE):
            results.append(RuleDetection("PREP:CALQUE", phrase, fix, reason))
    return results


def _detect_ser_cansado(text: str) -> list[RuleDetection]:
    """Heuristic: 'soy/eres/es/somos/son + cansado/triste/enfermo/ocupado' → should be 'estar'."""
    results: list[RuleDetection] = []
    TRANSITORY_ADJECTIVES = {
        "cansado", "cansada", "triste", "enfermo", "enferma",
        "ocupado", "ocupada", "contento", "contenta", "aburrido", "aburrida",
    }
    pattern = re.compile(
        r"\b(soy|eres|es|somos|sois|son)\s+(muy\s+)?([a-záéíóúñ]+)\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        ser, muy, adj = m.group(1), m.group(2) or "", m.group(3).lower()
        if adj in TRANSITORY_ADJECTIVES:
            ser_to_estar = {
                "soy": "estoy", "eres": "estás", "es": "está",
                "somos": "estamos", "sois": "estáis", "son": "están",
            }
            results.append(RuleDetection(
                "V:SER_ESTAR",
                f"{ser} {muy}{adj}",
                f"{ser_to_estar[ser.lower()]} {muy}{adj}",
                f"Estado transitorio avec 'estar' : '{ser_to_estar[ser.lower()]} {adj}' (et non 'ser').",
            ))
    return results


def _detect_gracias_para(text: str) -> list[RuleDetection]:
    """gracias para → gracias por (cause/motif)."""
    results: list[RuleDetection] = []
    for m in re.finditer(r"\bgracias\s+para\b", text, re.IGNORECASE):
        results.append(RuleDetection(
            "PREP:POR_PARA",
            "gracias para",
            "gracias por",
            "Motif/cause avec 'por' : 'gracias por' (et non 'gracias para').",
        ))
    return results


def detect_errors_es(text: str) -> list[RuleDetection]:
    """Main entry — aggregates all ES rule-based detectors.

    Returns a list of RuleDetection. Intentionally low-recall, high-precision.
    LLM layer (analyze_transcript with lang='es') fills the gap.
    """
    if not text or not text.strip():
        return []
    results: list[RuleDetection] = []
    results.extend(_detect_missing_interrog(text))
    results.extend(_detect_missing_enye(text))
    results.extend(_detect_article_before_profession(text))
    results.extend(_detect_false_friends(text))
    results.extend(_detect_prep_calques(text))
    results.extend(_detect_ser_cansado(text))
    results.extend(_detect_gracias_para(text))
    return results
