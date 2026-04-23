# A1-cleanup — Redis AOF persistence (Refactor 2026-H2)

**Status** : appliqué live 2026-04-23 (CONFIG SET appendonly yes)
**Last updated** : 2026-04-23
**Related** : [`a1-sessions-redis.md`](a1-sessions-redis.md)

## Contexte

Sessions opaques Redis livrées Session 46 (commit `941299b`). Persistance par défaut `appendonly = no` → seul un snapshot RDB toutes les `3600s 1` (heuristique save). Risque : un crash entre deux snapshots = users déconnectés.

## Action appliquée

```bash
docker exec redis-academie redis-cli CONFIG SET appendonly yes
# → OK
docker exec redis-academie redis-cli INFO persistence | grep aof_enabled
# → aof_enabled:1
```

## Limitation connue

Le container `redis-academie` a été créé sans config-file (probablement via Cosmos UI). `CONFIG REWRITE` retourne `ERR The server is running without a config file`. **Conséquence** : un `docker recreate` du container perdra le setting AOF (retombe sur `appendonly = no`).

## Reco persistance permanente (manuel Sinse)

Quand convenient, recréer le container avec `--appendonly yes` :

```bash
docker stop redis-academie
docker commit redis-academie redis-academie-snapshot:pre-aof  # optional safety
docker rm redis-academie

docker run -d \
  --name redis-academie \
  --network academie-net-bridge \
  --restart unless-stopped \
  -v 7f51671da32529d2a0b0d679c6b52a3ab9496c594dbabdee97085ad24da77823:/data \
  redis:7-alpine \
  redis-server --appendonly yes
```

Le volume nommé `7f516...` contient les données existantes — il faut le re-attacher.

**Risque** : si un user a une session active au moment du recreate, elle sera perdue (re-login). 1 user actif (sinse, dogfood). Acceptable.

## Alternative : intégrer dans docker-compose.webapp.yml

Plus propre long terme : ajouter le service `redis-academie` dans `webapp/docker-compose.webapp.yml` avec `command: ["redis-server", "--appendonly", "yes"]`. Permet `docker compose up` reproductible. À faire si Sinse veut consolider la stack.
