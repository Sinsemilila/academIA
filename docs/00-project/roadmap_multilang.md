---
status: superseded
superseded_by: ADR-013-language-scope-by-tier (2026-04-29) + ADR-016-authority-anchor-cross-lang (2026-04-29)
last_reviewed: 2026-05-01
note: 'Doc research/planning multilang Phase 0 (S26-S33). Conservé pour cross-reference ADRs. Roadmap canonique actuelle = TODO.md macro section + ADR-013/016.'
---

# Roadmap Multi-Langue — AcademIA

_Produit par agent d'exploration — 2026-04-18_

## TL;DR

| Langue | Agent | Effort total | Priorité |
|---|---|---|---|
| Espagnol | Maestro | ~13j (+ 3j one-time infra) | 1 |
| Italien | Professore | ~12j | 2 |
| Allemand | Lehrer | ~14-15j | 3 |
| Japonais | Sensei | ~22-26j | 4 |

**Infrastructure one-time (bénéficie à toutes les langues) : ~6-7j**

---

## PARTIE 1 — Ce qui est language-agnostic (zéro changement)

### academie-core
- **`domain/base.py`** — Protocol + tous les dataclasses (`GravityAxes`, `Tier`, `Error`, `UserContext`, `PromptContext`, `FeedbackPlan`, `StructuredResponse`, `Progression`, `Snapshot`). Neutre par design.
- **`domain/language.py`** — `LanguageDomain` lui-même : paramétré par `lang_target` à l'instantiation. Toutes les méthodes (`detect_errors`, `score_tier`, `compute_progression`, `build_dynamic_sections`, `parse_response`, `pedagogical_feedback`) sont agnostiques.
- **`taxonomy/differ.py`** — moteur diff edit-distance sur token sequences. Unicode-safe (JP/DE/IT).
- **`taxonomy/scoring.py`** — moteur de scoring complet (`enrich_error_fields`, `compute_error_profile`). Lit depuis YAML config. Zéro hardcoding langue.
- **`taxonomy/categories.py`** — les 57 codes (`TIER1_CATEGORIES`, `TIER1_DOMAINS`) mappent vers des familles grammaticales universelles. Applicable cross-linguistiquement (sauf JP qui nécessite additions).
- **`pedagogy/teacher_prompt.py`** — tout le moteur pédagogique est agnostique : `DOSAGE_BUDGET`, `TIER_TO_FEEDBACK_DEFAULT`, `arbitrate_dosage()`, `tier_to_feedback_type()`, `should_inject_level_reminder()`, `build_spaced_retrieval_block()`, `select_fewshots()`, `OUTPUT_SCHEMA_BLOCK`, `parse_teacher_response()`, `build_dynamic_sections()`. Le LLM écrit le `feedback` dans la langue cible par instruction, pas par contenu hardcodé.

### Infrastructure webapp
- `chat_router.py` — rate limiting, token budget, streaming, session tracking, XP log, spaced retrieval queue. Rien n'est EN-spécifique.
- Dify infra, LiteLLM proxy, n8n webhooks — les patterns HTTP et la gestion des réponses ne sont pas EN-spécifiques.
- Schema DB — `error_log`, `profils_eleves`, `spaced_retrieval_queue`, `user_sessions`, `curriculums`, `token_usage_daily`. Toutes les tables ont déjà une colonne `domaine` (actuellement `'anglais'`).

---

## PARTIE 2 — Ce qui est language-specific (doit être construit par langue)

### 2.1 Rubrics (`data/rubrics/{lang}.yaml`)
- **Ce qui existe** : dict `RUBRICS` dans `teacher_prompt.py` L83-161 (EN only, hardcodé Python).
- **Format** : YAML avec 6 entrées A1→C2 (~150 mots par niveau).
- **Contenu** : objectif communicatif par niveau CEFR, règles de tolérance par tier, anti-patterns, structures cibles spécifiques à la langue.
- **Sources** : ES=PCIC (Cervantes, open), DE=Profile Deutsch, IT=Sillabo CILS, JP=JF Standard.
- **Effort** : 1-2j par langue.

### 2.2 Couche règles (`rules_{lang}.py`)
- **Ce qui existe** : `rules.py` est quasi-entièrement EN-spécifique (FRENCH_COGNATES, PREP_CALQUES, CONTRACTION_MAP, LEX_CALQUE_PATTERNS, IRREGULAR_PAST_ERRORS, GERUND_VERBS…).
- **Ce qui est réutilisable** : `RuleDetection` et `ClassifiedError` dataclasses. `ORTH:CASE` pour langues à alphabet latin. `ORTH:SPACE` (universel).
- **Format** : `rules_{lang}.py` avec signature `detect_errors(text) -> list[RuleDetection]`. Dispatch dans `LanguageDomain.__init__` par `lang_target`.
- **Effort** : ES=3-4j, IT=3j, DE=4-5j, JP=7-10j (tokeniseur non-Latin requis).

### 2.3 Prompt LLM analyse erreurs (`taxonomy/llm.py` dispatch)
- **Ce qui existe** : `SYSTEM_PROMPT` L22 est "French speakers learning English". Le modèle fine-tuné `ft:gpt-4o-mini-2024-07-18:personal:academie-errors-v3` est EN-only.
- **Format** : system prompt + user prompt template par langue. Codes déjà neutres ; seuls les exemples et le framing changent. Fine-tune par langue : différé post-MVP ; base model (gpt-4o-mini) suffit au lancement.
- **Effort** : ES=2j, IT=2j, DE=2j, JP=3j.

### 2.4 Tolerance matrix (`data/tolerance_matrix/{lang}.yaml`)
- **Ce qui existe** : `tolerance_matrix_v2.yaml` calibré sur W&I BEA-2019 (EN, 2598 learners). Famille `calque` = "Calques français" → EN-spécifique.
- **Shortcut au lancement** : copier matrice EN, renommer famille calque, ajouter familles lang-spécifiques, flag `status: prior_only` dans header YAML. Recalibrer avec corpus dans sprint suivant.
- **Sources corpus** : ES=CEDEL2 (open, ~1M mots), DE+IT=MERLIN corpus (open), JP=JLPT/JF Standard (access limité).
- **Effort** : ES/IT/DE=1j, JP=2j.

### 2.5 Few-shots (`data/fewshots/{lang}.yaml`)
- **Ce qui existe** : `FEWSHOT_BANK` dans `teacher_prompt.py` L413-463 (14 exemples, tous EN).
- **Format** : 12-14 few-shots synthétiques par langue (2 par niveau CEFR, couvrant `silent`, `implicit_recast`, `elicitation`, `metalinguistic`, `prompt_plus_remediation`).
- **Effort** : 1j par langue.

### 2.6 L1 Transfer (`data/l1_transfer/{L1}_to_{lang}.yaml`)
- **Ce qui existe** : `L1_TRANSFER_SEED` dans `teacher_prompt.py` L337-352 — uniquement `fr→en` (5 familles avec multiplicateurs). Répertoire `data/l1_transfer/` vide.
- **Format** : YAML par paire L1→cible. Paires prioritaires : `fr→{lang}` (base francophone), puis `en→{lang}`. 3-8 familles par fichier.
- **Effort** : fr→ES=0.5j, fr→IT=0.5j, fr→DE=0.5-1j, fr→JP=1-1.5j.

### 2.7 Curriculum (`curriculum_{lang}.yaml` + seed DB)
- **Ce qui existe** : 92 concepts EN dans table `curriculums`. Source `/opt/academie-shared/curriculum_en.yaml`.
- **Format** : YAML avec concept keys, niveau CEFR, weight, family mapping. Même structure qu'EN.
- **Sources** : EGP (EN), PCIC (ES), Profile Deutsch (DE), CILS sillabo (IT), JF Standard (JP).
- **Effort** : ES/IT/DE=1-1.5j, JP=2.5j.

### 2.8 Persona + Onboarding (Dify chatflow)
- **Ce qui existe** : Teacher EN onboarding 2-phase (FR turns 1-3, EN diagnostic turns 4-10+), 6 types de questions.
- **Format** : persona text + 10 questions diagnostiques par niveau pour le placement test.
- **Effort** : 1-1.5j par langue.

### 2.9 DB `profils_eleves` + n8n webhooks
- **Problème** : `chat_router.py` hardcode `domaine = 'anglais'` aux lignes 441, 522, 380.
- **Solution** : dériver `domaine` depuis `req.agent` (e.g., `"maestro"` → `"espagnol"`). Vérifier que `profils_eleves` a `(eleve_id, domaine)` comme contrainte unique.
- **Effort** : one-time 0.5j refactor + 0.5j vérification n8n par langue.

---

## PARTIE 3 — Tableaux par langue

### ES — Espagnol / Maestro (~13j + 3j one-time)

| Composant | Statut | Effort | Notes |
|---|---|---|---|
| `rubrics/es.yaml` | Manquant | 1.5j | Source: PCIC. Delta: subjonctif B1, ser/estar, accord de genre. |
| `rules_es.py` | Manquant | 3-4j | Accords adj/nom, triggers subjonctif (B1+), ser vs estar, calques EN→ES. |
| Prompt LLM ES | Manquant | 2j | SPAN:GENDER, SPAN:SUBJ, ser/estar. Fine-tune différé. |
| `tolerance_matrix/es.yaml` | Manquant | 1j | Copier v2, ajouter SPAN:GENDER+SUBJ. Source: CEDEL2. |
| `fewshots/es.yaml` | Manquant | 1j | 2 par niveau. Erreurs clés: subjonctif (B1/B2), ser/estar (A2/B1). |
| `l1_transfer/fr_to_es.yaml` | Manquant | 0.5j | Faux amis, por/para, subjonctif absent en FR. |
| `l1_transfer/en_to_es.yaml` | Manquant | 0.5j | Subjonctif, accord de genre, verbes réfléchis, gustar. |
| `curriculum_es.yaml` | Manquant | 1.5j | ~80 concepts. Source: PCIC. |
| `language-tutor` chatflow Dify | Manquant (one-time) | 2-3j | Partagé avec toutes les langues. |
| Clone chatflow + `DIFY_KEY_MAESTRO` | Manquant | 0.5j | Après `language-tutor`. |
| Routing `chat_router.py` | Stub | 0.5j | `_DOMAIN_BY_AGENT` registry. |
| `LanguageDomain("es")` | Manquant | 0.25j | Une ligne Python. |
| Persona + onboarding | Manquant | 1j | Maestro persona + 10 questions diagnostiques ES. |
| n8n `domaine=espagnol` | Partiel | 0.5j | Vérifier param `domaine` dans workflows. |

### IT — Italien / Professore (~12j)

| Composant | Statut | Effort | Notes |
|---|---|---|---|
| `rubrics/it.yaml` | Manquant | 1j | Source: CILS sillabo. Accord de genre A1, subjonctif B1. |
| `rules_it.py` | Manquant | 3j | Accord adj/nom, essere/avere, subjonctif, pronoms doubles. |
| Prompt LLM IT | Manquant | 1.5j | IT:GENDER, IT:SUBJ, IT:AUX. |
| `tolerance_matrix/it.yaml` | Manquant | 1j | Source: MERLIN (sous-corpus IT). |
| `fewshots/it.yaml` | Manquant | 1j | Être/avere (A2), subjonctif (B1/B2). |
| `l1_transfer/fr_to_it.yaml` | Manquant | 0.5j | Langues très proches. Faux amis, prépositions a/in. |
| `curriculum_it.yaml` | Manquant | 1j | ~75 concepts. Source: CILS sillabo. |
| Clone chatflow + routing + Domain | Manquant | 1.5j | (chatflow one-time déjà fait avec ES) |
| Persona + onboarding + n8n | Manquant | 1.5j | |

### DE — Allemand / Lehrer (~14-15j)

| Composant | Statut | Effort | Notes |
|---|---|---|---|
| `rubrics/de.yaml` | Manquant | 1.5j | Source: Profile Deutsch. V2 order A1, cas A1 (Nom/Akk), Dat A2, Gen B1. |
| `rules_de.py` | Manquant | 4-5j | Déclinaisons (der/die/das/den/dem), V2 order, verbes séparables, terminaisons adj. |
| Prompt LLM DE | Manquant | 2j | DE:CASE, DE:V2, DE:SEP. |
| `tolerance_matrix/de.yaml` | Manquant | 1j | Source: MERLIN (sous-corpus DE). |
| `fewshots/de.yaml` | Manquant | 1j | V2 (A1/A2), Akkusativ (A2), Dativ (B1), Konjunktiv II (B2+). |
| `l1_transfer/fr_to_de.yaml` | Manquant | 0.5j | 3 genres vs 2, système de cas absent en FR, V2, verbes séparables. |
| `curriculum_de.yaml` | Manquant | 1.5j | ~80 concepts. Source: Profile Deutsch. |
| Clone chatflow + routing + Domain | Manquant | 1.5j | |
| Persona + onboarding + n8n | Manquant | 1.5j | |

### JP — Japonais / Sensei (~22-26j)

| Composant | Statut | Effort | Notes |
|---|---|---|---|
| `rubrics/jp.yaml` | Manquant | 2j | Source: JF Standard. Keigo, SOV, mapping CEFR non-trivial. |
| `rules_jp.py` | Manquant | 7-10j | **Requiert MeCab/SudachiPy**. Particules (は/が/を/に/で), keigo, classifieurs. |
| Prompt LLM JP | Manquant | 3j | JP_PARTICLE, JP_KEIGO, JP_COUNT nouveaux codes. |
| `tolerance_matrix/jp.yaml` | Manquant | 2j | Nouvelles familles: particles, keigo, kanji_reading, classifiers. |
| `fewshots/jp.yaml` | Manquant | 1.5j | En japonais. Particule は vs が (A2), て-form (A2), keigo (B1+). |
| `l1_transfer/fr_to_jp.yaml` | Manquant | 1.5j | Langues maximalement distantes. SOV, absence articles, temps/aspect entièrement différent. |
| `curriculum_jp.yaml` | Manquant | 2.5j | ~70 concepts. Hiragana/Katakana comme prérequis. Alignement JLPT N5→N1. |
| Clone chatflow + routing + Domain | Manquant | 1.5j | |
| Persona + onboarding + n8n | Manquant | 2j | Rendu des caractères japonais dans Dify. |

---

## PARTIE 4 — Infrastructure one-time (~6-7j)

| Tâche | Effort | Ce que ça débloque |
|---|---|---|
| Construire chatflow `language-tutor` Dify (coquille minimaliste paramétrée) | 2-3j | Chaque nouvelle langue réutilise ce chatflow. Remplace le Teacher EN 41-nœuds actuel. |
| Refactoriser `chat_router.py` : paramétrer `domaine` depuis `req.agent` | 0.5j | Actuellement hardcodé `domaine = 'anglais'` aux L441, L522, L380. Devient lookup `_AGENT_TO_DOMAIN[req.agent]`. |
| Ajouter registry `_DOMAIN_BY_AGENT` dans `chat_router.py` | 0.25j | Remplace singleton `_TEACHER_DOMAIN = LanguageDomain("en")` L38 par dict lookup. |
| Refactoriser `LanguageDomain.__init__` pour charger rules/rubrics/fewshots par `lang_target` | 1j | `detect_errors` appelle aujourd'hui `_detect()` EN-only. Dispatch: `self._rule_fn = _RULES_BY_LANG.get(lang_target)`. Idem rubrics/fewshots. |
| Migrer `RUBRICS`, `FEWSHOT_BANK`, `L1_TRANSFER_SEED` de Python hardcodé vers YAML `data/` | 1j | Ces dicts dans `teacher_prompt.py` L83-161/L413-463/L337-352 doivent être externalisés pour que les nouvelles langues puissent ajouter des données sans toucher au Python. |
| Étendre `build_l1_watch()` pour lire depuis YAML | 0.5j | Actuellement lit le dict `L1_TRANSFER_SEED` L366. Doit lire `data/l1_transfer/{l1}_to_{lang}.yaml`. |
| Audit n8n webhooks : vérifier param `domaine` géré | 0.5j | `dify-profil-get`, `dify-snapshot`, `dify-profil-update`, `dify-diagnostic` — tous doivent gérer des valeurs `domaine` arbitraires. |
| DB: vérifier contrainte PK `profils_eleves` (multi-langue par apprenant) | 0.25j | Probablement `(eleve_id, domaine)` comme clé unique, pas juste `eleve_id`. |

---

## PARTIE 5 — Ordre de priorité suggéré

**ES → IT → DE → JP**

### Raisonnement
1. **ES** : 2e langue mondiale, typologiquement proche du FR (L1 dominante des utilisateurs), CEDEL2 open et large, PCIC le plus complet des 4 curricula disponibles.
2. **IT** : proche de FR et ES, une fois la couche rules ES créée, IT réutilise ~60% des patterns. MERLIN couvre IT. Pas de système de cas.
3. **DE** : système de cas et V2 word order créent une couche rules plus complexe mais hautement systématique (bons patterns regex). MERLIN DE open.
4. **JP** : requiert tokeniseur non-Latin (MeCab/SudachiPy), extension taxonomique entière (particles, keigo, classifiers), mapping JLPT→CEFR approximatif. Sprint dédié.

### Multiplicateurs de complexité

| Langue | Morphologie | Écriture | Distance L1-FR | Multiplicateur rules |
|---|---|---|---|---|
| ES | Faible (2 genres, 0 cas) | Latin | 0.2 (très proche) | ×0.8 |
| IT | Faible (2 genres, 0 cas) | Latin | 0.3 | ×0.75 |
| DE | Haute (3 genres, 4 cas, V2) | Latin | 0.5 | ×1.2 |
| JP | Très haute (agglutinant, keigo, classifieurs) | Non-Latin (3 scripts) | 1.0 (max) | ×2.5 |

### Plan de sprints suggéré

| Sprint | Contenu | Livrable |
|---|---|---|
| S5-infra | Refactor one-time : `language-tutor` chatflow, paramétrage `chat_router.py`, externalisation YAML rubrics/fewshots/l1_transfer | Foundation. Teacher EN inchangé (garde son chatflow comme fallback). |
| S5-ES | Couche data Maestro : `rubrics/es.yaml`, `rules_es.py`, `tolerance_matrix/es.yaml`, `fewshots/es.yaml`, `curriculum_es.yaml`, `l1_transfer/fr_to_es.yaml` | Maestro alpha (test famille). |
| S6-IT | Couche data Professore | Professore alpha. |
| S7-DE | Couche data Lehrer (effort rules système de cas) | Lehrer alpha. |
| S8-JP | Couche data Sensei (tokeniseur + nouvelles familles taxonomiques) | Sensei alpha. |

Chaque alpha = chatbot fonctionnel A1-B1 avec couverture règles déterministes, LLM fallback pour niveaux supérieurs, L1 watch actif pour apprenants FR.

---

## Fichiers clés à modifier

| Fichier | Changement one-time |
|---|---|
| `packages/academie-core/academie_core/domain/language.py` | Dispatch rules/rubrics/fewshots par `lang_target` |
| `packages/academie-core/academie_core/pedagogy/teacher_prompt.py` | Externaliser L83/L413/L337 vers YAML |
| `packages/academie-core/academie_core/taxonomy/rules.py` | Refactoriser en `detect_errors_en()` + dict dispatch |
| `packages/academie-core/academie_core/taxonomy/llm.py` | Paramétrer system prompt L22 |
| `webapp/backend/app/routers/chat_router.py` | `DIFY_APP_KEYS` + `_TEACHER_DOMAIN` → `_DOMAIN_BY_AGENT` + L441/L522/L380 |

_Répertoires à peupler_ : `data/rubrics/`, `data/fewshots/`, `data/l1_transfer/` (tous vides aujourd'hui).
