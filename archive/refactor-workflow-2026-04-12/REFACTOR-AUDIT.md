# REFACTOR AUDIT — État actuel de l'infrastructure workflow/workspace

> **Snapshot complet** de l'infrastructure au 2026-04-11.
> Compagnon de `REFACTOR-PLAN.md` — l'audit de ce qu'on a aujourd'hui, ce que Peter fait, ce qu'on veut, et les idées potentielles.
> Méthode : scan exhaustif `/root/sinse-workspace/`, `/opt/academie/`, `~/.claude/`

## Métadonnées
- **Créé** : 2026-04-11 (session refactor avec Sinse)
- **Auteur** : Claude
- **Lié à** : `REFACTOR-PLAN.md` (le plan exploitable)

---

## 1. Découvertes clés (vs idées préconçues)

Avant cet audit, je supposais qu'on partait quasi de zéro. **C'est faux** :

1. **Slash commands déjà infrastructurés** : `.claude/commands/fin.md` (Claude Code) ET `.gemini/commands/fin.toml` (Gemini CLI) existent. L'infra est en place, on doit juste enrichir.

2. **Hook Stop déjà actif** : `claude-settings.json` contient un hook qui détecte les changements non commités dans `sinse-workspace` et rappelle de faire `/fin`. Automation existante.

3. **CLAUDE.md dupliqué** : il y en a UN dans `/opt/academie/CLAUDE.md` (9398 bytes, projet) ET UN dans `/root/sinse-workspace/context/CLAUDE.md` (8089 bytes, workspace). **C'est exactement le problème que résout le pointer pattern Peter (D8)**.

4. **Symlink déjà en place** : `/opt/academie/context → /root/sinse-workspace/context`. On a déjà commencé le pattern partagé.

5. **Lock file fonctionne** : `.lock` actuel contient `claude:1775934904`, gitignored proprement. Système opérationnel.

6. **Memory native Claude Code** : `/root/.claude/projects/-opt-academie/memory/reference_dify_api.md` existe ! Claude Code a sa propre couche de mémoire persistante qu'on n'exploite pas explicitement.

7. **DECISIONS.md riche** : 70+ entries. Culture de documentation déjà bien ancrée.

**Conclusion : ~30% du socle est déjà en place**. On enrichit/restructure plus qu'on ne crée from scratch.

---

## 2. Vision globale en une phrase

> On a déjà ~**30% du socle** en place (slash commands infra, hooks, lock, branches, conventions, contexte structuré, symlink), on doit **enrichir ~50%** (pointer pattern, slash commands enrichis, bash tools, refactor docs/, backup) et **créer ~20% from scratch** (worktrees, oracle, smoke-test, dashboard, disaster recovery).

---

## A. Documentation et contexte

| Item | Actuel | Peter | Notre plan | Statut |
|------|--------|-------|------------|--------|
| `STATE.md` | ✅ existe | ❌ pas équivalent | Garder | 🟢 |
| `TODO.md` | ✅ existe | ❌ | Garder + sections par IA | 🟡 |
| `HANDOFF.md` (1 unique) | ✅ existe | `/handoff` slash | → `HANDOFF-{agent}.md` (1/IA) | 🟡 |
| `DECISIONS.md` | ✅ 70+ entries | Pas équivalent | Garder tel quel | 🟢 |
| `CHANGELOG.md` | ✅ append-only | `/add-to-changelog` | Garder + slash command | 🟡 |
| `conventions.md` | ✅ existe | Inclus dans AGENTS.md | Fusionner dans AGENTS.md | 🟡 |
| `CLAUDE.md` workspace (8K) | ✅ existe | AGENTS.md court | → AGENTS.md télégraphique | 🟡 |
| `CLAUDE.md` projet (9K) | ✅ existe **(duplication)** | Pointer | → pointer vers shared | 🟢 |
| `GEMINI.md` | ✅ minimal | N/A | Fusionner dans AGENTS.md | 🟢 |
| `docs/*.md` avec `read_when:` | ❌ absent | ✅ vérifié prod | Créer (8 docs split) | 🟢 |
| `REFACTOR-PLAN.md` | ✅ créé aujourd'hui | N/A | Stabiliser en v1.0 | 🟡 |
| Memory `~/.claude/projects/.../memory/` | ✅ existe (réf Dify API) | N/A | Étudier + exploiter | 🟡 |

### Idées potentielles 🆕
- `INDEX.md` listant tous les fichiers contexte avec leur rôle (anti-perte pour nouvelle IA)
- `GLOSSARY.md` pour les termes spécifiques (TTT, CECRL, dify-snapshot, focus_concept, etc.)
- `ROADMAP.md` séparé du STATE pour vision long terme
- Section "Anti-patterns / Lessons learned" dans DECISIONS.md
- `ARCHITECTURE.md` avec diagrammes ASCII des flux (webapp ↔ FastAPI ↔ Dify ↔ n8n ↔ PG)

---

## B. Slash commands

| Item | Actuel | Peter | Notre plan | Statut |
|------|--------|-------|------------|--------|
| `/fin` Claude | ✅ existe | `/handoff` plus structuré | → renommer `/handoff` | 🟡 |
| `/fin` Gemini | ✅ existe (.toml) | N/A | Aligner sur `/handoff` | 🟡 |
| `/start` ou `/pickup` | ❌ absent | `/pickup` 6 sections | Créer `/pickup` | 🟢 |
| `/handoff` | ❌ absent | `/handoff` 7 sections | Créer (remplace `/fin`) | 🟢 |
| `/commit` | ❌ absent | `/commit` + bash `committer` | Bash tool `committer` (D10) | 🟢 |
| `/oracle` consultation | ❌ absent | npm `@steipete/oracle` | Installer vrai package (D11) | 🟢 |
| `/review` croisée | ❌ absent | Built-in Claude Code | Utiliser built-in | 🟢 |
| `/automerge` | ❌ absent | `/automerge` (PRs) | ⚪ pas pour nous | ⚪ |
| `/check` (run tests) | ❌ absent | `/check` | À discuter (lié au CI) | 🟡 |
| `/changelog-webapp` | ❌ absent | N/A | Règle dans AGENTS.md | 🟢 |

### Idées potentielles 🆕
- `/note` (formaliser le "Make a note" Peter) — ou rester en phrase naturelle
- `/sync` pour forcer une sync des branches IA
- `/decide` pour ajouter une décision au DECISIONS.md proprement
- `/lookup <term>` pour chercher dans le glossaire
- `/why <decision>` pour retrouver la rationale d'une décision dans DECISIONS.md

---

## C. Bash tools / CLIs maison

| Item | Actuel | Peter | Notre plan | Statut |
|------|--------|-------|------------|--------|
| `committer` (safety commits) | ❌ absent | ✅ bash 100 lignes | Porter (adapté) | 🟢 |
| `oracle` (consultation IA) | ❌ absent | npm `@steipete/oracle` | Installer (D11) | 🟢 |
| `docs-list` (read_when scanner) | ❌ absent | bin/docs-list (Bun) | Bash ou Python | 🟢 |
| `cly` wrapper | ❌ absent | ✅ verbatim trouvé | Porter | 🟢 |
| `deploy-teacher` | ⚠️ Python script `update_teacher_chatflow.py` (pas CLI propre) | N/A | Wrapper CLI propre | 🟢 |
| `smoke-test` | ❌ absent | N/A | Créer (S1) | 🟢 |
| `status` dashboard | ❌ absent | N/A | Créer (S3) | 🟢 |
| `profil_manager.py` | ✅ existe | N/A | CLI-fier (typer) | 🟡 |
| `pg-backup` | ❌ absent | N/A | Créer (S1) | 🟢 |
| `restic-backup` wrapper | ❌ absent | N/A | Créer (S1) | 🟢 |

### Idées potentielles 🆕
- `secrets-check` CLI (valide qu'aucun secret n'a été commité) — anti-leak
- `tmux-multi` CLI (démarrer/attacher rapidement plusieurs sessions IA) — futur
- `dify-rollback` CLI (restaurer un chatflow précédent en 1 cmd)
- `pg-restore` wrapper (restaurer un dump de manière sûre, avec backup auto avant)
- `webapp-redeploy` CLI (rebuild + restart propre)
- `agent-status` CLI (juste pour voir quelles IA tournent en ce moment)

---

## D. Architecture multi-IA

| Item | Actuel | Peter | Notre plan | Statut |
|------|--------|-------|------------|--------|
| Branches par IA (claude, gemini) | ✅ existe | ❌ rejette | Garder | 🟢 |
| Worktrees git | ❌ absent | ❌ rejette | Adopter (Modèle C+) | 🟢 |
| Fichier `.lock` multi-IA | ✅ fonctionne | N/A | Garder + améliorer (expiration ?) | 🟡 |
| `/opt/academie-shared/` (secrets partagés) | ❌ absent | N/A | Créer | 🟢 |
| Pointer pattern AGENTS.md | ❌ absent | ✅ vérifié | Adopter (D8) | 🟢 |
| Symlink `/opt/academie/context → workspace/context` | ✅ existe | N/A | Garder, étendre au shared/ | 🟢 |
| Communication oracle | ❌ absent | npm package | Installer | 🟢 |
| Communication review | ❌ absent | Built-in | Utiliser | 🟢 |
| Communication handoff | ❌ absent | Slash command | Créer | 🟢 |
| Tmux pour parallélisme réel | ❌ absent | ✅ utilise | ⚪ futur (6-12 mois) | ⚪ |
| Convention nommage branches | ✅ `claude`, `gemini` | N/A | + `codex` futur | 🟢 |
| Merge protocol (validation humaine) | ✅ manuel | ❌ direct main | Garder manuel + tags | 🟢 |
| Fichier `.agent` par worktree | ❌ absent | N/A | Créer | 🟢 |

### Idées potentielles 🆕
- Worktree "sandbox" `/opt/academie-worktrees/sandbox/` pour tester sans toucher claude/gemini
- "Witness IA" légère qui surveille les conflits potentiels et alerte
- Quotas par IA (limite tokens/jour pour éviter de griller un modèle)
- Heartbeat lock : chaque IA met à jour son timestamp régulièrement (détection lock orphelin)
- Convention de nommage des commits : prefix `[claude]`, `[gemini]`, `[codex]` automatique via committer

---

## E. Sécurité, backup, résilience

| Item | Actuel | Peter | Notre plan | Statut |
|------|--------|-------|------------|--------|
| Backup N1 (Proxmox snapshots) | ❌ absent | Time Machine | Créer S1 | 🟢 |
| Backup N2 (PG dumps horaires) | ❌ absent | N/A | Créer S1 | 🟢 |
| Backup N3 (Restic + GDrive) | ❌ absent | Arq vers B2 | Créer S1 | 🟢 |
| Backup N4 (Git pushé GitHub) | ✅ branche `claude` pushée | ✅ Git | Garder | 🟢 |
| Test de restore | ❌ jamais validé | "tested often" | Obligatoire S1 | 🟢 |
| `docs/disaster-recovery.md` | ❌ absent | N/A | Créer S1 | 🟢 |
| YOLO `--dangerously-skip-permissions` | ❌ absent | ✅ "saves an hour a day" | Activer S2 (après backup) | 🟢 |
| `smoke-test.sh` | ❌ absent | N/A | Créer S1 | 🟢 |
| Healthchecks Docker | ⚠️ partiels (audit S5 OK pour API/frontend) | N/A | Renforcer S3 | 🟡 |
| Pre-commit hooks anti-secrets | ❌ absent | ✅ committer fait safety | À discuter (gitleaks ?) | 🟡 |
| Protocole destructive ops | ❌ absent | "ask before delete/rename" | Créer `docs/destructive-ops.md` | 🟢 |
| Tags git "deploy-YYYY-MM-DD-HH" | ❌ absent | N/A | Dans `/handoff` ou `/merge` | 🟡 |
| Rotation secrets | ❌ absent | N/A | ⚪ Phase optionnelle | ⚪ |

### Idées potentielles 🆕
- Snapshot auto du chatflow Teacher AVANT chaque deploy (rollback rapide en 1 cmd)
- Monitoring Postgres : connections, slow queries, disk usage (`pg_stat_statements`)
- Alertes Telegram/email si backup échoue ou container down
- Test périodique de restore (cron mensuel) pour valider que les backups marchent encore
- Backup secondaire : Borg vers VPS Hetzner 5€/mois (en plus de GDrive, redondance)
- Audit log : qui a accédé à quels secrets quand (pas urgent)

---

## F. Environnement client et accès

| Item | Actuel | Peter | Notre plan | Statut |
|------|--------|-------|------------|--------|
| OS client Sinse | Windows | macOS | → WSL2 + Debian | 🟢 |
| Terminal | Windows par défaut | Ghostty | Windows Terminal (puis WezTerm) | 🟢 |
| SSH vers cosmos | ✅ Windows | SSH macOS natif | Depuis WSL Debian | 🟢 |
| Accès Proxmox | UI web pve.petit-pont.com | N/A | + SSH root (D6) | 🟡 |
| Multi-terminal splits | ❌ pas utilisé | Ghostty 4x splits | ⚪ futur (6-12 mois) | ⚪ |
| Tmux côté cosmos | ❌ pas utilisé | ✅ utilise | ⚪ futur (multi-IA réel) | ⚪ |

### Idées potentielles 🆕
- Tmux config dédié pour Sinse avec raccourcis pour les sessions IA
- Script `connect-cosmos.sh` qui auto-attach à un tmux master
- Aliases bash pour commandes courantes (`a logs`, `a deploy`, `a status`)

---

## G. Hooks et automation Claude Code

| Item | Actuel | Peter | Notre plan | Statut |
|------|--------|-------|------------|--------|
| Hook Stop (rappel git commit) | ✅ existe | ❌ pas mentionné | Garder, étendre | 🟢 |
| Hook PreToolUse / PostToolUse | ❌ absent | ❌ pas mentionné | À discuter | ⚪ |
| Git hooks (pre-commit) | ❌ absent | ❌ pas utilisé | À discuter (gitleaks ?) | 🟡 |
| Cron jobs cosmos | ⚠️ existe pour n8n | N/A | + crons backup | 🟢 |
| `subagents/` Claude Code natif | ✅ existe (auto pour aside questions) | ❌ rejette | Étudier ce qu'on a déjà | 🟡 |

### Idées potentielles 🆕
- Hook qui force `/pickup` au lancement d'une session sur un worktree
- Hook qui détecte si on travaille hors d'un worktree (anti-erreur en multi-IA)
- Cleanup mensuel des paste-cache et file-history Claude Code
- Hook qui détecte si un secret apparaît dans le diff avant commit

---

## Synthèse statuts

**🟢 Décidé** (pas besoin d'en rediscuter, juste à exécuter) : ~35 items
**🟡 À discuter** (pastilles jaunes à trancher avant v1.0) : ~15 items
**⚪ Optionnel / futur** (peut attendre Phase 4 ou plus tard) : ~10 items

Les pastilles jaunes (15 items) sont l'objet de la prochaine étape de discussion.

---

## Liste exhaustive des pastilles jaunes 🟡

### Documentation (7)
- **A1** : `TODO.md` — Garder + sections par IA (format multi-IA)
- **A2** : `HANDOFF.md` — → `HANDOFF-{agent}.md` (1 par IA)
- **A3** : `CHANGELOG.md` — Garder + créer slash command `/add-to-changelog`
- **A4** : `conventions.md` — Fusionner dans AGENTS.md
- **A5** : `CLAUDE.md` workspace (8K) — Refactor en AGENTS.md télégraphique
- **A6** : `REFACTOR-PLAN.md` — Stabiliser en v1.0 (méta, à la fin)
- **A7** : Memory native Claude Code (`~/.claude/projects/.../memory/`) — Étudier et décider si on l'exploite

### Slash commands (3)
- **B1** : `/fin` Claude — Renommer en `/handoff` ou garder les deux
- **B2** : `/fin` Gemini — Aligner sur le format `/handoff`
- **B3** : `/check` (run tests) — Lié à la décision CI Bloc A

### Bash tools (1)
- **C1** : `profil_manager.py` — CLI-fier avec typer (priorité ?)

### Architecture multi-IA (1)
- **D1** : Fichier `.lock` multi-IA — Améliorer (expiration auto, format)

### Sécurité (3)
- **E1** : Healthchecks Docker — Renforcer S3
- **E2** : Pre-commit hooks anti-secrets — Adopter gitleaks ?
- **E3** : Tags git `deploy-YYYY-MM-DD-HH` — Dans `/handoff` ou autre

### Environnement (1)
- **F1** : Accès Proxmox — confirmer SSH (D6 déjà décidé mais à valider en pratique)

### Hooks (2)
- **G1** : Git hooks pre-commit (gitleaks ?) — recoupe E2
- **G2** : Subagents Claude Code natifs — Étudier ce qui existe déjà

**Total : 18 items jaunes** (avec quelques recoupements E2/G1).
