---
title: Monitoring
status: draft
last_reviewed: 2026-04-15
---

# Monitoring

> État actuel (basique) + cible (enrichie) + KPIs produit à définir.

## État actuel

### Health checks automatiques

- **smoke-test** outil sur PATH, modes `--quick`, `--deep`, `--infra`, `--all`
- Vérifie : containers running, HTTP endpoints, DB queries, LiteLLM health, **n8n fail rate (48h)**
- Intégré au workflow : `/pickup` lance `--quick`, `/handoff` lance `--deep` pre-push
- Hook pre-push git : `smoke-test --deep` blocant
- Résultat : 15/15 quick en vert habituel

#### Alerte n8n fail rate (depuis Session 15, 2026-04-15)

Requête lancée à chaque `--quick` :
```sql
SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE status='error') / NULLIF(COUNT(*),0), 1)
FROM execution_entity
WHERE "startedAt" > NOW() - INTERVAL '48 hours';
```

Seuil : **> 5.0%** → warning (non-bloquant). Permet de détecter une régression workflow (ex : Dify endpoint qui répond 500, LLM qui renvoie du JSON malformé) sans attendre le handoff manuel.

### Widget admin token usage

- Frontend : `/admin` affiche
  - Barre quota gpt-4o-mini (journalier, % du 1.5M limit)
  - Source LiteLLM (truth) ou estimation locale
  - Breakdown par modèle (gpt-4o-mini + ft:gpt-4o-mini-v3)
  - Model actif courant
  - Warning si quota dépassé
- Backend : `/api/chat/token-usage` lit `LiteLLM_SpendLogs` avec fallback `token_usage_daily`

### Logs containers

- `docker logs <container>` brut, rotation par défaut
- Pas d'agrégation centralisée
- Pas de parsing structuré
- FastAPI logue en format structuré (via `logging.basicConfig`) mais sortie stdout/docker seulement

### Pas encore en place

- ❌ Métriques système (CPU, RAM, disque, réseau)
- ❌ Métriques applicatives (latence endpoints, RPS, erreurs par route)
- ❌ Alerting (email/slack/pushover)
- ❌ Dashboard consolidé (Grafana)
- ❌ Error tracking (Sentry / similar)
- ❌ APM / tracing distribué
- ❌ A/B testing infrastructure

## Cible court terme

### 1. Logs agrégés

Option simple : **loki + promtail** (Grafana stack) ou **vector + SQLite/postgres**.

Cas d'usage : chercher "erreur dans error_analysis hier entre 14h et 16h" sans faire `docker logs` de 3 containers.

### 2. Métriques basiques

**prometheus** + node_exporter + pg_exporter + redis_exporter + custom FastAPI exporter.

Vue : CPU/RAM des containers, DB query counts, FastAPI RPS/latency p50/p95/p99.

### 3. Dashboard Grafana

Vues :
- System health (CPU, RAM, disque)
- Application (RPS, latency, erreurs 4xx/5xx par route)
- Business (nb users actifs jour, nb messages envoyés, tokens consommés, cost $)
- LLM (par modèle : tokens/s, latency, failure rate)

### 4. Alerting minimal

- Disk > 80% → email/push à Sinse
- LiteLLM unreachable > 2 min → push
- FastAPI 5xx rate > 1% sur 5 min → push
- Daily PG backup failed → push

## Cible long terme (SaaS public)

Quand users > 100 :
- **Sentry** (ou équivalent open source comme GlitchTip) pour error tracking structuré
- **Tracing distribué** (OpenTelemetry) pour trace les appels multi-services
- **Synthetic monitoring** : bot qui joue un scénario utilisateur toutes les 5 min
- **SLA dashboard** (uptime 99.x%)

## KPIs produit à mesurer

**Proposition à valider** — quelle définition de "le produit marche" ?

### Engagement
- DAU / WAU / MAU (daily/weekly/monthly active users)
- Sessions par user par semaine
- Durée moyenne de session
- Taux de rétention à J+7, J+30, J+90

### Progression pédagogique
- Niveau CECRL moyen des users par cohorte
- Taux de progression de niveau sur 30 jours
- % users qui complètent l'onboarding
- Distribution des tiers d'erreur par niveau (si matrice bien calibrée, distribution attendue)

### Qualité du feedback
- % corrections "acceptées" par l'user (si on implémente un système de ack)
- Taux de recurrence d'erreur après feedback T3 (via spaced retrieval queue)
- Half-life d'erreur par famille × niveau (Cox PH)

### Coûts
- Tokens/jour par provider
- $/user/mois
- Coût marginal d'un nouveau user

### Qualité LLM
- Taux de faux positifs en error detection (sample manuel)
- Taux d'overcorrection (comparaison rules vs LLM)
- Drift CECRL dans conversations longues

## A/B testing infrastructure

Actuellement aucune. Quand on voudra mesurer l'impact d'une refonte de prompt ou d'un changement de taxonomie :

- Random assignment user → variant au login (cookie ou user_id hash)
- Track metric par variant (ex : rate of "correction accepted", duration of session)
- Durée test : >= 2 semaines avec >= 30 users par bras

Outils possibles : `growthbook` (open source) ou simple implémentation custom en BD.

## Re-évaluation

À re-évaluer à chaque Sprint : est-ce qu'on a besoin de monitoring plus riche pour valider ce qu'on fait ?

## Références

- [deployment.md](deployment.md) — stack actuel
- [../02-architecture/overview.md](../02-architecture/overview.md) — topologie
- Outils existants : `smoke-test`, widget `/admin`
- Cibles futures : Grafana, Prometheus, Loki, Sentry / GlitchTip
