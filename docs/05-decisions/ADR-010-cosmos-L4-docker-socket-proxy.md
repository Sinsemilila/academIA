---
title: ADR-010 — Cosmos L4 — docker-socket-proxy
status: accepted
last_reviewed: 2026-04-16
decision_date: 2026-04-16
authors: [sinse, claude]
---

# ADR-010 — Cosmos L4 hardening via `tecnativa/docker-socket-proxy`

## Contexte

Cosmos-server (`azukaar/cosmos-server@sha256:b7faf38...`, hardened L1-L3 en Session 18 ter) reste à ce stade le seul conteneur du stack monté sur `/var/run/docker.sock` en **RW direct**. Cela reste la surface d'attaque la plus lourde : un attaquant qui compromet cosmos (via une CVE, une faille de route, ou un routage reverse proxy mal configuré) obtient un accès **complet** à l'API Docker — création de conteneurs, mount arbitraire de l'host, build d'images malicious, accès aux secrets Swarm, etc.

Session 18 ter avait acté L4 en **backlog pré-SaaS public** ; le déployment Phase 7.1 (spaced retrieval activé en prod) rapproche l'échéance où le stack sera potentiellement exposé à des utilisateurs externes (famille élargie → tests early users → SaaS). L4 se justifie maintenant avant que la surface utilisateur grandisse.

## Options envisagées

### Option A — Accepter le risque, attendre L5 (cosmos → traefik)

- Pour : L5 (remplacement complet du reverse proxy par traefik/caddy) résout le problème **en supprimant la dépendance à cosmos** — plus besoin du socket docker. L4 devient caduque.
- Contre : L5 est un refactor lourd (~1-2 jours — DNS, routes, OIDC, Cloudflare tunnel) qui reste en backlog depuis Session 18. Accepter le RW direct en attendant laisse une fenêtre ouverte.

### Option B — L4 via `tecnativa/docker-socket-proxy` (retenue)

- Pour : déploiement rapide (~45 min), réversible via script (`cosmos-pre-L4-rollback.sh`), gain de sécurité mesurable **maintenant** — bloque `/build`, `/commit`, `/services`, `/plugins`, `/secrets`, `/configs` + empêche le démarrage des exec instances.
- Contre : limitation connue du proxy — `CONTAINERS=1` inclut `/containers/{id}/exec` (création d'exec instances). Les instances créées sont **dormant** (start bloqué par `EXEC=0`), mais l'API de création elle-même passe. Un attaquant sophistiqué pourrait chercher une autre voie d'exécution. Protection imparfaite, pas un remplacement de L5.

### Option C — Fork du proxy avec règles haproxy custom

- Pour : contrôle granulaire parfait — pourrait bloquer `/containers/{id}/exec` ET tout le reste nécessaire à cosmos.
- Contre : dette technique durable, divergence upstream, maintenance non-triviale. Pas justifié pour le gain marginal.

## Décision

**Option B retenue** — déployer `tecnativa/docker-socket-proxy:0.3.0` en `restart always`, sur `127.0.0.1:2375` (bind host, localhost-only, jamais exposé à l'extérieur), lui-même monté sur `/var/run/docker.sock:ro`.

Permissions env vars (minimum viable pour que cosmos fonctionne) :
- `CONTAINERS=1, NETWORKS=1, INFO=1, VERSION=1, EVENTS=1, IMAGES=1, VOLUMES=1, POST=1`
- **Deny** : `EXEC=0, BUILD=0, COMMIT=0, SERVICES=0, TASKS=0, PLUGINS=0, SECRETS=0, CONFIGS=0`

Cosmos-server rewiring :
- **Supprimer** le mount `/var/run/docker.sock`
- **Ajouter** `DOCKER_HOST=tcp://127.0.0.1:2375` env var
- Tout le reste identique (digest pin, hostname, cgroupns, cap_add CAP_NET_ADMIN, `/:/mnt/host:ro`)

**Justification** : L4 via proxy ferme **6 endpoints dangereux** (build, commit, services, plugins, secrets, configs) et empêche le démarrage d'exec instances, tout en restant rapide à déployer et **entièrement réversible**. La limitation exec-creation est documentée. L5 (remplacement cosmos par traefik/caddy) reste l'objectif final, mais n'est pas un blocage pour déployer L4 maintenant.

## Conséquences

- **Positives** :
  - L'attaquant via cosmos ne peut plus : build d'images (via `/build`), committer un conteneur en image (via `/commit`), lister/créer des services Docker Swarm, accéder aux plugins/secrets/configs stockés par le daemon, démarrer un exec attacher dans un conteneur (via `/exec/{id}/start`).
  - Proxy hardened lui-même : `--cap-drop ALL`, `--security-opt no-new-privileges`, socket monté RO, jamais exposé au-delà de 127.0.0.1.
  - Rollback trivial (< 60s) si cosmos UI casse — script prêt à `/opt/academia-shared/secrets/cosmos-pre-L4-rollback.sh`.

- **Négatives acceptées** :
  - `POST /containers/{id}/exec` passe (mais l'exec instance créée reste dormant — le start est bloqué par EXEC=0). Protection imparfaite mais effective.
  - Cosmos peut toujours arrêter/démarrer/redémarrer **tous les conteneurs** (nécessaire pour la fonction de management). Un attaquant pourrait stopper les services.
  - Cosmos peut toujours lister les images (`IMAGES=1`) et volumes (`VOLUMES=1`) — lecture seule, pas de pull.

- **Neutres (à surveiller)** :
  - Latence ajoutée par le proxy : négligeable (haproxy, <1ms en boucle locale).
  - Si upstream `tecnativa/docker-socket-proxy` pousse une image compromise → risk supply-chain. Mitigation = pinner le digest (`tecnativa/docker-socket-proxy:0.3.0` actuel, TODO digest-pin dans runbook).
  - Cosmos écrit proactivement son `cosmos.docker-compose.yaml` (gotcha Session 20) → la YAML peut diverger du runtime (le runtime est source de truth). Documenter : "ne PAS cliquer Redeploy dans cosmos UI" sans resync YAML.

## Actions de mise en œuvre

- [x] (claude, 2026-04-16) Deploy `tecnativa/docker-socket-proxy:0.3.0` avec env vars minimum viable, bind 127.0.0.1:2375.
- [x] (claude, 2026-04-16) Backup rollback script `/opt/academia-shared/secrets/cosmos-pre-L4-rollback.sh` (chmod +x).
- [x] (claude, 2026-04-16) Remplacement cosmos-server via `docker rm + docker run` (suppression mount docker.sock + ajout DOCKER_HOST env).
- [x] (claude, 2026-04-16) Verify : smoke deep 21/21 ALL CLEAR, proxy logs montrent trafic cosmos (inspect, networks, containers/json, stats).
- [ ] Sinse : valider cosmos.petit-pont.com UI fonctionne (list containers, logs, restart manuel OK). Retour d'info attendu dans cette session.
- [ ] (cron/manuel) : à J+7 (2026-04-23), supprimer `cosmos-pre-L4-rollback.sh` si L4 reste stable.
- [ ] (post-MVP) : pin digest `tecnativa/docker-socket-proxy@sha256:9e4b9e7517a6b660...` dans la commande `docker run` pour figer la supply chain.

## Re-évaluation

Cette ADR doit être re-examinée si :
- L5 (remplacement cosmos par traefik/caddy) est entrepris → L4 devient caduque (plus de docker.sock à protéger).
- Le bug CVE critique émerge dans cosmos-server → décision de accélérer L5.
- La limitation exec-creation est exploitée IRL → dur-prendre L4 (forker le proxy ou custom haproxy rules).
- Après 3 mois d'usage stable → envisager tighter permissions (IMAGES=0 si cosmos n'en a jamais besoin, VOLUMES=0 idem).

## Références

- tecnativa/docker-socket-proxy : https://github.com/Tecnativa/docker-socket-proxy
- Rollback script : `/opt/academia-shared/secrets/cosmos-pre-L4-rollback.sh`
- ADR L2/L3 prior : Sessions 18 ter, non formalisés en ADR à l'époque (voir `docs/99-runbooks/gotchas.md`)
- Runbook cosmos : `docs/99-runbooks/gotchas.md` — section Cosmos (à mettre à jour, marquer L4 appliqué)
- Files impactés : runtime cosmos-server (incantation `docker run`), `cosmos-pre-L4-rollback.sh`
