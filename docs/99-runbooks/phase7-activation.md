---
title: Phase 7.1 — Spaced Retrieval Activation Runbook
status: authoritative
last_reviewed: 2026-04-16
owner: claude
---

# Phase 7.1 — Spaced Retrieval Activation

**Activated** : 2026-04-16 (Session 23, after Phase 7 MVP shipped in commit `00cd2b5`)
**Flag** : `SPACED_RETRIEVAL_ENABLED=true` dans `/opt/academie/webapp/.env`
**Revisit target** : 2026-04-23 (+7 days) — review telemetry + decide next steps

## What changed

Le flag active les helpers `chat_router._fetch_due_retrieval_items` + `_persist_spaced_retrieval` :

- **Pre-turn** : à chaque chat, query `spaced_retrieval_queue WHERE eleve_id=X AND scheduled_at <= NOW() AND completed_at IS NULL LIMIT 3` → populer `ctx.spaced_retrieval_due` → le block `{{spaced_retrieval_today}}` est rendu dans PROMPT_SESSION_V2 avec le header `AUJOURD'HUI ON REVISITE`.
- **Post-turn** (dans `stream_with_xp` après collecte du full_answer) : parse le JSON Teacher → si `silenced_for_spaced_retrieval` non-vide, INSERT dans queue à `scheduled_at = NOW() + 1 day` ; si `spaced_retrieval_addressed` non-vide, UPDATE les rows matchées `completed_at = NOW(), outcome = 'addressed'`.

## Monitoring

Script : `/opt/academie/scripts/ops/monitor_spaced_retrieval.sh`

```bash
./scripts/ops/monitor_spaced_retrieval.sh
```

Affiche trois blocs :
- **TOTAL** : enqueued, completed, completion_pct, hours_since_first
- **PER ELEVE** (top 20 par enqueued)
- **BY ERROR FAMILY** (top 10)

### Seuils attendus à J+7 (2026-04-23)

| Métrique | Seuil attendu | Si sous le seuil → action |
|---|---|---|
| `enqueued` total | ≥ 5 | Check `docker logs academie-api \| grep spaced_retrieval` — peut-être aucune erreur silenced détectée (dosage budget jamais saturé avec le trafic actuel sparse) |
| `completion_pct` | ≥ 20 % | LLM V2 n'émet pas `spaced_retrieval_addressed` dans son JSON. Ajouter hint explicite dans `build_spaced_retrieval_block` : "⚠️ In your output JSON, add `spaced_retrieval_addressed: [\"concept_key\"]` for items you revisited." |
| p95 latence `/api/chat/send` | < Phase 6 baseline + 50ms | Rollback immédiat si +200ms+, investiguer pool size |
| Rows per user per day | ≤ 10 | Ajouter dedupe cron (Phase 7.2) |

## Verification (post-activation 2026-04-16)

✅ `SPACED_RETRIEVAL_ENABLED = True` dans le module Python (check via `docker exec academie-api python3 -c "from app.routers import chat_router; print(chat_router.SPACED_RETRIEVAL_ENABLED)"`)
✅ `smoke-test --quick` 15/15 ALL CLEAR
✅ `scripts/sprint3/tests/test_spaced_retrieval.py` 6/6 pass (flag ON + OFF scenarios)
✅ Monitor script s'exécute, queue vide initialement (no trafic producteur depuis activation)

## Rollback

En cas de régression observée (crash, latence +200ms, data corruption, etc.) :

```bash
# 1. Remove flag from .env
sudo sed -i '/^SPACED_RETRIEVAL_ENABLED=/d' /opt/academie/webapp/.env
sudo sed -i '/^# Sprint 3 Phase 7.1 activation/d' /opt/academie/webapp/.env

# 2. Recreate container (picks up removed env)
cd /opt/academie/webapp && docker compose -f docker-compose.webapp.yml up -d academie-api

# 3. Verify flag False
docker exec academie-api python3 -c "from app.routers import chat_router; print(chat_router.SPACED_RETRIEVAL_ENABLED)"
# Expect: False
```

**Pas de cleanup DB nécessaire** : les rows déjà inserées dans `spaced_retrieval_queue` sont orphelines inoffensives — flag OFF → fetch retourne `[]`, persist est no-op. Si tu veux clean complètement :

```bash
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "DELETE FROM spaced_retrieval_queue WHERE created_at >= '2026-04-16';"
```

## Deferred (post-activation)

- **Phase 7.2** — regression ladder J+3/J+7 + dedupe cron
- **Phase 7.3** — FSRS scheduling (remplace intervalle fixe par algo adaptatif)
- **`last_error_summary` column** : enrichir au-delà de l'error_code (join avec error_log ou colonne dédiée)

## References

- Phase 7 MVP commit : `00cd2b5`
- Unit tests : `scripts/sprint3/tests/test_spaced_retrieval.py`
- Helpers : `webapp/backend/app/routers/chat_router.py` — `_fetch_due_retrieval_items`, `_persist_spaced_retrieval`
- Block builder : `webapp/backend/app/teacher_prompt.py` — `build_spaced_retrieval_block`
- Design doc : `docs/01-pedagogy/sprint3_design.md` §7 (spaced retrieval)
