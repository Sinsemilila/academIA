# Decisions — Refactor Workflow v1.0

> Les 37 décisions prises lors de la phase de planification (2026-04-11 → 2026-04-12).
> Format : ID, titre, décision courte, rationale condensé.
> Pour les détails longs et l'historique de discussion, voir `archive/refactor-workflow-2026-04-12/REFACTOR-PLAN-working.md`.

---

## Fondations (D1-D7)

### D1 — Stratégie backup 4 niveaux
**Décision** :
| Niveau | Technologie | Fréquence | Rétention |
|--------|-------------|-----------|-----------|
| 1 | Snapshots Proxmox VM | Quotidien | 7d + 4w + 3m |
| 2 | Dumps PostgreSQL | Horaire | 24h + 7d + 4w |
| 3 | Restic + rclone + Google Drive (chiffré AES-256) | Quotidien | 7d + 4w + 12m + 2y |
| 4 | Git pour le code | À chaque commit | Illimité |

**Rationale** : défense en profondeur, 4 niveaux indépendants. Google Drive retenu car 5 To déjà dispo gratuitement. Test de restore obligatoire avant d'activer YOLO.

### D2 — Architecture multi-IA : Modèle C+ (worktrees isolés + collaboration explicite)
**Décision** :
```
/opt/academia/                     ← prod, branche main
/opt/academia-worktrees/
  ├── claude/                      ← worktree branche claude
  ├── gemini/                      ← worktree branche gemini (futur)
  └── codex/                       ← worktree branche codex (futur)
/opt/academia-shared/              ← secrets + fichiers partagés
```
Collaboration via slash commands : `/oracle` (remplacé par arbiter D28), `/review`, `/handoff`, `/merge` (remplacé par merge-to-main).

**Rationale** : sécurité d'isolation + vélocité de collaboration. Scalable (ajouter Codex = un nouveau worktree).

### D3 — Séquencement : 3 sessions intenses (pas 7 dispersées)
**Décision** : S1 Sécurisation (3-4h) → S2 Refactor archi (4h) → S3 Multi-IA réel (3h) + S4 Polish optionnel (2h).

**Rationale** : sessions denses > dispersées pour conserver la cohérence et éviter la perte de contexte entre sessions.

### D4 — Environnement client : WSL2 + Debian + Windows Terminal
**Décision** : Sinse passe Windows → WSL2 + Debian + Windows Terminal. Claude Code continue de tourner sur cosmos via SSH. Pas de Ghostty (Windows non supporté). Multi-terminal reporté à 6-12 mois.

### D5 — Fichiers contexte refactorés
**Décision** :
| Fichier | Rôle | Lu quand |
|---------|------|----------|
| `AGENTS.md` | Workflow rules (remplace CLAUDE.md + conventions.md + GEMINI.md) | Chaque session |
| `docs/*.md` avec `read_when:` | Docs détaillées par domaine | À la demande |
| `STATE.md` | État global projet | Chaque session |
| `TODO.md` | Format CLAIMED (voir D17) | Chaque session |
| `HANDOFF-{agent}.md` | 1 par IA | Session de l'agent |
| `CHANGELOG.md` | Append-only, formats D19 | Au `/pickup` |
| `DECISIONS.md` | Append-only | Rarement |

### D6 — Accès Proxmox : SSH root
**Décision** : accès SSH direct à l'hôte Proxmox pour accélérer la mise en place des snapshots automatiques.

### D7 — Budget modèle : full Opus 4.6 1M pour le refactor
**Décision** : pas de mix Sonnet, full Opus 1M context pour les sessions S1-S3. 14h dispo, 60% de limite restante = large.

---

## Bloc 1 — Fondation doc (D8-D16)

### D8 — Pointer pattern AGENTS.md
**Décision** : UN AGENTS.md canonical + pointers dans chaque worktree. Note : révisée par D12 (emplacement dans `/root/sinse-workspace/` au lieu de `/opt/academia-shared/`).

**Rationale** : élimine les merges sur AGENTS.md entre branches IA.

### D12 — Structure repo workspace : Option C revisitée
**Décision** : restructurer `/root/sinse-workspace/` pour séparer **workflow** (générique) de **state projet** (spécifique).

```
/root/sinse-workspace/
├── AGENTS.md                       ← canonical workflow
├── docs/                            ← docs workflow cross-project
├── tools/                           ← 15 bash tools maison
├── slash-commands/                  ← source tracked
│   ├── pickup.md
│   └── handoff.md
└── projects/
    └── academie-ia/
        ├── PROJECT.md
        ├── STATE.md
        ├── TODO.md
        ├── HANDOFF-<agent>.md
        ├── CHANGELOG.md
        ├── DECISIONS.md
        ├── merge-requests/
        └── docs/                   ← 6 docs projet (D16)
```

**Rationale** : workflow réutilisable pour 100% des futurs projets. Versionné git via sinse-workspace. Partagé multi-machines via clone.

### D13 — Style et langue des fichiers .md
**Décision** :
| Type de fichier | Style | Langue |
|-----------------|-------|--------|
| `AGENTS.md`, `docs/`, `slash-commands/`, `tools/*` | Télégraphique strict Peter | **Anglais** |
| `STATE.md`, `TODO.md`, `HANDOFF-*.md` | Télégraphique simple | Anglais (historique français préservé) |
| `REFACTOR-PLAN.md` (working temporaire) | Hybride | Français |
| Outputs scripts lisibles humain | Standard | **Français** |

**Rationale** : Sinse ne lit presque jamais les .md (il pilote via conversation). Les .md sont 100% pour l'IA → optimiser tokens via anglais télégraphique.

### D14 — Contenu AGENTS.md : 12 sections + 11 ajouts post-audit
**Décision** : 12 sections (READ ORDER, STYLE, WORKSPACE, MULTI-AGENT, GIT, TOOLS, SLASH COMMANDS, MAKE A NOTE, DESTRUCTIVE OPS, SESSION HYGIENE, WEB CONTEXT, FRONTEND AESTHETICS). Plus 11 ajouts récupérés depuis conventions.md existant (repo = shared memory, DECISIONS/CHANGELOG formats, append-only, lock cleanup, conflict resolution, hook Stop awareness, permissions reference, memory native note, project detection, branch convention).

Voir `reference/workflow-rules.md` pour le template complet.

### D15 — Native Claude Code memory : Option B fallback
**Décision** : documenter l'existence de `~/.claude/projects/<id>/memory/` dans AGENTS.md mais **ne pas s'y remettre pour les choses critiques**. Cross-AI content MUST be in `docs/`.

### D16 — Granularité docs projet : 6 fichiers regroupés
**Décision** :
```
projects/academie-ia/docs/
├── infra.md              ← Docker + nginx + Cloudflare + PG + LiteLLM
├── dify-teacher.md       ← Dify + Teacher v17 chatflow
├── n8n-workflows.md      ← 5 workflows + memory system
├── webapp.md             ← FastAPI + SvelteKit + users
├── pedagogy.md           ← TTT + taxonomies A1→C2
└── gotchas.md            ← notes importantes + pièges
```
Chaque fichier a YAML front-matter `read_when:`. Dispatch from current CLAUDE.md done in S2.3.5 (D37 G4).

---

## Bloc 2 — Organisation multi-IA fichiers (D17-D19)

### D17 — Format TODO.md : structure CLAIMED
**Décision** :
```
## OPEN (any AI can take)
- [ ] Task 1 — P1
- [ ] Task 2 — P2

## CLAIMED
- claude: Task 3 (started 2026-04-12 14:30, P1)
- gemini: Task 4 (started 2026-04-12 15:00, P2)

## DONE
- [x] (claude, 2026-04-10) Description
```

**Rationale** : parsable IA, évite conflits multi-IA (claim explicit), priorité visible dans l'item.

### D18 — Format HANDOFF multi-IA : 1 par IA, structure 7 sections
**Décision** : `HANDOFF-claude.md`, `HANDOFF-gemini.md`, `HANDOFF-codex.md` séparés. Structure 7 sections (Scope/Status, Working tree, Branch/PR/CI, Tests/checks, Next steps, Risks/gotchas, Open questions). Anglais télégraphique.

**Rationale** : zéro conflit de merge entre branches. Chaque IA maintient le sien.

### D19 — CHANGELOG format + bash tool `log`
**Décision** : format `YYYY-MM-DD AI — [type] message` avec 12 types (voir D27). Append-only préservé. Tool bash `log <type> "<message>"` pour append proprement (détecte l'IA courante, date auto, pas de doublon).

---

## Bloc 3 — Outils + lock (D20-D21)

### D20 — Suppression du fichier `.lock`
**Décision** : suppression complète du `.lock` et de toutes ses références.

**Rationale** : redondant avec worktrees isolés (D2) + TODO CLAIMED (D17) + HANDOFF par IA (D18) + git activity. Toutes les fonctions du `.lock` sont remplies par des mécanismes plus robustes.

### D21 — `profil_manager.py` hors scope refactor workflow
**Décision** : scripts academie-IA (`profil_manager.py`, `update_teacher_chatflow.py`, etc.) ne sont PAS touchés par le refactor workflow. Hors scope.

**Rationale** : cohérent avec D12 (séparation workflow/projet). Scripts projet seront audités séparément post-refactor (voir `AUDIT-TODO.md` G10).

---

## Bloc 4 — CI/Validation + Option E auto-merge (D22-D32)

### D22 — Niveau de CI : Niveau 2 Intermédiaire
**Décision** : sweet spot entre sécurité et complexité.
- `smoke-test.sh` automatisé
- Healthchecks Docker renforcés
- Pre-commit hook gitleaks
- Pre-push hook smoke-test --deep
- `/check` slash command (via `smoke-test` tool)

**Rationale** : compatible philosophie Peter (rejette TDD strict mais utilise des hooks). Suffisant pour YOLO sécurisé avec ~90% confiance × backups 4 niveaux = ~99% effectif.

### D23 — `smoke-test.sh` modulaire 4 variantes
**Décision** : `smoke-test --quick` (5s), `--deep` (15s), `--infra` (5s), `--all` (30s). Output émojis + code retour. Voir `reference/tools.md` pour détails.

### D24 — Healthchecks Docker : Option C délégué au smoke-test
**Décision** : pas de modification des healthchecks Docker existants. Le smoke-test gère toutes les vérifs via `docker exec` et `curl` externes.

**Rationale** : zéro risque sur la prod (pas de recreate containers), pas de duplication.

### D25 — Pre-commit hook gitleaks
**Décision** : gitleaks sur les 3 cibles repos (`/root/sinse-workspace/`, `/opt/academia/`, worktrees). Bloque dur si secret détecté. Faux positifs gérés via `.gitleaksignore`.

### D26 — Hooks split : pre-commit gitleaks + pre-push smoke-test
**Décision** : gitleaks en pre-commit (~2s), smoke-test --deep en pre-push (~15s). Bloque dur si fail. `--no-verify` interdit par règle AGENTS.md.

**Clarification D37 G7** :
- `/root/sinse-workspace/.git/hooks/pre-commit` = gitleaks seul
- `/opt/academia/.git/hooks/pre-commit` = gitleaks
- `/opt/academia/.git/hooks/pre-push` = smoke-test --deep
- Worktrees : héritent via `core.hooksPath`

### D27 — Option E auto-merge + 12 types Peter-aligned
**Décision** : adopter Option E (hybride par catégorie) directement, avec 12 types de commit et règles différenciées.

| # | Type | Description | Auto-merge |
|---|------|-------------|------------|
| 1 | `[feat]` | Nouvelle feature | ⚠️ IA arbitre toujours |
| 2 | `[fix]` | Bug fix non-critique | ✅ Auto si < seuil + pas fichier protégé |
| 3 | `[hotfix]` | Bug critique prod | ⚠️ IA arbitre + notif Sinse |
| 4 | `[docs]` | Documentation pure | ✅ TOUJOURS auto sauf fichier protégé |
| 5 | `[refactor]` | Restructuration sans changement comportement | ✅ Auto si < seuil |
| 6 | `[perf]` | Optimisation mesurable | ✅ Auto si < seuil |
| 7 | `[style]` | Formatage cosmétique | ✅ TOUJOURS auto |
| 8 | `[test]` | Tests uniquement | ✅ TOUJOURS auto |
| 9 | `[chore]` | Maintenance, configs, deps | ✅ Auto sauf fichier protégé |
| 10 | `[security]` | Fix vulnérabilité | 🛑 TOUJOURS humain |
| 11 | `[remove]` | Suppression code/fichiers | 🛑 TOUJOURS humain |
| 12 | `[wip]` | Work in progress | ❌ JAMAIS de merge |

Définitions sémantiques précises dans `reference/workflow-rules.md`.

### D28 — IA arbitre : bash tool `arbiter` custom avec CLIs officielles
**Décision** : arbiter = bash wrapper (~30 lignes) utilisant directement `claude -p` et `gemini -p` (CLIs déjà installées sur cosmos, utilisent les abonnements Sinse, 0€).

**Cross-review logic** : commit from claude → `gemini -p` review. Commit from gemini → `claude -p` review. Garantit la diversité d'opinion.

**Révocation D11** : `@steipete/oracle` npm package **plus nécessaire**.

### D29 — Séparation stricte LLM workflow vs LLM projet (règle d'or #8)
**Décision** :
| Usage | LLMs | Auth |
|-------|------|------|
| Workflow (arbiter, consultations) | Claude Pro/Max, Gemini Advanced, futur ChatGPT Plus | Abonnements personnels Sinse via CLIs officielles |
| Projet academie-IA (Teacher, Maestro, etc.) | Groq free, Mistral free, éventuel gpt-4o-mini | LiteLLM config + BYOK (futur) |

**Rationale** : protège les abonnements persos de la consommation user-facing. Garantit que le projet reste free-tier only.

### D30 — Liste complète des fichiers protégés
**Décision** : 3 niveaux de protection pour l'auto-merge.
- **🔴 ROUGE** (humain obligatoire) : secrets, configs infra, DB schema, git hooks, AGENTS.md, slash commands, tools maison, `.claude/settings.*`
- **🟠 ORANGE** (IA arbitre obligatoire) : code backend, frontend, scripts deploy, Dockerfile, LiteLLM config, deps (pyproject, package.json, locks), chatflow exports
- **🟢 VERT** (auto-merge OK) : docs, tests, state files, assets, configs cosmétiques
- **Règle committer** : refuse de stager les patterns `.gitignore` classiques (`node_modules/`, `__pycache__/`, `dist/`, etc.)

Voir `reference/file-protection.md` pour la liste complète.

### D31 — Seuils auto-merge : Option D différenciée par type
**Décision** :
| Type | Max lignes (add+remove) | Max fichiers |
|------|------------------------|--------------|
| `[fix]` | 30 | 3 |
| `[refactor]` | 80 | 5 |
| `[perf]` | 50 | 3 |

Méthode comptage : `git diff --stat` (insertions + deletions). Config stockée dans `/root/sinse-workspace/tools/merge-to-main-config.json` (ajustable via commit `[chore]`).

### D32 — Workflow MERGE-REQUEST.md
**Décision** :
- **Stockage** : `projects/academie-ia/merge-requests/YYYY-MM-DD-HHMM-<branch>.md`
- **Format** : markdown structuré (Status, Request info, Blocking reason, Arbiter eval, Files, Diff preview, Commands)
- **Notification** : stdout direct dans la session courante + fichier trace (**pas de Telegram** — pas nécessaire en sessions interactives actuelles)
- **Tools** : `merge-approve <branch>` et `merge-reject <branch> --reason "..."`
- **Multi-requests** : fichiers distincts par branche + timestamp
- **Filets** : `make status` affiche count pending, hook Stop rappelle si > 0

---

## Bloc 5 — Slash commands (D33)

### D33 — Templates `/pickup` et `/handoff` + placement P2
**Décision** :
- **Templates** : V2 télégraphique anglais corrigée après auto-analyse 7 problèmes
- **Placement P2** :
  ```
  Source (tracked git) : /root/sinse-workspace/slash-commands/{pickup,handoff}.md
  Target Claude Code   : ~/.claude/commands/{pickup,handoff}.md
  Target Gemini CLI    : ~/.gemini/commands/{pickup,handoff}.toml
  ```
- **Sync** : bash tool `install-slash-commands` converti MD → TOML pour Gemini, copie directe pour Claude
- **Anciens `/fin`** : supprimés (remplacés par `/handoff`)

Contenu verbatim dans `reference/slash-commands.md`.

---

## Bloc 6 — Tags deploy + rollback (D34)

### D34 — Tags deploy + tool `rollback-to`
**Décision** :
- **Format tag** : `deploy-YYYY-MM-DD-HHMM`
- **Création** : auto par `merge-to-main` et `merge-approve`
- **Rétention** : tout garder (pas de cleanup)
- **Tool `rollback-to <tag>`** : revert safe via `git revert` (pas de force push), backup branch automatique avant rollback, confirmation explicite (type "ROLLBACK" en majuscules), smoke-test post-rollback, prompt restart containers

---

## Bloc 7 — Exploration native Claude Code (D35)

### D35 — Memory native + subagents policy
**A7 — Memory native** : garder le contenu de `~/.claude/projects/<id>/memory/`, remplacer secrets en dur par références `$(cat /opt/shared/secrets/...)`. Règle dans AGENTS.md.

**G2 — Subagents natifs** : usage limité aux **recherches read-only** uniquement. Pas de modifications, pas de commits, pas de destructrices. Gemini/Codex pas d'équivalent (tradeoff acceptable, pas d'architecture basée dessus).

---

## Post-audit (D36-D37)

### D36 — Ajustements post-audit redondances
**Décision** :
- **36A** — Règle claire dans AGENTS.md sur qui update quoi : STATE → at merge-to-main, TODO → during session, HANDOFF → at /handoff, CHANGELOG → via log tool, DECISIONS → manual append
- **36B** — `cly` wrapper : version complète Peter verbatim (background title setter inclus, prête pour futur multi-terminal)
- **36C** — Fichiers REFACTOR-*.md temporaires : archivés post-v1.0 dans `projects/academie-ia/archive/`
- **36D** — Anciens `/fin` : suppression confirmée

### D37 — Résolution 10 gaps pre-v1.0 + structure v1.0 multi-fichiers
**Décision** :
- **G1** — Passphrase Restic : triple stockage (local chmod 600 + carnet papier offsite + password manager)
- **G2** — Structure v1.0 multi-fichiers Option C (ce dossier `refactor-v1.0/`)
- **G3** — Tool `init-worktree` ajouté comme 15ème bash tool
- **G4** — Dispatch auto CLAUDE.md → 6 docs projet en S2.3.5
- **G5** — Squelette `disaster-recovery.md` avec 4 scénarios obligatoires
- **G6** — Liste exhaustive secrets : grep récursif en S2.1.5
- **G7** — Git hooks par repo clarifiés (sinse-workspace = gitleaks seul, academie = gitleaks + smoke-test)
- **G8** — Checkpoints sessions via `.session-progress` file
- **G9** — `sinse-quickstart.md` créé en fin S2 (français, 1 page)
- **G10** — `AUDIT-TODO.md` académie-IA créé en fin S3 (9 points de D21)

---

## Décisions révoquées ou révisées

| Décision | Status | Raison |
|----------|--------|--------|
| D8 (pointer pattern AGENTS.md dans `/opt/academia-shared/`) | 🔄 **Révisée par D12** | Emplacement changé vers `/root/sinse-workspace/` pour cohérence projet-agnostique |
| D11 (oracle npm package `@steipete/oracle`) | ❌ **RÉVOQUÉE** | Remplacée par D28 (arbiter custom avec CLIs officielles gratuites) |
| D19 (6 types CHANGELOG) | 🔄 **Étendue par D27** | 6 → 12 types pour l'auto-merge Option E |

---

## Vue d'ensemble : les 8 règles d'or

1. **Backup avant tout**
2. **Prod intouchable**
3. **Code produit intact**
4. **Tester chaque brique avant la suivante**
5. **Documenter les décisions en temps réel**
6. **Aucun changement destructif sans confirmation**
7. **Plan v1.0 avant exécution. Une fois lancé, pas d'arrêt.**
8. **Séparation stricte LLM workflow vs LLM projet**

Toutes les 37 décisions respectent ces 8 règles. Voir `README.md` pour la formulation complète.
