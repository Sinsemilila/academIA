---
title: ADR-006 — LiteLLM BYOK familial pour les coûts LLM
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [sinse, claude]
---

# ADR-006 — LiteLLM BYOK familial pour les coûts LLM

## Contexte

Le produit doit **rester gratuit** tant qu'il reste familial/amis (&lt; ~20 users). Les tokens gpt-4o-mini "free tier" d'OpenAI ne suffisent que partiellement (limite quotidienne 1.5M pour notre setup actuel). Besoin de scalabilité gratuite multi-providers.

Question : comment assurer la disponibilité LLM à coût zéro à cette échelle ?

## Options envisagées

### Option A — 1 seule clé OpenAI, gpt-4o-mini payant dès dépassement free tier

- Pour : simple
- Contre : coût non-nul dès dépassement, dépendance mono-provider

### Option B — Pool de clés familial via LiteLLM (BYOK)

Plusieurs amis/proches fournissent chacun leur clé OpenAI/Groq/Mistral free tier. LiteLLM load-balance entre elles.

- Pour : gratuit total, redondance, plusieurs providers (Groq pour latency, Mistral pour FR/ES, OpenAI pour qualité)
- Contre : demander à des proches, risque de révocation d'une clé, gestion de rotation

### Option C — Self-hosting Llama/Qwen sur cosmos

- Pour : indépendance totale
- Contre : GPU inexistant sur cosmos, CPU inference trop lente

## Décision

**Option B — Pool BYOK via LiteLLM** (déjà TODO P4).

**Justification** :
- LiteLLM existe déjà dans le stack avec `routing_strategy: usage-based-routing-v2` qui load-balance nativement sur plusieurs clés du même modèle
- Providers free tier cumulables : OpenAI (gpt-4o-mini), Groq (Llama 3.3 70B, Mixtral), Mistral (mistral-small) — chacun avec son propre quota
- Config déjà préparée dans `/opt/litellm/config.yaml` avec blocs commentés à activer quand les clés sont fournies

## Conséquences

- Positives : coût quasi-nul à l'échelle familiale, redondance naturelle, multi-provider
- Acceptées : contrainte sociale (demander aux proches), risque qu'une clé soit révoquée (LiteLLM fallback prévu)
- Acceptées : complexité opérationnelle de rotation de clés (runbook à écrire)

## Actions de mise en œuvre

- [ ] Collecter les clés Groq d'amis (TODO P4 existant)
- [ ] Collecter les clés Mistral d'amis (TODO P4 existant)
- [ ] Décommenter les blocs correspondants dans `/opt/litellm/config.yaml`
- [ ] Restart LiteLLM proxy
- [ ] Écrire runbook `99-runbooks/rotate-litellm-keys.md`
- [ ] Monitorer les quotas par clé via `LiteLLM_DailyUserSpend` (table existe)

## Re-évaluation

À réviser si :
- Passage SaaS public avec &gt; 100 users actifs → obligation de monétiser, passer en paid tier
- Instabilité récurrente (clés révoquées, rate limits trop serrés)
- Arrivée d'un open model compétitif self-hostable (Qwen 72B/Llama 70B sur GPU loué)

## Références

- [ADR-001-monolith-vs-microservices.md](ADR-001-monolith-vs-microservices.md)
- TODO workspace P4 — "LLM pool BYOK"
- Session 12 (2026-04-15) — discussion coûts
