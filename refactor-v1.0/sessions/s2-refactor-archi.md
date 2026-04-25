# Session 2 — Refactor architecture + YOLO activation

> **Durée estimée** : 4h
> **Statut** : ⏳ Dépend de S1 validée
> **Livrable** : Worktrees + AGENTS.md + 15 bash tools + slash commands + YOLO activé
> **Règle d'or #7** : "Plan v1.0 avant exécution. Une fois lancé, pas d'arrêt."

---

## Objectif

Transformer la structure workspace/projet selon le plan v1.0 : créer les worktrees isolés, refactorer la documentation en AGENTS.md télégraphique, créer les 15 bash tools, installer les hooks de validation, activer le mode YOLO.

À la fin de cette session :
- ✅ Structure `/root/sinse-workspace/` restructurée (Option C D12)
- ✅ Worktree `/opt/academie-worktrees/claude/` opérationnel
- ✅ AGENTS.md canonical + pointers dans les worktrees
- ✅ 15 bash tools installés et fonctionnels
- ✅ Slash commands `/pickup` et `/handoff` installés
- ✅ Hooks pre-commit (gitleaks) + pre-push (smoke-test) actifs
- ✅ YOLO mode (`--dangerously-skip-permissions`) activé via `cly`
- ✅ Secrets migrés vers `/opt/academie-shared/secrets/`
- ✅ docs/projet/ enrichi depuis l'ancien CLAUDE.md

---

## Prérequis (vérifier avant de commencer)

- [ ] **Session 1 complètement validée** (tous les 10 critères)
- [ ] Backups actifs (crons running, premier backup Restic complet)
- [ ] `smoke-test` fonctionnel en 4 modes
- [ ] Passphrase Restic stockée en 3 endroits
- [ ] 4h de concentration dispo
- [ ] Claude Code full Opus 4.6 1M

---

## Checklist

### S2.0 — Préparation (10 min)

- [ ] Checkpoint : `echo "SESSION=S2\nSTEP=S2.0" > /root/.session-progress`
- [ ] Valider que la prod tourne : `smoke-test --deep` → tous verts
- [ ] Tag de sécurité : `cd /root/sinse-workspace && git tag "pre-refactor-s2-$(date +%Y-%m-%d)"`
- [ ] Backup manuel Restic : `/opt/academie-shared/scripts/restic-backup.sh`

### S2.1 — Migration secrets (30 min)

#### S2.1.5 — Inventaire exhaustif des secrets (D37 G6)

- [ ] Créer `/opt/academie-shared/secrets/` : `mkdir -p /opt/academie-shared/secrets && chmod 700 /opt/academie-shared/secrets`
- [ ] Grep récursif pour identifier les secrets :
  ```bash
  # Patterns de fichiers
  find /opt/academie /opt/litellm /opt/n8n /root/sinse-workspace \
    \( -name "*key*" -o -name "*secret*" -o -name "*password*" \
    -o -name "*token*" -o -name ".env*" -o -name "*.pem" \
    -o -name "*.crt" -o -name "*_rsa*" -o -name "*_ed25519*" \) \
    2>/dev/null | grep -v node_modules

  # Patterns de contenu (clés API)
  grep -rE "(api[_-]?key|bearer|authorization|password)" \
    /opt/academie /opt/litellm /opt/n8n --include="*.yaml" --include="*.yml" \
    --include="*.json" --include="*.py" --include="*.sh" 2>/dev/null
  ```
- [ ] Lister chaque secret trouvé avec son emplacement source
- [ ] Décider pour chaque : migrer vers `/opt/academie-shared/secrets/` ou laisser ?

#### Migration des secrets critiques

- [ ] `/opt/academie/.dify_admin_key` → `/opt/academie-shared/secrets/dify-admin-key`
  - `mv /opt/academie/.dify_admin_key /opt/academie-shared/secrets/dify-admin-key`
  - `ln -s /opt/academie-shared/secrets/dify-admin-key /opt/academie/.dify_admin_key`
- [ ] `/opt/n8n/encryption.key` → `/opt/academie-shared/secrets/n8n-encryption-key`
  - Idem avec symlink
  - ⚠️ Tester que n8n redémarre proprement après la migration
- [ ] Vérifier que n8n fonctionne encore : `docker restart n8n-academie && sleep 5 && curl http://localhost:5678/healthz`
- [ ] Vérifier que Dify API répond : `smoke-test --deep`

### S2.2 — Structure workspace refactorée (D12, 30 min)

- [ ] Créer la nouvelle arborescence :
  ```bash
  mkdir -p /root/sinse-workspace/tools
  mkdir -p /root/sinse-workspace/slash-commands
  mkdir -p /root/sinse-workspace/docs
  mkdir -p /root/sinse-workspace/projects/academie-ia/merge-requests/archive
  mkdir -p /root/sinse-workspace/projects/academie-ia/docs
  mkdir -p /root/sinse-workspace/projects/academie-ia/archive
  ```
- [ ] **Migrer les fichiers contexte existants** vers `projects/academie-ia/` :
  ```bash
  cd /root/sinse-workspace/context
  mv STATE.md TODO.md HANDOFF.md CHANGELOG.md DECISIONS.md ../projects/academie-ia/
  ```
- [ ] **Renommer HANDOFF.md → HANDOFF-claude.md** (D18) :
  ```bash
  mv /root/sinse-workspace/projects/academie-ia/HANDOFF.md /root/sinse-workspace/projects/academie-ia/HANDOFF-claude.md
  ```
- [ ] **Archiver temporairement** `REFACTOR-PLAN.md` + `REFACTOR-AUDIT.md` :
  ```bash
  mkdir -p /root/sinse-workspace/projects/academie-ia/archive/refactor-workflow-2026-04-12
  mv /root/sinse-workspace/context/REFACTOR-PLAN.md /root/sinse-workspace/projects/academie-ia/archive/refactor-workflow-2026-04-12/REFACTOR-PLAN-working.md
  mv /root/sinse-workspace/context/REFACTOR-AUDIT.md /root/sinse-workspace/projects/academie-ia/archive/refactor-workflow-2026-04-12/REFACTOR-AUDIT.md
  ```
- [ ] **Supprimer** `/root/sinse-workspace/context/` (vide maintenant) ou conserver `claude-settings.json` à la racine :
  ```bash
  mv /root/sinse-workspace/context/claude-settings.json /root/sinse-workspace/.claude-settings.json
  rmdir /root/sinse-workspace/context
  ```
- [ ] Vérifier la nouvelle structure : `tree /root/sinse-workspace/ -L 3`

### S2.3 — Créer AGENTS.md canonical + PROJECT.md (45 min)

#### S2.3.1 — AGENTS.md (workflow rules, télégraphique anglais)

- [ ] Créer `/root/sinse-workspace/AGENTS.md` en copiant le template depuis `reference/workflow-rules.md`
- [ ] Vérifier que toutes les 12 sections + 11 ajouts de D14 sont présentes
- [ ] Valider : format télégraphique, anglais, ~200-300 lignes max
- [ ] Commit :
  ```bash
  cd /root/sinse-workspace
  git add AGENTS.md
  git commit -m "[feat] Create canonical AGENTS.md (D14)"
  ```

#### S2.3.2 — PROJECT.md (academie-ia specific, court)

- [ ] Créer `/root/sinse-workspace/projects/academie-ia/PROJECT.md`
- [ ] Contenu : intro 2 lignes + pointers vers docs/infra.md, dify-teacher.md, etc. + liste des 6 utilisateurs actifs + racourcis des credentials (par référence, pas en clair)
- [ ] ~80 lignes max
- [ ] Commit : `git commit -m "[feat] Create PROJECT.md for academie-ia"`

#### S2.3.3 — Supprimer les anciens fichiers CLAUDE.md / conventions.md / GEMINI.md

- [ ] Dispatch depuis `/root/sinse-workspace/context/CLAUDE.md` (déjà archivé) et `/opt/academie/CLAUDE.md` → voir S2.3.5 ci-dessous
- [ ] Supprimer `/opt/academie/CLAUDE.md` (remplacé par pointer)
- [ ] Créer `/opt/academie/AGENTS.md` pointer :
  ```
  READ /root/sinse-workspace/AGENTS.md AND /root/sinse-workspace/projects/academie-ia/PROJECT.md BEFORE ANYTHING.
  ```

#### S2.3.4 — Mettre à jour le symlink context

- [ ] Supprimer l'ancien : `rm /opt/academie/context`
- [ ] Créer le nouveau : `ln -s /root/sinse-workspace/projects/academie-ia /opt/academie/context`

#### S2.3.5 — Dispatch CLAUDE.md → 6 docs projet (D37 G4)

**Important** : extraction intelligente, pas rédaction from scratch.

- [ ] Lire `archive/refactor-workflow-2026-04-12/REFACTOR-PLAN-working.md` (contient les décisions)
- [ ] Lire `archive/refactor-workflow-2026-04-12/REFACTOR-AUDIT.md` (référence structure)
- [ ] Lire l'ancien CLAUDE.md (depuis l'historique git si besoin)
- [ ] **Dispatch** selon le tableau D16 :
  - Architecture infrastructure + Stack Docker + LiteLLM + Postgres → `docs/infra.md`
  - Dify agents + Teacher v17 + chatflow → `docs/dify-teacher.md`
  - 5 n8n workflows + memory system → `docs/n8n-workflows.md`
  - Webapp + FastAPI + users → `docs/webapp.md`
  - Stratégie pédagogique + taxonomies A1→C2 → `docs/pedagogy.md`
  - Notes importantes + pièges connus → `docs/gotchas.md`
- [ ] **Ajouter YAML front-matter** à chaque fichier :
  ```yaml
  ---
  summary: "Short description of what this doc covers"
  read_when: "When you need X or modify Y"
  ---
  ```
- [ ] Commit : `git commit -m "[docs] Dispatch CLAUDE.md to 6 project docs (D16)"`

### S2.4 — Créer les 15 bash tools (60 min)

Pour chaque tool, voir `reference/tools.md` pour le template complet.

- [ ] `/root/sinse-workspace/tools/cly` (wrapper Claude complet Peter, D36B)
- [ ] `/root/sinse-workspace/tools/committer` (safe commits avec guardrails)
- [ ] `/root/sinse-workspace/tools/arbiter` (cross-review via claude -p / gemini -p)
- [ ] `/root/sinse-workspace/tools/docs-list` (walk docs/ + YAML front-matter)
- [ ] `/root/sinse-workspace/tools/smoke-test` (migrer depuis S1)
- [ ] `/root/sinse-workspace/tools/status` (dashboard multi-IA — stub pour S3)
- [ ] `/root/sinse-workspace/tools/deploy-teacher` (wrapper update_teacher_chatflow.py)
- [ ] `/root/sinse-workspace/tools/pg-backup` (migrer depuis S1)
- [ ] `/root/sinse-workspace/tools/restic-backup` (migrer depuis S1)
- [ ] `/root/sinse-workspace/tools/log` (append CHANGELOG avec type)
- [ ] `/root/sinse-workspace/tools/install-slash-commands` (sync source → targets)
- [ ] `/root/sinse-workspace/tools/init-worktree` (bootstrap nouveau worktree, D37 G3)
- [ ] `/root/sinse-workspace/tools/merge-to-main` (orchestrator Option E)
- [ ] `/root/sinse-workspace/tools/merge-approve`
- [ ] `/root/sinse-workspace/tools/merge-reject`
- [ ] `/root/sinse-workspace/tools/rollback-to` (D34)
- [ ] **Ajouter tous les tools au PATH** : `export PATH="/root/sinse-workspace/tools:$PATH"` dans `~/.bashrc`
- [ ] **Tester chaque tool** individuellement : `committer --help`, `arbiter --help`, etc.

### S2.5 — Slash commands (30 min)

#### S2.5.1 — Créer les fichiers source

- [ ] `/root/sinse-workspace/slash-commands/pickup.md` (depuis `reference/slash-commands.md`)
- [ ] `/root/sinse-workspace/slash-commands/handoff.md` (idem)

#### S2.5.2 — Installer via install-slash-commands

- [ ] Lancer : `install-slash-commands`
- [ ] Vérifier que ça a créé :
  - `~/.claude/commands/pickup.md`
  - `~/.claude/commands/handoff.md`
  - `~/.gemini/commands/pickup.toml`
  - `~/.gemini/commands/handoff.toml`

#### S2.5.3 — Supprimer les anciens `/fin`

- [ ] `rm /opt/academie/.claude/commands/fin.md`
- [ ] `rm /opt/academie/.gemini/commands/fin.toml`
- [ ] Si d'autres anciens slash commands existent, les supprimer aussi

### S2.6 — Git hooks (30 min)

#### S2.6.1 — Installer gitleaks

- [ ] `apt install gitleaks` (ou `curl -L ... | bash`)
- [ ] Tester : `gitleaks detect --source /tmp/test 2>&1 || echo OK`

#### S2.6.2 — Créer les hooks

Pour chaque repo, créer les hooks dans `.git/hooks/` :

**`/root/sinse-workspace/.git/hooks/pre-commit`** :
```bash
#!/bin/bash
gitleaks protect --staged --verbose || exit 1
```

**`/opt/academie/.git/hooks/pre-commit`** :
```bash
#!/bin/bash
gitleaks protect --staged --verbose || exit 1
```

**`/opt/academie/.git/hooks/pre-push`** :
```bash
#!/bin/bash
smoke-test --deep --quiet || exit 1
```

- [ ] Rendre tous les hooks exécutables : `chmod +x ...`
- [ ] **Test** : essayer de committer un fake secret → doit bloquer
- [ ] **Test** : essayer de push avec smoke-test cassé → doit bloquer

### S2.7 — Worktree Claude (20 min)

- [ ] Créer le répertoire parent : `mkdir -p /opt/academie-worktrees`
- [ ] Créer le worktree : `cd /opt/academie && git worktree add /opt/academie-worktrees/claude claude`
- [ ] Utiliser `init-worktree claude` pour finaliser :
  - Création du fichier `.agent` avec "claude"
  - Création du pointer `AGENTS.md`
  - Symlinks vers `/opt/academie-shared/`
  - Copie du template `.claude/settings.local.json`
  - Smoke-test initial
- [ ] Vérifier : `ls -la /opt/academie-worktrees/claude/`
- [ ] Test session depuis le worktree : `cd /opt/academie-worktrees/claude && cly`
  - Vérifier que Claude Code démarre avec --dangerously-skip-permissions
  - Vérifier que le titre de fenêtre est "claude — Claude"

### S2.8 — Activation YOLO + test cly wrapper (15 min)

- [ ] Configurer `cly` comme alias dans `~/.zshrc` ou `~/.bashrc`
- [ ] Source : `source ~/.zshrc`
- [ ] Test : `cly --help` → affiche l'aide Claude Code
- [ ] Test interactif : `cd /opt/academie-worktrees/claude && cly`
- [ ] Vérifier que Claude Code ne demande plus de permissions pour les actions basiques

### S2.9 — Transformation TODO.md vers format CLAIMED (D17, 10 min)

- [ ] Lire l'actuel `/root/sinse-workspace/projects/academie-ia/TODO.md`
- [ ] Restructurer en 3 sections : OPEN / CLAIMED / DONE
- [ ] Convertir les items P1-P5 vers OPEN avec préfixe P1-P5 sur la ligne
- [ ] Commit : `committer "[refactor] TODO.md to CLAIMED format (D17)" TODO.md`

### S2.10 — Docs de récupération finale (15 min)

- [ ] Créer `/root/sinse-workspace/docs/sinse-quickstart.md` (français, D37 G9)
- [ ] Contenu : 1 page max avec les commandes essentielles
- [ ] Créer `docs/destructive-ops.md` avec la liste des opérations bloquantes (règle d'or #6)

### S2.11 — Validation finale session (15 min)

- [ ] `smoke-test --all` → tous verts
- [ ] `committer --help` → fonctionne
- [ ] `arbiter --help` → fonctionne
- [ ] Premier test `/pickup` dans le worktree claude
- [ ] Premier test `/handoff` avec un petit changement (ex: typo dans README)
- [ ] Vérifier que merge-to-main crée bien un tag deploy
- [ ] **Supprimer** `/root/.session-progress`

---

## ✅ Critères de validation Session 2

1. ✅ Structure `/root/sinse-workspace/` conforme à D12
2. ✅ AGENTS.md canonical créé + PROJECT.md créé
3. ✅ 6 docs projet créés avec YAML `read_when:`
4. ✅ Anciens CLAUDE.md, conventions.md, GEMINI.md archivés/supprimés
5. ✅ 15 bash tools créés et fonctionnels
6. ✅ Slash commands installés (Claude + Gemini)
7. ✅ Git hooks actifs (gitleaks, smoke-test)
8. ✅ Worktree Claude opérationnel
9. ✅ YOLO mode activé via cly
10. ✅ Secrets migrés vers `/opt/academie-shared/secrets/`
11. ✅ `smoke-test --all` passe
12. ✅ Premier `/pickup` + `/handoff` complet réussi

---

## 🚨 Troubleshooting

### n8n ne démarre plus après migration encryption.key
- Vérifier que le symlink pointe bien vers le fichier : `ls -la /opt/n8n/encryption.key`
- Vérifier les permissions : `chmod 600 /opt/academie-shared/secrets/n8n-encryption-key`
- Restart : `docker restart n8n-academie`

### Worktree Claude refuse de se créer
- Vérifier que la branche claude existe : `cd /opt/academie && git branch`
- Si pas, la créer : `git branch claude`
- Retry : `git worktree add /opt/academie-worktrees/claude claude`

### gitleaks bloque un commit légitime (faux positif)
- Ajouter la ligne au `.gitleaksignore` du repo avec un commentaire justifiant

### smoke-test --deep fail après la migration
- Check container par container : `docker ps -a`
- Logs : `docker logs <container> --tail 30`
- Vérifier symlinks secrets

---

## Prochaine session

→ **`sessions/s3-multi-ia-reel.md`** — Multi-IA réel (arbiter + Gemini + dashboard, 3h)
