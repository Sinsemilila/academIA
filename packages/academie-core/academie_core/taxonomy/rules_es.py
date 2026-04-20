"""Spanish deterministic rule layer — surface + basic grammar error detection.

Wave 1 enrichment (2026-04-20) — extended from 7 to 15 detectors based on
Agent 1 research (PCIC + Bruhn de Garavito + Collentine + Montrul + Geeslin
+ Paquet 2018 + CEDEL2 FR L1 subcorpus). Intentionally low-recall, high-precision
pre-filter; LLM layer (llm.py ES) handles deep grammar/lexical analysis.

Rules implemented:
Surface / ortho :
- PUNCT:INTERROG        — missing ¿ or ¡
- ORTH:NY               — missing ñ (manana → mañana)

Lexique / false friends :
- LEX:FALSE             — embarazada, éxito, largo, constipado
- PREP:CALQUE           — soñar de, depender a, casarse a, pensar de (ambig)

Ser / estar :
- V:SER_ESTAR state     — soy cansado/triste/enfermo → estoy
- V:SER_ESTAR locative  — soy/es + en/aquí/allí → estar

Articles / apocope :
- ART:PROF              — soy un médico → soy médico

Préposition / mouvement :
- PREP:POR_PARA         — gracias para → por
- PREP:MOVEMENT         — voy en Madrid/cine → voy a Madrid/al cine (excluding transport)
- IDIOM:HACE_AGO        — antes/hay dos años → hace dos años

Morphosyntaxe / aspect / dative :
- ASPECT:PERF_OVERUSE   — he comido ayer → comí ayer (peninsular ES strict)
- V:GUSTAR_SUBJECT      — yo gusto la música → me gusta la música
- QUANT:MUY_MUCHO       — muy gusta → me gusta mucho ; mucho grande → muy grande

Interferencia FR :
- LEX:FR_RESIDUE        — 'ne', 'pas' tokens visibles en ES output

NOT covered (LLM layer handles): subjuntivo, preterito/imperfecto contextuel,
agreement chains, discourse-level patterns.

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


# ── Wave 1 enrichment (8 new detectors, Agent 1 Section C) ──

_SER_FORMS = {"soy", "eres", "es", "somos", "sois", "son"}
_SER_TO_ESTAR = {
    "soy": "estoy", "eres": "estás", "es": "está",
    "somos": "estamos", "sois": "estáis", "son": "están",
}


def _detect_ser_locative(text: str) -> list[RuleDetection]:
    """ser + lieu/direction → estar (Agent 1 pattern 1 locative branch).

    'soy en Madrid' → 'estoy en Madrid'. FP mitigation : exclude cleft
    constructions 'es en Madrid donde…' via lookahead for 'donde/que'.
    """
    results: list[RuleDetection] = []
    pattern = re.compile(
        r"\b(soy|eres|es|somos|sois|son)\s+(en|aquí|allí|ahí|cerca|lejos|dentro|fuera)\b"
        r"(?![^.!?]{0,20}\b(donde|que)\b)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        ser, loc = m.group(1).lower(), m.group(2)
        results.append(RuleDetection(
            "V:SER_ESTAR",
            f"{ser} {loc}",
            f"{_SER_TO_ESTAR[ser]} {loc}",
            f"Localisation/direction avec 'estar' : '{_SER_TO_ESTAR[ser]} {loc}' (et non 'ser').",
        ))
    return results


def _detect_gustar_nominative_subject(text: str) -> list[RuleDetection]:
    """'yo/tú/él…gustar' → 'me/te/le gust…' (Agent 1 pattern 7, très fréquent A1).

    Verbes d'affection : gustar, encantar, doler, faltar, interesar.
    FP risque quasi-nul (verbes dativement défectifs).
    """
    results: list[RuleDetection] = []
    pronouns_to_clitic = {
        "yo": "me", "tú": "te", "tu": "te", "él": "le", "ella": "le",
        "nosotros": "nos", "vosotros": "os", "ellos": "les", "ellas": "les",
    }
    pattern = re.compile(
        r"\b(yo|tú|tu|él|ella|nosotros|vosotros|ellos|ellas)\s+"
        r"(gust|encant|duel|falt|interes)(o|as|a|amos|áis|an)\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        pron = m.group(1).lower()
        stem = m.group(2).lower()
        # Verb should agree with logical-subject (thing liked), not speaker:
        # typical correction forces 3rd-person verb "gusta/encanta/duele/falta"
        correction_verb = f"{stem}a"
        clitic = pronouns_to_clitic.get(pron, "me")
        results.append(RuleDetection(
            "V:GUSTAR_SUBJECT",
            m.group(0),
            f"{clitic} {correction_verb}",
            f"Verbe d'affection en structure dative : '{clitic} {correction_verb}' (le sujet grammatical est la chose aimée).",
        ))
    return results


def _detect_hace_ago_calque(text: str) -> list[RuleDetection]:
    """'antes/hay + nombre + unité de temps' → 'hace' (Agent 1 pattern 14).

    FP risque : 'hay dos años de diferencia' (légitime existential). Filter :
    ne match que 'hay' direct + durée standalone, pas 'hay + nombre + de + autre nom'.
    """
    results: list[RuleDetection] = []
    pattern = re.compile(
        r"\b(antes|hay)\s+"
        r"(un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+)\s+"
        r"(año|años|mes|meses|semana|semanas|día|días|hora|horas)\b"
        r"(?!\s+de\s+)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        trigger = m.group(1).lower()
        num_unit = f"{m.group(2)} {m.group(3)}"
        results.append(RuleDetection(
            "IDIOM:HACE_AGO",
            f"{trigger} {num_unit}",
            f"hace {num_unit}",
            f"Durée passée avec 'hace + durée' : 'hace {num_unit}' (et non '{trigger} {num_unit}').",
        ))
    return results


_GUSTAR_STEMS = ("gust", "encant", "duel", "am", "ador", "odi")


def _detect_muy_before_verb(text: str) -> list[RuleDetection]:
    """'muy + verbe' → 'mucho' post-verbe (Agent 1 pattern 12, A1 fréquent).

    Détecte 'muy' devant verbes d'affection / d'intensité. Suggère 'mucho'
    déplacé après le verbe.
    """
    results: list[RuleDetection] = []
    stems_alt = "|".join(_GUSTAR_STEMS)
    pattern = re.compile(
        rf"\bmuy\s+(me|te|le|nos|os|les|se)?\s*({stems_alt})\w*",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        phrase = m.group(0)
        results.append(RuleDetection(
            "QUANT:MUY_MUCHO",
            phrase,
            phrase.replace("muy ", "", 1) + " mucho",
            "'muy' modifie adj/adv ; pour intensifier un verbe, utilise 'mucho' placé après : 'me gusta mucho' (et non 'muy me gusta').",
        ))
    return results


_MUCHO_BEFORE_ADJ_WHITELIST_TAIL = {"más", "mejor", "peor", "mayor", "menor"}


def _detect_mucho_before_adj(text: str) -> list[RuleDetection]:
    """'mucho + adjectif' → 'muy' (Agent 1 pattern 12, A1 fréquent).

    Whitelist : mucho más/mejor/peor/mayor/menor sont valides.
    """
    results: list[RuleDetection] = []
    target_adjs = (
        "grande", "pequeño", "pequeña", "bonito", "bonita", "feo", "fea",
        "alto", "alta", "bajo", "baja", "rápido", "rápida", "lento", "lenta",
        "caro", "cara", "barato", "barata", "bueno", "buena", "malo", "mala",
        "inteligente", "interesante", "difícil", "fácil",
    )
    adjs_alt = "|".join(target_adjs)
    pattern = re.compile(rf"\bmucho\s+({adjs_alt})\b", re.IGNORECASE)
    for m in pattern.finditer(text):
        adj = m.group(1).lower()
        if adj in _MUCHO_BEFORE_ADJ_WHITELIST_TAIL:
            continue
        results.append(RuleDetection(
            "QUANT:MUY_MUCHO",
            f"mucho {adj}",
            f"muy {adj}",
            f"Devant adjectif, 'muy' : 'muy {adj}' (et non 'mucho {adj}'). 'mucho' reste valide avec más/mejor/peor/mayor/menor.",
        ))
    return results


_TRANSPORT_NOUNS = {
    "tren", "coche", "auto", "avión", "metro", "bici", "bicicleta",
    "autobús", "bus", "barco", "taxi", "moto", "motocicleta",
}


def _detect_ir_en_preposition(text: str) -> list[RuleDetection]:
    """'voy/vas/va… + en + lieu' → 'a + lieu' (Agent 1 pattern 13, A1 fréquent).

    Exception légitime : transport ('voy en tren/coche'). Filter whitelist.
    """
    results: list[RuleDetection] = []
    ir_forms = ("voy", "vas", "va", "vamos", "vais", "van")
    place_candidates = (
        "cine", "teatro", "escuela", "universidad", "trabajo", "casa",
        "restaurante", "parque", "museo", "bar", "hospital", "médico",
        "playa", "mercado", "banco", "oficina", "gimnasio",
        "Madrid", "Barcelona", "Sevilla", "Valencia", "París", "Francia",
        "España", "Argentina", "México",
    )
    ir_alt = "|".join(ir_forms)
    place_alt = "|".join(place_candidates)
    pattern = re.compile(
        rf"\b({ir_alt})\s+en\s+(el|la|los|las)?\s*({place_alt})\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        ir, art, place = m.group(1).lower(), (m.group(2) or "").lower(), m.group(3)
        # Contraction a+el = al
        if art == "el":
            correction = f"{ir} al {place}"
            original = f"{ir} en el {place}"
        elif art:
            correction = f"{ir} a {art} {place}"
            original = f"{ir} en {art} {place}"
        else:
            correction = f"{ir} a {place}"
            original = f"{ir} en {place}"
        results.append(RuleDetection(
            "PREP:MOVEMENT",
            original,
            correction,
            f"Direction avec 'ir a' : '{correction}'. 'en' est réservé aux moyens de transport (voy en tren).",
        ))
    return results


def _detect_fr_residue(text: str) -> list[RuleDetection]:
    """Tokens FR 'ne' / 'pas' visibles en ES (Agent 1 pattern 11).

    FP risque quasi-nul : 'pas' et 'ne' n'ont pas d'équivalent libre en ES standard.
    """
    results: list[RuleDetection] = []
    for m in re.finditer(r"\b(ne|pas)\b", text):
        token = m.group(1)
        results.append(RuleDetection(
            "LEX:FR_RESIDUE",
            token,
            "(retirer)",
            f"Résidu français '{token}' détecté en espagnol. Négation ES = 'no' + optionnel postverbal (nada/nadie/nunca).",
        ))
    return results


_PAST_MARKERS_STRICT = (
    "ayer", "anoche", "anteayer",
    "la semana pasada", "el mes pasado", "el año pasado",
    "el lunes pasado", "el martes pasado", "el miércoles pasado",
    "el jueves pasado", "el viernes pasado", "el sábado pasado", "el domingo pasado",
)


def _detect_preterito_perfecto_past_marker(text: str) -> list[RuleDetection]:
    """'he/has/ha + participio + marqueur passé clos' → pretérito indefinido.

    Agent 1 pattern 4, A2 très fréquent (passé composé FR → perfecto ES calque).
    Cible la variante peninsular stricte. Pour LatAm plus tolérant, ce rule est
    over-strict — acceptable en pre-filter (LLM peut valider/débrayer).
    """
    results: list[RuleDetection] = []
    markers_alt = "|".join(re.escape(m) for m in _PAST_MARKERS_STRICT)
    year_alt = r"en\s+(19|20)\d{2}"
    pattern = re.compile(
        rf"\b(he|has|ha|hemos|habéis|han)\s+(\w+(?:ado|ido|to|cho|so))\b"
        rf"[^.!?]*?\b({markers_alt}|{year_alt})\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        aux, part, marker = m.group(1), m.group(2), m.group(3)
        results.append(RuleDetection(
            "ASPECT:PERF_OVERUSE",
            m.group(0)[:60],
            f"(pretérito indefinido au lieu de '{aux} {part}' avec '{marker}')",
            f"Marqueur passé clos '{marker}' → pretérito indefinido obligatoire (peninsular). Perfecto requiert marqueurs présent (hoy, esta semana, ya).",
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
    # Original 7 (Sprint 5 Phase 4)
    results.extend(_detect_missing_interrog(text))
    results.extend(_detect_missing_enye(text))
    results.extend(_detect_article_before_profession(text))
    results.extend(_detect_false_friends(text))
    results.extend(_detect_prep_calques(text))
    results.extend(_detect_ser_cansado(text))
    results.extend(_detect_gracias_para(text))
    # Wave 1 enrichment (8 new)
    results.extend(_detect_ser_locative(text))
    results.extend(_detect_gustar_nominative_subject(text))
    results.extend(_detect_hace_ago_calque(text))
    results.extend(_detect_muy_before_verb(text))
    results.extend(_detect_mucho_before_adj(text))
    results.extend(_detect_ir_en_preposition(text))
    results.extend(_detect_fr_residue(text))
    results.extend(_detect_preterito_perfecto_past_marker(text))
    return results
