---
title: Runbook — Migration taxonomie v2 (Sprint 2)
status: authoritative
last_reviewed: 2026-04-15
---

# Runbook — Migration taxonomie v2

> Procédure d'application de la migration schema Sprint 2 Phase A, et
> rollback si besoin. Cette migration est **idempotente** : re-runnable
> sans corruption.

## Pré-requis

1. **Backup safety net** récent (≤ 60 min) :
   ```bash
   ls -lh /mnt/cosmos-data/backups/postgres/academie_db_*.sql.gz | tail -1
   # OR force fresh backup
   docker exec postgres-academie pg_dump -U sinse academie_db | gzip > /tmp/pre-migration.sql.gz
   ```

2. **Smoke-test** vert en entrée :
   ```bash
   smoke-test --deep
   ```

3. **v2 tolerance matrix** active en prod (Session 15, bascule soft déjà faite).
   Vérifier : `docker exec academie-api env | grep USE_V2_TOLERANCE` → `=true`.

## Procédure forward

```bash
# 1. Exécuter la migration (idempotente)
python3 /opt/academie/scripts/migrate_sprint2_schema.py

# 2. Vérifier les counts attendus dans le output de la migration :
#    - error_log: 17 columns (11 original + 6 new)
#    - 4 new tables: l1_transfer_observations, domain_catalog,
#      spaced_retrieval_queue, snapshots_session_v1_archive
#    - domain_catalog: 1 row (lang:en)
#    - snapshots_session schema_version: 1 → 8 rows

# 3. Tests régression
cd /opt/academie/scripts/sprint2
../sprint1/venv/bin/pytest tests/ -v
# Attendu : 14 passed

# 4. Smoke-test final
smoke-test --deep
# Attendu : 21/21 PASS (la migration ne touche pas le code prod)
```

## Vérifications SQL manuelles

```sql
-- Nouveaux champs error_log
\d error_log

-- Nouvelles tables existent
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('l1_transfer_observations','domain_catalog',
                      'spaced_retrieval_queue','snapshots_session_v1_archive')
ORDER BY table_name;

-- Seed domain_catalog
SELECT * FROM domain_catalog;

-- Snapshots archivés correctement
SELECT schema_version, COUNT(*) FROM snapshots_session GROUP BY schema_version;
SELECT COUNT(*) FROM snapshots_session_v1_archive;
```

## Rollback

### Rollback soft — flag env (recommandé en premier)

Ne touche pas le schema, désactive seulement les weights v2 :

```bash
sed -i 's/USE_V2_TOLERANCE=true/USE_V2_TOLERANCE=false/' /opt/academie/webapp/.env
docker restart academie-api
# Vérif:
docker exec academie-api env | grep USE_V2
# puis smoke-test
smoke-test --quick
```

Effet : retour immédiat à `tolerance_matrix.yaml` v1 (~30s).

### Rollback hard — drop schema (si soft insuffisant)

Seulement si la migration a été appliquée puis on veut revenir à l'état v1
exact. ATTENTION : les nouvelles données éventuellement écrites dans les 6
colonnes ajoutées seront perdues.

```sql
-- 1. Drop colonnes error_log
ALTER TABLE error_log
    DROP CONSTRAINT IF EXISTS chk_error_log_tier,
    DROP CONSTRAINT IF EXISTS chk_error_log_criterial_emergence,
    DROP CONSTRAINT IF EXISTS chk_error_log_criterial_mastery,
    DROP COLUMN IF EXISTS tier,
    DROP COLUMN IF EXISTS gravity_linguistic,
    DROP COLUMN IF EXISTS gravity_communicative,
    DROP COLUMN IF EXISTS gravity_social,
    DROP COLUMN IF EXISTS criterial_level_emergence,
    DROP COLUMN IF EXISTS criterial_level_mastery;
DROP INDEX IF EXISTS idx_error_log_tier;

-- 2. Drop nouvelles tables
DROP TABLE IF EXISTS spaced_retrieval_queue;
DROP TABLE IF EXISTS domain_catalog;
DROP TABLE IF EXISTS l1_transfer_observations;

-- 3. Snapshot cut-off — remettre schema_version column
ALTER TABLE snapshots_session DROP COLUMN IF EXISTS schema_version;

-- 4. Archive table (garder par défaut pour historique, drop si nécessaire)
-- DROP TABLE snapshots_session_v1_archive;  -- seulement si vraiment besoin
```

### Rollback total (nuclear) — restore depuis backup

Si corruption complète :

```bash
# Stop application pour éviter writes concurrents
docker stop academie-api academie-frontend

# Drop + re-create DB
docker exec postgres-academie psql -U sinse -c "DROP DATABASE academie_db;"
docker exec postgres-academie psql -U sinse -c "CREATE DATABASE academie_db OWNER sinse;"

# Restore
gunzip < /tmp/pre-migration.sql.gz | \
    docker exec -i postgres-academie psql -U sinse -d academie_db

# Restart
docker start academie-api academie-frontend

# Verify
smoke-test --deep
```

Temps typique : ~5 min. Perte de données = tout ce qui est arrivé entre le
backup et le rollback (minutes à heures selon timing).

## Troubleshooting

### "INSERT has more expressions than target columns"

Happens si l'archive `snapshots_session_v1_archive` a été créée avant
l'ajout de `schema_version` sur `snapshots_session` (ordre inversé à la
main). Le script gère ce cas via projection explicite des colonnes v1.
Si le bug persiste : drop l'archive et re-run.

### CHECK constraint violation

Si existing rows dans `error_log` ont déjà des valeurs `tier` ne respectant
pas `T0..T4`, ajuster via `UPDATE error_log SET tier=NULL WHERE tier NOT IN
('T0','T1','T2','T3','T4');` avant de rerun.

### Migration interrompue

Chaque bloc SQL est indépendant et idempotent. Relancer le script suffit,
il reprendra où il en est sans corruption.

## Monitoring post-migration

Pour les ~48h suivantes, surveiller :
- `smoke-test --quick` dans `/var/log/smoke-alert.log` (cron 15min)
- `docker logs academie-api` — erreurs d'insertion sur `error_log`
- Valeurs NULL attendues sur `tier`, `gravity_*`, `criterial_level_*` pour
  tous les nouveaux rows jusqu'à Phase B (le LLM ne les produit pas encore)

## Références

- Script : `/opt/academie/scripts/migrate_sprint2_schema.py`
- Tests : `/opt/academie/scripts/sprint2/tests/`
- ADR-007 — Snapshot cut-off option C
- ADR-009 — Gravity axes schema
- Data model : [data-model.md](../02-architecture/data-model.md)
