# Maestro ES translation glossary — Wave 1

Shared reference for all 4 LLM prompt translations (FR → ES) + `code_exam_bilan` strings.

## Agent identity

| FR | ES |
|---|---|
| Teacher | Maestro |
| prof d'anglais | profe de español |
| professeur d'anglais | profesor de español |
| anglais (langue) | español |
| English (meta) | Spanish |
| niveau | nivel |

## Register

- **Tutoiement préservé** (target audience = FR family + close). Use `tú` forms in Spanish.
- NOT `usted` (too formal for tutoring chat).
- Emoji preserved verbatim (📋 🆕 ⏰ ⚡ ✅ 🎉 🏆 ✨).

## CECRL levels

Storage + internal logic uses lowercase `a1-c2`. User-facing Spanish label mirrors Teacher EN :
- A1 = Acceso, A2 = Plataforma, B1 = Umbral, B2 = Avanzado, C1 = Dominio operativo, C2 = Maestría (per PCIC)
- In prompt text: keep CECRL codes uppercase (`A1`, `A2`, `B1`…) for LLM parsing consistency.

## Pedagogical framework terminology

| EN/FR term | Recommended ES |
|---|---|
| TTT (Test → Teach → Test) | TTT (Test → Enseña → Test), keep acronym |
| DECOUVERTE / RENFORCEMENT / PRATIQUE / MAINTIEN | DESCUBRIMIENTO / REFUERZO / PRÁCTICA / MANTENIMIENTO |
| recast implicite / explicit | recast implícito / explícito (keep Lyster terminology) |
| elicitation | elicitación |
| prompt + remediation | prompt + remediación |
| metalinguistic | metalingüístico |
| silent (feedback) | silencioso |
| tier T1/T2/T3/T4 | tier T1/T2/T3/T4 (keep acronym) |
| ignored / noted / penalized / regressive | ignorado / notado / penalizado / regresivo |
| dosage | dosificación |
| spaced retrieval | recuperación espaciada |
| confusion / frustration / ennui / flow / gaming | confusión / frustración / aburrimiento / flow / gaming |
| drift | drift / deriva (both acceptable, prefer "drift" technical) |
| L1 watch | observación L1 / L1 watch |
| rubric | rúbrica |
| fewshot / few-shot | fewshot / ejemplo guía |

## DELE question types (exam node)

| Cambridge EN term | DELE / MCER ES |
|---|---|
| FILL | COMPLETAR |
| CORRECT | CORREGIR |
| TRANSFORM | TRANSFORMAR (note: Cambridge word-key ≠ DELE — use paraphrase) |
| CHOICE | ELEGIR |
| FORM | FORMAR (word derivation — Spanish has different patterns) |
| PRODUCE | PRODUCIR |

## MCER paliers references (onboarding Phase 2 examples)

Examples CALIBRATED to Spanish level descriptors (Instituto Cervantes), NOT Cambridge English :

| CEFR | ES Example (MCER-aligned) |
|---|---|
| A1-A2 | "Háblame de ti" / "¿Qué te gusta hacer?" |
| A2-B1 | "¿Qué hiciste el fin de semana pasado?" / "Descríbeme a tu mejor amigo/a" |
| B1 | "¿Qué harías si te tocara la lotería?" |
| B1-B2 | "Cuéntame una decisión difícil que tuviste que tomar" |
| B2 | "¿Cuáles son los pros y los contras del teletrabajo?" |
| B2-C1 | "¿Cómo sería el mundo si no se hubiera inventado internet?" |
| C1 | "Algunos sostienen que la IA reemplazará a los profesores. ¿Estás de acuerdo?" |
| C1-C2 | "¿En qué medida el lenguaje moldea el pensamiento?" |

## Micro-tasks (onboarding, tour 4-5)

| EN | ES |
|---|---|
| "Write a sentence to decline an invitation" | "Escribe una frase para rechazar una invitación" |
| "Describe this situation: you arrive at a restaurant and your reserved table is taken" | "Describe esta situación: llegas a un restaurante y tu mesa reservada está ocupada" |
| "Complete this sentence in your own words: If I had known..." | "Completa esta frase con tus palabras: Si hubiera sabido..." |
| "Write a short email to reschedule a meeting" | "Escribe un correo breve para cambiar la fecha de una reunión" |

## Literal markers — NEVER TRANSLATE

These strings are parsed by Python code nodes (code_eval_check, code_exam_track, code_exam_detect) :

- `[EVAL_READY]`
- `[EXAM_START]`
- `[EXAM_COMPLETE]`
- `[EXAM_ABORT]`
- `[REVIEW_LACUNES]`
- `[REPEAT_QUESTION]`
- `[DIAGNOSTIC INITIAL]`
- `[PROFIL ELEVE]` (profile marker)
- `[découverte]` (keep — embedded in plan choice prompt)

## Template refs — NEVER TOUCH

Leave all `{{#code_turn_check.X#}}`, `{{#start.Y#}}`, `{{#conversation.Z#}}`, `{{#code_profil_check.A#}}`, `{{#sys.B#}}` references exactly as-is.

## Sources

- [rubrics/es.yaml](/opt/academie/packages/academie-core/academie_core/data/rubrics/es.yaml) — target rubrics per level (PCIC-aligned, Wave 1 enriched)
- [concept_hints/es.yaml](/opt/academie/packages/academie-core/academie_core/data/concept_hints/es.yaml) — 34 ES concepts (richer than EN)
- [cefr_diagnostics/es.yaml](/opt/academie/packages/academie-core/academie_core/data/cefr_diagnostics/es.yaml) — MCER palier + microtasks
- [l1_transfer/fr_to_es.yaml](/opt/academie/packages/academie-core/academie_core/data/l1_transfer/fr_to_es.yaml) — 19 FR→ES patterns (Wave 1)
- [taxonomy/llm.py SYSTEM_PROMPT_ES](/opt/academie/packages/academie-core/academie_core/taxonomy/llm.py) — existing ES system prompt (40+ codes, native)
- PCIC Vol.1-3 gramática inventarios (Agent 1 Wave 1 research)
- DELE A1-C2 sample exams (Instituto Cervantes public)
- Session 29 decision D5 : "1 chatflow Dify par agent" — ES gets its own full ES-native chatflow, not parameterized shell.
