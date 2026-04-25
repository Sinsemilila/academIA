# File Protection Reference

> Liste complète des fichiers par niveau de protection pour l'Option E auto-merge (D30).
> Utilisée par le tool `merge-to-main` pour déterminer si un commit peut auto-merger, passer par l'arbiter, ou nécessiter une intervention humaine.

---

## Niveaux de protection

### 🔴 ROUGE — Humain obligatoire (Sinse)

Ces fichiers **bloquent l'auto-merge** même avec un diff minime. Trop sensibles pour être automatisés, même via IA arbitre.

#### Secrets et credentials
- `.env`, `.env.*`
- `*.key`, `*.pem`, `*.crt`, `*.cert`, `*_rsa*`, `*_ed25519*`
- `.dify_admin_key`, `encryption.key`, `restic-passphrase`
- `/opt/academie-shared/secrets/*` (tous les fichiers)

#### Credentials d'outils
- `.npmrc` (peut contenir `//registry.npmjs.org/:_authToken=...`)
- `.pypirc` (credentials PyPI)
- `.netrc` (credentials réseau)

#### Settings Claude Code / Gemini CLI
- `.claude/settings.json` (hooks, permissions system)
- `.claude/settings.local.json` (permissions utilisateur)
- `.gemini/settings.json`

#### Configs infra critique
- `docker-compose*.yml` (tous les compose files)
- `/etc/nginx/*`
- Configs Cloudflare tunnels
- `iptables` / `ufw` configs

#### Base de données schema
- `migrations/*.sql` (fichiers de migration DDL)
- Tous les fichiers avec des `CREATE TABLE`, `ALTER TABLE`, `DROP` SQL

#### Fichiers système
- `/etc/*`
- `systemd/*.service`
- `cron*`, `crontab`, `/etc/cron.*/`

#### Git config
- `.gitignore` (changer peut exposer des secrets)
- `.gitattributes`
- `.git/config`

#### Git hooks eux-mêmes
- `.git/hooks/*` (pre-commit, pre-push, etc.)
- `/root/sinse-workspace/.git/hooks/*`
- `/opt/academie/.git/hooks/*`

#### Méta-contrat du workflow
- `/root/sinse-workspace/AGENTS.md` (changer les règles du workflow = changer le contrat)

#### Slash commands sources
- `/root/sinse-workspace/slash-commands/*.md`

#### Bash tools maison
- `/root/sinse-workspace/tools/*` (committer, arbiter, docs-list, smoke-test, status, deploy-teacher, pg-backup, restic-backup, log, install-slash-commands, init-worktree, merge-to-main, merge-approve, merge-reject, rollback-to, cly)

#### Règle comportementale
- **Symlinks pointant vers des fichiers ROUGE sont eux-mêmes ROUGE**
- `~/.config/*` (si une IA y touche, configs CLIs avec credentials)

---

### 🟠 ORANGE — IA arbitre obligatoire

Ces fichiers nécessitent une review par l'arbiter (cross-review claude ↔ gemini via D28). Pas d'auto-merge direct, mais pas besoin de bloquer jusqu'à Sinse.

#### Backend API
- `/opt/academie/api/**/*.py`
- `api/**/*.py`

#### Frontend webapp
- `webapp/frontend/src/**/*.svelte`
- `webapp/frontend/src/**/*.ts`
- `webapp/frontend/src/**/*.js`

#### Scripts de deploy
- `scripts/*.py`
- `scripts/*.sh`
- `update_teacher_chatflow.py`
- `deploy-teacher` (le tool) → wait, celui-là est dans tools/ donc ROUGE
- Autres scripts "actifs" dans `/opt/academie/scripts/`

#### Docker images
- `Dockerfile`, `Dockerfile*` (sans extension ou avec suffixe)
- `.dockerignore`

#### LiteLLM config
- `/opt/litellm/config.yaml`

#### Dependencies Python
- `pyproject.toml`
- `poetry.lock`
- `uv.lock`
- `requirements.txt`
- `Pipfile*`
- `setup.py`

#### Dependencies JS/TS
- `package.json`
- `package-lock.json`
- `pnpm-lock.yaml`
- `yarn.lock`
- `bun.lockb`

#### Configs tooling
- `*.toml` (configs de tooling, autres que pyproject.toml qui est déjà listé)
- `tsconfig.json`
- `svelte.config.js`
- `vite.config.ts`, `vite.config.js`

#### CI/CD (futur)
- `.github/workflows/*.yml`
- `.gitlab-ci.yml`
- `Jenkinsfile`
- `.circleci/*`

#### Exports chatflow / workflows
- `*.chatflow.json`
- `*.n8n.json`
- Fichiers JSON exports Dify

---

### 🟢 VERT — Auto-merge OK (si autres critères OK)

Ces fichiers peuvent être auto-mergés si le type de commit le permet (D27) et qu'aucun fichier ROUGE/ORANGE n'est dans le même diff.

#### Documentation
- `docs/**/*.md`
- `README.md`, `CONTRIBUTING.md`, `PLAN.md`, `LICENSE.md`
- Code comments (dans les fichiers, pas les fichiers eux-mêmes)

#### Tests
- `tests/**/*`
- `*.test.*`
- `*.spec.*`
- `__tests__/**/*`

#### Fichiers contexte projet (peuvent être modifiés sans arbiter)
- `STATE.md`
- `TODO.md`
- `CHANGELOG.md`
- `DECISIONS.md`
- `HANDOFF-*.md`

#### Fichiers workflow state (temporaires)
- `REFACTOR-PLAN.md`
- `REFACTOR-AUDIT.md`

#### Assets statiques
- `*.png`, `*.jpg`, `*.jpeg`, `*.webp`, `*.gif`, `*.ico`
- `*.svg` (icônes)
- `*.woff`, `*.woff2`, `*.ttf` (fonts)

#### Public assets
- `public/**/*`
- `static/**/*`

#### Configs cosmétiques (style only)
- `.prettierrc`
- `.editorconfig`
- `.eslintrc` (lint rules uniquement, pas de logique)

#### Data pédagogique
- `curriculums/*.md`
- `curriculums/*.json`

#### Format files
- Fichiers `.css` de style pur (pas de logique)

---

## 🟣 Règle comportementale — Protection `committer`

Le bash tool `committer` **refuse de stager** les patterns `.gitignore` classiques, même si l'IA tente de les ajouter explicitement. C'est une protection anti-erreur contre les bugs d'auto-stage.

Patterns refusés :
- `node_modules/`, `node_modules/**`
- `__pycache__/`, `*.pyc`
- `dist/`, `build/`, `.next/`, `.svelte-kit/`, `.nuxt/`
- `.DS_Store`, `Thumbs.db`
- `*.log`, `logs/`
- `.cache/`, `tmp/`, `temp/`
- `coverage/`, `.nyc_output/`

Si l'IA tente `committer "..." node_modules/package.json` → **refusé**.

---

## Logique appliquée par `merge-to-main`

```python
# Pseudo-code
for file in git_diff_files:
    if matches_any(file, RED_PATTERNS):
        return "HUMAN_REQUIRED"
    elif matches_any(file, ORANGE_PATTERNS):
        return "ARBITER_REQUIRED"
    # else: file is GREEN, continue

# All files are GREEN:
commit_type = extract_type_from_last_commit()  # [feat], [fix], etc.

if commit_type in ["docs", "style", "test", "chore"]:
    return "AUTO_MERGE"
elif commit_type in ["fix", "refactor", "perf"]:
    stats = git_diff_stat()
    thresholds = load_thresholds(commit_type)  # from merge-to-main-config.json
    if stats.lines <= thresholds.max_lines and stats.files <= thresholds.max_files:
        return "AUTO_MERGE"
    else:
        return "ARBITER_REQUIRED"
elif commit_type in ["feat", "hotfix"]:
    return "ARBITER_REQUIRED"
elif commit_type in ["security", "remove"]:
    return "HUMAN_REQUIRED"
elif commit_type == "wip":
    return "NEVER_MERGE"
```

---

## Exemples concrets

| Scénario | Fichiers touchés | Type commit | Décision |
|----------|------------------|-------------|----------|
| Claude corrige un typo dans README.md | `README.md` | `[docs]` | ✅ AUTO-MERGE |
| Claude ajoute un test unitaire | `tests/test_login.py` | `[test]` | ✅ AUTO-MERGE |
| Claude refactore l'API de login (30 lignes) | `api/auth.py` | `[refactor]` | 🟠 ARBITER (ORANGE file) |
| Claude refactore un module petit (20 lignes) | `docs/infra.md` | `[refactor]` | ✅ AUTO-MERGE (VERT file, sous seuil) |
| Claude ajoute une nouvelle feature | `webapp/src/pages/Admin.svelte` | `[feat]` | 🟠 ARBITER (type [feat]) |
| Claude modifie le docker-compose | `docker-compose.yml` | `[chore]` | 🔴 HUMAN (ROUGE file) |
| Claude update une config LiteLLM | `/opt/litellm/config.yaml` | `[chore]` | 🟠 ARBITER (ORANGE file) |
| Claude modifie un secret | `.dify_admin_key` | `[chore]` | 🔴 HUMAN (ROUGE file) |
| Claude ajoute une migration DB | `migrations/001.sql` | `[feat]` | 🔴 HUMAN (ROUGE file) |
| Claude fait `git add .` | N/A | N/A | ❌ BLOCKED par committer |
| Claude ajoute `node_modules/` par erreur | `node_modules/package.json` | `[chore]` | ❌ BLOCKED par committer |
