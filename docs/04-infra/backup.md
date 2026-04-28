---
title: Backup Strategy
status: authoritative
last_reviewed: 2026-04-15
---

> **Changelog 2026-04-15 (Session 15)** : `litellm_db` + `dify_plugin` ajoutés au dump horaire. Weekly/monthly rotation pas cassée — simplement pas encore déclenchée (cron depuis 2026-04-13 Lundi ; premier Dimanche = 2026-04-19 ; premier 1er du mois = 2026-05-01).

# Backup Strategy

> 4 niveaux de protection : VM snapshots, DB dumps hourly, chiffré offsite, git pour code.

## Niveaux (théorie vs réalité)

| Niveau | Cible | Où | Fréquence | Rétention prévue | **Rétention réelle (2026-04-15)** |
|---|---|---|---|---|---|
| **1** | VM cosmos complète | Proxmox local (SSD1, 119G) via vzdump | Daily 4h | 7 jours | ⚠️ à auditer via Proxmox UI |
| **2** | PostgreSQL dump (3 DBs : academie_db + litellm_db + dify_plugin) | `/mnt/cosmos-data/backups/postgres/` | Hourly | 24h rolling + daily 7j + weekly 4w + monthly 12m | ✅ **multi-DB actif 2026-04-15** — weekly fires 2026-04-19, monthly 2026-05-01 |
| **3** | Restic chiffré offsite | Google Drive 5TB | Daily 3h30 | 30 daily / 12 monthly / unlimited yearly | ⚠️ à auditer |
| **4** | Git | GitHub (`academIA` code + `sinse-archive-2026-pre-vault` projet archivé) | Per commit | Illimité | ✅ OK |

### Gaps résiduels (post-fix Session 15)

1. ✅ **Niveau 2 scope** : les 3 DBs (`academie_db`, `litellm_db`, `dify_plugin`) sont dumpées hourly depuis 2026-04-15 14:13.
2. ✅ **Rotation weekly/monthly** : script vérifié, fire auto Dimanche 00:00 et 1er du mois 00:00. Patience jusqu'au 2026-04-19 pour voir le premier `weekly/` se peupler.
3. ⚠️ **Aucun test de restauration formel** effectué end-to-end sur les 3 DBs.
4. ⚠️ **Niveau 1 non vérifié** : procédures documentées mais Proxmox UI pas inspectée récemment.

## Niveau 1 — vzdump VM (local + offsite encrypted)

**Session 48 upgrade** : Niveau 1 est devenu **Niveau 1 + offsite encrypted Google Drive** via rclone crypt. 2 copies disponibles après chaque run :
- **Local** (pve-root `/var/lib/vz`, 40 GB LV, retention 1 jour) pour bare-metal recovery rapide
- **Offsite encrypted** (Google Drive via `gdrive-vzdump-crypt` remote, retention 14 jours) pour DR catastrophique

### Configuration

- **Driver** : custom script `/root/vzdump-cosmos.sh` sur host proxmox
- **Cron** : `/etc/cron.d/vzdump-cosmos` → `0 4 * * * root /root/vzdump-cosmos.sh`
- **Compression** : zstd (backup sparse, ~25 GB archive pour VM totale 900 GB / 93% zero data)
- **Mode** : snapshot (minimal downtime)

### Offsite Google Drive encrypted

- **Remote rclone** : `gdrive-vzdump-crypt:` (crypt layer AES-256 sur `gdrive:/Backups/academie/vzdump-encrypted`)
- **Passphrase** : `/opt/academie-shared/secrets/rclone-vzdump-passphrase` (44 bytes base64, 256-bit entropy) + copie sur proxmox `/root/.config/rclone/vzdump-crypt.password`
- **Chain de recovery** : si proxmox meurt → Niveau 3 Restic (cosmos) contient `/opt/academie-shared/` donc passphrase accessible → gdrive offsite déchiffrable depuis n'importe quelle machine rclone-équipée
- **Retention offsite** : `rclone delete --min-age 14d` après chaque upload
- **Timeout upload** : 1h (kill si réseau hangs)
- **Failure non-bloquant** : si gdrive fail, local backup conservé (warning seulement)

### Audits + fixes (Session 48)

- **2 runs consécutifs échoués Apr 22+23** : root cause = `find -mtime +1 -delete` gardait le snapshot d'exactement 24h → 2×24 GB ne rentrait pas dans 40 GB → `no space left on device` à 96%. Fix : suppression inconditionnelle avant backup.
- **Offsite Google Drive** : ajouté Session 48 pour DR catastrophique (avant : zéro copie offsite du VM image, data seule couverte par Restic Niveau 3).

### Restauration

```bash
# Option 1 — depuis local Proxmox (rapide, 1j de rollback)
qmrestore /var/lib/vz/dump/vzdump-qemu-100-LATEST.vma.zst <new_vmid>

# Option 2 — depuis gdrive offsite (14j rollback, bare-metal possible)
# Decrypt + download via rclone sur n'importe quelle machine :
rclone copy gdrive-vzdump-crypt:vzdump-qemu-100-YYYY_MM_DD-HH_MM_SS.vma.zst /tmp/
qmrestore /tmp/vzdump-qemu-100-YYYY_MM_DD-HH_MM_SS.vma.zst <new_vmid>
```

### Backups des scripts (safety)

- `/root/vzdump-cosmos.sh.bak-20260424` — version originale pre-fix `-mtime +1`
- `/root/vzdump-cosmos.sh.bak-pre-gdrive` — version post-fix, pre-offsite (si on veut rollback offsite)

## Niveau 2 — PG dump hourly

- **Script** : `pg-backup` tool (sur PATH)
- **Cron** : `/etc/cron.d/pg-backup` (hourly)
- **Target** : `/mnt/cosmos-data/backups/postgres/`
  - Dumps horaires à la racine : `<db>_YYYY-MM-DD_HHMM.sql.gz` — 3 fichiers par heure :
    - `academie_db_*` ~56 MB
    - `litellm_db_*` ~60 KB
    - `dify_plugin_*` ~15 KB
  - Sous-dossier `daily/` : copie à 00:00 (garde 7 jours glissants)
  - Sous-dossier `weekly/` : copie Dimanche 00:00 (garde 4 semaines)
  - Sous-dossier `monthly/` : copie 1er du mois 00:00 (garde 12 mois)
- **Fréquence** : toutes les heures (cron `/etc/cron.d/pg-backup`)
- **Scope** : **3 DBs** (`academie_db`, `litellm_db`, `dify_plugin`)

Restauration :
```bash
# Ajuster le nom de la DB dans la commande et le fichier
gunzip < /mnt/cosmos-data/backups/postgres/academie_db_YYYY-MM-DD_HHMM.sql.gz \
  | docker exec -i postgres-academie psql -U sinse -d academie_db

# Idem pour litellm_db ou dify_plugin :
gunzip < /mnt/cosmos-data/backups/postgres/litellm_db_YYYY-MM-DD_HHMM.sql.gz \
  | docker exec -i postgres-academie psql -U sinse -d litellm_db
```

## Niveau 3 — Restic encrypted offsite

- **Config** : rclone backend vers Google Drive
- **Encryption** : Restic native (passphrase dans `/opt/academie-shared/secrets/restic-passphrase`)
- **Inclus** : `/opt/academie`, `/opt/academie-shared`, `/mnt/cosmos-data/backups/postgres`, `/etc` (sélectif)
- **Exclus** : `node_modules/`, `__pycache__/`, `.venv/`, logs
- **Script** : `restic-backup` tool
- **Frequency** : daily 3h30
- **Rétention** : 30 daily / 12 weekly / 24 monthly / 10 yearly (élargie Session 48 post-audit ; footprint ~10 GiB sur 5 TiB disponibles = 0.2%)

Restauration :
```bash
restic -r <repo> snapshots
restic -r <repo> restore <snapshot-id> --target /tmp/restore
```

## Niveau 4 — Git

- **Repos** :
  - `/opt/academie` → `Sinsemilila/academIA` (public)
  - `/root/sinse-archive-2026-pre-vault` → `Sinsemilila/sinse-workspace` (private, archived 2026-04-25 post-vault migration)
  - `/root/sinse-vault` → `Sinsemilila/sinse-vault` (private)
  - `/root/sinse-tools` → `Sinsemilila/sinse-tools` (private)
  - `/root/.claude` → `Sinsemilila/sinse-claude-config` (private)
- **Commits** : gitleaks pre-commit hook + smoke-test pre-push
- **Push** : par session via `/handoff`

## Audit rapide (à faire avant SaaS public)

**Tests à effectuer** :
- [ ] Restauration niveau 1 testée (vzdump → nouvelle VM → vérif smoke-test)
- [ ] Restauration niveau 2 testée (dump → PG secondaire → queries de vérification)
- [ ] Restauration niveau 3 testée (restic restore → comparaison hash)
- [x] Runbook [99-runbooks/restore-backup.md](../99-runbooks/restore-backup.md) écrit (draft)
- [x] **Ajouter `litellm_db` + `dify_plugin` au pg-backup** (fait 2026-04-15 Session 15)
- [x] **Vérifier rotation weekly/monthly** (OK, déclenchement naturel Dimanche/1er)
- [ ] Vérifier Proxmox vzdump schedule actif

## Risques actuels

1. **Niveau 3 = Google Drive** — dépendance à un tiers externe. Si compte bloqué/supprimé → perte. Mitigation future : 2ᵉ target (OneDrive, B2, ou NAS distant familial).
2. **Niveau 1 + 2 sur le MÊME disque** (SSD-STOCKAGE) — panne disque = perte immédiate des 2 premiers niveaux. Niveau 3 (Restic) couvre. Mitigation envisageable : déplacer niveau 1 sur SSD-BOOT (ce qui est déjà le cas ✅).
3. **Pas de test restauration formel** — les backups existent mais restauration jamais validée en scénario réel. Runbook à écrire.

## Données **non** couvertes

- Conversations Dify (elles sont dans `academie_db.messages`, donc couvertes par niveau 2)
- Secrets dans `/opt/academie-shared/secrets/` : couverts par niveau 3 chiffré ✅
- Config LiteLLM : couvert par niveau 3 ✅
- n8n workflow data : dans `academie_db` (n8n utilise notre PG), donc couvert ✅
- LiteLLM SpendLogs (`litellm_db`) : couvert depuis Session 15 ✅
- Dify plugin daemon state (`dify_plugin`) : couvert depuis Session 15 ✅

## Références

- [deployment.md](deployment.md) — infra
- [../99-runbooks/restore-backup.md](../99-runbooks/restore-backup.md) (à écrire)
- Outils : `pg-backup`, `restic-backup` (sur PATH)
