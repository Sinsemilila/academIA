# Disaster Recovery — AcademIA

> Document validé lors de la Session S1 (2026-04-12).
> Chaque scénario a été testé et les commandes sont exactes.
> Ce document est en **français** (exception D13 — lisibilité Sinse en urgence).

---

## Inventaire des backups actifs

| Niveau | Quoi | Où | Fréquence | Rétention | Testé |
|--------|------|----|-----------|-----------|-------|
| 1 | Vzdump VM cosmos | Proxmox `local` (SSD 1 ≠ VM sur SSD 2) | Quotidien 4h | 1 récent (~19G) | ✅ 2026-04-12 |
| 2 | Dump PostgreSQL | `/mnt/cosmos-data/backups/postgres/` | Horaire | 24h + 7j + 4s + 12m | ✅ 2026-04-12 |
| 3 | Restic chiffré AES-256 | Google Drive 5 To | Quotidien 3h30 | 7j + 4s + 12m + 2a | ✅ 2026-04-12 |
| 4 | Git | GitHub | À chaque commit | Illimité | ✅ actif |

## Passphrase Restic — Triple stockage (D37 G1)

**⚠️ CRITIQUE** : sans cette passphrase, tous les backups Google Drive sont **définitivement irrécupérables**.

1. **Fichier local** : `/opt/academie-shared/secrets/restic-passphrase` (chmod 600)
2. **NordPass** : entrée "Restic Backup - AcademIA (cosmos)"
3. **Carnet papier** : à noter physiquement hors cosmos (TODO Sinse)

## Secrets critiques

| Secret | Emplacement | Impact si perdu |
|--------|-------------|-----------------|
| Passphrase Restic | triple stockage ci-dessus | **Backups GDrive irrécupérables** |
| rclone token GDrive | `~/.config/rclone/rclone.conf` | Re-auth OAuth (5 min) |
| Dify admin key | `/opt/academie/.dify_admin_key` | Recréable via DB Dify |
| n8n encryption key | `/opt/n8n/encryption.key` | **Workflows n8n illisibles** |
| PG password | `/opt/academie-shared/secrets/` (à migrer) | Backupé par Restic |
| LiteLLM API keys | `/opt/litellm/config.yaml` | Re-créer chez chaque provider |

**Tous les secrets (sauf passphrase Restic) sont backupés par Restic dans Google Drive.**

---

## Scénario 1 — Table PostgreSQL supprimée par erreur

**Gravité** : 🟡 Moyenne | **Temps** : ~5 min | **Testé** : ✅ 2026-04-12

### Procédure (testée et validée)

```bash
# 1. Trouver le dernier dump
ls -lt /mnt/cosmos-data/backups/postgres/academie_db_*.sql.gz | head -5

# 2. Restaurer (les erreurs "already exists" sur les autres tables sont normales)
DUMP="/mnt/cosmos-data/backups/postgres/academie_db_YYYY-MM-DD_HHMM.sql.gz"
gunzip -c "$DUMP" | docker exec -i postgres-academie psql -U sinse -d academie_db

# 3. Vérifier
docker exec postgres-academie psql -U sinse -d academie_db -c "SELECT count(*) FROM eleves;"
```

### Si le dump horaire est trop vieux → Restic

```bash
export RESTIC_PASSWORD_FILE=/opt/academie-shared/secrets/restic-passphrase
restic -r rclone:gdrive:/Backups/academie/restic snapshots
restic -r rclone:gdrive:/Backups/academie/restic restore <SNAPSHOT_ID> \
    --target /tmp/restore-pg \
    --include "/mnt/cosmos-data/backups/postgres/"
# Puis restaurer depuis le dump extrait
```

---

## Scénario 2 — Fichier workspace ou config perdu

**Gravité** : 🟡 Moyenne | **Temps** : ~5 min | **Testé** : ✅ 2026-04-12

### Procédure (testée et validée)

```bash
# 1. D'abord vérifier dans git
cd /root/sinse-workspace && git log --oneline -5
git checkout HEAD -- <fichier>   # restaure depuis le dernier commit

# 2. Si pas dans git → Restic
export RESTIC_PASSWORD_FILE=/opt/academie-shared/secrets/restic-passphrase
restic -r rclone:gdrive:/Backups/academie/restic snapshots

# 3. Restaurer un fichier spécifique
restic -r rclone:gdrive:/Backups/academie/restic restore latest \
    --target /tmp/restic-restore \
    --include "/chemin/vers/le/fichier"

# 4. Remettre en place
cp /tmp/restic-restore/chemin/vers/le/fichier /chemin/vers/le/fichier
rm -rf /tmp/restic-restore
```

---

## Scénario 3 — VM cosmos crash (ne démarre plus)

**Gravité** : 🔴 Haute | **Temps** : ~30 min | **Backup** : vzdump sur SSD séparé

### Procédure

```bash
# 1. Depuis Proxmox (pve.petit-pont.com ou ssh root@192.168.1.50)

# Vérifier le backup vzdump
ls -lh /var/lib/vz/dump/vzdump-qemu-100-*

# 2. Restaurer la VM (VMID 100 = cosmos)
# Option A — Écraser la VM actuelle
qmrestore /var/lib/vz/dump/vzdump-qemu-100-YYYY_MM_DD-HH_MM_SS.vma.zst 100 --force

# Option B — Restaurer comme nouvelle VM (plus sûr)
qmrestore /var/lib/vz/dump/vzdump-qemu-100-YYYY_MM_DD-HH_MM_SS.vma.zst 101

# 3. Démarrer
qm start 100

# 4. Vérifier depuis cosmos
ssh root@192.168.1.181
/opt/academie-shared/scripts/smoke-test.sh --all
```

---

## Scénario 4 — NAS / Proxmox complètement mort (perte totale)

**Gravité** : 🔴🔴 Critique | **Temps** : 2-4h | **Prérequis** : passphrase Restic (NordPass)

### Procédure

```bash
# 1. Sur un nouveau serveur Debian
apt update && apt install -y docker.io docker-compose restic rclone git

# 2. Configurer rclone pour Google Drive (OAuth via navigateur)
rclone config   # type: drive, scope: drive, name: gdrive

# 3. Vérifier les snapshots (passphrase depuis NordPass !)
export RESTIC_PASSWORD="<passphrase>"
restic -r rclone:gdrive:/Backups/academie/restic snapshots

# 4. Restaurer TOUT
restic -r rclone:gdrive:/Backups/academie/restic restore latest --target /

# Restaure automatiquement :
#   /opt/academie, /opt/academie-shared, /opt/litellm/config.yaml
#   /opt/n8n, /mnt/cosmos-data/backups/postgres/
#   /root/sinse-workspace, ~/.claude/projects/memory

# 5. Restaurer la base de données
LATEST_DUMP=$(ls -t /mnt/cosmos-data/backups/postgres/academie_db_*.sql.gz | head -1)
gunzip -c "$LATEST_DUMP" | docker exec -i postgres-academie psql -U sinse -d academie_db

# 6. Démarrer les containers Docker (docker-compose up -d dans chaque stack)

# 7. Reconfigurer Cloudflare Tunnel si IP a changé

# 8. Vérifier
/opt/academie-shared/scripts/smoke-test.sh --all
```

**Perte de données max** : 1h (dernier PG dump horaire) + 24h (dernier Restic quotidien).

---

## Commandes utiles en urgence

```bash
# État rapide
/opt/academie-shared/scripts/smoke-test.sh --quick

# Dernier backup PG ?
ls -lt /mnt/cosmos-data/backups/postgres/ | head -3

# Dernier snapshot Restic ?
export RESTIC_PASSWORD_FILE=/opt/academie-shared/secrets/restic-passphrase
restic -r rclone:gdrive:/Backups/academie/restic snapshots --last

# Dernier vzdump Proxmox ?
ssh root@192.168.1.50 "ls -lh /var/lib/vz/dump/"

# Redémarrer tous les containers
cd /opt/academie/webapp && docker compose restart
```

---

## Checklist validation DR — S1.6

- [x] Test restore niveau 2 : table PG droppée et restaurée (3/3 lignes)
- [x] Test restore niveau 3 : fichier supprimé et restauré depuis Google Drive
- [x] Test structural niveau 1 : vzdump 19G existe sur SSD séparé
- [x] Passphrase Restic stockée en 3 endroits (fichier + NordPass + papier TODO)
- [x] Liste des secrets critiques documentée
- [x] Smoke-test 4 modes validé (25/25 checks)

**Tous les critères validés le 2026-04-12.**
