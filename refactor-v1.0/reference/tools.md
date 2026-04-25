# Bash Tools Reference

> Les 15 bash tools maison du workflow refactor v1.0.
> Emplacement : `/root/sinse-workspace/tools/`
> Tous ajoutés au PATH via `~/.bashrc` / `~/.zshrc`.

---

## 1. `cly` — Claude Code wrapper (Peter verbatim)

**Rôle** : lance Claude Code avec `--dangerously-skip-permissions` + maintient le titre de fenêtre au nom du dossier courant (pour futur multi-terminal).

**Usage** : `cly` (dans un worktree)

**Code** (D36B, version complète Peter) :
```zsh
cly() {
    local folder=${PWD:t}
    _set_title "$folder — Claude"
    (
        while true; do
            _set_title "$folder — Claude"
            sleep 0.5
        done
    ) &
    local title_pid=$!
    "/usr/local/bin/claude" --dangerously-skip-permissions "$@"
    local exit_code=$?
    kill $title_pid 2>/dev/null
    wait $title_pid 2>/dev/null
    _set_title "%~"
    return $exit_code
}

_set_title() { print -Pn "\e]2;$1\a" }
```

**Note** : Peter utilise `$HOME/.claude/local/claude`. Pour nous, `/usr/local/bin/claude` (selon l'audit).

---

## 2. `committer` — Safe commits avec guardrails

**Rôle** : remplacer `git commit` direct. Enforce des safety invariants en dur (pas contournables par une IA).

**Usage** : `committer "[<type>] <message>" <file1> <file2> ...`

**Guardrails** (voir D25 D30) :
- Rejette message vide
- Bloque `"."` comme file arg (évite `git add .`)
- Valide que chaque file existe OU est in HEAD
- Unstage tout d'abord (`git restore --staged :/`)
- Stage uniquement les files listés
- Vérifie staged non vide avant commit
- Check type dans la liste autorisée (12 types D27)
- Refuse les patterns `.gitignore` classiques (node_modules, __pycache__, dist, .DS_Store, *.pyc, *.log)

**Pseudo-code** :
```bash
#!/bin/bash
set -euo pipefail

MESSAGE="$1"
shift
FILES=("$@")

# Validations
[[ -z "$MESSAGE" ]] && { echo "❌ Empty message"; exit 1; }
[[ ${#FILES[@]} -eq 0 ]] && { echo "❌ No files specified"; exit 1; }
[[ "${FILES[0]}" == "." ]] && { echo "❌ '.' is forbidden — list files explicitly"; exit 1; }

# Validate type in message
if ! grep -qE "^\[(feat|fix|hotfix|docs|refactor|perf|style|test|chore|security|remove|wip)\]" <<< "$MESSAGE"; then
    echo "❌ Message must start with [type] (see D27)"
    exit 1
fi

# Reject .gitignore patterns
for f in "${FILES[@]}"; do
    [[ "$f" == *node_modules* ]] && { echo "❌ node_modules forbidden"; exit 1; }
    [[ "$f" == *__pycache__* ]] && { echo "❌ __pycache__ forbidden"; exit 1; }
    [[ "$f" == *.pyc ]] && { echo "❌ .pyc forbidden"; exit 1; }
    [[ "$f" == .DS_Store ]] && { echo "❌ .DS_Store forbidden"; exit 1; }
    # ... etc
done

# Validate files exist
for f in "${FILES[@]}"; do
    [[ ! -f "$f" ]] && git ls-files --error-unmatch "$f" &>/dev/null || { echo "❌ File not found: $f"; exit 1; }
done

# Unstage everything, then stage listed files only
git restore --staged :/
git add -- "${FILES[@]}"

# Verify staged diff is non-empty
if git diff --cached --quiet; then
    echo "❌ No changes staged"
    exit 1
fi

# Commit
git commit -m "$MESSAGE"
```

---

## 3. `arbiter` — Cross-review IA via CLIs officielles

**Rôle** : valider/rejeter une demande de merge par cross-review IA (Claude review Gemini et vice-versa).

**Usage** : `arbiter --branch <branch> --type <commit_type> [--diff <file>]`

**Logique** (D28) : utilise la CLI **opposée** à l'auteur du commit pour garantir la diversité d'opinion.

**Output** :
```
DECISION: GO or NO-GO
REASON: <one paragraph>
ISSUES: <if NO-GO>
```

**Pseudo-code** :
```bash
#!/bin/bash
set -euo pipefail

BRANCH=""
COMMIT_TYPE=""
DIFF_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch) BRANCH="$2"; shift 2 ;;
        --type) COMMIT_TYPE="$2"; shift 2 ;;
        --diff) DIFF_FILE="$2"; shift 2 ;;
    esac
done

if [[ -z "$DIFF_FILE" ]]; then
    DIFF_FILE=$(mktemp)
    git diff main.."$BRANCH" > "$DIFF_FILE"
fi

PROMPT="You are reviewing a merge request for auto-merge approval.

BRANCH: $BRANCH
COMMIT TYPE: [$COMMIT_TYPE]

DIFF:
$(cat "$DIFF_FILE")

REVIEW CRITERIA:
1. Does this introduce regression?
2. Is the code consistent with existing patterns?
3. Any obvious bugs, security issues, or anti-patterns?
4. Is the commit type accurate?

OUTPUT FORMAT (strict, must be parsable):
DECISION: GO or NO-GO
REASON: <one paragraph>
ISSUES: <bullet list if NO-GO>"

# Cross-review: use CLI opposite to committing branch
case "$BRANCH" in
    claude*|claude-*)
        gemini -p "$PROMPT" -o text
        ;;
    gemini*|gemini-*)
        claude -p "$PROMPT" --output-format text
        ;;
    codex*|codex-*)
        gemini -p "$PROMPT" -o text
        ;;
    *)
        gemini -p "$PROMPT" -o text
        ;;
esac
```

---

## 4. `docs-list` — Walk docs/ + YAML front-matter

**Rôle** : lister tous les fichiers `docs/` avec leur `summary` et `read_when:` extraits du YAML front-matter. Utilisé par `/pickup` pour que l'IA sache quels docs lire sélectivement.

**Usage** : `docs-list` ou `docs-list <project>`

**Output exemple** :
```
📚 Available docs for academie-ia:

docs/infra.md
  summary: Docker stack, nginx, Cloudflare, Postgres, LiteLLM
  read_when: You modify containers, ports, or infrastructure

docs/dify-teacher.md
  summary: Dify agents + Teacher v17 chatflow (28 nodes)
  read_when: You modify the Teacher chatflow or other Dify agents
```

**Pseudo-code** :
```bash
#!/bin/bash
PROJECT="${1:-academie-ia}"
DOCS_DIR="/root/sinse-workspace/projects/$PROJECT/docs"
WORKFLOW_DOCS_DIR="/root/sinse-workspace/docs"

walk_dir() {
    local dir="$1"
    for f in "$dir"/*.md; do
        [[ -f "$f" ]] || continue
        echo "$f"
        awk '/^---$/{f++} f==1 && /^summary:/ {print "  "$0} f==1 && /^read_when:/ {print "  "$0} f==2{exit}' "$f"
        echo
    done
}

echo "📚 Workflow docs:"
walk_dir "$WORKFLOW_DOCS_DIR"
echo
echo "📚 Project docs ($PROJECT):"
walk_dir "$DOCS_DIR"
```

---

## 5. `smoke-test` — Health check modulaire

**Rôle** : valider l'état de la prod en 4 modes selon le besoin.

**Usage** :
- `smoke-test` → default (`--deep`)
- `smoke-test --quick` (~5s)
- `smoke-test --deep` (~15s)
- `smoke-test --infra` (~5s)
- `smoke-test --all` (~30s)
- Ajouter `--quiet` pour output minimal (utilisé par hooks)

**Contenu détaillé** (D23) :

**`--quick`** :
```bash
# Containers UP
for c in academie-frontend academie-api dify-api dify-worker postgres-academie redis-academie n8n-academie litellm-proxy; do
    docker ps --filter "name=^${c}$" --format "{{.Status}}" | grep -q "Up" && echo "✓ $c UP" || echo "✗ $c DOWN"
done

# Services HTTP
curl -sf -o /dev/null https://academie.petit-pont.com/ && echo "✓ webapp 200" || echo "✗ webapp fail"
curl -sf -o /dev/null http://localhost:8000/health && echo "✓ api health" || echo "✗ api fail"
```

**`--deep`** (inclut `--quick` +) :
```bash
# Endpoints API
curl -sf -o /dev/null http://localhost:8000/api/me/concepts -H "Cookie: session=<test>" && echo "✓ /api/me/concepts" || echo "✗"

# Dify chatflow nodes count
docker exec postgres-academie psql -U sinse -d dify -c "SELECT jsonb_array_length(graph->'nodes') FROM apps WHERE id='...'" | grep -q "28" && echo "✓ Teacher 28 nodes" || echo "✗"

# n8n workflows actifs
docker exec postgres-academie psql -U sinse -d n8n -c "SELECT count(*) FROM workflow_entity WHERE active=true" | grep -q "5" && echo "✓ n8n 5 workflows" || echo "✗"

# LiteLLM models
curl -sf http://localhost:4000/v1/models | jq '.data | length' | grep -q "5" && echo "✓ LiteLLM 5 models" || echo "✗"
```

**`--infra`** :
```bash
# Disk space
df -h /opt /var/lib/docker | awk 'NR>1 && int($5) < 80 {print "✓ "$6" "$5}'

# RAM
free -m | awk '/^Mem:/ {avail=$7; if (avail > 1024) print "✓ RAM "avail"M available"; else print "✗ RAM "avail"M low"}'

# Restart count
for c in academie-frontend academie-api; do
    n=$(docker inspect "$c" --format '{{.RestartCount}}')
    [[ $n -lt 5 ]] && echo "✓ $c restarts=$n" || echo "⚠ $c restarts=$n"
done
```

---

## 6. `status` — Dashboard multi-IA

**Rôle** : vue d'ensemble en 1 écran de l'état des worktrees, prod, backups, merge requests.

**Usage** : `status`

**Output** (français pour Sinse, D13 exception) :
```
=== Académie Workflow Status ===

WORKTREES
  claude   [2 ahead]  active 3 min ago   task: "XP triggers feat"
  gemini   [idle]     last 2h ago         task: none

PROD
  webapp:       ✓ OK
  dify:         ✓ OK
  n8n:          ✓ OK
  postgres:     ✓ OK
  containers:   12/12 UP

BACKUPS
  proxmox:   last 6h ago  (deploy-2026-04-12-0300)
  pg dump:   last 15 min ago
  restic:    last 8h ago  (Google Drive sync OK)

MERGE REQUESTS
  pending: 0
```

---

## 7. `deploy-teacher` — Wrapper chatflow update

**Rôle** : wrapper CLI propre autour de `/opt/academie/scripts/update_teacher_chatflow.py` avec snapshot avant deploy + restart.

**Usage** : `deploy-teacher [--dry-run] [--rollback <snapshot>]`

**Logique** :
1. Créer un snapshot du chatflow actuel : `docs/projects/academie-ia/teacher-chatflow-snapshots/YYYY-MM-DD-HHMM.json`
2. Lancer `python3 /opt/academie/scripts/update_teacher_chatflow.py`
3. Restart `dify-api dify-worker`
4. Smoke-test --deep pour valider
5. Si fail → rollback automatique au snapshot précédent

---

## 8. `pg-backup` — Dumps PostgreSQL

**Rôle** : dump horaire de `academie_db` avec rétention intelligente.

**Usage** : `pg-backup` (lancé par cron horaire)

**Voir** : S1.3 pour le code complet.

---

## 9. `restic-backup` — Offsite Google Drive

**Rôle** : backup quotidien chiffré vers Google Drive via Restic + rclone.

**Usage** : `restic-backup` (lancé par cron 3h du matin)

**Voir** : S1.5 pour le code complet.

---

## 10. `log` — Append CHANGELOG avec type

**Rôle** : ajouter une entrée au CHANGELOG.md du projet courant avec type valide.

**Usage** : `log <type> "<message>"`

**Exemples** :
```bash
log feat "AGENTS.md canonical created"
log refactor "TODO.md to CLAIMED format"
log fix "Onboarding Phase 1→2 transition"
```

**Logique** :
1. Détecte l'IA courante (via `.agent` file ou `$AGENT_NAME`)
2. Date automatique `$(date +%Y-%m-%d)`
3. Valide type dans la liste autorisée (12 types D27)
4. Append la ligne `<date> <agent> — [<type>] <message>` à `CHANGELOG.md`
5. Vérifie absence de doublon (même message, même date)
6. Exit 0 succès

---

## 11. `install-slash-commands` — Sync source → targets

**Rôle** : synchroniser les slash commands depuis `/root/sinse-workspace/slash-commands/` vers `~/.claude/commands/` et `~/.gemini/commands/`.

**Usage** : `install-slash-commands`

**Logique** :
1. Lit `slash-commands/*.md`
2. Pour chaque fichier, copie vers `~/.claude/commands/<name>.md` (copie directe)
3. Convertit en TOML pour `~/.gemini/commands/<name>.toml` :
   ```toml
   description = "..."
   prompt = """
   <markdown content>
   """
   ```
4. Check idempotent (skip si pas de diff)

---

## 12. `init-worktree` — Bootstrap nouveau worktree (D37 G3)

**Rôle** : créer un nouveau worktree avec toute l'infra nécessaire.

**Usage** : `init-worktree <agent>` (ex: `init-worktree gemini`)

**Logique** :
1. Vérifie que la branche `<agent>` existe (sinon la crée)
2. `git worktree add /opt/academie-worktrees/<agent> <agent>`
3. Crée `.agent` file : `echo "<agent>" > /opt/academie-worktrees/<agent>/.agent`
4. Crée AGENTS.md pointer :
   ```
   READ /root/sinse-workspace/AGENTS.md AND /root/sinse-workspace/projects/academie-ia/PROJECT.md BEFORE ANYTHING.
   ```
5. Symlinks vers `/opt/academie-shared/` pour les secrets
6. Copie template `.claude/settings.local.json` avec permissions worktree
7. Lance `smoke-test --quick` dans le worktree
8. Output : "✓ Worktree <agent> ready at /opt/academie-worktrees/<agent>"

---

## 13. `merge-to-main` — Merge orchestrator Option E

**Rôle** : tenter l'auto-merge de la branche courante vers main en appliquant Option E (D27-D32).

**Usage** : `merge-to-main` (dans un worktree)

**Logique** :
1. Vérifie qu'on est dans un worktree (pas main direct)
2. Récupère le commit type depuis le dernier commit de la branche
3. Classe chaque fichier modifié en ROUGE / ORANGE / VERT (D30)
4. Applique les règles de D27 + D31 :
   - Type + files → AUTO_MERGE / ARBITER_REQUIRED / HUMAN_REQUIRED / NEVER_MERGE
5. Si AUTO_MERGE :
   - `git merge <branch>` dans main
   - `git tag deploy-YYYY-MM-DD-HHMM`
   - `git push origin main <tag>`
   - Output : "✅ Auto-merged to main"
6. Si ARBITER_REQUIRED :
   - `arbiter --branch <branch> --type <type>`
   - Parse DECISION: GO/NO-GO
   - Si GO → auto-merge (comme ci-dessus)
   - Si NO-GO → create MERGE-REQUEST.md + exit 1
7. Si HUMAN_REQUIRED ou NEVER_MERGE :
   - Create MERGE-REQUEST.md in `projects/<project>/merge-requests/YYYY-MM-DD-HHMM-<branch>.md`
   - Output message (voir D32 format) + exit 1

---

## 14. `merge-approve` / `merge-reject` — Merge request handling

**Rôle** : approuver ou rejeter une MERGE-REQUEST pending.

**Usage** :
- `merge-approve <branch>` : approve et merge vers main
- `merge-reject <branch> --reason "..."` : rejette avec raison

**Logique** : voir D32 section 5D.

---

## 15. `rollback-to` — Safe rollback via git revert (D34)

**Rôle** : rollback rapide et safe vers un tag deploy précédent.

**Usage** : `rollback-to <tag>` (ex: `rollback-to deploy-2026-04-12-2130`)

**Logique** : voir D34 (11 étapes détaillées) dans decisions.md.

**Safety** :
- Confirmation explicite "ROLLBACK" en majuscules
- Backup branch automatique avant rollback
- Git revert (pas de force push)
- Smoke-test post-rollback
- Prompt restart containers

---

## Installation sur le PATH

Ajouter au `~/.bashrc` ou `~/.zshrc` :
```bash
export PATH="/root/sinse-workspace/tools:$PATH"
```

Puis `source ~/.bashrc`.

Tester : `which committer` → doit retourner le path.
