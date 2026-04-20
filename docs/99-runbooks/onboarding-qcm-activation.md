---
title: QCM onboarding — activation runbook
status: authoritative
last_reviewed: 2026-04-20
owner: claude
---

# QCM onboarding pre-chat — activation + monitoring

**Activé** : 2026-04-20 (Session 33, Sprint 5 Phase 5)
**Flag** : `QCM_ONBOARDING_ENABLED = true` dans `webapp/frontend/src/lib/config.ts`
**Revisit** : J+7 (2026-04-27) — review insert rate + drop-off + bugs Session 32

## Ce qui change

1. Modal bloquant 1re visite par domaine (Teacher/Maestro) avant accès chat
2. 8 items + 1 mini-probe conditionnelle (Bloc A universel + Bloc B can-do CEFR bi-skill + Bloc C Ideal L2 Self + FLA)
3. Profil persisté dans `learner_profiles` (JSONB 3 sections + `derived_tutor_hints`)
4. Injection Karpathy-style dans Dify inputs à chaque chat turn : `learner_profile_json` + `learner_profile_summary`
5. Placement CEFR conservateur : `min(comprehension, production) - 0.5 palier` + correction mini-probe

## Architecture

```
Frontend
  routes/chat/[agent]/+page.svelte (QCM_ONBOARDING_ENABLED gate)
    └── if !learner_profile → OnboardingModal.svelte (10 screens)
         └── submit → POST /api/learner-profile/{domain}

Backend
  onboarding_router.py (GET content / GET profile / POST / PATCH)
    └── _compute_derivations + _compute_tutor_hints + _render_nl_summary

  chat_router.py:487+ fetch learner_profiles
    └── dify_inputs["learner_profile_json"] = JSON compact
    └── dify_inputs["learner_profile_summary"] = NL ≤ 200 mots

Dify chatflow (Teacher + Maestro)
  Start node → 2 new inputs (learner_profile_json, learner_profile_summary)
    └── code_turn_check wires them for downstream
         └── llm_session, llm_plan_choice : prepend <learner_profile>{{#code_turn_check.learner_profile_summary#}}</learner_profile>
    └── llm_onboarding : branche bypasse code_turn_check (KNOWN, fix pending)

DB
  learner_profiles (5 ENUMs, 3 JSONB, unique eleve+domain+target_language, trigger updated_at)
```

## Monitoring

```bash
bash /opt/academie/scripts/ops/monitor_qcm_onboarding.sh
```

Affiche : inserts par domain (total / last_1h / last_24h) + 10 derniers QCM + users legacy pas encore re-onboardés + warnings `academie-api` + rollback commands.

### Seuils attendus J+7 (2026-04-27)

| Métrique | Seuil | Action si sous |
|---|---|---|
| `learner_profiles` INSERTs total | ≥ 3 (famille test) | Vérifier modal s'ouvre correctement : flag ON + 404 `GET /api/learner-profile/{domain}` |
| Drop-off mid-QCM (localStorage draft orphelin) | < 20 % | Check durée UX réelle : peut-être ajuster nb items ou wording |
| Warnings `learner_profiles fetch failed` | 0 | Exception loggée dans `chat_router.py:521` — investiguer DB state |
| Dify error `Variable #... not found` | 0 | `docker logs dify-worker \| grep not_found` — vérifier que revert Phase 12 tient |

## Gotchas

- **Dify onboarding-branch wiring** (Session 33 bug → Session 34 fix) : la branche `llm_onboarding` bypasse `code_turn_check` ET refuse les refs `{{#start.X#}}`. Seul node commun aux 2 branches `if_profil` = `code_profil_check`. Fix appliqué via `scripts/sprint5/13_wire_onboarding_branch.py` (wire vars dans `code_profil_check` + prepend `<learner_profile>{{#code_profil_check.learner_profile_summary#}}</learner_profile>` dans `llm_onboarding`) + `14_strengthen_llm_onboarding_override.py` (block `QCM_OVERRIDE_v1` à la FIN du system prompt pour forcer skip FASE 1 FR). Nouveaux ET retournants users bénéficient maintenant de l'injection profil au turn 1. Validation live Maestro OK 2026-04-20 (palier A1 respecté, 100% ES, zero Phase 1 FR).
- **Placeholder `{{language_display_fr}}`** dans les prompts (core.yaml + language.yaml) rendu côté backend (`academie_core.data.loader.load_onboarding_content`). Pour domaines non-langue (pymentor, cybermentor stubs), placeholder reste littéral — acceptable car items Bloc B+C sont vides en v1.
- **D6 legacy users** : 19 users EN + 0 ES avaient `profils_eleves` sans `learner_profiles` au moment de l'activation. Ils verront le modal fresh au prochain chat. Leur `profils_eleves.niveau_global` reste intact (observationnel) et continue d'être lu par chat_router.
- **Mini-probe conditionnelle** : déclenche si `max(cefr_comprehension, cefr_production) >= B1`. Scoring v1 = regex (strong/medium/weak depuis overlay). Fallback LLM-as-judge gpt-4.1-mini configuré dans les overlays mais pas encore wiré backend — à ajouter si le regex manque trop de cas.

## Rollback (5 min)

```bash
sed -i "s/QCM_ONBOARDING_ENABLED = true/QCM_ONBOARDING_ENABLED = false/" /opt/academie/webapp/frontend/src/lib/config.ts
cd /opt/academie/webapp
docker compose -f docker-compose.webapp.yml build academie-frontend
docker compose -f docker-compose.webapp.yml up -d academie-frontend
```

Table `learner_profiles` et endpoints backend conservés pour re-activation sans re-migration. Les données collectées restent disponibles. Le chat_router injecte toujours les dify inputs (défaut `{}` et `""` si pas de row) → Dify continue de fonctionner en mode legacy.

### Rollback complet (nuke)

```bash
# Dify chatflow : restore from backup
docker exec -i postgres-academie psql -U sinse -d academie_db <<'EOF'
UPDATE workflows w SET graph = b.graph, conversation_variables = b.conversation_variables
FROM dify_workflows_backup_sprint5_phase5 b
WHERE w.id = b.id;
EOF
docker restart dify-api dify-worker

# DB : drop table
docker exec -i postgres-academie psql -U sinse -d academie_db -f /opt/academie/scripts/sprint5/10_rollback_learner_profiles.sql

# Backend : flip ENABLE_QCM_ONBOARDING=false in env (optional, not currently used) + rebuild
cd /opt/academie/webapp
docker compose -f docker-compose.webapp.yml build academie-api academie-frontend
docker compose -f docker-compose.webapp.yml up -d academie-api academie-frontend
```

## Rotation QCM items (v2+)

Pour modifier les items (ajouter/retirer/reformuler) sans migration DB :

1. Éditer `packages/academie-core/academie_core/data/onboarding/{core,domains/*,overlays/*}.yaml`
2. Bump `version` dans le YAML (semver)
3. Valider parse : `python3 -c "import yaml; yaml.safe_load(open('packages/academie-core/academie_core/data/onboarding/core.yaml'))"`
4. Rebuild academie-api (loader a `@lru_cache(maxsize=16)`) : `docker compose build academie-api && docker compose up -d academie-api`
5. Les anciens `learner_profiles` rows restent valides (`schema_version` field) — si le nouveau schéma casse la compat, incrementer v2+ dans `_compute_derivations` et gérer branching dans le router

**Pas de migration DB tant que** la structure `universal_block / domain_level / domain_motivation / derived_tutor_hints` reste JSONB-compat.

## Références

- Plan : `/root/.claude/plans/atomic-beaming-alpaca.md`
- Recherche : `docs/00-project/onboarding-research-2026-04-20/` (7 rapports vague1+2)
- Décision : `docs/decisions.md` #17 (2026-04-20)
- Scripts :
  - Migration : `scripts/sprint5/10_create_learner_profiles.sql`
  - Dify patch : `scripts/sprint5/11_update_dify_onboarding_qcm.py`
  - Hotfix onboarding-branch : `scripts/sprint5/12_revert_llm_onboarding_prepend.py`
  - Monitor : `scripts/ops/monitor_qcm_onboarding.sh`
- Tests : `scripts/sprint5/tests/test_onboarding_helpers.py` (11/11 pass)
