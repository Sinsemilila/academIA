---
title: Roadmap d'exécution multi-langue — séquencement chronologique
date: 2026-04-18
status: superseded
superseded_by: ADR-013-language-scope-by-tier (2026-04-29) + ADR-016-authority-anchor-cross-lang (2026-04-29)
last_reviewed: 2026-04-19
author: Claude (Opus 4.7) — Session 27 + Session 28 (maturité) + Session 29 (pivot native JLPT/TORFL)
---

# Roadmap d'exécution multi-langue AcademIA

**Référence amont** :
- [`multilang_research_plan.md`](multilang_research_plan.md) = cartographie des ressources + effort par langue.
- [`multilang_maturity_research.md`](multilang_maturity_research.md) = recherche maturité Session 28 + pivot stratégie native JLPT/TORFL Session 29.

**Ce document** : ordre chronologique + factorisation + décisions stratégiques pour implémenter ES/IT/DE/JP/RU.

**Update Session 29 (2026-04-19)** : pivot Wave 3 (JP JLPT-native) et Wave 4 (RU TORFL-native) → **coût externe total = 40€ Profile Deutsch + ~$25-35 OpenAI synthetic**. Voir §2 (Phase 0 +0.7 levels), §5 (Wave 3 refondue), §6 (Wave 4 refondue).

---

## TL;DR (révisé Session 29)

| Scénario | Durée totale | Effort dev | Coût externe | Stratégie |
|---|---|---|---|---|
| **A. Séquentiel solo** (1 langue à la fois) | 12-15 mois | ~135-165j | 40€ + ~$30 OpenAI | ES → IT → DE → JP → RU |
| **B. Hybride recommandé** (ES seul, IT+DE parallèles, JP seul, RU seul) | **9-12 mois** | **~125-150j** | 40€ + ~$30 OpenAI | Wave 1 ES → Wave 2 IT+DE factorisé → Wave 3 JP JLPT-native → Wave 4 RU TORFL-native |
| **C. All-parallel** (≥2 devs) | 6-7 mois | ~180j cumulés | 40€ + ~$30 OpenAI | Toutes en parallèle après Phase 0 |

**Recommandation** : **Scénario B** — équilibre risk/efficiency. ES prouve le pipeline multi-langue, IT+DE factorisé économise ~30% d'effort vs séquentiel, JP JLPT-native et RU TORFL-native car langues distantes utilisent systèmes de niveau natifs, pas de forcing CEFR.

**Clé Session 29** : les **6 langues deviennent matures dans leur écosystème pédagogique natif** à coût externe quasi-nul (40€ Profile Deutsch + ~$25-35 OpenAI synthetic).

---

## 1. Décision stratégique : séquentiel, parallèle ou hybride ?

### Arguments pour SÉQUENTIEL (langue par langue complète)

| Pro | Con |
|---|---|
| Feedback loop rapide (ES en prod → apprend → ajuste IT) | Répétition process 5× (pas de factorisation) |
| Risque minimal (1 langue buggée ≠ bloquer les autres) | Coût temporel élevé (~18 mois) |
| Pipeline validé étape par étape | Tools et scripts non-réutilisables (chacun réinvente la roue) |
| Chaque alpha famille test indépendant | Les patterns cross-lang découverts tardivement |

### Arguments pour PARALLÈLE par étape (horizontal)

| Pro | Con |
|---|---|
| Factorisation maximale (corpus pipeline, GLMM script, Dify cloner) | Complexité de gestion (5 flux à coordonner) |
| Découverte patterns cross-lang tôt | Aucune langue en prod avant la fin |
| Uniformité méthodologique garantie | Si bug sur étape N, impacte toutes les langues |
| Total effort réduit ~20-30% | Requires ≥2 devs ou agents concurrents |

### HYBRIDE recommandé : 4 vagues (révisé Session 29)

```
Phase 0 — Infra factorisée (cross-lang tooling + levels.py mapping JLPT/TORFL)
         ↓
Wave 1  — ES finalisation CEFR (seul, alpha prod)  [validation pipeline]
         ↓
Wave 2  — IT + DE parallèle CEFR par étape         [factorisation langues européennes]
         ↓
Wave 3  — JP seul JLPT-native (N5-N1)              [tokenizer + Japan Foundation ressources]
         ↓
Wave 4  — RU seul TORFL-native (TEU-IV)            [Gosstandart ТРКИ ressources]
```

**Raison** :
- **ES d'abord** car drafts déjà faits et proof de concept nécessaire. **CEFR A1-C2**.
- **IT+DE ensemble** car typologiquement proches côté pipeline (corpus MERLIN shared, Pienemann théorique commune, rubrics CEFR européenne). **CEFR A1-C2**.
- **JP seul JLPT-native** (Session 29 pivot) — tokenizer MeCab obligatoire + utilisation **JLPT N5-N1** comme système de niveau natif (pas de CEFR forcé). Ressources open Japan Foundation, Tae Kim, Imabi, JLPT listes.
- **RU seul TORFL-native** (Session 29 pivot) — utilisation **TORFL TEU-IV** comme système officiel russe (pas de CEFR forcé). Ressources open Gosstandart ТРКИ, Lexical/Grammatical Minimum, RLC brut.

---

## 2. Phase 0 — Infrastructure factorisée (8-10j one-time)

**Pourquoi** : ces composants sont utilisés par TOUTES les langues suivantes. Les faire une fois au début économise 30% d'effort aval.

### 0.1 Script programmatique clone Dify app (~2j)

```python
# scripts/dify/clone_app.py
def clone_teacher_app(source_app_id: str, new_name: str,
                      new_description: str, prompts_override: dict) -> str:
    """Clone Teacher graph + create new app + translate prompts.
    Returns new app_id + API key for _DOMAIN_REGISTRY."""
```

**Livrable** : clone Teacher graph → nouvelle app Dify avec prompts traduits, retourne `app_id` + `app_key`.

**Utilisé par** : Maestro ES, Professore IT, Lehrer DE, Sensei JP, RussianTutor RU.

### 0.2 GLMM pipeline param par lang (~3j)

Actuellement `scripts/sprint1/*.py` hardcoded EN (W&I corpus). Refactor pour accepter `--lang es` argument.

**Livrable** :
- `scripts/sprint1/05_glmm_fit.py --lang {es,it,de,jp,ru}` → posterior par langue
- `scripts/sprint1/errant_to_academie.yaml` devient `errant_to_academie_{lang}.yaml` par langue
- Corpus normalization pipeline générique (peut avaler W&I, MERLIN, CEDEL2, RLC...)

**Utilisé par** : calibration T1-T4 weights par langue (étape 2 du pipeline).

### 0.3 Rules engine complet dispatch par lang (~2j)

Actuellement `taxonomy/rules.py` dispatch minimal (`if lang == 'es' → rules_es`). Étendre pour :
- Interface unifiée `detect_errors(text, lang)` qui route vers rules_{lang}.py
- Squelettes vides créés pour it, de, jp, ru (prêts à remplir)
- Tests fixtures par lang

**Livrable** : `rules_{en,es,it,de,jp,ru}.py` avec template commune, dispatcher complet.

### 0.4 Loader YAML multi-lang helpers (déjà fait partially, 0.5j)

Phase 3 Sprint 5 a créé `data/loader.py` avec :
- `load_rubrics(lang)`, `load_fewshots(lang)`, `load_concept_hints(lang)`
- `build_cefr_diagnostics_block(lang)`, `get_persona_label(lang)`

**À compléter** : `load_curriculum(lang)`, `load_l1_transfers(l1, target)` (déjà).

### 0.5 Battery framework paramétré par lang (~1.5j)

Actuellement `eval_live_battery.py` hardcoded EN (4 personas A1-B2 anglophones). Refactor :
- `eval_live_battery.py --lang es --persona-file data/battery/es_personas.yaml`
- Assertions par lang (JSON schema, dosage, tier mapping reste commun ; content varie)

**Livrable** : framework battery parametré, `data/battery/{lang}_personas.yaml` template.

### 0.6 Tokenizer abstraction (~1j)

Pour préparer JP/RU qui nécessitent tokenizers non-Latin :

```python
# academie_core/taxonomy/tokenizer.py
def tokenize(text: str, lang: str) -> list[Token]:
    """Dispatch: EN/ES/IT/DE → whitespace+regex, JP → SudachiPy, RU → pymorphy2."""
```

**Utilisé par** : JP (SudachiPy), RU (pymorphy2/MyStem) ; EN/ES/IT/DE utilisent fallback whitespace.

### 0.7 Niveaux natifs mapping JLPT/TORFL (~1j) — NOUVEAU Session 29

Module qui abstrait le système de niveau par domaine (CEFR pour EN/ES/IT/DE, JLPT pour JP, TORFL pour RU). Storage interne reste `a1-c2`, affichage et prompts utilisent le système natif.

```python
# academie_core/levels.py
JLPT_TO_CEFR = {"N5": "a1", "N4": "a2", "N3": "b1", "N2": "b2", "N1": "c1", "beyond_N1": "c2"}
CEFR_TO_JLPT = {v: k for k, v in JLPT_TO_CEFR.items()}

TORFL_TO_CEFR = {"TEU": "a1", "TBU": "a2", "TORFL-I": "b1", "TORFL-II": "b2",
                 "TORFL-III": "c1", "TORFL-IV": "c2"}
CEFR_TO_TORFL = {v: k for k, v in TORFL_TO_CEFR.items()}

LEVEL_SYSTEM_BY_DOMAIN = {
    "teacher": "cefr", "maestro": "cefr", "professore": "cefr", "lehrer": "cefr",
    "sensei": "jlpt", "maestro_ru": "torfl",
}

def display_level(cefr_level: str, domain: str) -> str:
    """Return user-facing level label. JP sees N5-N1, RU sees TEU-IV, others A1-C2."""
    system = LEVEL_SYSTEM_BY_DOMAIN[domain]
    if system == "jlpt":
        return CEFR_TO_JLPT[cefr_level]
    elif system == "torfl":
        return CEFR_TO_TORFL[cefr_level]
    return cefr_level.upper()

def parse_user_level(raw: str, domain: str) -> str:
    """Inverse: parse user input (N4, TORFL-I, B1) → internal a1-c2."""
    ...
```

**Utilisé par** : Dify prompts (via template variables), UI webapp (affichage), rubrics YAML (contenu rédigé selon natif mais indexé par clé interne).

### 0.8 Synthetic errors generation pipeline (~3j) — NOUVEAU Session 29

Paradigme two-stage 2024 (Latouche EMNLP 2024) — utilitaire Python réutilisable IT/DE/JP/RU.

```python
# scripts/synthetic/generate_errors.py
def generate_synthetic_errors(lang: str, level: str, n_examples: int,
                              descriptors_path: str, seed_corpus: list[str]) -> list[dict]:
    """Génère N examples erreurs guidés par descriptors (CEFR / JLPT / TORFL)."""
```

**Budget** : ~$5-8 OpenAI par langue × 5 = **$25-40 total**.

### 0.9 Discovery emails non-bloquants (~1j) — NOUVEAU Session 29

Emails non-contractuels aux contacts académiques identifiés (UCLouvain/Eurac/Nice/HU Berlin). **Non-bloquants** — stratégies Wave 1-4 ne dépendent PAS de ces réponses. Template email fourni en annexe `multilang_maturity_research.md`.

### Phase 0 total (révisé Session 29)

| Item | Effort | Priorité |
|---|---|---|
| 0.1 Dify app cloner | 2j | Critique (bloque toutes langues) |
| 0.2 GLMM pipeline param | 3j | Phase 0 mais optionnel pour ES (drafts sans GLMM ok) |
| 0.3 Rules dispatch complet | 2j | Utilisé dès Wave 2 |
| 0.4 Loader YAML | 0.5j | Quasi-fait |
| 0.5 Battery param | 1.5j | Nécessaire pour chaque wave |
| 0.6 Tokenizer abstraction | 1j | Anticipation JP/RU |
| **0.7 Levels JLPT/TORFL mapping** | **1j** | **Critique Wave 3/4 (nouveau Session 29)** |
| **0.8 Synthetic errors pipeline** | **3j** | **Utilisé Wave 1-4 (nouveau Session 29)** |
| **0.9 Discovery emails** | **1j** | **Non-bloquant (nouveau Session 29)** |
| **Total** | **~15j** | **One-time cross-lang investment (révisé Session 29)** |

---

## 3. Wave 1 — ES finalisation (12-15j, ~3-4 semaines calendaire)

**Objectif** : Maestro ES en prod alpha famille validé. Prouve que le pipeline multi-langue tient la route end-to-end.

### Chrono détaillé (updated Session 27 — inclus fine-tune synthétique)

| Jour | Tâche | Source | Livrable |
|---|---|---|---|
| J1 | PCIC Vol.1 A1-A2 lecture structurée | cvc.cervantes.es | Annotations §précises + structures cibles A1-A2 |
| J2 | PCIC Vol.2 B1-B2 + Vol.3 C1-C2 | cvc.cervantes.es | Annotations + enrichissement `rubrics/es.yaml` final |
| J3 | CEDEL2 download + exploration | cedel2.learnercorpora.com | Dataset local + scripts d'extraction FR subcorpus |
| J4 | CEDEL2 error patterns FR→ES analysis | CEDEL2 + COWS-L2H annotations | Liste top-20 erreurs FR→ES observées |
| J5 | Bruhn de Garavito 1986/2002 + Collentine 2010 lecture | Papers PDF | Notes structurées transfer patterns |
| J6 | Montrul 2022 + Geeslin ser/estar + RAE Nueva Gramática | Papers + cvc.cervantes.es | Notes + références edge cases |
| J7 | Enrichir `rules_es.py` 7 → 15-20 détecteurs | Synthesis J3-J6 | `rules_es.py` v2 + tests unitaires |
| J8 | Calibrer `l1_transfer/fr_to_es.yaml` multipliers (si CEDEL2 FR data) | CEDEL2 FR subcorpus frequencies | `l1_transfer/fr_to_es.yaml` v2 |
| J9 | Enrichir `fewshots/es.yaml` avec exemples réels corpus | Corpus + research | `fewshots/es.yaml` v2 (16 examples validés) |
| **J10** | **Générer 5000 examples synthétiques ES via GPT-4** (errant-like, basé sur taxonomy codes ES + corpus patterns J3-J6) | `scripts/generate_v1_training_data_es.py` | `train_v1_es.jsonl` + `val_v1_es.jsonl` |
| **J11** | **Lancer fine-tune OpenAI `ft:gpt-4o-mini-...academie-errors-es-v1`** (job ~2h) + validation F1 on hold-out | OpenAI fine-tuning API | Model ID + F1 score report |
| **J12** | **Activer fine-tune dans `ANALYSIS_MODEL_BY_LANG["es"]`** | Swap base model → fine-tune | Enhanced error analysis ES |
| J13 | Clone Teacher Dify → nouvelle app "Maestro" | Phase 0.1 script | `maestro_app_id` + `maestro_app_key` |
| J14 | Traduction prompts Dify Maestro (plan_choice, session, onboarding, exam) en ES natif | YAMLs enrichis | Maestro Dify chatflow complet |
| J15 | Battery ES 4 personas A1-B2 | `eval_live_battery.py --lang es` | Pass rate report ≥ 95% |
| J16 | Fix battery fails + itération 2 prompts | — | Pass rate ≥ 97% |
| J17 | Activation prod : `ENABLE_MAESTRO=true` + `DIFY_KEY_MAESTRO` + `maestro.available=true` | Env vars + config.ts flip | Maestro live |
| J18 | Monitor alpha famille 1 semaine (calendaire) | `error_log` + feedback | Liste ajustements wave 1.5 |

**Total Wave 1 ES** : ~18j effort (vs 15j initial, +3j pour fine-tune synthétique).

**Budget total** : ~15j effort dev + 1 semaine calendaire monitoring = **~4 semaines**.

### Dépendances

- **Phase 0.1 (Dify cloner)** obligatoire avant J10
- **Phase 0.5 (Battery param)** obligatoire avant J12
- **Phase 0.2 (GLMM pipeline)** **NON** requise pour Wave 1 (on reste sur drafts — Option B base model)

### Critères de succès Wave 1

- [x] Maestro ES HTTP 200 sur `/v1/chat-messages`
- [x] Battery 4 personas A1-B2 pass rate ≥ 95%
- [x] 3-5 users alpha famille testent 1 semaine, feedback collecté
- [x] Aucune régression Teacher EN (smoke test 20/20)
- [x] error_log ES populé avec ≥ 50 erreurs detectées sur semaine 1

---

## 4. Wave 2 — IT + DE parallèle par étape (35-40j, ~8-10 semaines calendaire)

**Pourquoi parallèle** : IT et DE sont typologiquement européennes flexionnelles qui partagent :
- **Même corpus source** : MERLIN (plateforme EURAC + CLARIN)
- **Même framework théorique** : Pienemann Processability Theory
- **Même loader pipeline** : européennes CEFR-alignées
- **Même exam framework** : CILS/CELI (IT) et Goethe/TestDaF (DE) sont structurellement comparables

Factorisation économise ~30% : séquentiel ferait 22-28j IT + 28-35j DE = 50-63j ; parallèle réduit à 35-40j cumulés.

### Chrono factorisé (par étape du pipeline)

| Semaine | Étape (shared avec IT+DE) | IT spécifique | DE spécifique |
|---|---|---|---|
| S1 | **Corpus download + exploration** | MERLIN IT (400 tx) + VALICO | MERLIN DE (1000 tx) + Falko (1500 tx) |
| S2 | **Rubrics extraction** | Profilo della lingua + Sillabo CILS | Goethe-Institut curriculum (public, Profile Deutsch optionnel payant) |
| S3 | **SLA research** | Bettoni & Giacalone Ramat + contrastive FR/IT | Pienemann + Håkansson + extrapolation EN→DE data |
| S4 | **Rules engineering** (IT simple, DE syntax-aware) | `rules_it.py` : subj trigger, essere/avere, clitics | `rules_de.py` : V2 detection via spaCy-de, case agreement, séparables. +spaCy-de intégration |
| S5 | **L1 transfer + Curriculum** | `l1_transfer/fr_to_it.yaml` (essere/avere, subj) + `curriculum_it.yaml` (75 concepts CILS) | `l1_transfer/fr_to_de.yaml` (V2, cases, gender) + `curriculum_de.yaml` (80 concepts Goethe) |
| S6 | **Fewshots** | `fewshots/it.yaml` 14 examples FR→IT | `fewshots/de.yaml` 14 examples FR→DE |
| S7 | **Dify apps + prompts** | Clone Teacher → Professore + traduction prompts IT | Clone Teacher → Lehrer + traduction prompts DE |
| S8 | **Battery** | 4 personas IT A1-B2 | 4 personas DE A1-B2 |
| S9 | **Activation alpha** | `ENABLE_PROFESSORE=true` + alpha famille | `ENABLE_LEHRER=true` + alpha famille |
| S10 | **Monitoring + iteration** | Semaine calendaire feedback | Semaine calendaire feedback |

### Décomposition effort IT vs DE

| Étape | Effort IT | Effort DE | Factorisation partagée | Total cumulé |
|---|---|---|---|---|
| Corpus | 2j | 3j | 1j (pipeline commun) | 6j |
| Rubrics | 2j | 3j | 1j (template commun) | 6j |
| SLA | 2j | 3j | 1j (Pienemann commun) | 6j |
| Rules | 3j | 6j (syntax-aware) | 2j (engine dispatch) | 11j |
| L1 + Curriculum | 2j | 2j | 0j | 4j |
| Fewshots | 2j | 2j | 0j | 4j |
| Dify apps | 2j | 2j | 1j (script cloner une fois) | 5j |
| Battery | 2j | 2j | 0j | 4j |
| Activation | 1j | 1j | 0j | 2j |
| **Cumulé** | **18j** | **24j** | **6j partagé** | **~35-40j** |

vs séquentiel : 22-28j IT + 28-35j DE = **50-63j**. Économie **30-35%**.

### Dépendances Wave 2

- **Wave 1 validée** (ES prouve le pipeline)
- **Phase 0 complète** (Dify cloner, rules dispatch, battery param tous prêts)
- **spaCy-de** installé pour DE syntax-aware rules
- **MERLIN download** (CLARIN registration si pas déjà fait)

### Critères de succès Wave 2

- [x] Professore IT + Lehrer DE HTTP 200 sur `/v1/chat-messages`
- [x] Battery IT + DE pass rate ≥ 95%
- [x] Alpha famille teste les 2 langues (rotation)
- [x] Teacher EN + Maestro ES restent intacts (smoke test 20/20)

---

## 5. Wave 3 — JP Sensei JLPT-native (30-35j, ~7-9 semaines calendaire)

**Pivot Session 29** : abandonner le forcing CEFR pour JP. Utiliser **JLPT N5-N1** comme système de niveau natif — standard de facto mondial pour l'apprentissage du japonais. Couverture **N5-N1 dans un seul Wave** (plus besoin de Wave 3.5 séparée). **Coût externe : 0€**.

**Scope** : N5-N1 couvert dans écosystème natif JLPT. Limites honnêtes : keigo niveau N1 = best-effort, aspect littéraire = best-effort (documentation transparente dans produit).

### Phase A — Infra JP (8-10j)

| Jour | Tâche | Livrable |
|---|---|---|
| J1-J2 | SudachiPy / MeCab integration + dict A/B/C granularity tests | `academie_core/taxonomy/tokenizer_jp.py` |
| J3 | Script normalization handling hiragana/katakana/kanji/rōmaji | `normalize_jp(text)` function |
| J4-J5 | Rōmaji → hiragana conversion + IME-aware handling | `romaji_to_hiragana()` + tests |
| J6 | Tokenization learner text tests (erreurs typiques) | 50 test cases validés |
| J7-J8 | POS filtering pour extraction particules (は/が/を/に/で) | Particle extractor |
| J9 | JMdict + KANJIDIC integration (Yomitan format) | Vocabulary + kanji readings lookup |
| J10 | Performance benchmarks (SudachiPy vs MeCab vs Juman++) | Decision record + tokenizer choice locked |

### Phase B — Content JLPT N5-N1 (15-18j)

| Semaine | Tâche | Source | Livrable |
|---|---|---|---|
| S1 | Télécharger corpus learner : **I-JAS brut** (NINJAL, 1050 learners tous L1) + **Lang-8 historical** (millions corrections) + **Tatoeba JP** + **JpWaC** natif | ninjal.ac.jp + lang-8.com archive + tatoeba.org | Dataset learner + natif |
| S2 | **Rubrics N5-N1** depuis Japan Foundation JF Standard + Tae Kim's Guide + Imabi.org + Minna no Nihongo structures | jfstandard.jp + guidetojapanese.org + imabi.org | `rubrics/jp.yaml` **JLPT-native N5-N1** (clés internes a1-c2 via levels.py) |
| S3 | **Vocab + kanji lists** officielles par niveau JLPT (N5/N4/N3/N2/N1) | JLPT Sensei + Jisho.org + Anki decks JLPT | `data/jp/vocab_jlpt.yaml` + `kanji_jlpt.yaml` |
| S4 | **Grammar points** par niveau JLPT (détaillés) | Tae Kim + Imabi + jlptsensei.com | `data/jp/grammar_jlpt.yaml` |
| S5 | `curriculum_jp.yaml` — concepts N5-N1 (~80 concepts total) | Synthesis Phase B | `curriculum_jp.yaml` |
| S6 | Oyama particules research + GEC papers | APU + github.com/gotutiyan/GEC-Info | `rules_jp.py` : particules, conjugaisons régulières, kanji homophonie |
| S7 | **FR→JP seed theoretical** (articles absents, SOV, particules, kanji orthographe) | Contrastive grammar + Higashi/Detey papers HAL | `l1_transfer/fr_to_jp.yaml` |
| S8 | **Synthetic errors generation** GPT-4 guidé par JLPT descriptors (~$5-8 OpenAI) via `scripts/synthetic/generate_errors.py --lang jp` | JLPT descriptors N5-N1 | `train_v1_jp.jsonl` (5000 synth examples) |
| S9 | **Cross-lingual transfer** mT5-Large + MAD-X depuis EN baseline → fine-tune léger RU | HuggingFace + MAD-X | `ft:jp-v1` model |
| S10 | Fewshots N5-N1 handcraft (18-20 examples FR→JP, 5 niveaux) | Research + Minna no Nihongo + Imabi | `fewshots/jp.yaml` |
| S11 | SYSTEM_PROMPT_JP + USER_PROMPT_TEMPLATE_JP **JLPT-native** (UI affiche N5-N1 via `display_level()`) | Synthesis | `llm.py` dispatch JP |

### Phase C — Dify + battery + alpha (7j)

| Semaine | Tâche | Livrable |
|---|---|---|
| S1 | Clone Teacher → Sensei Dify app + **prompts JLPT-native** (le chatbot parle N5-N1 au learner, pas A1-C1) | Sensei chatflow |
| S2 | Battery 5 personas JP FR-native N5-N1 + eval MultiGEC-2025 style | Pass rate ≥ 90% (target less strict que ES/IT/DE car langue distante) |
| S3 | Fix fails + activation alpha | `ENABLE_SENSEI=true` |

### Décisions JP (Session 29)

- **Système de niveau** : **JLPT N5-N1 natif** (storage interne a1-c2 via levels.py mapping).
- **Positionnement produit** : "Sensei t'aide à préparer N4 / N3 / N2 / N1" — learners JP reconnaissent ce langage, pas CEFR.
- **Keigo scope** : N5-N4 = teineigo (desu/masu) solide ; N3-N2 = introduction sonkeigo/kenjōgo patterns fréquents ; N1 = best-effort (documentation transparente).
- **Counters** : N5-N3 couverts (一人/二人/一本/二本 etc.) ; niveaux rares (丁目/番地) = best-effort N2-N1.
- **Aspect 〜ている** : N4+ couverts (progressive/resultant).
- **Fine-tune** : synthetic pretrain two-stage (Phase 0.8) + fine-tune léger sur I-JAS fragments et synthetic corpus.
- **Cost external** : **0€** (tout open).

### Critères de succès Wave 3

- [ ] Sensei JP HTTP 200 sur `/v1/chat-messages`
- [ ] Tokenization F1 ≥ 0.85 sur learner text mixed scripts
- [ ] Particle error detection F1 ≥ 0.70
- [ ] JLPT level display correct dans UI (N5-N1 visible, pas A1-C1)
- [ ] Alpha famille teste N5-N2 pendant 2 semaines
- [ ] Teacher + Maestro + Professore + Lehrer restent intacts
- [ ] F1 global ≥ 0.60 (variable par niveau, acceptable car mature dans écosystème JLPT)

### Note — Wave 3.5 supprimée

La Wave 3.5 (engagement $3-5K linguiste pour N3-N1) prévue en Session 27 est **SUPPRIMÉE** par le pivot Session 29. Le scope N3-N1 est désormais intégré dans Wave 3 unique, via JLPT-native resources open. Si qualité insuffisante constatée post-alpha, upgrade vers investissement linguiste natif reste une option business-déclenchée (pas par défaut).

---

## 6. Wave 4 — RU Maestro-RU TORFL-native (25-30j, ~6-8 semaines calendaire)

**Pivot Session 29** : abandonner le forcing CEFR pour RU. Utiliser **TORFL / ТРКИ (TEU-IV)** comme système de niveau natif — standard officiel du Ministère russe de l'éducation. Couverture **TEU-IV** (équivalent A1-C2). **Coût externe : 0€**.

**Scope** : TEU-TORFL-IV couvert dans écosystème natif TORFL. Limites honnêtes : aspect verbal niveau III+ et registres littéraires IV = best-effort (documentation transparente).

### Phase A — Infra RU (3-4j)

| Jour | Tâche | Livrable |
|---|---|---|
| J1 | **pymorphy2** / **pymystem3** integration pour morphologie russe | `academie_core/taxonomy/tokenizer_ru.py` |
| J2 | Normalisation cyrillique + transliteration tolérance | `normalize_ru(text)` function |
| J3 | Case detection via terminaisons (6 cases × 3 genres × 2 nombres) | Case extractor |
| J4 | Verb aspect detection (préfixes perfectifs, suffixes imperfectifs) | Aspect detector |

### Phase B — Content TORFL TEU-IV (15-18j)

| Semaine | Tâche | Source | Livrable |
|---|---|---|---|
| S1 | Télécharger **RLC brut** (Russian Learner Corpus HSE Moscow, ~7000 textes multi-L1) + **Russian National Corpus (RNC)** sample pour référence natif | web-corpora.net/RLC + ruscorpora.ru | Dataset learner + natif |
| S2 | **Email discovery non-bloquant UCA Nice** pour Russian Wheel RLC-French subcorpus (bonus si accès obtenu) | Dampierre-Debuchy contact | Emails envoyés, non-bloquant |
| S3 | **Rubrics TEU-IV** depuis **Gosstandart ТРКИ** descriptors + **Дорога в Россию** (Ministère Russia, aligné TORFL) + **Поехали** manuel intermédiaire | Gosstandart RU + Russian Ministry Education publications | `rubrics/ru.yaml` **TORFL-native TEU-IV** (clés internes a1-c2 via levels.py) |
| S4 | **Lexical Minimum** (Лексический минимум) officiel par niveau TORFL | Gosstandart publications | `data/ru/vocab_torfl.yaml` |
| S5 | **Grammatical Minimum** (Грамматический минимум) officiel par niveau TORFL | Gosstandart publications | `data/ru/grammar_torfl.yaml` |
| S6 | `curriculum_ru.yaml` — concepts TEU-IV (~80 concepts total) | Synthesis Phase B | `curriculum_ru.yaml` |
| S7 | **Errors typiques par niveau** depuis papers SLA RU open : HSE studies + **Guiraud-Weber** Aix-Marseille sur aspect verbal FR/RU | HAL + ResearchGate | Notes structurées FR→RU errors |
| S8 | **FR→RU seed theoretical** : cas (absents en FR), aspect verbal (absent en FR), genre masc/fém/neutre, verbes de mouvement | Contrastive grammar + Guiraud-Weber | `l1_transfer/fr_to_ru.yaml` |
| S9 | **Synthetic errors generation** GPT-4 guidé par TORFL descriptors (~$5-8 OpenAI) via `scripts/synthetic/generate_errors.py --lang ru` | TORFL descriptors TEU-IV | `train_v1_ru.jsonl` (5000 synth examples) |
| S10 | **Cross-lingual transfer** mT5-Large + MAD-X depuis EN+ES baseline → fine-tune léger RU | HuggingFace + MAD-X | `ft:ru-v1` model |
| S11 | `rules_ru.py` : détection cas par terminaisons, aspect par préfixe/suffixe, genre nominatif, accord adjectif-nom | pymorphy2 + synthesis | `rules_ru.py` |
| S12 | Fewshots TEU-III handcraft (18-20 examples FR→RU, 5 niveaux) | Research + Дорога в Россию + Поехали | `fewshots/ru.yaml` |
| S13 | SYSTEM_PROMPT_RU + USER_PROMPT_TEMPLATE_RU **TORFL-native** (UI affiche TEU/TBU/TORFL-I-IV via `display_level()`) | Synthesis | `llm.py` dispatch RU |

### Phase C — Dify + battery + alpha (5j)

| Semaine | Tâche | Livrable |
|---|---|---|
| S1 | Clone Teacher → Maestro-RU Dify app + **prompts TORFL-native** (chatbot parle TEU/TBU/TORFL-I-IV au learner, pas A1-C2) | Maestro-RU chatflow |
| S2 | Battery 5 personas RU FR-native TEU-TORFL-II + eval MultiGEC-2025 style | Pass rate ≥ 90% |
| S3 | Fix fails + activation alpha | `ENABLE_MAESTRO_RU=true` |

### Décisions RU (Session 29)

- **Système de niveau** : **TORFL TEU-IV natif** (storage interne a1-c2 via levels.py mapping).
- **Positionnement produit** : "Maestro-RU t'aide à préparer TORFL-I / TORFL-II" — standard russe reconnu internationalement.
- **Aspect verbal** : TEU-TORFL-I couvert basique, TORFL-II intermédiaire, III/IV = best-effort.
- **Cases** : détection morphologique via terminaisons fiable pour ~80% cas réguliers, exceptions best-effort.
- **Fine-tune** : synthetic pretrain two-stage (Phase 0.8) + fine-tune léger sur RLC fragments et synthetic corpus.
- **Russian Wheel UCA Nice** : email discovery non-contractuel (Phase 0.9). Bonus si accès obtenu, **non-bloquant** pour Wave 4.
- **Cost external** : **0€** (tout open Gosstandart ТРКИ + RLC open).

### Critères de succès Wave 4

- [ ] Maestro-RU HTTP 200 sur `/v1/chat-messages`
- [ ] Cases detection F1 ≥ 0.70 sur terminaisons régulières
- [ ] Aspect verbal detection F1 ≥ 0.60 sur préfixes perfectifs fréquents
- [ ] TORFL level display correct dans UI (TEU/TBU/TORFL-I-IV visible)
- [ ] Alpha famille teste TEU-TORFL-I pendant 2 semaines
- [ ] Teacher + Maestro + Professore + Lehrer + Sensei restent intacts
- [ ] F1 global ≥ 0.60 (variable par niveau)

### Note — Chemin A abandonné par défaut

Le Chemin A (€33-59K, linguiste SLA FR→RU + annotation ERRANT-like + grammar profile manuel) prévu en Session 28 est **abandonné par défaut** par le pivot Session 29. La stratégie TORFL-native atteint maturité dans écosystème russe sans cet investissement. Chemin A reste déclenchable si business traction forte (demande utilisateurs RU, partenariat institutionnel offert).

---

## 7. Timeline totale — 3 scénarios

### Scénario A — Séquentiel strict (solo dev, révisé Session 29)

```
Q2 2026 : Phase 0 infra   (15j → ~3 semaines, inclus levels.py + synthetic pipeline)
Q2 2026 : Wave 1 ES       (14-18j → ~4 semaines)
Q3 2026 : IT Professore   (22-28j → ~6-7 semaines)
Q4 2026 : DE Lehrer       (28-35j → ~8 semaines) [Profile Deutsch par Sinse]
Q1 2027 : JP Sensei JLPT-native N5-N1 (30-35j → ~8 semaines)
Q2 2027 : RU Maestro TORFL-native TEU-IV (25-30j → ~7 semaines)

Total : 14-18 mois calendaires, ~135-165j effort
Cost external : 40€ (Profile Deutsch) + ~$30 OpenAI synthetic
```

### Scénario B — Hybride recommandé (révisé Session 29)

```
Q2 2026 :
  - Phase 0 infra            (15j → ~3 semaines, inclus levels.py + synthetic pipeline)
  - Wave 1 ES validation     (14-18j → ~4 semaines, inclus fine-tune synth +3j)
  TOTAL Q2 : ~7 semaines

Q3 2026 (overlap S8 calendaire) :
  - Wave 2 IT+DE parallèle  (39-46j → ~11 semaines, Profile Deutsch Sinse + fine-tune synth +6j)
  TOTAL Q3 : ~11 semaines

Q4 2026-Q1 2027 :
  - Wave 3 JP Sensei JLPT-native  (30-35j → ~8 semaines, N5-N1 dans Wave unique)
  TOTAL : ~8 semaines

Q2 2027 :
  - Wave 4 RU Maestro-RU TORFL-native  (25-30j → ~7 semaines)

Total 5 langues (EN/ES/IT/DE/JP/RU) : ~125-150j effort, 10-13 mois calendaires
Cost external : 40€ (Profile Deutsch) + ~$30 OpenAI synthetic
```

### Scénario C — All-parallel (≥2-3 devs ou agents concurrents, révisé Session 29)

```
Q2 2026 :
  - Phase 0 infra (shared, 15j)
  - Wave 1 ES (dev A, 14-18j)

Q3 2026 (sprint massif) :
  - Wave 2 IT (dev A, 22-28j)
  - Wave 2 DE (dev B, 28-35j)
  - Wave 3 JP Phase A infra JLPT-native (dev C, 8-10j)

Q4 2026 :
  - Wave 3 JP Phase B+C JLPT-native (dev C continues, 22-25j)
  - Wave 4 RU Phase A TORFL-native (dev B, 3-4j) + Phase B démarre

Q1 2027 :
  - Wave 4 RU Phase B+C TORFL-native (dev B, 22-26j)

Total : 6-7 mois calendaires, ~180j effort cumulé (hire nécessaire)
Cost external : 40€ + ~$30 OpenAI synthetic
```

---

## 8. Critical path (dépendances strictes)

```
┌─────────────────┐
│   Phase 0       │  (bloque tout, 15j révisé Session 29)
│   - Dify cloner │
│   - GLMM param  │
│   - Rules disp  │
│   - Battery par │
│   - Tokenizer   │
│   - Levels.py   │  (nouveau, JLPT/TORFL mapping)
│   - Synthetic   │  (nouveau, generator pipeline)
│   - Discovery   │  (nouveau, emails non-bloquants)
└────────┬────────┘
         ↓
┌─────────────────┐
│   Wave 1 ES     │  (bloque Wave 2, proof of concept)
│   14-18j CEFR   │
└────────┬────────┘
         ↓
┌─────────────────┐
│   Wave 2 IT+DE  │  (factorisé parallèle, CEFR)
│   39-46j        │
└────────┬────────┘
         ↓
┌──────────────────┐          ┌──────────────────┐
│   Wave 3 JP      │   OR     │   Wave 4 RU      │
│   JLPT-native    │ parallel │   TORFL-native   │
│   30-35j N5-N1   │          │   25-30j TEU-IV  │
└──────────────────┘          └──────────────────┘
```

**Seules les dépendances dures** (impossible de paralléliser) :
- Phase 0 avant tout le reste (Dify cloner + levels.py nécessaires pour chaque langue)
- Wave 1 ES avant Wave 2 (pipeline validé sur 1 langue avant industrialiser)

Tout le reste peut paralléliser si ressources disponibles.

---

## 9. Décisions stratégiques (validées Session 29)

### 1. RU : stratégie TORFL-native intégrée [RÉVISÉE Session 29]

**Ancienne décision (Session 27)** : defer RU jusqu'à Q2 2027+.

**Nouvelle décision (Session 29)** : **Wave 4 engagée** avec stratégie **TORFL-native 0€** (25-30j). Ancien blocage (zero FR→RU SLA, grammar profile absent) résolu par pivot : utilisation système officiel russe (Gosstandart ТРКИ) au lieu de forcer CEFR. Chemin A €33-59K abandonné par défaut, déclenchable si business traction.

### 2. Solo dev ou hire ?

**Si solo Claude** : scénario B hybride, 10-13 mois.
**Si hire 1 dev additionnel** : scénario C parallel, 6-7 mois mais coût hire.

**Recommandation** : **solo Claude + scénario B** pour commencer, évaluer hire après Wave 2.

### 3. ES first ou parallel direct ?

**ES first** (recommandé) : valide pipeline, moins de risk, drafts déjà là.
**Parallel direct** : plus rapide mais risk fragmentation qualité.

**Recommandation** : **ES first** (Wave 1 avant Wave 2).

### 4. JP : stratégie JLPT-native intégrée [RÉVISÉE Session 29]

**Ancienne décision (Session 27)** : MVP N5-N4 Wave 3 + engagement ferme Wave 3.5 N3-N1 avec budget $3-5K linguiste.

**Nouvelle décision (Session 29)** : **Wave 3 unique JLPT-native 0€** (30-35j) couvrant **N5-N1 complet** dans écosystème natif JLPT. Ressources open Japan Foundation + Tae Kim + Imabi + JLPT listes officielles suffisent. Wave 3.5 séparée **supprimée** — N3-N1 inclus dans Wave 3.

**Limites honnêtes acceptées** : keigo niveau N1 = best-effort, aspect littéraire = best-effort. Documentation transparente dans produit. Upgrade business-déclenché reste possible si qualité insuffisante constatée post-alpha.

### 5. Fine-tune synthétique two-stage [VALIDÉE Session 28-29]

**Décision** : **fine-tune synthétique two-stage (Latouche EMNLP 2024) dès Wave 1** pour toutes les langues.

**Process par langue** :
1. **Stage 1 — Synthetic pretrain** : 5000 examples générés via GPT-4 guidés par descriptors natifs (CEFR pour EN/ES/IT/DE, JLPT pour JP, TORFL pour RU) + corpus learner/research sources.
2. **Stage 2 — Fine-tune** : OpenAI API → `ft:gpt-4o-mini-...academie-errors-{lang}-v1`.
3. Cross-lingual transfer optionnel via mT5 + MAD-X pour langues distantes (JP/RU).

**Coût** : ~$25-35 cumulé pour 5 langues (ES/IT/DE/JP/RU) OpenAI fine-tune. Budget négligeable.

### 6. Timeline agressive (6-7 mois) ou confortable (10-13 mois) ?

Dépend disponibilité ressources. Si solo Claude : confortable obligatoire. Si hire : agressive possible.

**Recommandation** : **confortable 10-13 mois** (scénario B) solo.

### 7. Stratégie niveaux natifs vs CEFR forcé [NOUVELLE Session 29]

**Décision** : **niveaux natifs** pour langues non-européennes (JP = JLPT, RU = TORFL), **CEFR** pour européennes (EN/ES/IT/DE).

**Pourquoi** :
- Learners JP/RU utilisent naturellement JLPT/TORFL, pas CEFR.
- Ressources pédagogiques officielles JLPT/TORFL sont **gratuites et complètes** (Japan Foundation, Gosstandart ТРКИ).
- Forcer CEFR pour JP/RU nécessiterait construction grammar profile manuel = $3-59K externe.
- Mapping interne a1-c2 conservé pour analytics cross-lang.

**Architecture** : `academie_core/levels.py` module mappe JLPT/TORFL↔CEFR. Storage interne reste unifié, UI et prompts utilisent système natif par domaine. Voir Phase 0.7.

---

## 10. Next steps immédiats (cette semaine)

Après validation de ce plan par Sinse :

### Immédiat (prochain pickup)

1. [ ] **Décisions** : trancher les 6 questions Section 9
2. [ ] **Phase 0 démarrage** : commencer par 0.1 Dify cloner (bloque tout)
3. [ ] **Wave 1 ES** : une fois 0.1 done, attaquer J1 PCIC deep dive

### Court terme (2 semaines)

- [ ] Phase 0 complète (10j effort)
- [ ] Wave 1 ES J1-J7 (rubrics + CEDEL2 + SLA enrichissement)

### Moyen terme (1 mois)

- [ ] Wave 1 ES J8-J15 (Dify Maestro + battery + activation alpha)
- [ ] Monitor 1 semaine famille
- [ ] Kick-off Wave 2 IT+DE si ES validé

### Long terme (6 mois)

- [ ] Wave 2 IT+DE en prod alpha
- [ ] Kick-off Wave 3 JP infra (Phase A)
- [ ] Décision finale RU

---

## Annexe — Règles d'or

1. **Une langue ne démarre pas sans Phase 0 (pour elle) complète**
2. **ES valide le pipeline avant d'industrialiser** (Wave 1 strict prerequisite)
3. **Chaque wave livre un alpha famille** (pas de lab permanent)
4. **Feature flag OFF par défaut** jusqu'à validation alpha (zero risk prod)
5. **error_log populé dès le premier user** (feedback loop = base Wave n+1)
6. **Pas de native speaker bloquant** (recherche online + corpus + alpha famille suffisent)
7. **Chaque source consultée produit ≥ 1 artefact concret** (YAML entry, rule, fewshot, weight)
8. **Chaque wave teste régression non-regression** sur langues précédentes (smoke test obligatoire)
9. **Fine-tune synthétique dès première activation** (pas d'attente 500 msgs réels, contexte familial)
10. **Chaque langue avec MVP scope doit avoir son extension Wave n.5 schedulée** (pas "peut-être plus tard")

---

_Document produit Session 27, synthèse multilang_research_plan.md + experience Sprint 5._
