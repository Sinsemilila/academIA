---
title: Restore backup
status: draft
last_reviewed: 2026-04-15
---

# Restore backup

> Procédure de restauration selon le niveau de backup à utiliser. **Non encore testée end-to-end** — priorité pour un audit avant SaaS public.

**Statut** : `draft` — à valider par test de restauration réelle.

## Décision du niveau à utiliser

| Scénario | Niveau |
|---|---|
| Un fichier supprimé sans intention | Niveau 3 (Restic) — granulaire |
| Corruption table PG | Niveau 2 (PG dump hourly) |
| Panne VM cosmos complète | Niveau 1 (vzdump) + Niveau 3 pour data récente |
| Panne Proxmox host / NAS | Niveau 3 (Restic offsite sur GDrive) |
| Perte du code | Niveau 4 (Git GitHub) |

Cf. [backup.md](../04-infra/backup.md) pour la stratégie complète.

## Niveau 4 — Git (le plus simple)

```bash
cd /tmp
git clone https://github.com/Sinsemilila/academIA.git
git clone https://github.com/Sinsemilila/sinse-workspace.git
# copier vers /opt/academie/ et /root/sinse-workspace/
```

## Niveau 2 — Restore PostgreSQL depuis dump

### Lister les dumps disponibles

```bash
ls -lt /mnt/cosmos-data/backups/postgres/ | head -20
```

### Restore sur une DB secondaire (test)

```bash
# Créer une DB test
docker exec postgres-academie psql -U sinse -c "CREATE DATABASE academie_restore_test;"

# Restore
gunzip < /mnt/cosmos-data/backups/postgres/academie_db_YYYYMMDD_HHMM.sql.gz \
  | docker exec -i postgres-academie psql -U sinse -d academie_restore_test

# Vérifier
docker exec postgres-academie psql -U sinse -d academie_restore_test -c "SELECT COUNT(*) FROM eleves;"

# Cleanup
docker exec postgres-academie psql -U sinse -c "DROP DATABASE academie_restore_test;"
```

### Restore en prod (destructif)

⚠️ **Warning** : écrase academie_db. Assurez-vous :
1. Tous les containers qui utilisent academie_db sont **stoppés** (`docker stop academie-api dify-api n8n-academie`)
2. Vous avez un dump très récent **avant** le restore (en cas de rollback)

```bash
# Pre-backup de sécurité
docker exec postgres-academie pg_dump -U sinse academie_db | gzip > /tmp/pre_restore_$(date +%Y%m%d_%H%M).sql.gz

# Restore
docker exec postgres-academie psql -U sinse -c "DROP DATABASE academie_db;"
docker exec postgres-academie psql -U sinse -c "CREATE DATABASE academie_db;"
gunzip < /mnt/cosmos-data/backups/postgres/academie_db_YYYYMMDD_HHMM.sql.gz \
  | docker exec -i postgres-academie psql -U sinse -d academie_db

# Restart containers
docker start academie-api dify-api n8n-academie

# Smoke test
smoke-test --deep
```

## Niveau 3 — Restic restore

### Lister les snapshots

```bash
restic -r <restic-repo> snapshots
```

### Browse un snapshot (dry-run)

```bash
restic -r <repo> ls <snapshot-id> /opt/academie/webapp/backend/app/routers
```

### Restore vers `/tmp/restore` (safe)

```bash
restic -r <repo> restore <snapshot-id> --target /tmp/restore
# Contenu disponible dans /tmp/restore/opt/academie/...
# Copier manuellement ce qui est nécessaire
```

### Restore sélectif (fichier précis)

```bash
restic -r <repo> restore <snapshot-id> --target /tmp/restore \
  --include /opt/academie/webapp/backend/app/routers/chat_router.py
```

## Niveau 1 — vzdump VM entière

⚠️ **Reset complet**. Utiliser seulement si cosmos est en état inutilisable.

### Via Proxmox UI

1. Se connecter à Proxmox : `pve.petit-pont.com`
2. Datacenter → cosmos (VMID 100) → Backup
3. Sélectionner le backup à restaurer
4. `Restore` → choisir target (nouvelle VM ou remplacement)

### Via CLI

```bash
# Sur Proxmox host
qmrestore /var/lib/vz/dump/vzdump-qemu-100-YYYY_MM_DD-HH_MM_SS.vma.zst <new_vmid>
```

Après restore :
- La VM sera l'image du dernier backup (daily 4h → max 24h de data perdue)
- Compléter avec restore niveau 2 ou 3 pour data plus récente

## Procédure "le NAS est mort"

Scénario catastrophe : plus de Proxmox, plus de cosmos, plus de backup local.

1. Depuis un autre Linux avec accès internet + Google Drive credentials
2. Installer Restic et rclone
3. Configurer rclone vers le Google Drive de Sinse
4. `restic -r <gdrive-repo> snapshots`
5. Restaurer sur nouvelle VM / machine

**Pré-requis** :
- Avoir la **Restic passphrase** (backup dans password manager + backup papier physique — à vérifier)
- Avoir accès Google Drive (comptes de secours ?)

## Audit à faire

Aucune de ces procédures n'a été testée end-to-end. Action :

- [ ] Test restore niveau 2 mensuel (automatisable via script)
- [ ] Test restore niveau 3 trimestriel
- [ ] Test restore niveau 1 annuel (demande Proxmox disponible)
- [ ] Test procédure "NAS mort" une fois pour validation

## Références

- [backup.md](../04-infra/backup.md)
- [deployment.md](../04-infra/deployment.md)
- Outils : `pg-backup`, `restic-backup`
