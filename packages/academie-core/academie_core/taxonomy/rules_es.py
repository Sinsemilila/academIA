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


# ── Wave 2 (Session 51 — coverage gap audit) ────────────────────────
# Source: oracle scenarios maestro_es/ — 6 critical scenarios were failing
# detection (a2_t2_preterite, a2_t2_a_personal, a1_t2_concord_gender, …).
# These 3 P0 detectors close the most impactful gaps.

# Closed-past temporal markers — context for preterite irregulars
_PAST_MARKERS_ES = (
    r"\b(ayer|anoche|anteayer|antier|"
    r"el\s+(?:lunes|martes|miércoles|jueves|viernes|sábado|domingo)\s+pasad[oa]|"
    r"la\s+semana\s+pasada|"
    r"el\s+(?:mes|año|verano|invierno|fin\s+de\s+semana)\s+pasad[oa]|"
    r"hace\s+(?:una?\s+)?\w+\s+(?:días?|semanas?|meses?|años?))\b"
)

# Common irregular preterite forms — keys are wrong forms to flag, values are corrections.
# Includes both genuine errors (yo + 3rd-person form) and learner-invented forms (e.g., "veí").
IRREGULAR_PRET_WRONG_TO_RIGHT: dict[str, tuple[str, str]] = {
    # Pattern: learner says wrong form → correction
    "veí": ("vi", "Pretérito irrégulier de 'ver' à la 1ère pers : 'vi' (pas 'veí')"),
    "andé": ("anduve", "Pretérito de 'andar' : 'anduve/-iste/-uvo' (pas 'andé')"),
    "tení": ("tuve", "Pretérito de 'tener' : 'tuve/-iste/-uvo' (pas 'tení')"),
    "sabí": ("supe", "Pretérito de 'saber' : 'supe/-iste/-upo' (pas 'sabí')"),
    "podí": ("pude", "Pretérito de 'poder' : 'pude/-iste/-udo' (pas 'podí')"),
    "querí": ("quise", "Pretérito de 'querer' : 'quise/-iste/-iso' (pas 'querí')"),
}

# Person-form mismatches: pronoun + 3rd-person form (yo + fue → fui)
_PRET_3SG_TO_1SG: dict[str, str] = {
    "fue": "fui",     # ir/ser
    "vio": "vi",      # ver
    "hizo": "hice",   # hacer
    "tuvo": "tuve",   # tener
    "estuvo": "estuve",
    "anduvo": "anduve",
    "supo": "supe",
    "pudo": "pude",
    "quiso": "quise",
    "dijo": "dije",
    "trajo": "traje",
    "vino": "vine",
    "puso": "puse",
}


def _detect_preterite_irregulars(text: str) -> list[RuleDetection]:
    """V:PRET — irregular preterite errors.

    Two patterns flagged :
      (1) learner-invented forms ("veí", "andé") regardless of context
      (2) "yo" + 3rd-person preterite ("yo fue" → "yo fui") in past-marker context
    """
    results: list[RuleDetection] = []
    has_past_marker = bool(re.search(_PAST_MARKERS_ES, text, re.IGNORECASE))

    # (1) Invented forms — always flag
    for wrong, (right, reason) in IRREGULAR_PRET_WRONG_TO_RIGHT.items():
        if re.search(rf"\b{re.escape(wrong)}\b", text, re.IGNORECASE):
            results.append(RuleDetection("V:PRET", wrong, right, reason))

    # (2) Person-form mismatch: 'yo' + 3sg preterite (only if past-marker context to reduce FP)
    if has_past_marker:
        for wrong_form, right_form in _PRET_3SG_TO_1SG.items():
            pattern = re.compile(rf"\byo\s+{re.escape(wrong_form)}\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                results.append(RuleDetection(
                    "V:PRET",
                    m.group(0),
                    f"yo {right_form}",
                    f"Pretérito 1ère pers : 'yo {right_form}' (pas 'yo {wrong_form}' — c'est la 3ème personne).",
                ))
    return results


# Transitive verbs that take 'a' before human direct objects (a-personal)
_A_PERSONAL_VERBS = (
    "ver", "veo", "ves", "vemos", "veis", "vio", "viste", "vi", "vimos",
    "conocer", "conozco", "conoces", "conoce", "conocí", "conociste", "conoció",
    "buscar", "busco", "buscas", "busca", "busqué", "buscaste", "buscó",
    "recordar", "recuerdo", "recuerdas", "recuerda",
    "ayudar", "ayudo", "ayudas", "ayuda", "ayudé",
    "invitar", "invito", "invitas", "invita", "invité", "invitó",
    "abrazar", "abrazo", "abrazas", "abraza",
    "llamar", "llamo", "llamas", "llama", "llamé", "llamó",
    "saludar", "saludo", "saludas", "saluda",
    "esperar", "espero", "esperas", "espera",
    "mirar", "miro", "miras", "mira",
    "escuchar", "escucho", "escuchas", "escucha",
    "encontrar", "encuentro", "encuentras", "encuentra",
    "visitar", "visito", "visitas", "visita",
)
_A_PERSONAL_OBJECTS = (
    "padre", "madre", "papá", "mamá", "hermano", "hermana", "hermanos", "hermanas",
    "hijo", "hija", "hijos", "hijas", "amigo", "amiga", "amigos", "amigas",
    "primo", "prima", "primos", "primas", "tío", "tía", "tíos", "tías",
    "abuelo", "abuela", "abuelos", "abuelas", "novio", "novia",
    "esposo", "esposa", "marido", "mujer",
    "profesor", "profesora", "maestro", "maestra", "estudiante", "estudiantes",
    "vecino", "vecina", "vecinos", "vecinas", "compañero", "compañera",
    "niño", "niña", "niños", "niñas", "chico", "chica", "chicos", "chicas",
)


def _detect_a_personal_missing(text: str) -> list[RuleDetection]:
    """PREP:A_PERSONAL — missing 'a' before human direct object.

    FR→ES key transfer error : 'veo mi madre' → 'veo a mi madre'.
    Pattern : transitive_verb + (mi/tu/su/el/la/los/las) + animate_noun, no 'a' before.
    """
    results: list[RuleDetection] = []
    verbs_alt = "|".join(_A_PERSONAL_VERBS)
    objs_alt = "|".join(_A_PERSONAL_OBJECTS)
    # Match : verb + space + (det) + noun, NOT preceded by 'a '
    pattern = re.compile(
        rf"\b({verbs_alt})\s+(mi|tu|su|el|la|los|las|mis|tus|sus)\s+({objs_alt})\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        verb, det, obj = m.group(1), m.group(2), m.group(3)
        # Check the verb isn't already preceded or followed by 'a '
        full = m.group(0)
        # Look at the slice between verb and det in the original text
        # If 'a ' was there it would be: verb + 'a ' + det → wouldn't match this pattern
        # So matches here are missing 'a'.
        results.append(RuleDetection(
            "PREP:A_PERSONAL",
            full,
            f"{verb} a {det} {obj}",
            f"Préposition 'a' obligatoire devant objet direct humain : '{verb} a {det} {obj}' (a personal).",
        ))
    return results


# Gender lexicon — high-frequency nouns where gender differs from FR or is irregular.
# Format : noun → gender ('M' or 'F'). Only nouns where mismatch likely from FR transfer.
_NOUN_GENDER: dict[str, str] = {
    # Masculine despite -a ending (false-cognate gender)
    "día": "M", "mapa": "M", "sistema": "M", "problema": "M", "tema": "M",
    "idioma": "M", "programa": "M", "clima": "M", "drama": "M", "poema": "M",
    "planeta": "M", "fantasma": "M",
    # Feminine despite -o or unusual pattern
    "mano": "F", "foto": "F", "moto": "F", "radio": "F",
    # Common feminine
    "casa": "F", "mesa": "F", "silla": "F", "ciudad": "F", "verdad": "F",
    "libertad": "F", "felicidad": "F", "salud": "F", "luz": "F", "voz": "F",
    "noche": "F", "tarde": "F", "gente": "F", "muerte": "F", "suerte": "F",
    "leche": "F", "carne": "F", "sangre": "F", "fuente": "F", "frente": "F",
    "solución": "F", "decisión": "F", "información": "F", "cuestión": "F",
    "razón": "F", "nación": "F", "explicación": "F",
    "víctima": "F", "persona": "F", "estrella": "F",
    # Common masculine
    "libro": "M", "coche": "M", "perro": "M", "gato": "M", "niño": "M",
    "padre": "M", "amigo": "M", "trabajo": "M", "tiempo": "M", "ejemplo": "M",
    "país": "M", "lugar": "M", "momento": "M", "número": "M", "color": "M",
    "papel": "M", "error": "M", "amor": "M", "calor": "M", "dolor": "M",
}
_DET_GENDER: dict[str, str] = {
    "el": "M", "los": "M", "un": "M", "unos": "M",
    "la": "F", "las": "F", "una": "F", "unas": "F",
}


def _detect_gender_disagreement(text: str) -> list[RuleDetection]:
    """CONCORD:GEN — article-noun gender mismatch on high-frequency nouns.

    Uses a curated lexicon of common nouns (~50 entries) where gender differs
    from FR or is otherwise high-error-rate. Restricted scope avoids false
    positives on nouns absent from lexicon (LLM layer covers gap).
    """
    results: list[RuleDetection] = []
    pattern = re.compile(
        r"\b(el|la|los|las|un|una|unos|unas)\s+([a-záéíóúñ]+)\b",
        re.IGNORECASE,
    )
    # Skip the 'a' before fem-as-masc nouns rule : "el agua/águila" — accepted
    FEM_AS_MASC_ARTICLE = {"agua", "águila", "alma", "área", "hambre"}
    for m in pattern.finditer(text):
        det_raw, noun = m.group(1).lower(), m.group(2).lower()
        if noun in FEM_AS_MASC_ARTICLE:
            continue
        det_g = _DET_GENDER.get(det_raw)
        noun_g = _NOUN_GENDER.get(noun)
        if det_g and noun_g and det_g != noun_g:
            # Pick the right determiner
            corrections = {"M": {"el": "el", "los": "los", "un": "un", "unos": "unos"},
                           "F": {"la": "la", "las": "las", "una": "una", "unas": "unas"}}
            # Map current det → opposite gender determiner of same number/definite-ness
            det_to_opposite = {
                "el": "la", "la": "el",
                "los": "las", "las": "los",
                "un": "una", "una": "un",
                "unos": "unas", "unas": "unos",
            }
            right_det = det_to_opposite[det_raw]
            results.append(RuleDetection(
                "CONCORD:GEN",
                f"{det_raw} {noun}",
                f"{right_det} {noun}",
                f"Concordancia de género : '{noun}' es {noun_g} → '{right_det} {noun}' (pas '{det_raw} {noun}').",
            ))
    return results


# ── Wave 2 P2 — Subjunctive trigger detection ───────────────────────
# High-impact for B1+ scenarios (b1_t3_subjuntivo_pres_001, multi_b1_subj_partial).
# Triggers : volitional/desiderative verbs + 'que' + indicative form. The LLM
# layer handles deeper morphology ; this rule catches the most common cases.

# Volitional/desiderative triggers requiring subjunctive in subordinate
_SUBJ_TRIGGERS = (
    r"quiero\s+que",
    r"quieres\s+que",
    r"quiere\s+que",
    r"queremos\s+que",
    r"queréis\s+que",
    r"quieren\s+que",
    r"espero\s+que",
    r"esperas\s+que",
    r"espera\s+que",
    r"esperamos\s+que",
    r"deseo\s+que",
    r"deseamos\s+que",
    r"para\s+que",
    r"prefiero\s+que",
    r"prefiere\s+que",
    r"pido\s+que",
    r"pide\s+que",
    r"necesito\s+que",
    r"necesita\s+que",
    r"ojalá(?:\s+que)?",
    r"es\s+importante\s+que",
    r"es\s+necesario\s+que",
    r"dudo\s+que",
    r"duda\s+que",
    r"no\s+creo\s+que",
)

# Common indicative present forms that should be subjunctive after triggers.
# Maps wrong (indicative) → right (subjunctive) for high-frequency verbs.
_IND_TO_SUBJ_PRES: dict[str, str] = {
    # ar verbs
    "hablo": "hable", "hablas": "hables", "habla": "hable",
    "hablamos": "hablemos", "habláis": "habléis", "hablan": "hablen",
    "trabaja": "trabaje", "trabajas": "trabajes",
    "estudio": "estudie", "estudias": "estudies", "estudia": "estudie",
    # er verbs
    "como": "coma", "comes": "comas", "come": "coma",
    "comemos": "comamos", "coméis": "comáis", "comen": "coman",
    "bebes": "bebas", "bebe": "beba",
    # ir verbs
    "vivo": "viva", "vives": "vivas", "vive": "viva",
    "vivimos": "vivamos", "viven": "vivan",
    "escribes": "escribas", "escribe": "escriba",
    # irregular high-freq
    "vienes": "vengas", "viene": "venga", "venimos": "vengamos", "vienen": "vengan",
    "vas": "vayas", "va": "vaya", "vamos": "vayamos", "van": "vayan",
    "tienes": "tengas", "tiene": "tenga", "tenemos": "tengamos", "tienen": "tengan",
    "haces": "hagas", "hace": "haga", "hacemos": "hagamos", "hacen": "hagan",
    "dices": "digas", "dice": "diga", "decimos": "digamos", "dicen": "digan",
    "puedes": "puedas", "puede": "pueda", "podemos": "podamos", "pueden": "puedan",
    "sabes": "sepas", "sabe": "sepa", "sabemos": "sepamos", "saben": "sepan",
    "eres": "seas", "es": "sea", "somos": "seamos", "son": "sean",
    "estás": "estés", "está": "esté", "estamos": "estemos", "están": "estén",
}


def _detect_subjunctive_missing(text: str) -> list[RuleDetection]:
    """V:SUBJ — indicative form after subjunctive trigger.

    Pattern : trigger phrase + (optional pronoun) + indicative-form-of-known-verb.
    Suggests the subjunctive equivalent. Limited to common verbs to keep
    high-precision (LLM layer handles long tail).
    """
    results: list[RuleDetection] = []
    # Match : trigger + optional pronoun (yo|tú|él|...) + indicative verb form (within ~3 tokens)
    pronouns_alt = r"(?:yo|tú|él|ella|usted|nosotros|vosotros|ellos|ellas|ustedes)"
    verbs_alt = "|".join(re.escape(v) for v in _IND_TO_SUBJ_PRES.keys())
    for trigger in _SUBJ_TRIGGERS:
        # \s+ between trigger and (optional pronoun + space)? + verb. Allow up to 2 short
        # adverbs/connectors between (e.g. "Quiero que tú no comas demasiado" should still flag).
        pattern = re.compile(
            rf"\b({trigger})\s+(?:{pronouns_alt}\s+)?(?:no\s+)?({verbs_alt})\b",
            re.IGNORECASE,
        )
        for m in pattern.finditer(text):
            trig_full, ind_verb = m.group(1), m.group(2).lower()
            subj_verb = _IND_TO_SUBJ_PRES.get(ind_verb)
            if not subj_verb:
                continue
            results.append(RuleDetection(
                "V:SUBJ",
                f"{trig_full} ... {ind_verb}",
                f"{trig_full} ... {subj_verb}",
                f"Después de '{trig_full}' se requiere subjuntivo : '{subj_verb}' (no '{ind_verb}').",
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
    # Wave 2 P0 (Session 51 — oracle scenario coverage gap fix)
    results.extend(_detect_preterite_irregulars(text))
    results.extend(_detect_a_personal_missing(text))
    results.extend(_detect_gender_disagreement(text))
    # Wave 2 P2 (Session 51 — subjunctive triggers)
    results.extend(_detect_subjunctive_missing(text))
    return results
