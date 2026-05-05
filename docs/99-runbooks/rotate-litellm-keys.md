---
title: Rotate LiteLLM API keys
status: draft
last_reviewed: 2026-04-15
---

# Rotate LiteLLM API keys

> Procédure pour roter une clé API LLM (OpenAI, Groq, Mistral) sans downtime.

**Statut** : `draft` — à solidifier après la migration SOPS (cf. [credentials.md](../04-infra/credentials.md)).

## Scénarios de rotation

1. **Clé suspectée compromise** (leak, commit accidentel, partage non souhaité) — rotation immédiate
2. **Clé rate-limit épuisée** — ajouter une nouvelle clé en parallèle (load-balancing)
3. **Contributeur BYOK retire sa clé** — retirer de la config
4. **Rotation préventive** (recommandée : tous les 90 jours)

## Procédure actuelle (dette — SOPS pas encore en place)

### Étape 1 — Obtenir la nouvelle clé

- Pour OpenAI : [platform.openai.com/api-keys](https://platform.openai.com/api-keys), créer une nouvelle clé
- Pour Groq : [console.groq.com/keys](https://console.groq.com/keys)
- Pour Mistral : [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)

### Étape 2 — Éditer `/opt/litellm/config.yaml`

```bash
ssh cosmos
sudo vim /opt/litellm/config.yaml
```

Trouver le bloc du modèle concerné :
```yaml
- model_name: gpt-4o-mini
  litellm_params:
    model: openai/gpt-4o-mini
    api_key: "sk-proj-OLD_KEY_HERE"       # ← remplacer
```

### Étape 3 — Restart LiteLLM

```bash
docker restart litellm-proxy
```

**Downtime** : ~10 secondes. Les chats en cours retry via la logique LiteLLM fallback (`num_retries: 3`).

### Étape 4 — Vérifier

```bash
curl -s http://localhost:4000/health/readiness | jq
# Expect: "status": "healthy"

# Test inline
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-master-key" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' | jq
```

### Étape 5 — Révoquer l'ancienne clé

- Retourner sur la console provider
- **Révoquer** (delete) l'ancienne clé
- Ne pas laisser "just in case" — la dette s'accumule

### Étape 6 — Logger

Dans `CHANGELOG.md` :
```bash
log security "rotated <provider> API key (reason: <X>)"
```

## Procédure cible (post-SOPS)

```bash
# Édit en local, SOPS decrypt → edit → encrypt
sops /opt/academia/secrets/litellm.yaml.enc

# Rebuild + redeploy container avec nouveau secret
docker compose -f /opt/litellm/docker-compose.yml up -d --force-recreate

# Révoquer côté provider + log
```

## Cas spécifique — ajouter une clé BYOK d'un contributeur

**Précondition** : migration SOPS effective (cf. [credentials.md](../04-infra/credentials.md)). **Ne pas ajouter de clé BYOK avant cette migration.**

### Étapes (post-SOPS)

1. Obtenir la clé du contributeur (chat privé, pas par email)
2. Ajouter un bloc `model_list` en plus de l'existant (même `model_name`, LiteLLM load-balance) :
   ```yaml
   - model_name: gpt-4o-mini
     litellm_params:
       model: openai/gpt-4o-mini
       api_key: "sk-proj-NEW_BYOK_KEY"
     model_info:
       owner: "prénom-du-contributeur"
       tier: "free"
   ```
3. Encrypt via SOPS, commit, deploy
4. Vérifier que LiteLLM route vers les 2 clés (`routing_strategy: usage-based-routing-v2`)
5. Monitorer `LiteLLM_SpendLogs` pour vérifier répartition

### Rotation / révocation d'une clé BYOK

Si le contributeur retire sa clé :
- Le bloc correspondant doit être retiré de `config.yaml`
- Restart LiteLLM
- Vérifier qu'aucune request ne route vers un modèle 404

## Impact chez les users

**Aucun impact perceptible** si rotation bien faite :
- Chats actifs : retry automatique via fallback chain
- Nouveaux chats : routés vers la nouvelle clé
- Budget tokens : continuité (compteur local + SpendLogs tenus en parallèle)

## Références

- [credentials.md](../04-infra/credentials.md) — stratégie globale
- [ADR-006](../05-decisions/ADR-006-litellm-byok-familial.md) — pool BYOK
- [deployment.md](../04-infra/deployment.md) — stack LiteLLM
- [`/opt/litellm/config.yaml`](file:///opt/litellm/config.yaml) — config actuelle
