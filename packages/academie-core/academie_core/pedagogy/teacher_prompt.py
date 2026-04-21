"""Sprint 3 — Teacher prompt assembly helpers.

Computes all dynamic sections injected into the Dify Teacher chatflow:
- Rubric per CEFR level (A1..C2)
- Dosage budget per turn + arbitration over budget
- Tier→feedback type mapping with diversity rule
- Anti-drift level reminder (every 5 turns) + drift self-grade request (every 10)
- L1 transfer watch hints (Phase 6)
- Spaced retrieval prompts (Phase 7)
- Few-shots selection
- JSON output schema + parse helper

Source of truth for Sprint 3 design: `docs/01-pedagogy/sprint3_design.md`.
Few-shots library: `docs/01-pedagogy/sprint3_fewshots.md`.

This module is imported by:
  - chat_router.py: builds dify_inputs at request time
  - scripts/update_teacher_chatflow.py: indirectly (template references the placeholders)
  - scripts/sprint3/tests/test_prompt_assembly.py: unit tests
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from academie_core.data.loader import (
    load_rubrics as _load_rubrics,
    load_fewshots as _load_fewshots,
    load_l1_names as _load_l1_names,
    load_l1_transfers,
)


# ── Constants ────────────────────────────────────────────────────────

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
TIERS = ("T0", "T1", "T2", "T3", "T4")
FEEDBACK_TYPES = (
    "silent",
    "implicit_recast",
    "elicitation",
    "metalinguistic",
    "prompt_plus_remediation",
)

# Dosage budget per CEFR level (max corrections in one Teacher response).
# Source: feedback-delivery.md table + sprint3_design.md §5.
DOSAGE_BUDGET = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 3,
    "C1": 4,
    "C2": 4,
}
# Hard cap when ALL detected errors are T4 regressive (override budget).
DOSAGE_HARD_CAP = {
    "A1": 2,
    "A2": 3,
    "B1": 4,
    "B2": 5,
    "C1": 5,
    "C2": 5,
}

# Tier → feedback type mapping (Lyster & Saito 2010).
# T1 silent (log only). T2 recast. T3 alternates elicitation/metalinguistic.
# T4 prompt + remediation + flag for spaced retrieval.
TIER_TO_FEEDBACK_DEFAULT = {
    "T0": "silent",
    "T1": "silent",
    "T2": "implicit_recast",
    "T3": "elicitation",   # default; alternates with metalinguistic via diversity rule
    "T4": "prompt_plus_remediation",
}

# Lazy reconciliation interval against drift validation.
RECONCILE_DRIFT_TURN = 10
LEVEL_REINJECT_TURN = 5


# ── Rubric per CEFR level ────────────────────────────────────────────

# Compact rubrics (~150 words each) injected dynamically as `{{rubric_for_level}}`.
# Detailed source: docs/01-pedagogy/sprint3_design.md §3.
# Loaded from data/rubrics/{lang}.yaml; hardcoded EN dict as fallback.
_RUBRICS_YAML = _load_rubrics("en")
RUBRICS: dict[str, str] = _RUBRICS_YAML if _RUBRICS_YAML else {
    "A1": (
        "RUBRIC A1 — Survival\n"
        "Communicative goal: greet, introduce, request basic info (time, price, name, place). "
        "Short sentences (5-10 words), present simple + can/want. Concrete vocab (~500 words BNC).\n"
        "Tolerance:\n"
        "- T1/T2 surface (spelling, capitalization), morphology (3rd-person -s), prepositions: omnipresent, do not correct.\n"
        "- T3 broken SVO structure (incomprehensible): correct 1× max per turn.\n"
        "- T4 communicative breakdown: correct immediately with L1 contrast.\n"
        "Preferred T2 feedback: implicit recast inline with follow-up question. NEVER elicit at A1.\n"
        "Target structures: present simple +/-, articles a/an/the, prepositions of place, personal pronouns.\n"
        "ANTI-PATTERNS: metalinguistic terms (banned), >2 corrections/turn, vocab >800 BNC, your sentences >12 words."
    ),
    "A2": (
        "RUBRIC A2 — Waystage\n"
        "Communicative goal: tell recent experience, express likes, simple comparisons, shopping. "
        "Past simple + going-to + would like.\n"
        "Tolerance:\n"
        "- T1 articles, common prepositions: silent.\n"
        "- T2 verb forms (goed→went), word order: light recast.\n"
        "- T3 on session target: elicitation, alternate with light metalinguistic ('Past or present?').\n"
        "- T4 on supposedly-acquired A1 structure: prompt + remediation, flag spaced retrieval.\n"
        "Preferred phrasings: T2 inline recast ('Oh you went to Paris! And what did you eat?'), "
        "T3 simple elicit ('Almost — past form of go?').\n"
        "Target structures: past simple regular+irregular (top 50), going-to future, comparatives -er/more, modal will/would basic."
    ),
    "B1": (
        "RUBRIC B1 — Threshold\n"
        "Communicative goal: hold conversation on familiar topics, narrate events, give opinion+reason, "
        "manage travel. Past tenses + present perfect + first conditional.\n"
        "Tolerance:\n"
        "- T1 articles, common prepositions: silent.\n"
        "- T2 lower-level structures (A1/A2 forms): recast.\n"
        "- T3 on B1 target structures (since/for, present perfect, conditionals): prompts dominant. "
        "Alternate elicitation and metalinguistic, max 2× same type consecutive on same family.\n"
        "- T4: prompt + explicit remediation + spaced retrieval.\n"
        "Preferred T3 phrasings: elicit ('Almost — when started in past, continues now, which tense?'), "
        "metalinguistic ('Watch the tense. Action finished or ongoing?').\n"
        "Target structures: present perfect (since/for, ever/never, just), conditionals 0+1, reported speech basic, phrasal verbs (top 50)."
    ),
    "B2": (
        "RUBRIC B2 — Vantage\n"
        "Communicative goal: argue, nuance position, cultural comparison, debate. "
        "All structures except rare + lexical precision.\n"
        "Tolerance:\n"
        "- T1/T2 fillers, hesitations: silent.\n"
        "- T3 on B2 target structures (subjunctive, inversion, complex tenses): "
        "elicitation + metalinguistic + stylistic nuance.\n"
        "- T4: prompt + remediation + pragmatic nuance.\n"
        "Preferred T3 phrasings: rich metalinguistic ('Were vs was — subjunctive after wish for unreal present'), "
        "pushed output ('How could you say that more precisely?').\n"
        "Target structures: conditionals 2+3, subjunctive (wish, if only), linking words (however/therefore), "
        "lexical precision (idiomatic collocations)."
    ),
    "C1": (
        "RUBRIC C1 — Effective Operational Proficiency\n"
        "Communicative goal: precise mastery, register-aware, academic debate, structured writing. "
        "Stylistic subtleties + idioms.\n"
        "Tolerance:\n"
        "- T1/T2 near-native disfluencies: silent.\n"
        "- T3 on lexical precision (C1 false friend, atypical collocation): metalinguistic + alternative phrasings.\n"
        "- T4 on supposedly-acquired A1-B2 structure: prompt + remediation + self-regulation reflection.\n"
        "Preferred phrasings: metalinguistic stylistic ('Whilst is more formal than while — context-appropriate?'), "
        "self-regulation prompt ('You tend to use make where do fits. Want me to flag this for review?').\n"
        "Target structures: idioms (transparent + opaque), literary inversion, advanced collocations, registers."
    ),
    "C2": (
        "RUBRIC C2 — Mastery\n"
        "Communicative goal: near-native, pragmatic nuance, linguistic creativity. "
        "Residual errors = fluency markers, not competence gaps.\n"
        "Tolerance:\n"
        "- T1 and T2: nearly always silent.\n"
        "- T3: metalinguistic + stylistic alternatives + cultural references.\n"
        "- T4: prompt + metapragmatic reflection.\n"
        "Preferred phrasings: 'That works, but a native might say X for the connotation of Y.', "
        "pushed creative output ('Can you make this less direct?').\n"
        "Target structures: cleft sentences, focus structures, pragmatic implicature, sarcasm/irony, native fluency markers."
    ),
}


@dataclass
class LanguageData:
    """Language-specific data bundle loaded from YAML (or hardcoded fallback)."""
    lang_target: str
    rubrics: dict[str, str]
    fewshots: list[dict]
    l1_names: dict[str, str]

    @classmethod
    def for_lang(cls, lang_target: str) -> "LanguageData":
        return cls(
            lang_target=lang_target,
            rubrics=_load_rubrics(lang_target) or RUBRICS,
            fewshots=_load_fewshots(lang_target) or FEWSHOT_BANK,
            l1_names=_load_l1_names() or L1_NAMES,
        )


def rubric_for_level(level: str, lang_data: LanguageData | None = None) -> str:
    """Returns the compact rubric block for the given CEFR level."""
    rubrics = lang_data.rubrics if lang_data else RUBRICS
    return rubrics.get(level.upper().rstrip("+"), rubrics.get("B1", ""))


# ── Dosage budget computation ───────────────────────────────────────


@dataclass
class DosageDecision:
    """Result of dosage arbitration for a single Teacher turn."""
    budget: int
    saturated: bool  # True if all detected errors couldn't fit
    to_correct: list[dict]  # errors selected for feedback
    silenced_for_spaced_retrieval: list[dict]  # errors deferred


def compute_dosage_budget(level: str, all_t4: bool = False) -> int:
    """Return max number of corrections to apply this turn for the given level."""
    level = level.upper().rstrip("+")
    if all_t4:
        return DOSAGE_HARD_CAP.get(level, 3)
    return DOSAGE_BUDGET.get(level, 3)


def arbitrate_dosage(
    level: str,
    errors_detected: list[dict],
) -> DosageDecision:
    """Apply the priority rule T4 > T3 > T2 > T1, respecting the level budget.

    Each error dict should at least contain `tier` and `error_code`.
    Errors above budget are returned in `silenced_for_spaced_retrieval`
    so the caller can persist them to the spaced retrieval queue.
    """
    by_tier: dict[str, list[dict]] = {t: [] for t in TIERS}
    for e in errors_detected:
        tier = e.get("tier") or "T1"
        if tier in by_tier:
            by_tier[tier].append(e)

    all_t4 = bool(by_tier["T4"]) and all(
        (e.get("tier") or "T1") == "T4" for e in errors_detected
    )
    budget = compute_dosage_budget(level, all_t4=all_t4)

    to_correct: list[dict] = []
    # T4 always included (within hard cap)
    for e in by_tier["T4"]:
        if len(to_correct) < budget:
            to_correct.append(e)
    # T3 next
    for e in by_tier["T3"]:
        if len(to_correct) < budget:
            to_correct.append(e)
    # T2 if remaining + linguistic gravity ≥ 0.5
    for e in by_tier["T2"]:
        if len(to_correct) >= budget:
            break
        if e.get("gravity_linguistic", 0) >= 0.5:
            to_correct.append(e)
    # T1 always silenced (just logged separately, not even spaced retrieval)
    silenced = [
        e for e in errors_detected
        if e not in to_correct and (e.get("tier") or "T1") != "T1"
    ]
    saturated = len(silenced) > 0
    return DosageDecision(
        budget=budget,
        saturated=saturated,
        to_correct=to_correct,
        silenced_for_spaced_retrieval=silenced,
    )


# ── Tier → feedback type mapping (with diversity rule) ──────────────


def tier_to_feedback_type(
    tier: str,
    family: str,
    last_feedback_per_family: dict[str, list[str]] | None = None,
    gravity: dict | None = None,
) -> str:
    """Map a tier to a feedback type, applying:
      - default mapping (TIER_TO_FEEDBACK_DEFAULT)
      - diversity rule for T3 (alternate elicitation ↔ metalinguistic)
      - gravity-axes overrides:
          * gravity_communicative ≥ 0.7 + tier T1 → upgrade to implicit_recast
          * gravity_social ≥ 0.6 + tier T2 → upgrade to elicitation
    """
    g = gravity or {}
    # Gravity overrides BEFORE default mapping
    if tier == "T1" and g.get("communicative", 0) >= 0.7:
        tier = "T2"
    elif tier == "T2" and g.get("social", 0) >= 0.6:
        tier = "T3"

    base = TIER_TO_FEEDBACK_DEFAULT.get(tier, "silent")

    # Diversity rule only meaningful for T3 (the only tier with two interchangeable types)
    if tier == "T3" and last_feedback_per_family:
        history = last_feedback_per_family.get(family, [])
        if len(history) >= 2 and history[-1] == history[-2] == "elicitation":
            return "metalinguistic"
        if len(history) >= 2 and history[-1] == history[-2] == "metalinguistic":
            return "elicitation"

    return base


# ── Anti-drift mechanism ────────────────────────────────────────────


def should_inject_level_reminder(turn_count: int) -> bool:
    """True if the level reminder block should be injected this turn (every 5 turns)."""
    return turn_count > 0 and turn_count % LEVEL_REINJECT_TURN == 0


def should_request_drift_check(turn_count: int) -> bool:
    """True if the Teacher should self-grade for drift (every 10 turns)."""
    return turn_count > 0 and turn_count % RECONCILE_DRIFT_TURN == 0


def build_level_reminder(level: str) -> str:
    """Returns the LEVEL REMINDER block to inject when turn % 5 == 0."""
    rubric = rubric_for_level(level).split("\n", 1)[0]  # title line only for compactness
    return (
        "=== LEVEL REMINDER ===\n"
        f"You are teaching at {level} level. Re-anchor:\n"
        f"  → {rubric}\n"
        "If your last messages crept into a higher register, recalibrate now.\n"
        "=== END REMINDER ==="
    )


def build_drift_check_request() -> str:
    """Returns the DRIFT SELF-CHECK block (turn % 10 == 0)."""
    return (
        "=== DRIFT SELF-CHECK ===\n"
        "Look at YOUR last 5 messages. Grade yourself :\n"
        "- 'compliant' if all messages stayed at the learner's level\n"
        "- 'drift_detected' if any message used vocabulary/structures > level+1\n"
        "Set the drift_self_grade field accordingly in your JSON output.\n"
        "=== END SELF-CHECK ==="
    )


# ── L1 transfer hook (Phase 6) ──────────────────────────────────────


# ISO-639-1 → English name (for `build_l1_watch` prose — LLM reads language names
# better than codes). Kept minimal to the languages we reasonably support today;
# unknown codes fall back to the code itself.
# Loaded from data/l1_transfer/l1_names.yaml; hardcoded dict as fallback.
_L1_NAMES_YAML = _load_l1_names()
L1_NAMES: dict[str, str] = _L1_NAMES_YAML if _L1_NAMES_YAML else {
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "zh": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "en": "English",
    "nl": "Dutch",
    "tr": "Turkish",
    "pl": "Polish",
    "ko": "Korean",
}


# Minimal seed for FR→EN. Now loaded from data/l1_transfer/*_to_*.yaml.
# Hardcoded dict as fallback.
_L1_SEED_YAML_FR_EN = load_l1_transfers("fr", "en")
L1_TRANSFER_SEED = {"fr": {"en": _L1_SEED_YAML_FR_EN}} if _L1_SEED_YAML_FR_EN else {
    "fr": {
        "en": [
            ("articles", 1.5,
             "Surutilisation 'the' (the love → love), omission 'a/an' (I am student → I am a student)."),
            ("prepositions", 1.4,
             "'I think to it' (calque 'à') → 'I think about it'. 'on the train' vs 'in the train'."),
            ("false_friends", 1.3,
             "actually ≠ actuellement (currently); library ≠ librairie (bookshop); to assist ≠ assister."),
            ("modals", 1.2,
             "'I should to go' (calque 'devoir') → 'I should go'."),
            ("word_order_questions", 1.1,
             "'What you want?' (calque) → 'What do you want?'."),
        ]
    }
}


def build_l1_watch(l1: str | None, target_lang: str = "en", top_n: int = 3, lang_data: LanguageData | None = None) -> str:
    """Returns the L1 WATCH block. Empty string if no L1 set or no transfer data.

    Renders the native language NAME in prose (e.g., "French" instead of "fr")
    so the LLM produces natural EXPLICIT_CONTRAST feedback — "In French we say X"
    reads better than "In fr we say X" and increases L1 mention rate in battery.
    """
    if not l1:
        return ""
    l1_code = l1.lower()
    target_code = target_lang.lower()
    # Try YAML loader first, then fall back to module-level seed
    transfers = load_l1_transfers(l1_code, target_code)
    if not transfers:
        transfers = L1_TRANSFER_SEED.get(l1_code, {}).get(target_code, [])
    if not transfers:
        return ""
    names = lang_data.l1_names if lang_data else L1_NAMES
    l1_name = names.get(l1_code, l1_code)
    target_name = names.get(target_code, target_code)
    top = sorted(transfers, key=lambda t: -t[1])[:top_n]
    bullets = "\n".join(f"  - {family} (×{mult}): {ex}" for family, mult, ex in top)
    return (
        "=== L1 WATCH ===\n"
        f"Learner's native language is {l1_name} ({l1_code}). "
        f"Common {l1_name}→{target_name} transfer errors to anticipate:\n"
        f"{bullets}\n"
        "When you detect such errors, prefer EXPLICIT_CONTRAST feedback:\n"
        f"\"In {l1_name} we say X, but in {target_name} Y because Z.\" (Lardiere 1998).\n"
        "=== END L1 WATCH ==="
    )


# ── Spaced retrieval (Phase 7) ──────────────────────────────────────


def build_spaced_retrieval_block(items_due: list[dict]) -> str:
    """Returns the SPACED RETRIEVAL TODAY block. Empty if no items due.

    Each item dict should at least have `concept_key` and `last_error_summary`.
    """
    if not items_due:
        return ""
    bullets = "\n".join(
        f"  - {item['concept_key']}: {item.get('last_error_summary', 'review needed')}"
        for item in items_due[:3]
    )
    return (
        "=== AUJOURD'HUI ON REVISITE ===\n"
        "Items due for spaced retrieval (J+1, J+3, J+7 from previous sessions):\n"
        f"{bullets}\n"
        "In your first 1-2 prompts of this session, weave in a question targeting ONE of these.\n"
        "Make it feel organic, not a quiz.\n"
        "=== END SPACED RETRIEVAL ==="
    )


# ── Few-shots selection (synthetic) ─────────────────────────────────


# Compact bank of synthetic few-shots (id, level, learner_turn → teacher_response, feedback_type).
# Detailed source: docs/01-pedagogy/sprint3_fewshots.md (24 examples).
# Here we keep a minimal bank for runtime selection; full library is for human review.
# Loaded from data/fewshots/{lang}.yaml; hardcoded EN list as fallback.
_FEWSHOTS_YAML = _load_fewshots("en")
FEWSHOT_BANK: list[dict] = _FEWSHOTS_YAML if _FEWSHOTS_YAML else [
    # A1
    {"id": "a1-recast-past-go", "level": "A1", "type": "implicit_recast",
     "learner": "Yesterday I go to the market with my mother.",
     "teacher": "Oh you *went* to the market! Did you buy something nice?"},
    {"id": "a1-silence-spelling", "level": "A1", "type": "silent",
     "learner": "I lik pizza very much, especialy with chees.",
     "teacher": "Pizza is great! What's your favorite topping? Pepperoni, mushrooms, ham?"},
    {"id": "a1-explicit-comm-breakdown", "level": "A1", "type": "prompt_plus_remediation",
     "learner": "I want bring food for my friend tomorrow him.",
     "teacher": "Wait — for your friend, tomorrow? Try again: \"I want to bring food...\" who is it for, and when?"},
    # A2
    {"id": "a2-elicit-irreg-past", "level": "A2", "type": "elicitation",
     "learner": "Yesterday I goed to school and I taked the bus.",
     "teacher": "Almost! Past form of *go*? And of *take*?"},
    {"id": "a2-metalinguistic-after-elicit", "level": "A2", "type": "metalinguistic",
     "learner": "Yes I goed last weekend, but I learn yesterday how to say went.",
     "teacher": "Watch the tense — *learn* or *learned* yesterday? Past, finished, so...?"},
    # B1
    {"id": "b1-elicit-pres-perfect", "level": "B1", "type": "elicitation",
     "learner": "I live in Paris since 5 years and I love it.",
     "teacher": "Almost — when an action started in the past and continues now, which tense?"},
    {"id": "b1-metalinguistic-conditional", "level": "B1", "type": "metalinguistic",
     "learner": "If I will have time tomorrow, I will call you.",
     "teacher": "Watch the conditional structure. After *if* in first conditional, present simple — never *will*. Try again?"},
    {"id": "b1-prompt-regression", "level": "B1", "type": "prompt_plus_remediation",
     "learner": "I think he is more stronger than his brother.",
     "teacher": "Hmm — *more* OR *-er*, not both. *Stronger*, that's it. We saw this at A2, I'll add it to your review queue."},
    # B2
    {"id": "b2-elicit-subjunctive", "level": "B2", "type": "elicitation",
     "learner": "I wish I was able to speak Mandarin fluently.",
     "teacher": "Almost — after *wish* for an unreal present, which form of *to be*?"},
    {"id": "b2-metalinguistic-collocation", "level": "B2", "type": "metalinguistic",
     "learner": "He made a big mistake by saying he could do the job alone — now they fired him.",
     "teacher": "*Big* mistake works informally — *serious* mistake fits your context better. And *they fired* → present perfect feel? Try with *they've fired*."},
    # C1
    {"id": "c1-metalinguistic-false-friend", "level": "C1", "type": "metalinguistic",
     "learner": "I assisted to a fascinating conference on AI ethics last weekend.",
     "teacher": "False friend alert: *assist* in English = \"help\". You *attended* the conference. What was the most thought-provoking idea?"},
    {"id": "c1-prompt-regression-articles", "level": "C1", "type": "prompt_plus_remediation",
     "learner": "I went to gym this morning before going to work.",
     "teacher": "Watch the article — *to the gym*. At C1, this should be automatic — adding to spaced retrieval."},
    # C2
    {"id": "c2-metalinguistic-connotation", "level": "C2", "type": "metalinguistic",
     "learner": "His comments were quite controversial, almost provocative — a deliberate move to stimulate debate.",
     "teacher": "*Quite* + strong adjective in BrE often softens (almost ironic). For emphasis, *highly* or *deeply* controversial. Connotation matters — softening or emphasis?"},
    {"id": "c2-silence-creative-style", "level": "C2", "type": "silent",
     "learner": "Were I in his shoes, scarcely a moment would pass without my second-guessing the decision.",
     "teacher": "Nicely turned — that inversion lands. What would you actually do, then?"},
]


def select_fewshots(level: str, max_examples: int = 3, lang_data: LanguageData | None = None) -> list[dict]:
    """Pick few-shots most relevant for the level + diversity of feedback types.

    Returns a list of fewshot dicts (id, level, type, learner, teacher).
    """
    bank = lang_data.fewshots if lang_data else FEWSHOT_BANK
    level = level.upper().rstrip("+")
    candidates = [fs for fs in bank if fs["level"] == level]
    if not candidates:
        # fallback: pick from adjacent level
        candidates = [fs for fs in bank if fs["level"] in {"B1", "A2"}]
    # diversify by type
    seen_types: set[str] = set()
    selected: list[dict] = []
    for fs in candidates:
        if fs["type"] not in seen_types:
            selected.append(fs)
            seen_types.add(fs["type"])
        if len(selected) >= max_examples:
            break
    # if not enough, pad with remaining
    for fs in candidates:
        if len(selected) >= max_examples:
            break
        if fs not in selected:
            selected.append(fs)
    return selected


def render_fewshots_block(level: str, max_examples: int = 3, lang_data: LanguageData | None = None) -> str:
    """Returns a markdown-flavored block listing the few-shots for the given level."""
    fewshots = select_fewshots(level, max_examples=max_examples, lang_data=lang_data)
    if not fewshots:
        return ""
    lines = ["=== FEW-SHOT EXAMPLES ==="]
    for i, fs in enumerate(fewshots, 1):
        lines.append(
            f"\nExample {i} ({fs['type']}):\n"
            f"  Learner: \"{fs['learner']}\"\n"
            f"  Teacher: \"{fs['teacher']}\""
        )
    lines.append("\n=== END EXAMPLES ===")
    return "\n".join(lines)


# ── JSON output schema + parsing ────────────────────────────────────


# JSON schema embedded in the prompt for the LLM to follow.
OUTPUT_SCHEMA_BLOCK = """=== OUTPUT FORMAT (JSON STRICT) ===

You MUST wrap your response in <output>...</output> tags containing valid JSON
matching this schema.

HONESTY REQUIREMENT — `tier_applied` MUST list EVERY tier whose error you address in your feedback this turn. If your feedback mentions a previously-learned structure the learner has regressed on (signals: "we saw this", "previously learned", "adding to spaced retrieval", "this should be automatic at your level", "you know this one"), you MUST include "T4" in tier_applied — even when combined with T2/T3. Do not omit tiers you actually addressed.

<output>
{
  "reasoning": "<200 words max, justifies tier choices per Lyster framework, NOT shown to learner>",
  "feedback": "<your actual response to the learner, respects all rules above>",
  "tier_applied": ["T2", "T3"],
  "feedback_types": ["implicit_recast", "elicitation"],
  "error_codes": ["V:TENSE", "PREP"],
  "dosage_check": "2/3",
  "silenced_for_spaced_retrieval": [],
  "spaced_retrieval_addressed": [],
  "drift_self_grade": "compliant",
  "level_reinjected": false,
  "observed_level": "A2"
}
</output>

NOTE `observed_level` (v2) : à CHAQUE turn émets ton estimation CEFR
(A1/A2/B1/B2/C1/C2) cumulée. OBLIGATOIRE dès turn 3. "" seulement si turns
1-2 sans production. N'en parle jamais au learner — télémétrie interne.

QUOTE HYGIENE : jamais de " non-échappés dans les strings JSON. Cite avec
« … », '…' ou \\"…\\". Exemple : "feedback": "Dis « buenos días »."

JSON malformé → fallback raw text. PREFER VALID JSON.

=== FIN OUTPUT FORMAT ==="""


_OUTPUT_TAG_RE = re.compile(r"<output>(.*?)</output>", re.DOTALL)


@dataclass
class TeacherResponse:
    feedback: str
    reasoning: str = ""
    tier_applied: list[str] = field(default_factory=list)
    feedback_types: list[str] = field(default_factory=list)
    error_codes: list[str] = field(default_factory=list)
    dosage_check: str = ""
    silenced_for_spaced_retrieval: list[str] = field(default_factory=list)
    spaced_retrieval_addressed: list[str] = field(default_factory=list)
    drift_self_grade: Literal["compliant", "drift_detected", "not_checked"] = "not_checked"
    level_reinjected: bool = False
    observed_level: str = ""  # Session 36 — CEFR estimate ("" if uncertain)
    parse_ok: bool = True
    raw_text: str = ""


def parse_teacher_response(raw_text: str) -> TeacherResponse:
    """Extract the <output>JSON</output> block. Falls back gracefully if malformed."""
    match = _OUTPUT_TAG_RE.search(raw_text or "")
    if not match:
        # No <output> tags — treat the whole response as the feedback (legacy mode)
        return TeacherResponse(feedback=(raw_text or "").strip(), parse_ok=False, raw_text=raw_text)
    payload = match.group(1).strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        # Malformed JSON inside tags — fallback to raw text outside tags
        outside = _OUTPUT_TAG_RE.sub("", raw_text).strip() or raw_text
        return TeacherResponse(feedback=outside, parse_ok=False, raw_text=raw_text)
    return TeacherResponse(
        feedback=str(data.get("feedback") or ""),
        reasoning=str(data.get("reasoning") or ""),
        tier_applied=list(data.get("tier_applied") or []),
        feedback_types=list(data.get("feedback_types") or []),
        error_codes=list(data.get("error_codes") or []),
        dosage_check=str(data.get("dosage_check") or ""),
        silenced_for_spaced_retrieval=list(data.get("silenced_for_spaced_retrieval") or []),
        spaced_retrieval_addressed=list(data.get("spaced_retrieval_addressed") or []),
        drift_self_grade=data.get("drift_self_grade") or "not_checked",
        level_reinjected=bool(data.get("level_reinjected") or False),
        observed_level=str(data.get("observed_level") or "").strip().upper(),
        parse_ok=True,
        raw_text=raw_text,
    )


# ── Diversity rule history update ───────────────────────────────────


def update_feedback_history(
    history: dict[str, list[str]],
    error_codes: list[str],
    feedback_types: list[str],
    family_lookup: dict[str, str] | None = None,
    cap: int = 4,
) -> dict[str, list[str]]:
    """Append the feedback types applied this turn to the per-family history.

    `family_lookup` maps error_code → family. If missing, family defaults to
    the error_code itself (degraded mode).
    Each family's history is capped at `cap` most recent entries.
    """
    out = {k: list(v)[-cap:] for k, v in (history or {}).items()}
    for code, ftype in zip(error_codes, feedback_types):
        family = (family_lookup or {}).get(code, code)
        out.setdefault(family, []).append(ftype)
        out[family] = out[family][-cap:]
    return out


# ── Top-level prompt builder ────────────────────────────────────────


@dataclass
class PromptContext:
    level: str
    turn_count: int
    errors_detected: list[dict] = field(default_factory=list)
    last_feedback_per_family: dict[str, list[str]] = field(default_factory=dict)
    l1: str | None = None
    spaced_retrieval_due: list[dict] = field(default_factory=list)
    target_lang: str = "en"
    # Session 35 — L1/L2 scaffolding policy signals
    fla_category: str | None = None   # "low" | "medium" | "high" — from learner_profiles.domain_motivation
    target_lang_name: str = ""        # Human name e.g. "Español", "English" (optional display override)
    l1_name: str = "français"         # Human name of L1 used in the scaffolding block
    # Session 37 — per-item FLA routing + self-efficacy/autonomy for intensity shift
    fla_items: dict[str, int] | None = None  # {"fla_a": 1-5, "fla_b": 1-5, "fla_c": 1-5}
    self_efficacy: int | None = None          # 1-5 Likert
    autonomy_pref: str | None = None          # "guided" | "semi_autonomous" | "autonomous"
    # Session 37 — post-QCM welcome flag (True only on turn 1 with fresh QCM profile)
    post_qcm_welcome: bool = False


def build_dynamic_sections(ctx: PromptContext, lang_data: LanguageData | None = None) -> dict:
    """Pre-compute every dynamic section of PROMPT_SESSION_v2.

    Returns a dict that maps to the Dify variable names so chat_router.py
    can pass them as `dify_inputs`. Each value is a string ready to be
    injected (or empty string if not applicable).
    """
    rubric = rubric_for_level(ctx.level, lang_data=lang_data)
    dosage = arbitrate_dosage(ctx.level, ctx.errors_detected)
    fewshots = render_fewshots_block(ctx.level, max_examples=3, lang_data=lang_data)

    level_reminder = (
        build_level_reminder(ctx.level)
        if should_inject_level_reminder(ctx.turn_count)
        else ""
    )
    drift_check = (
        build_drift_check_request()
        if should_request_drift_check(ctx.turn_count)
        else ""
    )

    l1_watch = build_l1_watch(ctx.l1, ctx.target_lang, lang_data=lang_data)
    spaced_retrieval = build_spaced_retrieval_block(ctx.spaced_retrieval_due)

    # Session 35 — L1/L2 scaffolding policy (level × typological-distance × FLA).
    # See docs/01-pedagogy/l1-l2-scaffolding-policy.md.
    from .typological_distance import get_distance
    from .scaffolding_policy import build_scaffolding_block, _normalize_fla
    distance = get_distance(ctx.l1 or "", ctx.target_lang)
    fla_band = _normalize_fla(ctx.fla_category)
    target_display = ctx.target_lang_name or ctx.target_lang
    scaffolding_block = build_scaffolding_block(
        cefr_placement=ctx.level,
        distance=distance,
        fla=fla_band,
        target_lang_name=target_display,
        l1_name=ctx.l1_name or "français",
        turn_count=ctx.turn_count,
        # Session 37 — anxiety routing + intensity shift
        self_efficacy=ctx.self_efficacy,
        autonomy_pref=ctx.autonomy_pref,
        fla_items_raw=ctx.fla_items,
        post_qcm_welcome=ctx.post_qcm_welcome,
    )

    # tier_summary describes what the LLM will see for arbitration
    tier_summary_lines = []
    for e in ctx.errors_detected:
        family = e.get("family", "?")
        tier = e.get("tier") or "T1"
        ftype = tier_to_feedback_type(
            tier=tier,
            family=family,
            last_feedback_per_family=ctx.last_feedback_per_family,
            gravity={
                "linguistic": e.get("gravity_linguistic", 0),
                "communicative": e.get("gravity_communicative", 0),
                "social": e.get("gravity_social", 0),
            },
        )
        tier_summary_lines.append(
            f"  - {e.get('error_code', '?')} ({family}) tier={tier} → suggested={ftype}"
        )
    tier_summary = "\n".join(tier_summary_lines) if tier_summary_lines else "(no errors this turn)"

    dosage_block = (
        "=== DOSAGE THIS TURN ===\n"
        f"Budget for {ctx.level}: max {dosage.budget} corrections in this response.\n"
        f"Errors detected: {len(ctx.errors_detected)} "
        f"(to_correct={len(dosage.to_correct)}, "
        f"silenced={len(dosage.silenced_for_spaced_retrieval)}).\n"
        f"\nTier summary:\n{tier_summary}\n"
        "\nIf budget exceeded, ARBITRATE: T4 > T3 > T2 (linguistic ≥0.5) > T1 silent.\n"
        "Silenced errors are auto-logged to spaced_retrieval_queue (no action needed).\n"
        "=== END DOSAGE ==="
    )

    return {
        "rubric_for_level": rubric,
        "fewshots_block": fewshots,
        "dosage_block": dosage_block,
        "level_reminder_inject": level_reminder,
        "drift_validation_request": drift_check,
        "l1_watch": l1_watch,
        "spaced_retrieval_today": spaced_retrieval,
        "output_schema_block": OUTPUT_SCHEMA_BLOCK,
        "scaffolding_block": scaffolding_block,
        # Metadata for chat_router.py to log
        "_dosage_decision": dosage,
        "_scaffolding_cell": f"{ctx.level}|{distance}|{fla_band}",
    }
