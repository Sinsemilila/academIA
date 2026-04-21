# Politique L1/L2 — scaffolding adaptatif au niveau × distance typologique × anxiété

**Statut** : livré Session 35 (2026-04-21) — MVP code-level, sans patch Dify (Phase 2)
**Scope** : tous les tuteurs langues (Teacher EN, Maestro ES, futurs Professore IT / Lehrer DE / Sensei JP / agent RU)

---

## 1. Rationale empirique

AcademIA partait d'une politique **100% L2 dès turn 1** (block `QCM_OVERRIDE_v1`, script `14_strengthen_llm_onboarding_override.py`). Validé live Session 35 sur FR→ES A1 (un cas où les cognats romans compensent). Mais cette politique est :

### 1.1 Empiriquement indéfendable pour l'adulte A1

- **Butzkamm & Caldwell (2009)** *The Bilingual Reform* — le monolinguisme est "the last taboo", la L1 est la plus grande ressource pédagogique. La **sandwich technique** (Butzkamm 2003, *Language Learning Journal* 28) alterne L2 → bref gloss L1 → L2.
- **Cook (2001)** "Using the first language in the classroom", *Canadian Modern Language Review* 57(3) — démantèle la "monolingual assumption" sur 4 plans : réalité cognitive du L2-user, efficacité, authenticité des tâches bilingues, naturalité du codeswitching.
- **Macaro (2005)** — 3 positions d'enseignant : *virtual* (jamais L1), *maximal* (L1 = mal nécessaire), **optimal** (L1 principiée apporte une valeur pédagogique). L'évidence empirique n'offre aucun support à la position "virtual".
- **Hall & Cook (2012)** — état de l'art *Language Teaching* 45(3) : "the monolingual principle is not empirically supported".
- **Horwitz et al. (1986) FLCAS** + **Levine (2003)** : plus de L1 en classe corrèle avec moins d'anxiété rapportée — critique pour A1.
- **CEFR 2020 Companion Volume** (Council of Europe) — introduit médiation et plurilinguisme comme compétences. Descripteurs A1 : "peut interagir de façon simple si l'interlocuteur parle lentement, répète, **aide à formuler**". Renverse la dérive monolingue du CEFR 2001.

### 1.2 Contredite par le marché

Survey de 10 apps majeures (Session 35) :

| App | % L1 à A1 turn 1 | Pattern |
|---|---|---|
| Duolingo | ~80% L1 / 20% L2 | UI chrome et tips en L1, tap-tile bilingue |
| Babbel | ~60% L1 / 40% L2 | L1 pour grammaire/culture, méthode explicitement bilingue |
| Pimsleur | L2→L1→L2 | Sandwich canonique, narrateur L1 backbone |
| Rosetta Stone | 0% L1 (sauf JA/KO/TR = L1 Units 1-4) | Seul "claim 100% L2", concède pour distances typologiques |
| Busuu | Mix, AI conv gated | A1 lessons L1-heavy, AI conv feedback en L1 |
| Speak | L1 intro + L2 drills | Video tutor en L1, roleplay L2 mais task framing L1 |
| TalkPal / Langotalk / Gliglish | Toggle L1 disponible | Aucun ne démarre 100% L2 par défaut |
| iTalki tutors | Consensus pro : anti-pattern L2-only A1 | TPR + realia + intermediary L1 |

**9/10 apps utilisent L1 à A1 turn 1**. Seul Rosetta Stone est l'exception, et même eux plient face à la distance typologique.

### 1.3 Insoutenable à l'échelle multi-langue

Roadmap inclut Sensei (JP) et un agent RU. Distance typologique FR→JP ≈ plafond linguistique (Chiswick & Miller 2005, Ringbom 2007). 100% L2 à A1 + distance extrême = catastrophe pédagogique. On doit baker la distance dans la politique dès maintenant.

---

## 2. Matrice de politique

Trois signaux :
- **CEFR placement** du QCM (`learner_profiles.domain_level.cefr_placement`)
- **Distance typologique** L1×target (`pedagogy/typological_distance.py`)
- **FLA** (`learner_profiles.domain_motivation.fla_category` — low/medium/high)

| CEFR placement | Close (FR↔ES/IT/PT/CA) | Medium (FR↔EN/DE/NL) | Distant (FR↔JP/KO/RU/ZH/AR/TR) |
|---|---|---|---|
| **A1** | 90% L2, sandwich méta | 85% L2, L1 grammaire+consignes | 55% L2, L1 réassurance+méta+sandwich nouveauté |
| **A2** | 95% L2 | 90% L2, sandwich rare | 80% L2, sandwich ciblé |
| **B1+** | 100% L2 | 100% L2 | 95% L2, L1 minimal |

**Modulation FLA high** : shift +1 bande (close→medium, medium→distant). Low/medium : baseline.

**Modulation turn** : `sandwich=true` désactivé après turn 6 (anti-fatigue). `reassurance_l1` seulement turn 1-2.

---

## 3. Classification distance typologique

Fondée sur Chiswick & Miller (2005) *J. Multilingual and Multicultural Development* 26 et Ringbom (2007) *Cross-linguistic Similarity in Foreign Language Learning*.

| Bucket | Critères | Exemples paires |
|---|---|---|
| `close` | Même sous-famille, densité cognate élevée, morphosyntaxe partagée | FR↔ES/IT/PT/CA, ES↔IT, EN↔DE/NL |
| `medium` | Familles différentes mais script commun + floor latin/grec | FR↔EN/DE/NL, FR↔PL/CS, ES↔EN |
| `distant` | Script ou typologie différente, pas de floor cognate partagé | FR↔JA/KO/ZH/AR/RU/TR/HE, EN↔JA/KO/ZH/AR/RU |

Table sous `packages/academie-core/academie_core/pedagogy/typological_distance.py`. Ajout d'une nouvelle paire : éditer `_DISTANCE_TABLE` + test dans `test_typological_distance.py`.

---

## 4. Architecture

### 4.1 Pipeline

```
QCM submit → learner_profiles row
             ├ domain_level.cefr_placement
             └ domain_motivation.fla_category
                        ↓
chat_router.py (per turn)
  1. Fetch learner_profiles → niveau, fla_category
  2. Build PromptContext(level, fla_category, target_lang_name, l1_name, ...)
  3. teacher_prompt.build_dynamic_sections(ctx) →
       - rubric_for_level, fewshots, dosage, ...
       - scaffolding_block ← nouveau (scaffolding_policy.build_scaffolding_block)
  4. [MVP] Append scaffolding_block à learner_profile_summary (channel already wired)
  5. dify_inputs → Dify LLM (llm_onboarding ou llm_session selon branche)
```

### 4.2 Architecture Phase 2 (differée)

Splitter `scaffolding_block` en input Dify Start dédié + wiring via `code_profil_check` + `code_turn_check` + références `{{#code_XXX.scaffolding_block#}}` dans les 3 LLM nodes. Script `scripts/sprint5/16_register_scaffolding_input.py` à écrire.

### 4.3 Kill switch

Env var `SCAFFOLDING_BLOCK_ENABLED=true` (défaut). Si `false` → `dify_inputs["scaffolding_block"] = ""`, pas d'append, fallback comportement 100% L2 Session 34.

---

## 5. Sandwich technique

Quand `policy.sandwich == true` et `turn_count <= 6`, le block inclut :

> When introducing anything brand-new:
>   1) say it in {target_lang},
>   2) add a short {l1_name} gloss between parentheses,
>   3) repeat it in {target_lang}.

Phase 2 enrichira avec des few-shots par distance (`data/fewshots/sandwich_{close,medium,distant}.yaml`).

---

## 6. Interaction avec systèmes existants

| Système | Précédence |
|---|---|
| `QCM_OVERRIDE_v1` (Dify prompt, Session 34) | Hook scaffolding AVANT les 6 steps QCM_OVERRIDE — la politique L1/L2 encadre, QCM_OVERRIDE définit les étapes |
| `<learner_profile>` block (Session 33) | Scaffolding_block est appendé au contenu via chat_router (MVP). Même channel. |
| `l1_watch` (Phase 6) | Indépendant — surveille les transferts L1→L2 dans la production learner. Non-conflit. |
| `learner_profile_summary` | Reçoit l'append scaffolding en queue (MVP) |

---

## 7. Validation

### Tests unitaires

- `tests/test_typological_distance.py` — 6 tests (symétrie, case, défaut medium)
- `tests/test_scaffolding_policy.py` — 13 tests paramétrés sur 9 cells + shifts FLA + turn-count gates

### Plan de test live (matrice)

| # | Scénario | Attendu |
|---|---|---|
| 1 | FR→ES A1 FLA=low | 90% L2, sandwich méta — reg. faible (proche Session 35) |
| 2 | FR→ES A1 FLA=high | Shift vers medium : 85% L2 + L1 grammaire |
| 3 | FR→EN A1 FLA=low | 85% L2 + sandwich on grammaire/consignes |
| 4 | FR→EN A2 FLA=low | 90% L2, sandwich rare |
| 5 | FR→JP A1 simulé | 55% L2 + réassurance turn 1-2 + sandwich systématique |
| 6 | FR→ES B1 | No-op (block vide) — 100% ES |

---

## 8. Open questions (P2+)

- Généralisation L1 non-FR : la table distance est symétrique, mais `l1_name` est figé "français" → `_L1_NAMES` mapping à étendre.
- C1 suppression totale sandwich : mesurable après alpha.
- Per-domain overrides (Sensei vs Teacher) : nécessaire quand JP livré.
- A/B test quantitatif ratio L2 réel (via log LLM output) — Phase 3.
- Monitoring : logger `user_sessions.scaffolding_cell` (`level|distance|fla`) pour analyse offline.
- Remplacer l'append sur `learner_profile_summary` par un input Dify dédié (propreté).

---

## 9. Sources clés

- Butzkamm W. & Caldwell J. (2009). *The Bilingual Reform: A Paradigm Shift in Foreign Language Teaching*. Narr Verlag.
- Cook V. (2001). Using the first language in the classroom. *Canadian Modern Language Review* 57(3).
- Macaro E. (2005). Codeswitching in the L2 classroom. *Modern Language Journal* 85. Macaro 2005 in Llurda (ed.) *Non-Native Language Teachers*.
- Hall G. & Cook G. (2012). Own-language use in language teaching and learning. *Language Teaching* 45(3).
- Horwitz, Horwitz, Cope (1986). Foreign Language Classroom Anxiety. *Modern Language Journal* 70(2).
- Levine G. (2003). Student and instructor beliefs about target language use, first language use, and anxiety. *MLJ* 87.
- Ringbom H. (2007). *Cross-linguistic Similarity in Foreign Language Learning*. Multilingual Matters.
- Chiswick B. & Miller P. (2005). Linguistic Distance. *J. Multilingual and Multicultural Development* 26.
- Council of Europe (2020). *CEFR Companion Volume*.
- ACTFL (2012, softened 2021). *Use of the Target Language in the Classroom*.
- Instituto Cervantes. *Plan Curricular del Instituto Cervantes* — Inventario 13 Procedimientos de aprendizaje.

## 10. Changelog

- **2026-04-21 (Session 35)** — MVP : typological_distance + scaffolding_policy modules + build_scaffolding_block wired through learner_profile_summary. Kill switch env var.
