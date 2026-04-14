# Plan de test — 40 features AcademIA

## ONBOARDING

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 1 | Onboarding (3 FR + 5-7 EN + diagnostic) | Nouveau user sans profil | Dify → n8n diagnostic → DB | PASS* |
| 2 | Onboarding tour 3 : intérêts + style correction | 3e tour FR | Prompt → diagnostic LLM → personnalite JSONB | PASS |
| 3 | Bilan post-diagnostic (chat) | Premier message post-diagnostic | profil-get → PROMPT_SESSION | PASS |
| 4 | Bilan post-diagnostic (dashboard card) | onboarding_completed_at + pas de session | Profile API → carte provisoire | PASS |

## SESSION NORMALE

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 5 | Session plan (choix 2 concepts, spaced repetition) | Tour 1 d'une conversation | code_turn_check → PROMPT_PLAN | PASS |
| 6 | TTT cycle (Test → Teach → Test) | Tours 2-9 | PROMPT_SESSION + focus_concept + focus_mode | PASS |
| 7 | Modes concept (DECOUVERTE/RENFORCEMENT/PRATIQUE/MAINTIEN) | Score du concept | code_turn_check → instructions TTT adaptées | PASS |
| 8 | Accueil adapté à l'absence (1h / 1-6j / 7j+) | minutes_since_last >= 60 | code_turn_check → plan_prefix | PASS |

## PERSONNALITÉ

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 9 | Ton adaptatif (direct/encourageant/humour) | Champ Style dans profil | PROMPT_SESSION section TON ET STYLE | PASS |
| 10 | Contextes par centres d'intérêt | Champ Interets dans profil | PROMPT_SESSION section VARIETE CONTEXTES | PASS |
| 11 | Objectif de l'élève (travail/voyage/culture/examen) | Champ Objectif dans profil | PROMPT_SESSION section OBJECTIF | PASS |
| 12 | Profilage progressif (collecte en session) | Champs vides + tours 1-4 | PROMPT_SESSION → snapshot → personnalite | PASS |

## ERREURS

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 13 | Error detection rules temps réel (17 codes A1-C1) | Chaque message user | chat_router → detect_errors() | PASS |
| 14 | Filtrage tolerance_matrix (shadow/noted/penalized) | Chaque détection | chat_router → matrice YAML × niveau | PASS |
| 15 | Error feedback en conversation | Erreur détectée (non shadow) | error_feedback + tags → Dify → Teacher corrige | PASS |
| 16 | Style correction par type d'erreur (grammar/transfert/surface) | Type d'erreur | PROMPT_SESSION section STYLE DE CORRECTION | PASS |
| 17 | Repeated errors escalation | Même code dans error_log 7j | chat_router → repeated_errors → prompt | PASS |
| 18 | Protocole d'escalade corrective (4 niveaux) | Erreur répétée en session | PROMPT_SESSION → recast → métalinguistique → règle → explicite | PASS |
| 19 | Snapshot (scores + mémoire) | Tous les 10 tours | dify-snapshot → scores_confiance + personnalite | PASS |
| 20 | Error analysis LLM (persistence) | Après snapshot | /internal/analyze-errors → error_log | PASS |

## EXAMEN

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 21 | Exam request | User dit "examen" | [EXAM_START] → exam mode modulaire | PASS |
| 22 | Exam questions (modules + types) | En mode exam | code_exam_track → questions | PASS* |
| 23 | Exam persist (resume après déconnexion) | Chaque question exam | dify-exam-persist → DB | PASS |
| 24 | Exam scoring + promotion | [EXAM_COMPLETE] | dify-exam-scoring → niveau_global + XP | PASS* |
| 25 | Exam cooldown progressif (3/7/14j selon tentatives) | Post-échec exam | code_turn_check → plan_prefix cooldown | PASS |
| 26 | Célébration post-promotion | Post-réussite exam | code_turn_check → plan_prefix félicitations | PASS* |
| 27 | Scoring recovery (technique) | exam_mode=scoring bloqué | code_turn_check → plan_prefix excuse + reprise | PASS* |

## MODES SPÉCIAUX

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 28 | Review mode (lacunes) | User dit "revoir mes lacunes" | [REVIEW_LACUNES] → concepts faibles en priorité | PASS |
| 29 | Quiz mode (mock exam) | Bouton Quiz frontend | mock_exam input → 10 questions → bilan | PASS |

## DÉTECTION COMPORTEMENTALE

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 30 | Détection comportementale (5 états) | Signaux timing + patterns | PROMPT_SESSION → confusion/frustration/ennui/flow/gaming | PASS |

## GAMIFICATION

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 31 | Streaks (consécutifs + freeze automatique) | Activité quotidienne | chat_router → streaks table | PASS |
| 32 | XP (session 50 / exam 200 / promo 500) | 10 messages ou exam | chat_router + /internal/exam-result | PASS |
| 33 | Badges (9 définitions, calculés live) | Activité cumulée | /api/me/badges | PASS |
| 34 | Rangs XP (Débutant → Maître, 6 paliers) | Total XP | /api/me/xp | PASS |

## WEBAPP

| # | Feature | Trigger | Pipeline | Statut |
|---|---|---|---|---|
| 35 | Dashboard home (stats, popover concepts, weekly recap) | Chargement page | 4 API calls | PASS |
| 36 | Stats page (progression, XP graph 30j, badges, exams) | Chargement page | 5 API calls | PASS |
| 37 | Concepts detail (scores par module, tips, insights) | Clic depuis stats | /api/me/concepts | PASS |
| 38 | Profile/settings (nom, avatar, thème, goal, intérêts, style, password, sessions) | Page profil | settings API | PASS |
| 39 | Admin (users, reset, delete) | Page admin | admin API | PASS |
| 40 | Mode toggle (structure/libre) | Bouton chat header ou settings | PATCH /api/me/mode | PASS |
