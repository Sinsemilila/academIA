# A2 — Argon2id password hashing (refactor 2026-H2 Phase A)

**Status** : code livré, migration silencieuse activée à la prochaine connexion de chaque user
**Last updated** : 2026-04-23
**Related** : [`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`](../05-decisions/ADR-001-refactor-complete-2026-H2.md)

Migration de bcrypt(12) vers Argon2id (RFC 9106 winner, recommandation OWASP 2026). Stratégie : aucune migration forcée, **rehash silencieux à la première connexion réussie** de chaque user. Comptes dormants (jamais re-loggés) conservent bcrypt indéfiniment, à couvrir par un job force-reset (étape 2).

## Code livré (Session 46)

- **`webapp/backend/requirements.txt`** :
  - `passlib[bcrypt]==1.7.4` → `passlib[bcrypt,argon2]==1.7.4`
  - + `argon2-cffi==23.1.0`
- **`webapp/backend/app/auth.py`** :
  - `CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto", argon2__type="ID")`
  - argon2 = scheme par défaut pour `hash_password()`
  - bcrypt = legacy verify only, marqué deprecated → `needs_update()` retourne True
  - Nouvelle fonction `verify_and_rehash(plain, hashed) -> (ok, new_hash | None)` exposée
- **`webapp/backend/app/routers/auth_router.py`** :
  - Login flow utilise `verify_and_rehash` au lieu de `verify_password`
  - Si `new_hash` non-None → `UPDATE users SET password_hash = $1` silencieux
  - User ne voit aucune différence

## Paramètres Argon2id appliqués

Defaults passlib 1.7.4 (RFC 9106 compliant) :
- `memory_cost` = 65536 KiB (64 MiB)
- `time_cost` = 3 iterations
- `parallelism` = 4
- `hash_len` = 32 bytes
- `salt_len` = 16 bytes
- `type` = ID (data-independent + data-dependent, résiste GPU + side-channel)

À ajuster ultérieurement si load CPU/RAM problématique : passer `argon2__memory_cost=32768` (32 MiB) et `argon2__time_cost=4`. Pour 141 users alpha, defaults OK.

## Activation

```bash
cd /opt/academia/webapp
docker compose -f docker-compose.webapp.yml build academie-api
docker compose -f docker-compose.webapp.yml up -d academie-api
```

Vérif :
```bash
docker exec academie-api pip show argon2-cffi | grep -i version
docker exec academie-api python -c "from passlib.context import CryptContext; c=CryptContext(schemes=['argon2','bcrypt'],deprecated='auto',argon2__type='ID'); h=c.hash('test'); print('hash:', h[:30]); print('verify:', c.verify('test', h)); print('needs_update bcrypt:', c.needs_update('\$2b\$12\$abc...defghij'))"
```

Attendu : hash commence par `$argon2id$v=19$m=65536,t=3,p=4$...`

## Validation post-deploy

À chaque login d'un user existant (bcrypt) :
- 1ère connexion : `verify_and_rehash` → `ok=True`, `new_hash` = nouveau hash argon2 → `UPDATE users` silencieux
- 2e connexion et suivantes : `ok=True`, `new_hash=None` (déjà argon2)

Smoke test manuel :
```bash
# 1. Vérifier qu'un user existant est encore en bcrypt
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "SELECT id, username, substring(password_hash for 30) AS hash_prefix FROM users LIMIT 5;"

# 2. Login via UI / curl avec credentials valides
# 3. Re-vérifier que le hash a changé en argon2id
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "SELECT id, username, substring(password_hash for 30) AS hash_prefix FROM users WHERE username='<user>';"
```

Attendu : prefix passe de `$2b$12$...` (bcrypt) à `$argon2id$v=19$...` (argon2id).

Monitoring de la migration (% comptes migrés) :
```sql
SELECT
  COUNT(*) FILTER (WHERE password_hash LIKE '$argon2id$%') AS argon2_count,
  COUNT(*) FILTER (WHERE password_hash LIKE '$2b$%' OR password_hash LIKE '$2a$%') AS bcrypt_count,
  COUNT(*) AS total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE password_hash LIKE '$argon2id$%') / COUNT(*), 1) AS pct_migrated
FROM users;
```

## À faire — Étape 2 : couvrir comptes dormants (>90j inactivité)

Les users qui ne se reconnectent jamais resteront en bcrypt indéfiniment. Mitigation prévue ADR-001 : job cron force password reset après 90j d'inactivité.

**Pas urgent en alpha** (141 users, peu de comptes vraiment dormants pour l'instant). À implémenter avant ouverture beta privée fermée Phase D :
- Détection via `users.last_login_at` (vérifier si la colonne existe ou ajouter)
- Email de notification → lien reset password unique-use → user re-login
- Fallback : si pas de réponse au bout de 14 jours, suspendre le compte (`users.status='dormant_locked'`)

## Risques + rollback

- **Performance login** : argon2id avec defaults = ~100-200ms CPU + 64 MiB RAM par hash. Pour 141 users alpha, négligeable. À monitorer si trafic monte.
- **Cold cache** : à la 1ère connexion post-migration, login a un coût additionnel `verify(bcrypt) + hash(argon2) + UPDATE`. ~200-300ms total au lieu de ~150ms. Imperceptible utilisateur.
- **Rollback** : revert le commit + redeploy → CryptContext repasse à `["bcrypt"]` deprecated="auto". Les hashes argon2 produits entre-temps deviennent **invalides** (passlib avec scheme uniquement bcrypt rejette argon2). Donc si rollback nécessaire après migration, il faut TOUS les users en argon2 reset password. Risque réel : tester en staging avant prod si on doute.

## Lien avec PR Dependabot #11 (bcrypt 4→5)

PR #11 propose `bcrypt 4.0.1 → 5.0.0` (major). Avec argon2id en place comme default, bcrypt n'est utilisé que pour verify legacy hashes. Le major bump bcrypt n'apporte rien (et peut casser passlib qui dépend d'une version bcrypt précise). **Décision : fermer PR #11 sans merger**. Une fois 100% des comptes migrés argon2 (étape 2 force-reset terminée), on peut retirer bcrypt de requirements.txt entièrement.
