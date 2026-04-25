# Session 1 — Sécurisation (backup + test restore + smoke-test)

> **Durée estimée** : 3-4h
> **Statut** : 🟡 Prête à lancer
> **Livrable** : backup 4 niveaux opérationnel + test restore validé + smoke-test script
> **Règle d'or #1** : "Backup avant tout — zéro changement structurel tant que le test de restore n'est pas validé"

---

## Objectif

Mettre en place l'infrastructure de backup et de validation **avant** d'activer YOLO mode ou de toucher à la structure du workspace. C'est le filet de sécurité non-négociable qui permet toutes les autres sessions.

À la fin de cette session :
- ✅ Les 4 niveaux de backup tournent automatiquement
- ✅ Un test de restore complet a été validé pour chaque niveau
- ✅ Le script `smoke-test.sh` est opérationnel avec 4 variantes
- ✅ Doc `disaster-recovery.md` écrite avec 4 scénarios
- ✅ On est en sécurité pour lancer S2

---

## Prérequis (vérifier avant de commencer)

- [ ] Accès SSH root à l'hôte Proxmox (D6)
- [ ] Compte Google Drive avec au moins 5 Go dispo (D1 niveau 3)
- [ ] 3-4h de concentration dispo (règle d'or #7 — pas d'arrêt en milieu de session)
- [ ] Claude Code full Opus 4.6 1M (D7)
- [ ] Accès sudo sur cosmos

---

## Checklist

### S1.0 — Préparation (10 min)

- [ ] Vérifier que les containers sont UP : `docker ps`
- [ ] Vérifier l'espace disque : `df -h /opt /var/lib/docker`
- [ ] Créer le répertoire backup local : `mkdir -p /opt/backups/postgres`
- [ ] Tester l'accès SSH Proxmox depuis cosmos : `ssh root@<proxmox-ip> hostname`
- [ ] Créer un fichier `.session-progress` : `echo "SESSION=S1\nSTEP=S1.0" > /root/.session-progress`

### S1.1 — Inventaire Proxmox (15 min)

- [ ] SSH vers Proxmox, récupérer les infos :
  - `pvesm status` (liste des storages configurés)
  - `lsblk` (disques physiques présents)
  - `qm list` (VMs actives)
  - `qm config <cosmos-vmid>` (config de la VM cosmos)
- [ ] Identifier **où est actuellement stocké le disque de la VM cosmos** (quel storage)
- [ ] Identifier **s'il y a un storage séparé disponible** pour les snapshots (idéal : 2e disque physique)
- [ ] **Décision conditionnelle** : si un seul disque, snapshots sur même disque acceptés. Si 2+, snapshots sur le 2e pour redondance.

### S1.2 — Backup niveau 1 : Snapshots Proxmox quotidiens (30 min)

- [ ] Configurer job de backup via `pvesh` ou UI Proxmox :
  - Fréquence : quotidien (3h du matin)
  - Cible : cosmos VM
  - Compression : zstd
  - Rétention : 7 quotidiens + 4 hebdomadaires + 3 mensuels
- [ ] Ou : installer Proxmox Backup Server (PBS) si 2+ disques dispos (plus propre mais plus lourd)
- [ ] **Tester manuellement** : `vzdump <vmid> --storage <storage> --compress zstd`
- [ ] Vérifier que le snapshot est bien listé dans `pvesm list <storage>`

### S1.3 — Backup niveau 2 : Dumps PostgreSQL horaires (30 min)

- [ ] Créer le script `/opt/academie-shared/scripts/pg-backup.sh` :
  ```bash
  #!/bin/bash
  set -euo pipefail
  BACKUP_DIR="/opt/backups/postgres"
  TIMESTAMP=$(date +%Y-%m-%d_%H)
  FILE="$BACKUP_DIR/$TIMESTAMP.sql.gz"
  docker exec postgres-academie pg_dump -U sinse academie_db | gzip > "$FILE"
  # Rétention : 24h
  find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +1 -delete
  # Sauf : quotidien à minuit, hebdo le dimanche, mensuel le 1
  # (logique à implémenter avec find + mv vers sous-dossiers)
  ```
- [ ] Rendre exécutable : `chmod +x /opt/academie-shared/scripts/pg-backup.sh`
- [ ] Créer un cron horaire : `crontab -e`
  ```
  0 * * * * /opt/academie-shared/scripts/pg-backup.sh
  ```
- [ ] Test manuel : `/opt/academie-shared/scripts/pg-backup.sh`
- [ ] Vérifier : `ls -la /opt/backups/postgres/`
- [ ] Noter : ce script deviendra le bash tool `pg-backup` en S2 (moved to `/root/sinse-workspace/tools/`)

### S1.4 — Préparation Google Drive pour Restic (15 min)

- [ ] Créer le folder `/Backups/academie/` dans Google Drive (UI web)
- [ ] **Décision** : type d'authentification
  - **Option A** : OAuth user (plus simple, expire après plusieurs mois)
  - **Option B** : Service account (plus stable, setup plus complexe)
  - **Recommandation** : Option A pour démarrer, Option B plus tard si besoin
- [ ] Installer rclone sur cosmos : `apt install rclone` (ou `curl https://rclone.org/install.sh | bash`)
- [ ] Configurer rclone : `rclone config`
  - Nom : `gdrive`
  - Type : `drive`
  - Scope : `drive.file` (minimal, seul accès aux fichiers créés par rclone)
- [ ] Tester : `rclone lsd gdrive:` (doit lister le root de ton Drive)

### S1.5 — Backup niveau 3 : Restic + Google Drive (45 min)

- [ ] Installer Restic : `apt install restic`
- [ ] **CRITIQUE — Passphrase Restic (D37 G1)** :
  - Générer une passphrase forte : `openssl rand -base64 48`
  - **Stockage triple** :
    1. Fichier local : `echo "<passphrase>" > /opt/academie-shared/secrets/restic-passphrase && chmod 600 /opt/academie-shared/secrets/restic-passphrase`
    2. **Écrire à la main** sur un carnet papier stocké hors cosmos
    3. Ajouter dans password manager (Bitwarden / 1Password / KeePass)
  - **⚠️ Sans cette passphrase, tous les backups offsite sont inaccessibles !**
- [ ] Initialiser le repo Restic sur Google Drive via rclone :
  ```bash
  export RESTIC_PASSWORD_FILE=/opt/academie-shared/secrets/restic-passphrase
  restic -r rclone:gdrive:/Backups/academie/restic init
  ```
- [ ] Créer le script `/opt/academie-shared/scripts/restic-backup.sh` :
  ```bash
  #!/bin/bash
  set -euo pipefail
  export RESTIC_PASSWORD_FILE=/opt/academie-shared/secrets/restic-passphrase
  restic -r rclone:gdrive:/Backups/academie/restic backup \
    /opt/backups/postgres \
    /opt/academie \
    /opt/litellm/config.yaml \
    /opt/n8n \
    /opt/academie-shared \
    /root/sinse-workspace \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='dist' \
    --exclude='*.log'
  # Retention : 7d + 4w + 12m + 2y
  restic -r rclone:gdrive:/Backups/academie/restic forget \
    --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --keep-yearly 2 \
    --prune
  ```
- [ ] Rendre exécutable + ajouter cron quotidien à 3h :
  ```
  0 3 * * * /opt/academie-shared/scripts/restic-backup.sh
  ```
- [ ] **Premier backup manuel** : `/opt/academie-shared/scripts/restic-backup.sh` (peut prendre 10-30 min la première fois)
- [ ] Vérifier : `restic -r rclone:gdrive:/Backups/academie/restic snapshots`

### S1.6 — TEST DE RESTORE (CRITIQUE — 45 min)

**Règle d'or #1** : **aucun passage à S2 tant que ces tests ne passent pas**.

#### Test restore niveau 2 (dump PG)

- [ ] Créer une table de test : `docker exec postgres-academie psql -U sinse -d academie_db -c "CREATE TABLE test_restore (id INT, data TEXT);"`
- [ ] Insérer des données : `INSERT INTO test_restore VALUES (1, 'hello'), (2, 'world');`
- [ ] Lancer un backup manuel : `/opt/academie-shared/scripts/pg-backup.sh`
- [ ] **Simuler perte** : `DROP TABLE test_restore;`
- [ ] **Restaurer** : extraire le dernier dump, restaurer la table :
  ```bash
  LATEST_DUMP=$(ls -t /opt/backups/postgres/*.sql.gz | head -1)
  gunzip -c "$LATEST_DUMP" | docker exec -i postgres-academie psql -U sinse -d academie_db
  ```
- [ ] Vérifier : `SELECT * FROM test_restore;` → doit retourner les 2 lignes
- [ ] Nettoyer : `DROP TABLE test_restore;`
- [ ] ✅ Marqué validé

#### Test restore niveau 3 (Restic depuis Google Drive)

- [ ] Créer un fichier test : `echo "RESTORE TEST $(date)" > /opt/academie-shared/test-restore-marker.txt`
- [ ] Backup manuel : `/opt/academie-shared/scripts/restic-backup.sh`
- [ ] Supprimer le fichier : `rm /opt/academie-shared/test-restore-marker.txt`
- [ ] Restaurer via Restic :
  ```bash
  export RESTIC_PASSWORD_FILE=/opt/academie-shared/secrets/restic-passphrase
  restic -r rclone:gdrive:/Backups/academie/restic restore latest \
    --target /tmp/restic-test-restore \
    --include "/opt/academie-shared/test-restore-marker.txt"
  ```
- [ ] Vérifier : `cat /tmp/restic-test-restore/opt/academie-shared/test-restore-marker.txt`
- [ ] Nettoyer : `rm -rf /tmp/restic-test-restore`
- [ ] ✅ Marqué validé

#### Test restore niveau 1 (Proxmox snapshot)

- [ ] **Ne PAS tester en rollback de la VM active** (trop disruptif pour la prod)
- [ ] **Alternative** : vérifier que le snapshot existe et qu'il est cohérent :
  - `pvesh get /nodes/<node>/storage/<storage>/content`
  - Check size + date du dernier snapshot
- [ ] ✅ Marqué "test structural validé" (restore complet testé uniquement en cas de catastrophe réelle)

### S1.7 — Script `smoke-test.sh` (30 min)

- [ ] Créer `/opt/academie-shared/scripts/smoke-test.sh` (deviendra `/root/sinse-workspace/tools/smoke-test` en S2)
- [ ] Implémenter les 4 variantes (voir `reference/tools.md` pour le template complet) :
  - `smoke-test --quick` (containers UP + services HTTP ~5s)
  - `smoke-test --deep` (quick + endpoints API + chatflow ~15s)
  - `smoke-test --infra` (disk + RAM + restart count ~5s)
  - `smoke-test --all` (tout ~30s)
- [ ] Rendre exécutable : `chmod +x smoke-test.sh`
- [ ] Tester les 4 modes :
  - `./smoke-test.sh --quick` → doit afficher tous les checks verts
  - `./smoke-test.sh --deep` → idem
  - `./smoke-test.sh --infra` → doit afficher espace disque + RAM
  - `./smoke-test.sh --all` → combinaison
- [ ] **Test en conditions cassées** : stopper un container (`docker stop n8n-academie`), relancer `smoke-test --quick`, vérifier qu'il fail proprement avec le bon message, puis restart (`docker start n8n-academie`)

### S1.8 — Documentation disaster-recovery (20 min)

- [ ] Créer `/root/sinse-workspace/projects/academie-ia/refactor-v1.0/reference/disaster-recovery.md` (ou le copier depuis le squelette Batch 3)
- [ ] Documenter les 4 scénarios validés (D37 G5) :
  1. **PG table drop** : commandes exactes validées en S1.6
  2. **Fichier workspace perdu** : Restic restore granulaire
  3. **VM cosmos crash** : restore snapshot Proxmox (procédure, pas exécution)
  4. **NAS total cramage** : restore depuis Google Drive (procédure complète, inclut l'install initial Restic)
- [ ] **Liste des secrets critiques** (D37 G6 — préparation, liste complétée en S2) :
  - `/opt/academie/.dify_admin_key`
  - `/opt/n8n/encryption.key`
  - Passphrase Restic
  - Credentials Google Drive (rclone config)
  - LiteLLM config avec clés API
- [ ] Doc en français pour Sinse (exception à D13 pour ce fichier)

### S1.9 — Validation finale session (15 min)

- [ ] Lancer `smoke-test --all` → tous verts
- [ ] Vérifier que les crons sont actifs : `crontab -l`
- [ ] Vérifier que le cron quotidien Proxmox est actif
- [ ] Vérifier `ls /opt/backups/postgres/` → présence du dump de test
- [ ] Vérifier `restic snapshots` → présence du snapshot de test
- [ ] **Supprimer** `/root/.session-progress`
- [ ] Commit des scripts créés (si dans le repo sinse-workspace) via `git commit` classique (committer n'existe pas encore, ce sera en S2)

---

## ✅ Critères de validation Session 1

Avant de déclarer S1 terminée et de passer à S2, **TOUS** ces points doivent être vrais :

1. ✅ Snapshots Proxmox quotidiens configurés et testés (au moins 1 snapshot visible)
2. ✅ Cron horaire PG dump actif (au moins 1 dump visible dans `/opt/backups/postgres/`)
3. ✅ Cron quotidien Restic actif + premier backup complet uploadé sur Google Drive
4. ✅ Passphrase Restic stockée en **3 endroits** (fichier local + papier + password manager)
5. ✅ **Test restore niveau 2 validé** (table recréée depuis dump)
6. ✅ **Test restore niveau 3 validé** (fichier restauré depuis Google Drive)
7. ✅ **Test structural niveau 1 validé** (snapshot existe et cohérent)
8. ✅ Script `smoke-test.sh` fonctionne en 4 modes (quick, deep, infra, all)
9. ✅ Document `disaster-recovery.md` écrit avec 4 scénarios + commandes exactes
10. ✅ Liste préliminaire des secrets critiques documentée

**Si un seul point n'est pas validé → NE PAS passer à S2. Revenir, compléter, retester.**

---

## 🚨 Troubleshooting

### rclone ne peut pas se connecter à Google Drive
- Vérifier que le token OAuth n'a pas expiré : `rclone about gdrive:`
- Réauthentifier : `rclone config reconnect gdrive:`

### Proxmox snapshot lent ou en timeout
- Vérifier l'espace dispo sur le storage cible
- Utiliser `zstd` au lieu de `gzip` (plus rapide)
- Considérer PBS si les snapshots deviennent trop gros

### Restic backup très long la première fois
- C'est normal : la première fois, tout est envoyé (pas encore de dedup)
- Les backups suivants sont incrémentaux et beaucoup plus rapides
- Si > 1h, envisager d'exclure des dossiers moins critiques (`node_modules`, etc.)

### smoke-test fail sur un container
- Check les logs : `docker logs <container-name> --tail 50`
- Check les healthchecks natifs : `docker inspect <container> | grep Health`
- Restart si besoin : `docker restart <container>`

---

## Prochaine session

→ **`sessions/s2-refactor-archi.md`** — Refactor architecture + YOLO activation (4h)

Avant de lancer S2 :
- Tous les critères de validation S1 validés ci-dessus
- Repos d'au moins 30 min (session S2 est encore plus dense)
- Confirmation mentale "le filet de sécurité est en place"
