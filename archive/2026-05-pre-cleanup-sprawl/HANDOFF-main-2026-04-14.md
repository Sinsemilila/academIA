# HANDOFF — main — 2026-04-14 09:02

## 1. Scope/Status
- Session discussion uniquement — aucun code modifié sur le repo.
- Diagnostic onboarding complet : Teacher chatflow a déjà Phase 1 (4 tours FR) + Phase 2 (5-10+ tours diagnostic CECRL EN) + marqueur [EVAL_READY] → n8n dify-diagnostic → set niveau_global. Problème : aucune couche webapp pour accueillir le nouvel user avant le chat.
- 3 options proposées à Sinse (A légère wizard webapp / B sérieuse + auto-éval / C refonte complète). Scope pas encore choisi.
- Aparté opérationnel : migration claude auto-updater vers native install user-local (`~/.local/bin/claude` v2.1.92). Plus besoin de sudo pour futurs updates.

## 2. Working tree
- Branch: main
- Modified: 0
- Unpushed: 0
- Clean: yes

## 3. Branch/PR/CI
- Ahead of main: 0 commits
- PR: none
- CI: none

## 4. Tests/checks
- smoke-test --deep: 20 passed / 0 failed / 0 warnings (ALL CLEAR)
- Manual: vérifié absence `onboarding_done` DB + absence route `/onboarding` frontend + existence workflow n8n dify-diagnostic

## 5. Next steps
1. Sinse choisit scope (Option A/B/C) avant toute implémentation
2. Selon choix : créer route `/onboarding` SvelteKit + endpoint `POST /api/me/onboarding` FastAPI + colonne `users.onboarding_done` + gate layout
3. Brancher Teacher avec `display_name` pré-rempli via dify-profil-get (éviter que Teacher redemande le prénom)

## 6. Risks/gotchas
- Teacher chatflow fait déjà onboarding côté chat (Phase 1+2). Toute refonte doit coexister ou remplacer proprement, sinon double-onboarding.
- Utilisateurs existants (nico, julien, noz_project, waigosan, 0tha) ont des `profils_eleves` plus ou moins complets — prévoir migration pour ne pas les forcer à refaire l'onboarding.
- `mode_apprentissage` (structure/libre) est choisi en Phase 1 chat. À décider : garder dans chat ou déplacer en wizard webapp.

## 7. Open questions
- Waiting for Sinse on: choix scope (A/B/C) + quel problème concret observé (drop-off, confusion, abandon diagnostic ?) qui motive la refonte.
