---
title: Plan d'action recherche multi-langue — ES/IT/DE/JP/RU
date: 2026-04-18
status: superseded
superseded_by: ADR-013-language-scope-by-tier (2026-04-29) + ADR-016-authority-anchor-cross-lang (2026-04-29)
last_reviewed: 2026-04-19
author: Claude (Opus 4.7) — Session 27 + Session 29 (pivot JP/RU native JLPT/TORFL)
---

# Plan d'action recherche multi-langue AcademIA

**Contexte** : Teacher EN a été bâti via pipeline rigoureux (corpus learner → GLMM → EGP rubrics → rules + prompts + fewshots → fine-tune v3 → battery). Pour les autres langues, on applique **la même méthodologie** avec sourcing equivalents. Ce doc synthétise le pipeline EN comme template reproductible + plan d'action concret par langue.

---

## PART 1 — Pipeline Teacher EN (méthodologie template, 12 étapes)

| # | Étape | Source externe | Artefact | Effort EN |
|---|---|---|---|---|
| 1 | **Corpus learner download + normalize** | W&I+LOCNESS (BEA 2019, 2671 learners) + NUCLE (5249) = 7920 total via ERRANT M2 annotations | `scripts/sprint1/*.py` + `errant_to_academie.yaml` + 70k erreurs mappées parquet | 3-5j |
| 2 | **Calibration statistique** | GLMM hiérarchique bayésien (NumPyro NUTS 2 chains 1000+1000, R-hat 1.01, ESS 429, 0 divergences) sur β_tier × niveau × famille | `glmm_posterior.nc`, `weights_from_posterior.json`, `tolerance_matrix_v2.yaml` | 3-5j |
| 3 | **Tolerance matrix v2 + review adversariale** | 12 familles × 6 niveaux CEFR = 72 cellules ; review SLA literature (Lyster & Saito, Lardiere) = 19 ACCEPT / 1 FLAG / 1 OVERRIDE | `tolerance_matrix_v2.yaml` + `tolerance_matrix_v2_overrides.yaml` + `matrix_v2_review.md` | 2j |
| 4 | **Rubrics CEFR A1-C2** | **English Grammar Profile (EGP, Cambridge, 1222 criterial features)** + CEFR Companion Volume 2020 | `data/rubrics/en.yaml` (6 niveaux × ~150 mots, objectif + tolérance + structures cibles + anti-patterns) | 3-5j |
| 5 | **Framework pédagogique** | **Lyster & Ranta 1997** (6 feedback types) + **Lyster & Saito 2010** (d=1.16 prompts vs 0.71 recasts) + **Swain Output Hypothesis** + **Cowan 2001** (WM ≈ 4 items) + **Pienemann Teachability** | `docs/01-pedagogy/{feedback-delivery, taxonomy-framework, bibliography}.md` + `DOSAGE_BUDGET` dict | 2j (invariant cross-lang) |
| 6 | **Rules deterministic detection** | Dictionnaires SPACING_ERRORS, FRENCH_COGNATES (52), PREP_CALQUES, CONTRACTION_MAP, LEX_CALQUE_PATTERNS (14 regex), IRREGULAR_PAST, PROPER_NOUNS (40) | `taxonomy/rules.py` (764 lignes, 100% precision, 57/63 codes = 90.5% recall) | 5-8j |
| 7 | **Fewshots (24 examples A1-C2)** | Handcraft 4 personas × 6 niveaux + Lyster-mapped diversity rule + gravity override demos | `data/fewshots/en.yaml` (14 selected) + `sprint3_fewshots.md` (24 complets) | 3-5j |
| 8 | **L1 transfer FR→EN** | URIEL/lang2vec typological distances (Littell 2017) + Selinker interlanguage 1972 + Jarvis & Pavlenko 2008 | `data/l1_transfer/fr_to_en.yaml` (5 familles × multiplicateur) | 2j |
| 9 | **Curriculum EN (92 concepts)** | EGP 1222 features → clustered par niveau CEFR + emergence vs mastery empirique W&I | `data/curriculum_en.yaml` + `data/concept_hints/en.yaml` (92 concepts × hints ~30 mots) | 2-5j |
| 10 | **Fine-tune v3 academie-errors** | 5000 training examples générés via GPT-4 + 6 fusion catégories + W&I balanced validation → OpenAI fine-tuning API | `ft:gpt-4o-mini-...academie-errors-v3:DU6GUv6v` (F1 85%) | 2-3j |
| 11 | **Battery + eval** | 4 personas × 10 turns + 6 edge cases = 46 turns, 273 checks (JSON validity, dosage, tier mapping, diversity, anti-drift, drift self-grade) | `eval_personas.py` + `eval_live_battery.py` + report 99.4% GREEN | 3-5j |
| 12 | **Prompts Dify (41 nodes)** | CoT + few-shot + output schema Pydantic + re-injection anti-drift (Pak et al. 2025) | `teacher_prompt.py` (500L) + `update_teacher_chatflow.py` | 0j (auto per lang) |

**Total Teacher EN** : ~45 jours cumulés (Sprint 1 + 1.5 + 2 + 3 + infra Sprints 4-6). Sources toutes **open access** (W&I/NUCLE/EGP) + **research papers** indexés.

---

## PART 2 — Plan d'action par langue

### 🟢 ES — MAESTRO (content pack DRAFT déjà mergé)

**Situation actuelle** : Phase 4 Sprint 5 complétée, YAMLs drafts sur main gated par `ENABLE_MAESTRO=true`. Reste l'**enrichissement via recherche** (pas de native speaker requis — même playbook que Teacher EN).

**Ressources identifiées** :

| Étape pipeline | Ressource ES | Accès | Effort |
|---|---|---|---|
| 1. Corpus learner | **CEDEL2** (Univ Granada, 6560 learners, 1.5M tokens, 15 L1s dont français, CC BY-NC-ND 3.0) | ✅ Open, télécharg. | 3-4j |
| 1bis. Complément | **CAES** (Instituto Cervantes + Santiago Compostela, 1.4M tokens, 11 L1s dont FR) | ⚠️ 404 actuellement, vérifier | 3-4j |
| 1ter. Annotations | **COWS-L2H** (UC Davis, 500 essays, 6 error types annotés) | ✅ GitHub public | 2j |
| 2. Calibration FR→ES | GLMM sur CEDEL2 French subcorpus | ✅ Même pipeline que Sprint 1 | 3-5j |
| 3. Tolerance matrix | Adapter 12 familles (+ SPAN:GENDER, SPAN:SUBJ, SPAN:SER_ESTAR) | ✅ template EN | 1j |
| 4. Rubrics | **PCIC** (Plan Curricular Instituto Cervantes, 3 volumes A1-C2, 13 inventaires : Gramática, Funciones, Nociones, etc.) | ✅ Open cvc.cervantes.es | 5-7j |
| 5. Framework | Lyster & Ranta (invariant) | — | 0j |
| 6. Rules | Adapter FRENCH_COGNATES → SER_ESTAR detection, POR_PARA, GENDER, ORTH:NY, PUNCT:INTERROG | ⚠️ Partiellement fait (rules_es.py squelette) | 3-4j restant |
| 7. Fewshots | 24 examples handcraft FR→ES typiques (embarazada, gustar, subj) | ⚠️ Partiellement fait (14 drafts) | 2-3j restant |
| 8. L1 transfer | **Bruhn de Garavito 1986, 2002, 2010+** (FR→ES gender/number), **Lardiere 2009**, **Montrul 2018/2022**, **Collentine 2010** (subj), **Geeslin** (ser/estar) | ✅ Papers indexés | 3-5j |
| 9. Curriculum | PCIC inventaires → 80 concepts ES mappés CEFR | ⚠️ Partiellement fait (52 drafts) | 2j restant |
| 10. Fine-tune (optionnel) | Générer 5000 examples ES synthétiques ou rester base `gpt-4o-mini` (Option B audit) | 🟡 Défere sprint +1 | 2-3j (optionnel) |
| 11. Battery | Adapter 4 personas ES + edge cases culturellement adaptés | — | 3-5j |
| 12. Prompts Dify | Cloner Teacher graph → nouveau app "Maestro" + traduction prompts ES natifs | 🔄 À faire | 2-3j |
| **Autoritaires** | **RAE + Asale** : Nueva Gramática, Diccionario Panhispánico de Dudas, CREA (160M words), CORPES XXI | ✅ Tous online cvc.cervantes.es/rae.es | 1j curation |
| **Exam ref** | **DELE modelos officiels** A1-C2 (cvc.cervantes.es/aula/dele) | ✅ Open | 1j |

**Total ES enrichi** : **~25-35j** pour compléter les drafts existants + activation prod. Minimal viable alpha : ~12-15j (focus PCIC rubrics + CEDEL2 SLA papers + Dify Maestro app).

**Priorité drafts déjà en place** :
- ✅ `rubrics/es.yaml`, `fewshots/es.yaml`, `concept_hints/es.yaml`, `cefr_diagnostics/es.yaml`, `l1_transfer/fr_to_es.yaml`, `curriculum_es.yaml`
- ✅ `rules_es.py` squelette (7 détecteurs)
- ✅ `SYSTEM_PROMPT_ES` + `USER_PROMPT_TEMPLATE_ES` (50+ codes)
- ✅ `LanguageDomain("es")` gated `ENABLE_MAESTRO`

**Reste à faire (minimum viable)** :
1. Deep dive PCIC 3 volumes pour enrichir rubrics/es.yaml (2j)
2. Analyse CEDEL2 French subcorpus pour calibrer l1_transfer multipliers (3j)
3. Intégration Bruhn de Garavito + Collentine findings dans rules_es.py (2j)
4. Créer new Dify app Maestro + traduction prompts ES (3j)
5. Battery ES 4 personas + E2E test famille (3j)

---

### 🟡 IT — PROFESSORE (langue la plus proche du français)

**Difficulty rating** : **1.5/5** (romance sister, SVO, 2-gender, 0-case). FR speakers transfer advantage.

| Étape | Ressource | Accès | Effort |
|---|---|---|---|
| 1. Corpus | **MERLIN IT** (EURAC, 400 textes, A1-C1, CEFR-annotated, 70 features, CC-BY-SA 4.0) | ✅ Open CLARIN | 2j |
| 1bis. Complément | **VALICO** (Univ Turin, 200 textes mixed L1s, non-CEFR mais morpho-syntaxe UD) | ✅ Open | 1j |
| 1ter. Exam contexte | **CELI corpus 2024** (Univ Perugia, pseudo-longitudinal B1-C2) | ⚠️ Semi-open | 1j |
| 2. Calibration | GLMM sur MERLIN IT (subset FR L1 si disponible) | ✅ | 2-3j |
| 3. Tolerance matrix | Adapter 12 familles + IT:AUX (essere/avere), IT:SUBJ | ✅ template | 1j |
| 4. Rubrics | **Profilo della lingua italiana** (Univ Perugia/CVCL, A1-B2 officiel) + **Sillabi CILS** (Siena, A1-C2) + **QCER IT** | ✅ public | 2-3j |
| 5. Framework | Lyster & Ranta (invariant) | — | 0j |
| 6. Rules | IT:AUX (essere/avere calque), IT:SUBJ (subj plus fréquent qu'FR), ADJ:ORDER, ART:CONTRACT (al/dal/nel) | — | 3j |
| 7. Fewshots | 24 examples FR→IT typiques (essere/avere, subj dopo penso che, faux amis largo/lungo) | — | 2j |
| 8. L1 transfer | **Bettoni & Giacalone Ramat** (Pavia project L2 italien) + derivations contrastives FR/IT | ⚠️ Pas de FR→IT dédié, reverse-engineer via MERLIN | 2-3j |
| 9. Curriculum | CILS syllabus → ~75 concepts mappés CEFR | ✅ | 1-2j |
| 10. Fine-tune | Base `gpt-4o-mini` + SYSTEM_PROMPT_IT | ✅ | 0.5j |
| 11. Battery | 4 personas IT FR-native | — | 2-3j |
| 12. Prompts Dify | Nouvelle app "Professore" clone Teacher + prompts IT natifs | — | 2j |
| **Autoritaire** | **Accademia della Crusca** (Florence, 1583, Vocabolario) | ✅ Online | 0.5j |

**Total IT** : **~22-28j** (effort le plus faible après ES).

**Blockers mineurs** :
- Pas de recherche SLA FR→IT dédiée → reverse-engineer via MERLIN error analysis
- CELS/CILS samples limités accès → utiliser specs publics + Instituto Italiano di Cultura contacts

---

### 🟡 DE — LEHRER (V2 + cas + gender 3-way)

**Difficulty rating** : **3.5/5** (OV+V2 majeur, 3-gender, 4-case, verbes séparables, Konjunktiv II). SLA literature extensive mais pas FR→DE spécifique.

| Étape | Ressource | Accès | Effort |
|---|---|---|---|
| 1. Corpus | **MERLIN DE** (1000 textes, A1-C1) + **Falko** (FU Berlin Humboldt, 1500+ textes B1-C2, error-rich annotated) | ✅ Open CLARIN | 3j |
| 2. Calibration | GLMM sur MERLIN + Falko combined | ✅ | 3-4j |
| 3. Tolerance matrix | Adapter 12 familles + DE:CASE (Nom/Akk/Dat/Gen), DE:V2, DE:SEP (séparables), DE:GENDER (3-way) | ✅ | 2j |
| 4. Rubrics | **Profile Deutsch** (Glaboniat et al., Langenscheidt, ISBN 978-3-468-49493-6, A1-C2 officiel tri-national DE/AT/CH) + **Goethe-Institut curriculum** | ⚠️ Profile Deutsch = livre payant 40€ | 3-5j |
| 5. Framework | Lyster & Ranta (invariant) + **Pienemann Processability Theory** (V2 acquisition 5-stage sequence) | ✅ | 1j (intégration Pienemann) |
| 6. Rules | DE:CASE (der→den), DE:V2 (Ich weiss nicht warum er kommt → kommt en V2), DE:SEP (anrufen), DE:GENDER (das/die/der), cognates trompeurs (Gift=poison, bekommen=get) | — | 5-8j (complexe, nécessite syntax-aware rules) |
| 7. Fewshots | 24 examples FR→DE (V2 misplacement, case errors, gender confusion, separable verb errors) | — | 2-3j |
| 8. L1 transfer | **Pienemann, Klein, Dittmar** (ZISA corpus) + **Håkansson, Pienemann, Sayehli 2002** (typological proximity). FR→DE not directly tested, extrapolate | ✅ Papers | 3-4j |
| 9. Curriculum | Profile Deutsch + Goethe → ~80 concepts | ✅ | 2j |
| 10. Fine-tune | Base `gpt-4o-mini` + SYSTEM_PROMPT_DE | ✅ | 0.5j |
| 11. Battery | 4 personas DE + V2/case edge cases | — | 3j |
| 12. Prompts Dify | Nouvelle app "Lehrer" | — | 2j |
| **Autoritaire** | **Duden** (675k entries online) + **Wortschatz Leipzig** (frequency lists) | ✅ Online | 1j |

**Total DE** : **~28-35j**.

**Blockers moyens** :
- V2 detection nécessite **syntax-aware rules** (pas juste regex) → utiliser TreeTagger ou spaCy-de + UDPipe
- Cas + gender 3-way = **complexité 3-5× EN** (morpho plus riche)
- Pienemann theory pas FR-testée → risque sur prédictions L1 transfer

---

### 🔴 JP — SENSEI (JLPT-native, révisé Session 29 — 0€ externe)

**Difficulty rating** : **4/5** (langue distante mais ressources JLPT open complètes). Requires tokenizer + dispatch levels JLPT-native. **Pivot Session 29** : utilisation **JLPT N5-N1 natif** au lieu de forcer CEFR → ressources pédagogiques complètes en open source.

| Étape | Ressource | Accès | Effort |
|---|---|---|---|
| 1. Corpus | **I-JAS brut** (NINJAL, 1050 learners tous L1, on ne filtre pas FR) + **Lang-8 historical** (millions de corrections crowdsourced) + **Tatoeba JP** + **JpWaC/JpTenTen** (natif 100M+) | ✅ Open | 3j (exploration, noise clean léger) |
| 1bis. Reference native | **BCCWJ** (NINJAL, 104M words) + **CSJ** (spoken) via Kotonoha | ✅ | 1j |
| 2. Calibration | Synthetic pretrain two-stage (Latouche 2024) + fine-tune léger sur I-JAS/synthetic | ✅ | 2j (pipeline réutilisable Phase 0.8) |
| 3. Tolerance matrix | Familles : JP_PARTICLE (は/が/を/に/で), JP_KEIGO (teineigo/sonkeigo/kenjōgo), JP_KANJI_READING, JP_COUNTER, JP_ASPECT (〜ている), JP_VERB_FORM | — | 2j |
| 4. **Rubrics JLPT-native** | **Japan Foundation JF Standard** (jfstandard.jp) + **Tae Kim's Guide** (guidetojapanese.org) + **Imabi.org** + **JLPT official** (jlpt.jp) + **Minna no Nihongo** + **Genki** structures | ✅ Open | 3-4j (**N5-N1 natif**, mapping interne a1-c2 via `levels.py`) |
| 5. Framework | Lyster & Ranta (invariant) | — | 0j |
| 6. **Tokenizer** | **SudachiPy** (recommended) ou MeCab/Juman++ — via Phase 0.6 dispatch | ✅ pip install | 5-6j (intégration + dict + testing mixed scripts) |
| 6bis. Rules | Particules (POS), conjugaisons régulières, kanji homophonie, counters N5-N3, aspect 〜ている N4+ | — | 5-7j |
| 7. Vocab + kanji | **Listes JLPT officielles** N5-N1 (vocab + kanji + radicaux) + Jisho.org API + Anki decks JLPT | ✅ Open | 1-2j |
| 8. Grammar points | Grammar points par niveau JLPT détaillés depuis Tae Kim + Imabi + jlptsensei.com | ✅ Open | 2j |
| 9. Fewshots | 18-20 examples FR→JP handcraft (5 niveaux N5-N1) depuis Minna no Nihongo + Imabi + research | ✅ Semi-open (fair-use) | 3j |
| 10. L1 transfer | Seed theoretical FR→JP : articles absent, SOV, particules は/が/を/に/で, keigo (FR tu/vous→JP 3-tier), kanji orthographe. Enrichi par thèses Higashi (INALCO), Detey (Rouen) HAL | ✅ Grey lit open | 3j |
| 11. Curriculum | JF Standard + Marugoto → ~80 concepts mappés JLPT N5-N1 | ✅ | 2-3j |
| 12. Synthetic + fine-tune | GPT-4 guidé par JLPT descriptors (~$5-8 OpenAI) + mT5-Large cross-lingual transfer depuis EN baseline | ✅ | 2j |
| 13. Battery | 5 personas JP FR-native N5-N2 + eval MultiGEC-2025 style | — | 2-3j |
| 14. Prompts Dify | Nouvelle app "Sensei" + prompts **JLPT-native** (UI affiche N5-N1) | — | 2j |
| **Ressources complémentaires** | **JMdict/KANJIDIC** (EDRDG, Yomitan format) + **NINJAL Kotonoha** + **Weblio** | ✅ Open | 1j (intégration) |

**Total JP** : **~30-35j** (révisé Session 29, ancien 45-60j).

**Limites honnêtes acceptées (pas des blockers)** :
- **Keigo niveau N1** : détection patterns standards OK, subtilités littéraires manquées (sans native validation).
- **Aspect littéraire C1-C2** : plafonné (corpus learner sous-représentent niveau expert).
- **Kanji error detection** : vocabulaire OK, stroke-level hors scope.
- **Analytics cross-lang** : JLPT N1 ≠ strictement CEFR C1 (mapping documenté dans glossary, non bijectif).

**Position produit** : Sensei = "Teacher JLPT-native" — aide learners FR à progresser N5→N1 dans système qu'ils utilisent déjà.

**Cost external** : **0€**.

---

### 🟠 RU — MAESTRO-RU (TORFL-native, révisé Session 29 — 0€ externe)

**Difficulty rating** : **3.5/5** (morphologie riche mais Gosstandart ТРКИ fournit référentiel officiel complet). **Pivot Session 29** : utilisation **TORFL TEU-IV natif** au lieu de forcer CEFR → grammar profile officiel disponible en open source.

**Note** : RU passe de "optionnel deferred 2027" à **Wave 4 engagée** grâce au pivot TORFL-native.

| Étape | Ressource | Accès | Effort |
|---|---|---|---|
| 1. Corpus | **RLC brut** (HSE Moscow, ~7000 textes multi-L1, open) + **CoRST** (subset, 3.1M tokens) | ✅ Open | 3j |
| 1bis. Reference natif | **Russian National Corpus RNC** (RAS, 600M tokens, open query) | ✅ | 1j |
| 1ter. Bonus discovery | **Russian Wheel RLC-French** (UCA Nice, Dampierre-Debuchy) — email non-contractuel Phase 0.9 | ⚠️ Discovery | 0j si obtenu, bonus non-bloquant |
| 2. Calibration | Synthetic pretrain two-stage (Latouche 2024) + fine-tune léger sur RLC fragments/synthetic | ✅ | 2j (pipeline réutilisable Phase 0.8) |
| 3. Tolerance matrix | Familles : RU:CASE (6 cas × 3 genres × 2 nombres), RU:ASPECT (perfective/imperfective pairs), RU:MOTION (идти/ходить/ехать), RU:WORD_ORDER, RU:GENDER | — | 2j |
| 4. **Rubrics TORFL-native** | **Gosstandart ТРКИ descriptors** (Ministère Éducation Russia, officiel, open) + **"Дорога в Россию"** (manuel Ministère aligné TORFL) + **"Поехали"** (intermédiaire) | ✅ Open | 3-4j (**TEU-IV natif**, mapping interne a1-c2 via `levels.py`) |
| 5. Framework | Lyster & Ranta (invariant) + Kempe & MacWhinney (case acquisition) | ✅ | 1j |
| 6. Rules | Cyrillique UTF-8 OK + **pymorphy2** / **pymystem3** (morphologie), cas détection par terminaisons (~80% cas réguliers), aspect pairs lookup dict open (~1500-2000 verbs), prépositions+cas pairing (в/на/у) | ✅ Open | 7-10j |
| 7. **Lexical Minimum** | Listes officielles Gosstandart par niveau TORFL (TEU-TORFL-IV) | ✅ Open | 1-2j |
| 8. **Grammatical Minimum** | Inventaire officiel Gosstandart par niveau TORFL | ✅ Open | 1-2j |
| 9. Fewshots | 18-20 examples FR→RU handcraft (5 niveaux TEU-TORFL-III) depuis Дорога в Россию + Поехали + research | ✅ Semi-open | 3j |
| 10. L1 transfer | Seed theoretical FR→RU enrichi par **Guiraud-Weber** (Aix-Marseille) papers open sur aspect verbal FR/RU + HSE studies + CoRST patterns. Cas absent FR, aspect lexical vs tense-based | ✅ Open | 3j |
| 11. Curriculum | TORFL syllabus + Lexical/Grammatical Minimum → ~80 concepts mappés TEU-IV | ✅ | 2-3j |
| 12. Synthetic + fine-tune | GPT-4 guidé par TORFL descriptors (~$5-8 OpenAI) + mT5-Large cross-lingual transfer depuis EN+ES baseline | ✅ | 2j |
| 13. Battery | 5 personas RU FR-native TEU-TORFL-II + eval MultiGEC-2025 style | — | 2-3j |
| 14. Prompts Dify | Nouvelle app "Maestro-RU" + prompts **TORFL-native** (UI affiche TEU/TBU/TORFL-I-IV) | — | 2j |
| **Autoritaires** | **Gramota.ru** (govt portal depuis 2000, dict normatifs Lopatin/Kuznetsov) | ✅ Online | 0.5j |

**Total RU** : **~25-30j** (révisé Session 29, ancien 45-55j).

**Limites honnêtes acceptées (pas des blockers)** :
- **Aspect verbal niveau TORFL-III+** : détection patterns fréquents OK, cas rares/littéraires manqués.
- **Cases complexes** (exceptions morphologiques) : ~80% réguliers OK via terminaisons, exceptions best-effort.
- **Registres littéraires niveau IV** : corpus learner sous-représentent ce niveau.
- **Chemin A (linguiste €33-59K)** : abandonné par défaut, déclenchable business-only.

**Position produit** : Maestro-RU = "Teacher TORFL-native" — aide learners FR à progresser TEU→TORFL-IV dans standard officiel russe reconnu internationalement.

**Cost external** : **0€**.

---

## PART 3 — Priorisation roadmap suggéré (révisé Session 29)

### Tableau récapitulatif (Session 29 — pivot stratégie native)

| Langue | Système niveau | Difficulty | Effort total | Ressources % | Coût ext | Priorité |
|---|---|---|---|---|---|---|
| **ES Maestro** | CEFR A1-C2 | 2/5 | ~20-25j | 95% | 0€ | **P1 Wave 1** |
| **IT Professore** | CEFR A1-C2 | 1.5/5 | ~22-28j | 98% | 0€ | **P2 Wave 2** |
| **DE Lehrer** | CEFR A1-C2 | 3.5/5 | ~28-35j | 95% | 40€ Profile Deutsch (Sinse) | **P3 Wave 2** |
| **JP Sensei** | **JLPT N5-N1 natif** | 4/5 | **~30-35j** | **95% natif** | **0€** | **P4 Wave 3 (pivot S29)** |
| **RU Maestro-RU** | **TORFL TEU-IV natif** | 3.5/5 | **~25-30j** | **95% natif** | **0€** | **P5 Wave 4 (pivot S29)** |

**Changement majeur Session 29** : JP et RU passent de "blockers majeurs" et "defer 2027" à **ressources complètes dans écosystème natif** grâce au pivot JLPT/TORFL-native.

### Ordre d'exécution recommandé (révisé Session 29)

**Q2 2026 (33-43j)** — Phase 0 infra + Wave 1 ES
- Phase 0 infra factorisée (15j inclus levels.py + synthetic pipeline + discovery emails)
- Wave 1 ES Maestro : enrichissement drafts + CEDEL2 + Dify + battery + activation (14-18j)
- **Activation prod `ENABLE_MAESTRO=true`**

**Q3 2026 (39-46j)** — Wave 2 IT + DE parallèle
- Professore IT : MERLIN-IT + VALICO + CELI + Profilo della lingua + rules_it.py
- Lehrer DE : MERLIN-DE + Falko + DISKO + **Profile Deutsch (Sinse 40€)** + rules_de.py avec V2/cases syntax-aware
- Factorisation pipeline commun → économie ~30% vs séquentiel

**Q4 2026–Q1 2027 (30-35j)** — Wave 3 JP JLPT-native (pivot S29)
- Intégration tokenizer (SudachiPy/MeCab)
- **Rubrics JLPT N5-N1 natif** depuis Japan Foundation + Tae Kim + Imabi (0€)
- Synthetic GPT-4 + mT5 cross-lingual transfer
- UI affiche N5-N1 (mapping levels.py interne)
- **Couverture N5-N1 complète, pas de Wave 3.5 séparée**

**Q2 2027 (25-30j)** — Wave 4 RU TORFL-native (pivot S29)
- **Rubrics TORFL TEU-IV natif** depuis Gosstandart ТРКИ + Дорога в Россию (0€)
- pymorphy2 + cas détection terminaisons + aspect pairs
- Synthetic GPT-4 + mT5 cross-lingual transfer depuis EN/ES
- UI affiche TEU/TBU/TORFL-I-IV (mapping levels.py interne)
- Email discovery UCA Nice Russian Wheel non-bloquant

**Total timeline** : 10-13 mois calendaires, ~125-150j effort (Scénario B hybride).
**Cost external cumulé** : **40€ Profile Deutsch + ~$25-35 OpenAI synthetic**.

### Option alternative — compression si urgence

Si besoin de livrer 3 langues en Q2-Q3 2026 :
- ES + IT + DE en parallel (requires ≥2 devs) = ~75-90j total calendrier, 50-60j effort si bien parallélisé
- Factorisation pipeline : corpus extraction concurrent, rubrics séquentiel, Dify apps parallel
- Risk : rules engine IT/DE pourrait diverger vs EN si pas code review serré

---

## PART 4 — Next steps actionnables

### Session prochaine (immédiat, ES Maestro enrichissement)

Par tranche de ~2j, dans l'ordre :

1. **Deep dive PCIC volumes 1-3** — produire `rubrics/es_enriched.yaml` avec citations §précises + structures cibles complètes par niveau (2j)
2. **CEDEL2 download + exploration** — vérifier présence FR L1 subcorpus, extract error patterns FR→ES typiques (2j)
3. **SLA research integration** — Bruhn de Garavito 1986/2002/2010, Collentine subj, Geeslin ser/estar → enrichir `rules_es.py` (5→15-20 détecteurs) + `l1_transfer/fr_to_es.yaml` multipliers calibrés (2j)
4. **Create Dify Maestro app** — script Python qui clone Teacher via DB + traduit prompts (plan_choice, session, onboarding, exam) en ES natif à partir des YAMLs enrichis (3j)
5. **E2E battery ES** — 4 personas (A1-B2) + edge cases + rapport pass rate (3j)
6. **Alpha activation famille** — flip `ENABLE_MAESTRO=true` + `maestro.available: true` + iteration 1 semaine feedback (5j calendaire)

**Total ES Maestro enrichi + livré alpha** : ~12-15j effort dev, 20j calendaire.

### Pour IT/DE/JP/RU — prérequis avant démarrage

Chaque langue nécessite :
- [ ] Décision Sinse : on fait cette langue ? (input utilisateur)
- [ ] Effort allocation (qui, combien de jours)
- [ ] Téléchargement corpus (MERLIN/Falko/I-JAS/RLC) + vérification license commerciale si applicable
- [ ] Papers SLA clés téléchargés + annotés pour intégration pipeline
- [ ] Création nouveau Dify app (clone Teacher via script)
- [ ] Env vars + feature flags (ENABLE_PROFESSORE, ENABLE_LEHRER, etc.)

### Blockers généraux à résoudre une fois

- [ ] **Script de cloning Dify app programmatique** — actuellement pas encore fait, empêche automation Maestro/Professore/Lehrer/Sensei
- [ ] **GLMM pipeline parametré par lang** — actuellement `scripts/sprint1/` hardcoded EN, refactor pour lang-agnostic (4-5j one-time)
- [ ] **Rules engine multi-lang abstraction** — `rules.py` dispatch par lang (Phase 4 fait partially), finaliser pour IT/DE (syntax-aware pour V2), pour JP/RU (morpho-analyzer integration)
- [ ] **Spaced retrieval per-lang** — actuellement error_code family map hardcoded EN, adapter pour familles ES/IT/DE/JP/RU spécifiques

---

## Références principales (bibliographie recherche)

### Corpus learner (tous open access)

- **W&I+LOCNESS** (BEA 2019) : https://www.cl.cam.ac.uk/research/nl/bea2019st/
- **NUCLE** : https://www.comp.nus.edu.sg/nlp/corpora.html
- **CEDEL2** : https://cedel2.learnercorpora.com/ (Lozano 2022, Language Learning & Technology 26:2)
- **CAES** : https://galvan.usc.es/caesv1 (Instituto Cervantes + Univ Santiago Compostela)
- **COWS-L2H** : https://github.com/ucdaviscl/cowsl2h (Yamada & Davidson LREC 2020)
- **MERLIN IT/DE** : https://www.merlin-platform.eu (EURAC + CLARIN, Boyd et al. LREC 2014)
- **Falko DE** : https://www.linguistik.hu-berlin.de/en/institut-en/professuren-en/korpuslinguistik/research/falko (Reznicek et al. LREC 2012)
- **I-JAS JP** : https://www2.ninjal.ac.jp/jll/lsaj/ihome2-en.html
- **TMU TEC-JL** : https://github.com/koyama-aomi/TEC-JL (Koyama LREC 2020)
- **RLC RU** : http://www.web-corpora.net/RLC (HSE Moscow)

### Grammar profiles officiels

- **EGP** : https://www.englishprofile.org/ (O'Keeffe & Mark IJCL 2017)
- **PCIC** : https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/ (Instituto Cervantes 2006-2011, 3 vol.)
- **Profilo della lingua italiana** : https://www.unistrapg.it/profilo_lingua_italiana (Univ Perugia CVCL)
- **Profile Deutsch** : Langenscheidt, ISBN 978-3-468-49493-6 (Glaboniat et al. 2006)
- **JF Standard** : https://www.jfstandard.jpf.go.jp/ (Japan Foundation 2010)
- **TRKI/TORFL** : gct.msu.ru, russian-test.com (Russian Ministry Education)

### SLA research clés

- Lyster, R. & Ranta, L. (1997). SSLA 19(1), 37-66
- Lyster, R. & Saito, K. (2010). SSLA 32, 265-302
- Pienemann, M. (1998). *Language Processing and Second Language Development*, Benjamins
- Håkansson, G., Pienemann, M. & Sayehli, S. (2002). IRAL 40(2)
- Bruhn de Garavito, J. & White, L. (2002). In Pérez-Leroux & Liceras (eds), *The Acquisition of Spanish Morphosyntax*, Kluwer
- Lardiere, D. (2009). SLR 23(2), 121-139
- Montrul, S. (2022). *Native Speakers, Interrupted*, Cambridge UP (LSA Bloomfield Award 2024)
- Collentine, J. (2010). *ADFL Bulletin* 42(1), 30-39
- Geeslin, K. (various). Ser/estar acquisition corpus studies
- Kempe, V. & MacWhinney, B. (1998+). RU case/gender acquisition constraints

### Frameworks pédago

- Corder (1967). IRAL 5
- Swain (1985, 2005). Output Hypothesis
- Krashen (1982). Input Hypothesis, Affective Filter
- Cowan (2001). *Behavioral & Brain Sciences* 24 (WM ≈ 4 items)
- Hattie & Timperley (2007). *RER* 77(1) (d moyen 0.79)

### Autoritaires

- **RAE + Asale** (ES) : https://www.rae.es/ + https://corpus.rae.es/creanet.html (CREA 160M words) + https://www.rae.es/banco-de-datos/corpes-xxi
- **Accademia della Crusca** (IT) : https://www.accademiadellacrusca.it
- **Duden** (DE) : https://www.duden.de
- **Gramota.ru** (RU) : https://gramota.ru
- **NINJAL** (JP) : https://clrd.ninjal.ac.jp/en/

### Exam references

- **Cambridge EN** : https://www.cambridgeenglish.org/
- **DELE ES** : https://cervantes.org/es/examenes/dele + https://cvc.cervantes.es/aula/dele/
- **CILS/CELI IT** : https://www.unistrapg.it
- **Goethe-Zertifikat DE** : https://www.goethe.de/en/spr/prf
- **JLPT JP** : https://www.jlpt.jp/e/
- **TRKI RU** : https://russian-test.com

### Tools

- **ERRANT** (error annotation) : https://github.com/chrisjbryant/errant
- **NumPyro** (GLMM) : https://num.pyro.ai/
- **SudachiPy** (JP tokenizer) : https://github.com/WorksApplications/Sudachi
- **pymorphy2/MYSTEM** (RU morpho) : https://github.com/kmike/pymorphy2

---

_Document produit via 4 agents parallèles (~50K tokens research) — Session 27._
