# REFACTOR PLAN — Socle Académie-IA

> **Document vivant.** Enrichi à chaque décision pendant les discussions de refactor.
> À stabiliser avant les sessions d'exécution, puis intégré aux fichiers contexte permanents.

## Métadonnées

- **Créé** : 2026-04-11 (session 20 Claude avec Sinse)
- **Statut** : ✅ **v1.0 STABILISÉ** — ready to execute Session 1
- **Version** : **v1.0** 🎉
- **Dernière maj** : 2026-04-12 (stabilisation v1.0)
- **Compagnon** : `REFACTOR-AUDIT.md` (snapshot état actuel)
- **Livrable stabilisé** : `projects/academie-ia/refactor-v1.0/` (12 fichiers structurés)
- **Note** : ce fichier working (1940+ lignes) sera archivé en S2.2 dans `projects/academie-ia/archive/refactor-workflow-2026-04-12/REFACTOR-PLAN-working.md`. La source de vérité pour l'exécution est maintenant `projects/academie-ia/refactor-v1.0/`.

---

## 1. Contexte et objectif

### 1.1 Pourquoi ce refactor

Notre workflow actuel fonctionne mais présente des faiblesses structurelles :

- **Pas de filet de sécurité** : backups limités, risque de perte si bug ou manipulation destructive
- **Pas de multi-IA** : on prévoit Claude + Gemini + Codex, l'archi actuelle ne le supporte pas
- **Pas d'outillage workflow** : aucun slash command structuré, aucun CLI maison, aucun dashboard
- **Documentation monolithique** : CLAUDE.md ~500 lignes lu à chaque session → 3-5k tokens consommés pour rien
- **Protocoles répétitifs** : début/fin de session recopiés manuellement dans chaque HANDOFF
- **Pas de YOLO sécurisé** : chaque action demande permission → frottement constant

### 1.2 Ambition

Construire un socle professionnel inspiré de Peter Steinberger (Claude Code power user), adapté à notre stack spécifique (Dify + n8n + Postgres + FastAPI + SvelteKit en prod sur Proxmox), permettant :

- ✅ Backup 4-niveaux robuste avec test de restore validé
- ✅ Multi-IA collaboratif (Claude + Gemini + Codex)
- ✅ Mode YOLO (`--dangerously-skip-permissions`) sécurisé
- ✅ Slash commands réutilisables remplaçant les protocoles recopiés
- ✅ Documentation scalable (AGENTS.md court + `docs/` détaillés avec `read_when:`)
- ✅ Observability minimale (smoke-test, dashboard, destructive-ops protocol)

### 1.3 Règles d'or du refactor (à ne jamais violer)

1. **Backup avant tout** — zéro changement structurel tant que le test de restore n'est pas validé
2. **Prod intouchable** — academia.petit-pont.com doit continuer à fonctionner pendant tout le refactor
3. **Code produit intact** — on refactore l'infrastructure AUTOUR du code, pas le code lui-même (webapp, Teacher)
4. **Tester chaque brique avant la suivante** — valider worktree claude avant de créer worktree gemini
5. **Documenter les décisions en temps réel** — ce fichier + `DECISIONS.md` mis à jour à chaque choix
6. **Aucun changement destructif sans confirmation explicite** de Sinse, même en YOLO
7. **Plan v1.0 avant exécution. Une fois lancé, pas d'arrêt.** Aucune session d'exécution (S1+) ne démarre tant que : (a) toutes les zones d'ombre sont résolues ou explicitement mises en "future work", (b) tous les `[DISCUSS]` de la TODO sont tranchés, (c) le plan est officiellement passé en v1.0. Une fois une session lancée, elle va jusqu'au livrable complet défini dans ses critères de validation. Mesure deux fois, coupe une fois.
8. **Séparation stricte LLM workflow vs LLM projet.** Les abonnements personnels de Sinse (Claude Pro/Max, Gemini Advanced, futur ChatGPT Plus) sont UNIQUEMENT utilisés pour le workflow (via les CLIs `claude`, `gemini`, `codex` + l'arbiter custom). Ils ne servent JAMAIS les features user-facing du projet academie-IA. Le projet academie-IA utilise EXCLUSIVEMENT LiteLLM + fournisseurs free tier (Groq, Mistral free, etc.) pour ses agents Dify (Teacher, Maestro, etc.). Cette séparation protège les abonnements personnels de la consommation user-facing et garantit que le projet reste "free-tier only" tant que les clés BYOK ne sont pas en place.

---

## 2. Inspirations — Peter Steinberger (synthèse v2 vérifiée)

> ✅ Recherche ciblée v2 complétée le 2026-04-11. 64 tool uses, sources vérifiées sur `steipete.me` et `github.com/steipete`. Toutes les citations ci-dessous sont verbatim depuis les sources publiques.

### 2.1 État actuel de son workflow (CRITIQUE)

**Peter a largement abandonné Claude Code pour Codex (GPT-5.2 high)** en fin 2025. Quotes verbatim :

> "5x more done on one codex session than with claude."
> "Claude Code is much more eager—great for smaller edits—not so good for larger features or refactors."
> "I used to play with slash commands, but just never found them too useful."
> "Plan mode feels like a hack that was necessary for older generations of models."

**Canonical source actuelle** : `github.com/steipete/agent-scripts` (l'ancien `agent-rules` est archivé depuis 31 déc 2025).

**Conséquence pour nous** : on adopte ses **patterns** (model-agnostic) mais pas son **outillage récent** (Codex-specific). Ses slash commands archivés dans `agent-rules` restent utiles comme **templates de prompt** mais pas comme doctrine actuelle.

### 2.2 Philosophie (5 principes, inchangée)

| # | Principe | Résumé |
|---|----------|--------|
| 1 | Just Talk To It | Zéro framework, zéro spec élaborée |
| 2 | Context is precious | Chaque token compte, AGENTS.md télégraphique |
| 3 | I ship code I don't read | Closed-loop validation via CI |
| 4 | CLI > MCP | Tools maison auto-documentés via `--help` |
| 5 | Pas de worktrees | Multi-agents dans le même dossier (nous, on diverge) |

### 2.3 Wrapper `cly` (code verbatim)

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
    "$HOME/.claude/local/claude" --dangerously-skip-permissions "$@"
    local exit_code=$?
    kill $title_pid 2>/dev/null
    wait $title_pid 2>/dev/null
    _set_title "%~"
    return $exit_code
}

_set_title() { print -Pn "\e]2;$1\a" }
```

Stocké dans `~/.config/zsh/claude-wrapper.zsh`, sourcé depuis `~/.zshrc`. La boucle background restore le titre toutes les 0.5s (Claude Code l'override sinon).

### 2.4 Slash commands — ce qu'il utilise VRAIMENT

**Dans "Just Talk To It" (oct 2025), Peter explicite** : il n'utilise que peu de slash commands.

**Actuellement utilisés** :
- `/commit` — "usually I just type 'commit'"
- `/automerge` — traite les PRs une par une, réagit aux bot comments
- `/massageprs` — idem sans squashing
- `/review` — built-in Claude Code, sélectif
- `/handoff` et `/pickup` (dans `~/.codex/prompts/`) — pour sessions longues

**Slash commands archivés** (`agent-rules/project-rules/*.mdc`, mid-2025, legacy mais utiles comme templates) :
- `/commit` — pré-commit checks, conventional + emojis, suggère splits
- `/commit-fast` — auto-execute, **exclut "Co-Authored-By: Claude"**
- `/context-prime` — 5 phases : overview → AI guidelines → structure → config → dev context
- `/implement-task` — 5 sections : strategy → approaches → tradeoffs → steps → best practices
- `/bug-fix` — issue first, failing test before fix, format `fix: msg (#num)`
- `/pr-review` — **6 personas** (PM, Dev, QA, Sec, DevOps, Design). Quote verbatim : *"Improvements scheduled for 'later' must be addressed NOW!"*
- `/check` — `npm run check` (ou équivalent par langue), sans commit ni version bump
- `/clean` — format/quality auto-fix (black, prettier, eslint, etc.)
- `/five` — Five Whys root-cause analysis
- `/add-to-changelog` — "Keep a Changelog" convention

### 2.5 Tools maison vérifiés

**`committer` (bash)** — Pas un slash command, un **script bash PATH-installé**. Source vérifiée à `github.com/steipete/agent-scripts/scripts/committer`.

Guardrails en dur (inviolables par l'IA) :
- Rejette message vide
- Rejette si arg 1 est un file path (mistake detection)
- **Bloque `"."` comme file arg** ("defeats the helper's safety guardrails")
- Valide que chaque file existe OU est dans HEAD (pour staging des deletions)
- Unstage tout (`git restore --staged :/`)
- Stage uniquement les files listés (`git add -A -- "${files[@]}"`)
- Vérifie staged non vide avant commit
- Sur error index.lock avec `--force`, extrait le lock path de stderr et le remove

Existe SPÉCIFIQUEMENT pour empêcher les agents de faire `git add .` en multi-agent.

**`oracle` (Node.js)** — `npm install -g @steipete/oracle` ou `brew install steipete/tap/oracle`. Core : *"Bundles your prompt and files so another AI can answer with real context"*.

Flags : `-p/--prompt`, `-f/--file` (globs + excludes), `-e/--engine` (api/browser), `-m/--model` (default gpt-5.4-pro), `--copy`, `--render`.

Session hygiene rule dans AGENTS.md : *"run `npx -y @steipete/oracle --help` once/session before first use."* (parce que les flags changent).

**`peekaboo` (Swift, macOS only)** — Screenshots + UI automation + vision QA. 25+ commands. macOS-only, donc pas applicable pour nous directement.

**Autres tools maison** (contexte) : `bird` (CLI Twitter), `sonoscli` (CLI Sonos), `clawdis` (CLI WhatsApp), `mcporter` (launcher MCP à la demande), `bin/docs-list` (Bun-compiled, walk docs/), `bin/browser-tools` (Chrome DevTools helper standalone), `gh` CLI **mandaté** over web search.

### 2.6 Pointer pattern AGENTS.md (majeur)

Peter garde UN AGENTS.md canonical dans `~/Projects/agent-scripts/AGENTS.MD`. Chaque repo a juste une ligne pointer :

> `"READ ~/Projects/agent-scripts/AGENTS.MD BEFORE ANYTHING (skip if missing)."`

Les notes repo-local vont **sous** cette ligne. **Élimine la duplication et les merges sur AGENTS.md entre branches/repos.**

### 2.7 Docs framework avec `read_when:` (confirmé production)

Chaque doc dans `docs/` a YAML front-matter obligatoire :
```yaml
---
summary: ...
read_when: ...
---
```

Un script `bin/docs-list` (Bun-compiled) walk `docs/`, enforce front-matter, print summaries.

**AGENTS.md verbatim** :
> "Start: run docs list (`docs:list` script, or `bin/docs-list`); open docs before coding."
> "Follow links until domain makes sense; honor `Read when` hints."
> "Keep notes short; update docs when behavior/API changes (no ship w/o docs)."
> "Add `read_when` hints on cross-cutting docs."

C'est sa **version zero-dependency du RAG** : pas d'embedding, pas de vector search. L'IA reçoit la liste des docs avec summaries au démarrage, décide quoi lire.

### 2.8 Pattern "Make a note" (verbatim)

Dans son AGENTS.MD :
> `"'Make a note' => edit AGENTS.md (shortcut; not a blocker). Ignore CLAUDE.md."`

- **Phrase naturelle** (pas de slash command)
- **Shortcut, not blocker** — l'agent le fait en side effect
- **Directement sur AGENTS.md** — pas CLAUDE.md (Peter ignore CLAUDE.md)
- **Bloat prevention** = style télégraphique obligatoire

### 2.9 Parallélisme : tmux, pas subagents Claude

Peter **rejette explicitement** le Task tool de Claude Code. Son parallélisme = tmux sessions séparées :

```bash
tmux new-session -d -s claude-haiku 'claude --model haiku'
tmux new-session -d -s claude-main 'claude'
```

Communication via `bun scripts/agent-send.ts`. Mode interactif avec `tmux send-keys` + `tmux capture-pane`. Supervisor loop via `bun scripts/ralph.ts` qui parse réponses contenant `CONTINUE`, `SEND: ...`, `RESTART`.

**Valide notre choix de worktrees + sessions séparées** : Peter fait pareil mais dans le même dossier. Nous, avec les worktrees, on a une isolation en plus.

### 2.10 Pattern `/handoff` et `/pickup` (à copier)

**`/handoff` — checklist 7 sections** :
1. Scope/status
2. Working tree (`git status -sb` + unpushed commits)
3. Branch/PR (current branch, PR details, CI status)
4. Running processes (tmux sessions avec attach commands)
5. Tests/checks (ce qui a run, résultats, restants)
6. Next steps (liste ordonnée)
7. Risks/gotchas (flaky tests, credentials, feature flags)

Format : **concise bullet list**.

**`/pickup` — reverse** :
1. Read AGENTS.MD + docs (`pnpm run docs:list`)
2. `git status -sb` + branch/PR check
3. `gh pr view <num> --comments --files`
4. `tmux list-sessions` + attach
5. Identifier tests prior + plan fresh runs
6. Outline 2-3 immediate actions, begin

**Pour nous** : on **remplace `/start` + `/fin`** (notre plan initial) par **`/pickup` + `/handoff`**. Meilleur design, économise de réinventer la roue.

### 2.11 SDD pattern (legacy, remplacé par discussion itérative)

Peter l'a utilisé jusqu'en juin 2025, puis remplacé par "iterative discussion with Codex" en oct 2025.

Workflow legacy (pour référence) :
1. Brain-dump voice via **Wispr Flow** → Gemini 2.5 Pro
2. `repo2txt` pour convertir OSS repos en markdown
3. Critique loop verbatim : *"Take this SDD apart. Give me 20 points that are underspecified, weird, or inconsistent."*
4. 3-5 rounds jusqu'à ~500 lignes
5. `docs/spec.md`, puis `"Build spec.md"` dans Claude Code

**Mitigation "context amnesia"** : blocs logiques séparés, concaténation manuelle, requirements checklist cross-iterations.

**Statut actuel (oct 2025)** : *"No elaborate spec-driven development. Instead: start a discussion with codex, paste in some websites, some ideas, ask it to read code, and we flesh out a new feature together."*

### 2.12 Claude + Codex comparaison (verbatim, déc 2025)

- **Claude Code** : eager, better on small edits, worse at context, worse long refactors
- **Codex (GPT-5.2)** : reads code 10-15 min before writing, better context, 4x plus lent per task **mais élimine le rework**, 5x plus productif per session, no session restart needed, `tool_output_token_limit = 25000`, `model_auto_compact_token_limit = 233000`

Pas de matrice de routing explicite — le shift est wholesale.

### 2.13 Règles diverses (verbatim)

**Style AGENTS.md** :
> "Work style: telegraph; noun-phrases ok; drop grammar; min tokens."
> "Style: telegraph. Drop filler/grammar. Min tokens (global AGENTS + replies)."

**`gh` over web search** :
> "Given issue/PR URL: use `gh`, not web search."
> "Web: search early; quote exact errors; prefer 2024–2025 sources."

**Multi-agent safety** :
> "Multi-agent: check `git status/diff` before edits; ship small commits."
> "Unrecognized changes: assume other agent; keep going; focus your changes."

**Frontend aesthetics** (surprise bonus dans son AGENTS.MD) :
> "Avoid 'AI slop' UI. Be opinionated + distinctive. Typography: pick a real font; avoid Inter/Roboto/Arial. Commit to a palette; CSS vars; bold accents > timid gradients."

**Model preferences (23 nov 2025)** :
> "Model preference: latest only. OK: Anthropic Opus 4.5 / Sonnet 4.5, OpenAI GPT-5.2, xAI Grok-4.1 Fast, Google Gemini 3 Flash."

### 2.14 Backup (inchangé)

Arq Backup (horaires cloud B2) + SuperDuper! (clone bootable macOS) + Time Machine (NAS local) + Git (commits atomiques)

### 2.15 Ce qu'il rejette (confirmé verbatim)

- ❌ Spec files élaborés (SDD abandonné oct 2025)
- ❌ TDD rigoureuse : *"the model almost always finds issues when you ask it to write tests IN THE SAME CONTEXT"*
- ❌ Subagents Claude (tmux à la place)
- ❌ Plan mode : *"feels like a hack"*
- ❌ Slash commands lourds : *"never found them too useful"*
- ❌ MCPs marketing (`mcporter` à la demande seulement)
- ❌ Worktrees (nous on diverge justifié)
- ❌ Manual approvals : `--dangerously-skip-permissions` *"saves him an hour a day"*

---

## 3. Décisions prises

### D1 — Stratégie backup 4 niveaux (2026-04-11)

| Niveau | Technologie | Fréquence | Rétention |
|--------|-------------|-----------|-----------|
| 1 | Snapshots Proxmox VM entière | Quotidien | 7d + 4w + 3m |
| 2 | Dumps PostgreSQL | Horaire | 24h + 7d + 4w |
| 3 | Restic + Rclone + Google Drive (chiffré AES-256) | Quotidien | 7d + 4w + 12m + 2y |
| 4 | Git pour le code | À chaque commit | Illimité |

**Google Drive retenu** : 5 To déjà disponibles, 0€ supplémentaires. Restic gère chiffrement client-side AES-256 + dedup.

**Rationale** : 4 niveaux indépendants = défense en profondeur. Test de restore obligatoire avant activation YOLO.

### D2 — Architecture multi-IA : Modèle C+ (2026-04-11)

**Infrastructure (isolation physique)** :

```
/opt/academia/                     ← prod, branche main
/opt/academia-worktrees/
  ├── claude/                      ← worktree branche claude
  ├── gemini/                      ← worktree branche gemini (futur)
  └── codex/                       ← worktree branche codex (futur)
/opt/academia-shared/              ← secrets + symlinks
```

**Workflow (collaboration explicite)** via slash commands :

- `/oracle` — consulter une autre IA sur une question précise
- `/review` — demander revue croisée asynchrone
- `/handoff` — passer une tâche à une autre IA
- `/merge` — review + merge vers main + tag deploy

**Rationale** : sécurité d'isolation + vélocité de collaboration = meilleur des deux mondes. Scalable (ajout de Codex = juste un nouveau worktree).

### D3 — Séquencement : 3 sessions intenses (2026-04-11)

| Session | Durée | Livrable |
|---------|-------|----------|
| S1 — Sécurisation | 3-4h | Backup 4 niveaux + test restore + `smoke-test.sh` |
| S2 — Refactor archi | 4h | Worktrees + AGENTS.md + slash commands base + YOLO activé |
| S3 — Multi-IA réel | 3h | `/oracle` `/review` `/handoff` + dashboard + premier Gemini |
| S4 (opt) — Polish | 2h | CLI-fication + tests auto + hooks |

**Rationale** : 3 sessions denses > 7 dispersées pour conserver la cohérence et éviter la perte de contexte.

### D4 — Environnement client (2026-04-11)

- WSL2 + Debian (cohérent avec cosmos) + Windows Terminal
- Claude Code continue à tourner sur cosmos via SSH (pas en local)
- Pas de Ghostty (pas prêt pour Windows)
- Multi-terminal reporté à 6-12 mois quand projet mature

### D5 — Fichiers contexte refactorés (2026-04-11)

| Fichier | Rôle | Lu quand |
|---------|------|----------|
| `AGENTS.md` (remplace CLAUDE.md) | Court, essentiel, règles | Chaque session |
| `docs/*.md` avec `read_when:` | Verbeux, par domaine | À la demande |
| `STATE.md` | État global | Chaque session |
| `TODO.md` | Sections par IA + pool commun | Chaque session |
| `HANDOFF-{agent}.md` | Un par IA | Session de l'agent |
| `CHANGELOG.md` | Append-only partagé | Au `/start` |
| `DECISIONS.md` | Append-only partagé | Rarement |

### D6 — Accès Proxmox : SSH root (2026-04-11)

Décision Sinse : accès SSH pour accélérer la mise en place backup.

### D7 — Budget modèle : full Opus 4.6 1M (2026-04-11)

14h de travail dispo jusqu'à demain, 60% de limite restante. Pas besoin de mix Sonnet pour ce refactor.

### D8 — Pointer pattern AGENTS.md (2026-04-11, post-recherche v2)

Au lieu d'un AGENTS.md par worktree, **UN seul AGENTS.md canonical** dans `/opt/academia-shared/AGENTS.md`. Chaque worktree a juste un fichier pointer :

```
READ /opt/academia-shared/AGENTS.md BEFORE ANYTHING (skip if missing).
```

Notes repo-local sous cette ligne.

**Rationale** : élimine les merges sur AGENTS.md entre branches IA. Game changer pour le multi-IA.

### D9 — Slash commands minimaux (2026-04-11, post-recherche v2)

Peter dit verbatim : *"I used to play with slash commands, but just never found them too useful."* On passe de **10+ slash commands prévus à 4** :

- **`/pickup`** (remplace notre `/start`) — checklist 6 étapes verbatim Peter
- **`/handoff`** (remplace notre `/fin`) — checklist 7 sections verbatim Peter
- **`/oracle`** (consultation autre IA via LiteLLM)
- **`/review`** — built-in Claude Code, à utiliser tel quel

**Remplacements** :
- `/commit` → **`committer` bash tool** (PATH-installed, safety invariants en dur)
- `/deploy-teacher` → **bash tool** `deploy-teacher`
- `/changelog-webapp` → **règle dans AGENTS.md** (à respecter lors des modifs webapp)
- `/merge` → intégré dans `/handoff` (avec tag deploy)

### D10 — Tools maison en priorité (2026-04-11, post-recherche v2)

Au lieu de créer que des slash commands, on crée des **bash/python CLIs PATH-installés** pour la safety-critical logic. Rationale : un IF dans du bash est inviolable, un prompt dans un slash command peut être "oublié" par l'IA.

Priorité CLIs :
1. **`committer`** — porté depuis Peter (bash, ~100 lignes)
2. **`docs-list`** — bash ou python, walk docs/, lit YAML front-matter, print summaries
3. **`deploy-teacher`** — wrapper autour de `update_teacher_chatflow.py`
4. **`smoke-test`** — déjà prévu en S1
5. **`status`** — déjà prévu en S3 (dashboard multi-IA)

### D11 — Oracle : vrai npm package `@steipete/oracle` (2026-04-11, **[REVOKED 2026-04-12]** — remplacé par D28)

~~Installation via `npm install -g @steipete/oracle`.~~

**[REVOKED 2026-04-12]** : décision révoquée suite à découverte que les CLIs officielles `claude` et `gemini` déjà installées sur cosmos supportent le mode one-shot (`-p` / `--print`) et utilisent directement les abonnements de Sinse. Plus besoin d'installer oracle.

**Remplacé par D28** : arbiter custom bash utilisant `claude -p` et `gemini -p` directement.

### D12 — Structure repo workspace : Option C revisitée (2026-04-11, validé Sinse)

**Décision** : restructurer `/root/sinse-workspace/` pour séparer **workflow** (générique, réutilisable) de **state projet** (spécifique à academie-IA).

**Structure cible** :

```
/root/sinse-workspace/                         ← repo workflow sur GitHub
├── AGENTS.md                                   ← canonical, workflow-only, télégraphique
├── docs/                                       ← docs workflow cross-project (read_when:)
│   ├── git-workflow.md
│   ├── multi-ia-collaboration.md
│   ├── slash-commands.md
│   └── ...
├── tools/                                      ← bash tools maison
│   ├── committer
│   ├── docs-list
│   └── ...
├── slash-commands/                             ← templates réutilisables
│   ├── handoff.md
│   ├── pickup.md
│   └── ...
└── projects/                                   ← état des projets spécifiques
    └── academie-ia/
        ├── PROJECT.md                          ← infos spécifiques académie (stack, n8n, etc.)
        ├── STATE.md
        ├── TODO.md
        ├── HANDOFF-claude.md
        ├── HANDOFF-gemini.md
        ├── CHANGELOG.md
        ├── DECISIONS.md
        ├── REFACTOR-PLAN.md                    ← déplacé depuis context/
        ├── REFACTOR-AUDIT.md                   ← déplacé depuis context/
        └── docs/                               ← docs spécifiques académie (read_when:)
            ├── infra.md
            ├── teacher.md
            ├── webapp.md
            └── ...
```

**Pointer dans chaque projet** :
```
/opt/academia/AGENTS.md  →  "READ /root/sinse-workspace/AGENTS.md + projects/academie-ia/PROJECT.md BEFORE ANYTHING"
```

**Avantages** :
- ✅ Workflow réutilisable pour 100% des futurs projets
- ✅ Versionné git via sinse-workspace (déjà sur GitHub)
- ✅ Partagé multi-machines via `git clone`
- ✅ Séparation propre workflow vs state
- ✅ Quand on lance un 2ème projet, on crée juste `projects/projet2/` et c'est parti
- ✅ Cohérent avec le pattern Peter (canonical AGENTS.md à la racine du repo workflow)

**Coûts (refactor à faire en S2)** :
- Déplacer `context/*` → `projects/academie-ia/*` (~10 min)
- Adapter symlink `/opt/academia/context → /root/sinse-workspace/projects/academie-ia/` (~5 min)
- Mettre à jour `claude-settings.json` (hook) avec nouveaux paths (~5 min)
- Mettre à jour `conventions.md` (paths) — sera fusionné dans AGENTS.md de toute façon
- Mettre à jour le `/fin` slash command (paths) — sera remplacé par `/handoff` de toute façon

**Estimation totale** : ~30 min de refactor structure, à faire en S2 dans le bloc "refactor archi".

**Note importante** : cette décision rend caduque l'idée initiale d'un `/opt/academia-shared/` séparé pour les secrets (D8). Les secrets resteront dans `/opt/academia-shared/` (ou similaire) côté infra, mais la doc workflow vit dans `/root/sinse-workspace/`.

### D13 — Style et langue des fichiers .md (2026-04-11, validé Sinse)

**Découverte clé** : Sinse ne lit presque jamais les `.md`. Il pilote via la conversation avec l'IA. Les fichiers .md sont **100% pour l'IA**, pas pour le lecteur humain.

**Décision** : optimiser tous les fichiers .md pour l'IA, pas pour la lisibilité humaine.

**Règles** :

| Type de fichier | Style | Langue |
|-----------------|-------|--------|
| `AGENTS.md` (workflow) | Télégraphique strict (à la Peter) | **Anglais** |
| `docs/*.md` workflow (read_when:) | Télégraphique strict | **Anglais** |
| `slash-commands/*.md` | Télégraphique strict | **Anglais** |
| `tools/*` (scripts bash) | Code propre, comments minimaux | **Anglais** (commentaires) |
| `PROJECT.md` (projet) | Télégraphique structuré | **Anglais** |
| `docs/projects/*/` (read_when:) | Télégraphique structuré | **Anglais** |
| `STATE.md` / `TODO.md` / `HANDOFF-*.md` | Format télégraphique simple | **Anglais** pour nouvelles entrées (historique français préservé) |
| `CHANGELOG.md` / `DECISIONS.md` | Append-only, format simple | **Anglais** pour nouvelles entrées (historique français préservé) |
| `REFACTOR-PLAN.md` / `REFACTOR-AUDIT.md` | Hybride structure + texte | **Français** (méta-doc temporaire de transition, supprimable post v1.0) |

**Exception — outputs lisibles humain** : les scripts qui produisent des outputs visuels pour Sinse (`smoke-test.sh`, `status.sh`, dashboards) → **français** pour les rares fois où il veut jeter un coup d'œil (panne, audit visuel rapide, démo).

**Style télégraphique strict — règles verbatim Peter** :
> "Work style: telegraph; noun-phrases ok; drop grammar; min tokens."
> "Style: telegraph. Drop filler/grammar. Min tokens (global AGENTS + replies)."

Fragments OK, pas d'articles, impératif, abréviations standards (cmd, repo, env, etc.), pas de transitions narratives.

**Rationale** :
- Économie de tokens à chaque session = plus de contexte dispo pour le vrai travail
- Vocabulaire technique anglais plus dense que français
- Les modèles sont plus précis sur leur langue d'entraînement primaire
- Pas de coût pour Sinse (il ne lit pas)
- L'historique français reste lisible dans CHANGELOG/DECISIONS pour la trace

### D14 — Contenu AGENTS.md : 12 sections + 11 ajouts (2026-04-11, validé Sinse)

**Structure complète** validée :

1. **READ ORDER** — séquence de lecture (this file → PROJECT.md → docs/)
2. **STYLE** — telegraph rule, English mandatory for new content
3. **WORKSPACE** — locations (workspace dir, projects dir, tools on PATH)
4. **MULTI-AGENT** — branches, worktrees, lock, conflict resolution
5. **GIT** — committer mandate, no `git add .`, never amend, gh > web search
6. **TOOLS** — list of CLIs available (committer, oracle, docs-list, etc.)
7. **SLASH COMMANDS** — list (`/pickup`, `/handoff`, `/oracle`, `/review`)
8. **MAKE A NOTE** — natural language pattern for self-updating AGENTS.md
9. **DESTRUCTIVE OPS** — pointer to docs/destructive-ops.md
10. **SESSION HYGIENE** — oracle --help once/session, docs-list at start, smoke-test after changes
11. **WEB CONTEXT** — gh for GitHub URLs only
12. **FRONTEND AESTHETICS** — pointer to project-specific design system

**Plus 11 ajouts post-audit** (récupérés depuis l'existant) :
1. "Repo = shared memory across AIs" principe central (de conventions.md)
2. Format `DECISIONS.md` : `[DATE] [AI] — decision — rationale`
3. Format `CHANGELOG.md` : `[DATE] [AI] — what was done`
4. Append-only rule + `[CORRECTION]` syntax
5. Lock file expiration : 24h + cleanup procedure
6. Conflict resolution : "keep best of both, document"
7. Hook Stop awareness ("if you see RAPPEL, run /handoff")
8. Permissions baseline reference (cf. settings.local.json)
9. Native Claude Code memory note (Claude-only, fallback)
10. Project detection : pointer file in worktree
11. Branch convention explicite (`<agent>` = `claude` / `gemini` / `codex`)

### D15 — Native Claude Code memory : Option B fallback (2026-04-11, validé Sinse)

**Découverte** : `~/.claude/projects/-opt-academie/memory/reference_dify_api.md` existe et utilise YAML front-matter (`name`, `description`, `type`). C'est exactement le pattern docs/ avec read_when: de Peter, mais en natif Claude Code.

**Décision** : on documente l'existence dans AGENTS.md mais on ne s'y remet pas pour les choses critiques.

**Règle dans AGENTS.md** :
> Native Claude Code memory exists at `~/.claude/projects/<id>/memory/`. If you are Claude, you can put non-critical notes there for auto-loading benefits. Critical project knowledge MUST live in `docs/projects/<name>/` (cross-AI, accessible to Gemini/Codex).

**Rationale** : reste model-agnostic (Gemini/Codex n'ont pas accès à cette memory), mais ne pas gaspiller la fonctionnalité native pour Claude.

### D16 — Granularité docs projet : 6 fichiers regroupés (2026-04-11, validé Sinse)

**Décision** : `projects/academie-ia/docs/` contient 6 fichiers regroupés thématiquement (pas 12 granulaires à la Peter).

**Structure** :

```
projects/academie-ia/
├── PROJECT.md                    ← court (~50 lignes), pointers vers docs/
└── docs/
    ├── infra.md                  ← Docker + nginx + Cloudflare + Postgres + LiteLLM
    ├── dify-teacher.md           ← Dify agents + Teacher v17 + chatflow
    ├── n8n-workflows.md          ← 5 workflows + memory system
    ├── webapp.md                 ← FastAPI + SvelteKit + users + auth
    ├── pedagogy.md               ← stratégie + scoring + taxonomies A1→C2
    └── gotchas.md                ← notes importantes + pièges connus
```

**Chaque fichier** doit avoir un YAML front-matter `read_when:` clair :

```yaml
---
summary: ...
read_when: ...
---
```

**Rationale** : 6 fichiers c'est gérable, regroupements logiques, économie de tokens marginale ne justifie pas 12 fichiers fragmentés. Sci ndable plus tard si un fichier devient trop gros.

**Bloc 1 du refactor terminé ✅**. Tous les 🟡 du Bloc 1 (A4, A5, A6) sont tranchés via D8, D12, D13, D14, D15, D16.

### D17 — Format TODO.md : structure CLAIMED (2026-04-11, validé Sinse)

**Format** :

```
## OPEN (any AI can take)
- [ ] Tâche 1 — P1
- [ ] Tâche 2 — P1
- [ ] Tâche 3 — P2

## CLAIMED
- claude: Tâche A (started 2026-04-11 21:30, P1)
- gemini: Tâche B (started 2026-04-11 22:00, P2)

## DONE
- [x] (claude, 2026-04-10) Description
- [x] (gemini, 2026-04-09) Description
```

**Workflow** :
1. Une IA veut prendre une tâche → la déplace de OPEN vers CLAIMED avec son nom + timestamp
2. Une IA finit une tâche → la déplace de CLAIMED vers DONE
3. Pas de duplication, pas de conflit

**Rationale** :
- Format clair pour parsing IA (facile à scanner pour `make status`)
- Évite les conflits multi-IA (claim explicit)
- Compatible pattern Peter
- Priorité visible dans l'item lui-même (`— P1`)
- Pas de "Pool commun" ni "Pour Claude" séparés (OPEN = pool commun, CLAIMED = en cours)

**Migration** : le TODO.md actuel (organisé P1/P2/P3/P4/P5) sera converti en S2.

### D18 — Format HANDOFF multi-IA (2026-04-12, validé Sinse)

**Décision** : un fichier `HANDOFF-{agent}.md` par IA, anglais télégraphique, structure 7 sections.

**Fichiers** :
- `projects/academie-ia/HANDOFF-claude.md`
- `projects/academie-ia/HANDOFF-gemini.md` (futur)
- `projects/academie-ia/HANDOFF-codex.md` (futur)

**Rationale fichiers séparés** :
- Zéro conflit de merge entre branches IA
- Quand IA merge sa branche → son HANDOFF mergé naturellement
- Autres IA peuvent consulter les HANDOFF des autres pour comprendre l'état parallèle
- Pattern Peter (multi-agent natif)

**Structure 7 sections** :

```markdown
# HANDOFF — <agent> — <YYYY-MM-DD HH:MM>

## 1. Scope/Status
- What was done this session
- Bullet points, telegraph

## 2. Working tree
- Branch: <name>
- Modified: <files>
- Unpushed commits: <count>
- Clean: yes/no

## 3. Branch/PR/CI
- Branch ahead of origin/main: <N> commits
- PR: <link or none>
- CI: <status or none>

## 4. Tests/checks
- smoke-test.sh: <result>
- Manual: <what was verified>

## 5. Next steps
1. ...
2. ...
3. ...

## 6. Risks/gotchas
- Deprecations
- Blockers
- Things to watch

## 7. Open questions (optional)
- Waiting for Sinse on: ...
```

**Style** : anglais télégraphique strict (cohérent D13).

**Génération** : automatique via `/handoff` slash command (basé sur le pattern Peter `~/.codex/prompts/handoff.md`).

### D19 — CHANGELOG format + bash tool `log` (2026-04-12, validé Sinse)

**Format CHANGELOG.md** : préfixe `[type]` inline, garde la simplicité actuelle.

```
2026-04-12 Claude — [feat] AGENTS.md structure validated (D14)
2026-04-12 Claude — [refactor] TODO.md → CLAIMED format (D17)
2026-04-12 Claude — [docs] REFACTOR-PLAN v0.4 with 19 decisions
2026-04-11 Claude — [fix] Onboarding Phase 1→2 transition (Teacher v17)
```

**Types autorisés** (12 types alignés Peter, voir D27 pour règles auto-merge) :
- `[feat]` nouvelle feature
- `[fix]` bug fix non-critique
- `[hotfix]` bug fix critique (prod down, user bloqué)
- `[docs]` documentation pure
- `[refactor]` restructuration sans changement de comportement
- `[perf]` optimisation performance mesurable
- `[style]` formatage cosmétique pur
- `[test]` ajout/modification de tests
- `[chore]` maintenance, configs non-critiques, deps
- `[security]` fix vulnérabilité sécurité
- `[remove]` suppression de code/fichiers
- `[wip]` work in progress (incomplet)

**Définitions sémantiques précises** : voir AGENTS.md (anti-confusion entre `[fix]`/`[hotfix]`, `[refactor]`/`[perf]`, etc.)

**Append-only conservé** : règle existante préservée.

**Historique français préservé** : les anciennes entrées sans `[type]` restent telles quelles (D13 : "historique préservé").

**Mécanisme d'ajout** : bash tool `log` (PATH-installed CLI), pas un slash command.

**Usage** :
```bash
log feat "AGENTS.md structure validated (D14)"
log refactor "TODO.md → CLAIMED format"
log fix "Onboarding Phase 1→2 transition"
```

**Comportement du tool** :
1. Détecte l'IA courante (via `.agent` file ou variable env `$AGENT_NAME`)
2. Date automatique (`date +%Y-%m-%d`)
3. Ajoute la ligne formatée au CHANGELOG.md actif (du projet courant)
4. Vérifie absence de doublon (utile multi-IA)
5. Exit 0 en cas de succès

**Intégration `/handoff`** : le slash command appelle `log` en interne pour ajouter une entrée résumant la session.

**Rationale bash > slash command** : cohérent D10 (safety-critical et utilitaires fréquents → bash, contextuel → slash). `log` est utilisé fréquemment, doit être rapide à invoquer.

**Bloc 2 du refactor terminé ✅**. Tous les 🟡 du Bloc 2 (A1, A2, A3) sont tranchés via D17, D18, D19.

### D20 — Suppression du fichier `.lock` (2026-04-12, validé Sinse)

**Décision** : suppression complète du fichier `.lock` et de toutes ses références.

**Rationale** : avec la nouvelle architecture (D2 worktrees + D17 TODO CLAIMED + D18 HANDOFF par IA + D12 structure repo), le `.lock` devient redondant.

| Fonction historique du `.lock` | Maintenant remplie par |
|--------------------------------|------------------------|
| Détecter qu'une autre IA est active | Worktrees isolés (chacun son dossier physique) |
| Éviter conflits sur fichiers | Branches séparées par IA |
| Savoir qui fait quoi | TODO.md format CLAIMED (D17) |
| Trace dernière activité | HANDOFF-{agent}.md timestamp + git log |
| Heartbeat / activité courante | `tmux list-sessions` (futur) ou `git log --all --since=...` |

**Tous les besoins sont couverts par des mécanismes plus robustes** que le `.lock`.

**Migration en S2** :
1. Supprimer `/root/sinse-workspace/.lock`
2. Retirer `.lock` du `.gitignore` (devient inoffensif, ou laisser)
3. Pas écrire la règle `.lock` dans AGENTS.md (le concept disparaît)
4. `make status` lit `git log` + timestamps `HANDOFF-{agent}.md` au lieu du `.lock`
5. `/pickup` et `/handoff` n'interagissent plus avec `.lock`

**Bonus implication** : `D1` est barré de la liste des pastilles jaunes (il devient une suppression, pas une amélioration).

### Audit redondances — à faire après parcours pastilles jaunes (2026-04-12, validé Sinse)

**Nouvelle étape ajoutée à la roadmap** : une fois toutes les pastilles jaunes tranchées, faire un audit complet du nouveau design pour trouver d'autres redondances comme celle du `.lock`.

**Méthode** : pour chaque composant (fichier, slash command, bash tool, hook, convention), demander :
1. Quelles fonctions remplit-il ?
2. Ces fonctions sont-elles déjà couvertes ailleurs ?
3. Si oui, le composant est candidat à la suppression ou simplification.

**Output attendu** : une liste de composants à supprimer/simplifier avant la stabilisation v1.0.

**Position dans la roadmap** : étape 8.5 (entre "discuter blocs jaunes" et "stabiliser plan en v1.0").

### D21 — `profil_manager.py` hors-scope refactor workflow (2026-04-12, validé Sinse)

**Décision** : `profil_manager.py` (et autres scripts académie-IA) ne sont PAS touchés par le refactor workflow.

**Rationale** :
- Cohérent avec D12 (séparation workflow vs projet)
- `/opt/academia/scripts/` appartient au projet académie, pas au workflow
- Pas de bénéfice immédiat à CLI-fier maintenant
- Évite le scope creep

**Action** : C1 sort de la liste des pastilles jaunes du refactor workflow.

**À faire post-refactor** : audit complet du projet académie-IA pour restructurer sa structure et la rendre compatible avec le nouveau workflow. Voir nouvelle étape ci-dessous.

### Audit + restructuration complète du projet académie-IA — post-refactor workflow (2026-04-12, validé Sinse)

**Nouvelle étape ajoutée à la roadmap** : une fois le refactor workflow terminé (toutes pastilles jaunes tranchées + audit redondances + plan v1.0 + Sessions S1+S2+S3 exécutées), faire un **audit complet du projet académie-IA** pour le restructurer et le rendre compatible avec le nouveau workflow.

**Périmètre de l'audit académie-IA** :
1. **Scripts** (`/opt/academia/scripts/`) : à CLI-fier ? à déplacer ? à grouper sous `tools/` projet ?
2. **`/opt/academia/CLAUDE.md`** : à supprimer (remplacé par pointer vers `/root/sinse-workspace/AGENTS.md` + `projects/academie-ia/PROJECT.md`)
3. **`/opt/academia/.claude/`** : à adapter (settings, commands, hooks)
4. **`/opt/academia/.gemini/`** : idem
5. **Symlinks** : `/opt/academia/context` → adapter selon nouvelle structure
6. **`/opt/academia/curriculums/`** : organiser dans `projects/academie-ia/data/` ou laisser ?
7. **`/opt/academia/api/`**, **`/opt/academia/webapp/`** : code, garder en place mais référencer depuis `docs/`
8. **Fichiers d'accès** (`.dify_admin_key`) : déplacer dans `/opt/academia-shared/secrets/` ?
9. **Worktrees academie** : créer la structure `/opt/academia-worktrees/{claude,gemini}/`

**Position dans la roadmap** : étape 11 (post-Sessions exécution).

**Bloc 3 du refactor terminé ✅**. Tous les 🟡 du Bloc 3 (D1 supprimé via D20, C1 hors-scope via D21).

### D22 — Niveau de CI / validation : Niveau 2 — Intermédiaire (2026-04-12, validé Sinse)

**Décision** : adopter le Niveau 2 (Intermédiaire) — sweet spot entre sécurité et complexité.

**Composants** :
1. **`smoke-test.sh`** — valide webapp + Dify + n8n + Postgres + LiteLLM en 30s
2. **Healthchecks Docker renforcés** — chaque container définit son healthcheck propre
3. **Pre-commit hook gitleaks** — bloque tout commit contenant un secret
4. **Pre-commit hook smoke-test** — lance smoke-test, bloque si fail
5. **`/check` slash command** — invoque smoke-test + healthcheck + gitleaks à la demande

**Rationale** :
- Sweet spot entre sécurité et complexité
- Compatible philosophie Peter (rejette TDD strict mais utilise des hooks)
- Suffisant pour activer YOLO avec ~90% confiance (× backups 4 niveaux = ~99% effectif)
- Setup réaliste : 3-4h en S1
- Évite l'over-engineering du Niveau 3 (Playwright/pytest qu'on n'a pas)
- Évolutif : on peut monter au Niveau 3 plus tard si besoin

**Niveaux rejetés** :
- ❌ Niveau 1 (minimal) : trop dépendant de la discipline IA, YOLO trop risqué
- ❌ Niveau 3 (complet) : 8-10h de setup, gain marginal, over-engineering pour notre échelle

**Prochain step** : décliner les 5 composants un par un avec Sinse.

### D23 — `smoke-test.sh` modulaire avec sous-commandes (2026-04-12, validé Sinse)

**Décision** : `smoke-test` est un bash CLI modulaire avec 4 sous-commandes selon le contexte d'usage.

**Variantes** :

| Variante | Durée | Usage |
|----------|-------|-------|
| `smoke-test --quick` | ~5s | Pre-commit hook (rapide pour ne pas ralentir les commits) |
| `smoke-test --deep` | ~15s | Validation manuelle après modif (endpoints API + chatflow) |
| `smoke-test --infra` | ~5s | Audit santé système (disk, RAM, container restarts) |
| `smoke-test --all` | ~30s | Validation exhaustive (gros milestone, fin de session) |
| `smoke-test` | = `--deep` | Default |

**Contenu détaillé** :

**`--quick`** (containers + services HTTP) :
- Containers UP : academie-frontend, academie-api, dify-api, dify-worker, postgres-academie, redis-academie, n8n-academie, litellm-proxy
- Webapp HTTP 200 sur https://academia.petit-pont.com/
- FastAPI HTTP 200 sur localhost:8000/health

**`--deep`** (= --quick + endpoints + chatflow) :
- POST /api/auth/login (test user) → 200
- GET /api/me/concepts → 200 + JSON valide
- GET /api/me/streaks → 200
- Dify chatflow Teacher : nodes count = 28
- n8n workflows actifs (dify-profil-get, dify-snapshot, dify-profil-update)
- LiteLLM /v1/models → liste les 5 modèles

**`--infra`** :
- Disk space /opt > 5GB libre
- Disk space /var/lib/docker > 5GB libre
- Memory available > 1GB
- No container restart in last hour

**Output format** :
- Émojis (✓ vert / ✗ rouge / ⚠ jaune)
- Une ligne par check
- Code retour 0 si OK, 1 si fail
- Mode `--quiet` (pour pre-commit hook) : n'affiche que les erreurs

**Implementation** : bash script dans `/root/sinse-workspace/tools/smoke-test`, sur PATH via alias.

### D24 — Healthchecks Docker : Option C — délégué au smoke-test (2026-04-12, validé Sinse)

**Décision** : pas de modification des healthchecks Docker. Le smoke-test gère toutes les vérifications de santé containers via `docker exec` et `curl` externes.

**Healthchecks existants conservés** (S6 SaaS) :
- `academie-api` : DB check
- `academie-frontend` : node fetch

**Containers couverts par smoke-test (sans healthcheck Docker dédié)** :
- `dify-api`, `dify-worker`, `dify-plugin-daemon`
- `postgres-academie`, `redis-academie`
- `n8n-academie`, `litellm-proxy`

**Commands smoke-test pour chaque** :

```bash
# Postgres
docker exec postgres-academie pg_isready -U sinse -q

# Redis
docker exec redis-academie redis-cli ping

# Dify API
curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/console/api/workspaces \
  -H "Authorization: Bearer $ADMIN_KEY"

# n8n
curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz

# LiteLLM
curl -s http://localhost:4000/health

# dify-worker, dify-plugin-daemon (just check UP)
docker ps --filter "name=dify-worker" --format "{{.Status}}" | grep -q "Up"
```

**Caveats acceptés** :
1. Pas de restart auto sur "unhealthy" (mais `restart: unless-stopped` gère déjà les crash réels)
2. Pas de détection passive (mais cron `smoke-test --quick` peut être ajouté en Phase 4)

**Rationale** :
- Zéro risque sur la prod (pas de recreate containers)
- Pas de duplication "healthcheck + smoke-test"
- Cohérent D22 (Niveau 2, pas d'over-engineering)
- Plus simple à maintenir (un seul mécanisme)

### D25 — Pre-commit hook gitleaks (anti-secrets) (2026-04-12, validé Sinse)

**Décision** : adopter **gitleaks** comme pre-commit hook anti-secrets sur les 3 cibles repos.

**Outil** : Gitleaks (open source, Go, standard de l'industrie). Détecte ~150 patterns de secrets connus (AWS, GCP, Azure, OpenAI, Anthropic, GitHub, GitLab, Stripe, etc.).

**Cibles** :
- `/root/sinse-workspace/` (workflow + projects state)
- `/opt/academia/` (code académie-IA — le plus critique)
- `/opt/academia-worktrees/{claude,gemini,codex}/` (chacun des worktrees)

**Comportement** :
- **Bloque dur** le commit si un secret est détecté (pas juste warning)
- Override `--no-verify` **interdit par règle AGENTS.md** (jamais skipper un hook sans permission Sinse)

**Faux positifs** :
- Gérés au cas par cas via `.gitleaksignore` (fichier per-repo)
- Convention : commenter chaque ignore avec la raison ("UUID Dify legitimate", "test fixture", etc.)

**Patterns custom à ajouter pour notre stack** :
- `dify_admin_key` (clé API Dify locale)
- `n8n_encryption_key` (clé chiffrement n8n)
- Format `Bearer app-...` (Dify app keys)
- LiteLLM master key

**Setup** : 5-10 min en S2. Installation via apt/binaire + init du hook git.

**Workflow type bloqué** :
```bash
git commit -m "feat: add Dify integration"
[gitleaks scan...]
WARNING — secret detected in src/api/dify-client.py:42
Pattern: anthropic-api-key
Line: ANTHROPIC_API_KEY = "sk-ant-api03-xxxx..."
❌ Commit blocked. Remove the secret and try again.
```

### D26 — Hooks split : pre-commit gitleaks + pre-push smoke-test (2026-04-12, validé Sinse)

**Décision** : architecture hooks en 2 étapes pour optimiser friction vs sécurité.

**Pre-commit hook** (~2s par commit) :
- gitleaks (D25)
- Bloque si secret détecté
- Tourne sur CHAQUE commit

**Pre-push hook** (~15s par push) :
- `smoke-test --deep` (D23)
- Bloque dur si fail
- Tourne sur CHAQUE push (rare comparé aux commits)

**Comportement** :
- Bloque dur si fail (pas de warning)
- `--no-verify` interdit par règle AGENTS.md (jamais skipper sans permission Sinse)

**Rationale** :
- Gitleaks DOIT être pre-commit : un secret committé même localement est dans l'historique git, plus dur à enlever
- Smoke-test peut être pre-push : on accepte que les commits intermédiaires soient WIP, on valide juste avant de partager
- Workflow rapide : 2s/commit + 15s/push (push rare)
- Compatible YOLO multi-IA

### D27 — Option E auto-merge + 12 types Peter-aligned (2026-04-12, validé Sinse)

**Décision** : adopter Option E (hybride par catégorie) DIRECTEMENT (pas de phase intermédiaire), avec 12 types de commit alignés sur le pattern Peter, et règles d'auto-merge différenciées par type.

**Rationale** : cohérent avec règle d'or #7 (v1.0 avant exécution, pas d'aller-retour). Si on doit ajouter des types plus tard, c'est de la dette technique gratuite.

**Activation** : opérationnel dès que le tool `merge-to-main` est créé en S2. Avant ça, le merge reste manuel par défaut (pas d'aller-retour, juste pas encore activé).

**Les 12 types et leurs règles d'auto-merge** :

| # | Type | Description précise | Auto-merge |
|---|------|---------------------|------------|
| 1 | `[feat]` | Nouvelle feature visible utilisateur ou nouvelle capacité interne | ⚠️ **IA arbitre toujours** |
| 2 | `[fix]` | Bug fix fonctionnel non-critique | ✅ Auto si < seuil + pas fichier protégé, sinon IA arbitre |
| 3 | `[hotfix]` | Bug fix CRITIQUE (prod down, user bloqué) | ⚠️ IA arbitre **+ notification immédiate Sinse** |
| 4 | `[docs]` | Documentation pure (.md, comments, README) | ✅ **TOUJOURS auto** sauf fichier protégé |
| 5 | `[refactor]` | Restructuration sans changement de comportement | ✅ Auto si < seuil + pas fichier protégé, sinon IA arbitre |
| 6 | `[perf]` | Optimisation performance mesurable | ✅ Auto si < seuil + pas fichier protégé, sinon IA arbitre |
| 7 | `[style]` | Formatage, espaces, lint (cosmétique pur) | ✅ **TOUJOURS auto** |
| 8 | `[test]` | Ajout/modification de tests | ✅ **TOUJOURS auto** |
| 9 | `[chore]` | Maintenance, configs non-critiques, deps, lockfiles | ✅ Auto sauf fichier protégé |
| 10 | `[security]` | Fix vulnérabilité sécurité | 🛑 **TOUJOURS humain** (jamais auto, jamais IA arbitre) |
| 11 | `[remove]` | Suppression de code/fichiers | 🛑 **TOUJOURS humain** (destructif par nature) |
| 12 | `[wip]` | Work in progress (incomplet) | ❌ **JAMAIS de merge** |

**Définitions sémantiques précises** (à mettre dans AGENTS.md, anti-confusion) :

```
[feat]     : Adds new functionality (user-facing or internal capability).
             Test: "Does this enable something the system couldn't do before?"

[fix]      : Corrects incorrect behavior in existing functionality.
             Not critical to prod (system still works for most users).
             Test: "Was this code doing the wrong thing?"

[hotfix]   : Critical bug blocking production users RIGHT NOW.
             Test: "Are users currently unable to use the system?"
             If yes → [hotfix]. If just annoying → [fix].

[docs]     : Documentation only. No code logic changes.
             Includes .md files, code comments, README updates.

[refactor] : Code restructured without behavior change.
             Test: "Would the same inputs produce the same outputs after this?"
             If yes → [refactor]. If outputs differ → [fix] or [feat].

[perf]     : Performance improvement with measurable gain.
             Test: "Did I measure this is faster/lighter?"
             If no measurement → use [refactor] instead.

[style]    : Cosmetic only (whitespace, formatting, semicolons, indentation).
             No semantic change whatsoever.

[test]     : Adds or modifies tests only. No production code changes.

[chore]    : Tooling, configs, dependencies, lockfiles, CI configs, build scripts.
             Not user-facing, not bug-related.

[security] : Fixes a security vulnerability.
             Test: "Could this be exploited by an attacker?"
             If yes → [security], not [fix], even if it looks like a normal bug.

[remove]   : Deletes code, files, features, or capabilities.
             Test: "Am I removing something?"
             If yes → [remove], even if accompanied by a refactor.

[wip]      : Work in progress, not ready for merge.
             Used to save partial work before continuing later.
             Should be replaced by a final commit type before merge attempt.
```

**Implications** :
- D19 mis à jour (12 types au lieu de 6)
- AGENTS.md doit contenir la table de définitions sémantiques
- Tool `committer` valide que le type est dans la liste (12 valeurs)
- Tool `log` idem
- Tool `merge-to-main` (S2) applique les règles d'auto-merge selon le type
- L'IA marque juste le type, le tool calcule mineur/majeur automatiquement (pas de tricherie possible)

**Sous-questions restantes** :
- Sous-Q2 : comment fonctionne l'IA arbitre ? **✅ Résolue par D28**
- Sous-Q3 : liste précise des "fichiers protégés"
- Sous-Q4 : seuil de lignes pour auto-merge mineur
- Sous-Q5 : workflow `MERGE-REQUEST.md` quand humain requis

### D28 — IA arbitre : bash tool `arbiter` custom avec CLIs officielles (2026-04-12, validé Sinse)

**Découverte clé** : les CLIs officielles `claude` (v2.1.101) et `gemini` (v0.36.0) sont DÉJÀ installées sur cosmos et supportent le mode one-shot (`-p` / `--print`). Elles utilisent **directement les abonnements personnels de Sinse** (Claude Pro/Max, Gemini Advanced) — pas de clé API nécessaire.

**Décision** : l'IA arbitre est un **bash tool `arbiter` custom** (~30 lignes) qui wrappe `claude -p` et `gemini -p` directement. Pas d'oracle de Peter (D11 révoquée).

**Logique cross-review** (garantit la diversité d'opinion) :

| Branche commitante | Arbiter utilisé | Raison |
|--------------------|-----------------|--------|
| `claude` / `claude-*` | `gemini -p` | Cross-review (éviter le biais d'auto-validation) |
| `gemini` / `gemini-*` | `claude -p` | Idem |
| `codex` / `codex-*` | `gemini -p` ou `claude -p` | Alterne ou choisit selon dispo |
| Autre | `gemini -p` (par défaut) | Gemini free tier Advanced |

**Avantages vs oracle de Peter** :
- ✅ **0€** absolu (utilise abonnements existants)
- ✅ Cross-review naturel (diversité d'opinion)
- ✅ Zéro dépendance externe (npm package)
- ✅ Zéro maintenance (CLIs maintenues par Anthropic/Google)
- ✅ Pas de clé API à gérer
- ✅ Pas de browser automation complexe

**Emplacement** : `/root/sinse-workspace/tools/arbiter` (bash, ~30 lignes).

**Input/Output** :
```bash
arbiter --branch <branch> --type <commit_type> [--diff <file>]
# Output on stdout:
# DECISION: GO
# REASON: <paragraph>
# OR
# DECISION: NO-GO
# REASON: <paragraph>
# ISSUES: ...
```

**Prompt template** (à standardiser dans `arbiter`) :

```
You are reviewing a merge request for auto-merge approval.

BRANCH: <branch>
COMMIT TYPE: [<type>]

DIFF:
<git diff>

REVIEW CRITERIA:
1. Does this introduce regression?
2. Is the code consistent with existing patterns?
3. Any obvious bugs, security issues, or anti-patterns?
4. Is the commit type accurate?

OUTPUT FORMAT (strict, must be parsable):
DECISION: GO or NO-GO
REASON: <one paragraph>
```

**Intégration dans `merge-to-main`** : quand le tool détecte qu'un commit nécessite l'IA arbitre (selon D27), il appelle `arbiter --branch ... --type ...` et parse l'output. Si `DECISION: GO` → merge. Sinon → créer `MERGE-REQUEST.md` pour review humain.

**Règle importante (D27+règle d'or #8)** : l'arbiter n'utilise QUE les CLIs officielles (`claude`, `gemini`, futur `codex`), jamais LiteLLM. LiteLLM reste dédié aux agents du projet academie-IA.

### D29 — Séparation stricte : abonnements workflow vs LiteLLM projet (2026-04-12, validé Sinse)

**Décision** : formaliser en tant que règle architecturale fondamentale.

**Règle** :

| Usage | LLMs utilisés | Auth |
|-------|---------------|------|
| **Workflow** (Claude Code, Gemini CLI, arbiter, oracle-like consultations) | Claude Pro/Max, Gemini Advanced, futur ChatGPT Plus | Abonnements personnels Sinse (via CLIs officielles) |
| **Projet academie-IA** (Teacher, Maestro, Sensei, curriculum gen, examens, etc.) | LiteLLM + Groq free, Mistral free, éventuellement gpt-4o-mini payant | LiteLLM config avec BYOK (futur) ou free tiers |

**Rationale** :
1. **Protection des abonnements personnels** : si le projet academie-IA utilisait les abonnements de Sinse, les users consommeraient directement ses quotas → rate limits, coûts imprévus
2. **Scalabilité projet** : BYOK multi-users requiert LiteLLM, pas les abonnements personnels
3. **Séparation claire** : workflow (devs avec IA) vs projet (app pour users)
4. **Cohérence avec D12** : workflow vs projet séparés dans tous les aspects

**Implications** :
- `arbiter` utilise `claude -p` et `gemini -p` (abonnements Sinse) ✅
- Teacher utilise `groq-standard` via LiteLLM (free tier) ✅
- JAMAIS appeler `claude -p` depuis un workflow n8n (ce serait workflow dans projet)
- JAMAIS configurer Claude Pro comme backend Dify (ce serait abonnement dans projet)

**Formalisé en règle d'or #8** (Section 1.3 du plan).

**Note future (hors scope refactor workflow)** : quand le projet academie-IA voudra évoluer vers des modèles premium, il devra passer par des clés API payantes (BYOK ou OpenRouter/Groq payant), jamais par les abonnements personnels de Sinse. Ceci sera traité dans l'audit complet du projet academie-IA post-refactor.

### D30 — Liste complète des fichiers protégés (2026-04-12, validé Sinse)

**Décision** : 3 niveaux de protection pour les règles d'auto-merge du tool `merge-to-main`.

### 🔴 Niveau ROUGE — Humain obligatoire (toi, Sinse)

Ces fichiers bloquent l'auto-merge même avec un diff minime. Ils sont trop sensibles pour être automatisés, même via IA arbitre.

**Patterns** :
- **Secrets env** : `.env`, `.env.*`
- **Secrets files** : `*.key`, `*.pem`, `*.crt`, `*.cert`, `*_rsa*`, `*_ed25519*`
- **Secrets spécifiques projet** : `.dify_admin_key`, `encryption.key`, `/opt/academia-shared/secrets/*`
- **Credentials d'outils** : `.npmrc`, `.pypirc`, `.netrc`
- **Claude Code settings** : `.claude/settings.json`, `.claude/settings.local.json`
- **Gemini CLI settings** : `.gemini/settings.json`
- **Configs infra critique** : `docker-compose*.yml`, `/etc/nginx/*`, configs Cloudflare
- **Base de données schema** : `migrations/*.sql`, fichiers DDL (CREATE TABLE, ALTER TABLE, DROP)
- **Fichiers système** : `/etc/*`, `systemd/*`, cron tabs
- **Git config** : `.gitignore`, `.gitattributes`, `.git/config`
- **Git hooks eux-mêmes** : `.git/hooks/*`
- **AGENTS.md** : `/root/sinse-workspace/AGENTS.md` (méta-contrat du workflow)
- **Slash commands** : `/root/sinse-workspace/slash-commands/*.md`
- **Bash tools maison** : `/root/sinse-workspace/tools/*` (committer, arbiter, docs-list, merge-to-main, etc.)
- **Règle comportementale** : symlinks pointant vers des fichiers ROUGE sont eux-mêmes ROUGE
- **~/.config/***: (si une IA y touche) configs CLIs avec credentials

### 🟠 Niveau ORANGE — IA arbitre obligatoire

Ces fichiers nécessitent une review par l'arbiter (cross-review claude/gemini via D28). Pas d'auto-merge direct, mais pas besoin de bloquer jusqu'à toi.

**Patterns** :
- **Backend API** : `/opt/academia/api/**/*.py`, `api/**/*.py`
- **Frontend webapp** : `webapp/frontend/src/**/*.svelte`, `webapp/frontend/src/**/*.ts`
- **Scripts de deploy** : `scripts/*.py`, `scripts/*.sh`, `update_teacher_chatflow.py`
- **Docker images** : `Dockerfile`, `Dockerfile*`
- **LiteLLM config** : `/opt/litellm/config.yaml`
- **Dependencies Python** : `pyproject.toml`, `poetry.lock`, `uv.lock`, `requirements.txt`, `Pipfile*`
- **Dependencies JS/TS** : `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`
- **Configs tooling** : `*.toml` (autres que `pyproject.toml` qui est déjà listé)
- **CI/CD (futur)** : `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`
- **Exports chatflow/workflows** : `*.chatflow.json`, `*.n8n.json`
- **TypeScript configs** : `tsconfig.json`, `svelte.config.js`, `vite.config.ts`

### 🟢 Niveau VERT — Auto-merge OK (si autres critères OK)

Ces fichiers peuvent être auto-mergés si le type de commit le permet (D27) et qu'aucun fichier ROUGE/ORANGE n'est dans le même diff.

**Patterns** :
- **Documentation** : `docs/**/*.md`, `README.md`, `CONTRIBUTING.md`, `PLAN.md`, code comments
- **Tests** : `tests/**/*`, `*.test.*`, `*.spec.*`
- **Fichiers contexte projet** : `STATE.md`, `TODO.md`, `CHANGELOG.md`, `DECISIONS.md`, `HANDOFF-*.md`
- **Fichiers workflow state** : `REFACTOR-PLAN.md`, `REFACTOR-AUDIT.md` (temporaires)
- **Assets** : `*.png`, `*.svg`, `*.webp`, `*.jpg`, `*.ico`, `*.woff`, `*.woff2`, `*.ttf`
- **Public assets** : `public/*`, `static/*`
- **Configs cosmétiques** : `.prettierrc`, `.editorconfig`, `.eslintrc` (lint rules uniquement)
- **Data pédagogique** : `curriculums/*.md`, `curriculums/*.json`
- **Format files** : fichiers `.css` de style cosmétique (pas de logique)

### 🟣 Règle comportementale — Protection `committer`

Le bash tool `committer` **refuse de stager** les patterns `.gitignore` classiques, même si l'IA tente de les ajouter :

- `node_modules/`, `node_modules/**`
- `__pycache__/`, `*.pyc`
- `dist/`, `build/`, `.next/`, `.svelte-kit/`, `.nuxt/`
- `.DS_Store`, `Thumbs.db`
- `*.log`, `logs/`
- `.cache/`, `tmp/`, `temp/`
- `coverage/`, `.nyc_output/`

→ Protection contre les bugs d'auto-stage d'une IA qui fait `git add` par erreur.

### Logique appliquée par `merge-to-main`

```
for each file in git diff:
    if file matches ROUGE pattern:
        return "HUMAN_REQUIRED"
    elif file matches ORANGE pattern:
        return "ARBITER_REQUIRED"

# All files are GREEN:
if commit_type in ALWAYS_AUTO_MERGE (D27: docs, style, test, chore):
    return "AUTO_MERGE"
elif commit_type in CONDITIONAL_AUTO_MERGE (D27: fix, refactor, perf):
    if line_count < threshold (D31):
        return "AUTO_MERGE"
    else:
        return "ARBITER_REQUIRED"
elif commit_type in ARBITER_REQUIRED (D27: feat, hotfix):
    return "ARBITER_REQUIRED"
elif commit_type in HUMAN_REQUIRED (D27: security, remove):
    return "HUMAN_REQUIRED"
elif commit_type == "[wip]":
    return "NEVER_MERGE"
```

### D31 — Seuils auto-merge : Option D différenciée par type (2026-04-12, validé Sinse)

**Décision** : seuils différenciés par type de commit + limite de fichiers, pour déterminer si un commit "CONDITIONAL_AUTO_MERGE" (D27) peut effectivement auto-merger ou doit passer par l'IA arbitre.

**Méthode de comptage** : `git diff --stat` (additions + deletions, valeur `insertions(+)` + `deletions(-)` dans le stat).

**Seuils** (valeurs de départ, ajustables après observation) :

| Type | Max lignes (add+remove) | Max fichiers modifiés |
|------|------------------------|------------------------|
| `[fix]` | **30** | **3** |
| `[refactor]` | **80** | **5** |
| `[perf]` | **50** | **3** |

**Règles** :
- Si `lines > max_lines` OU `files > max_files` → `ARBITER_REQUIRED`
- Sinon (et si aucun fichier ROUGE/ORANGE dans le diff, D30) → `AUTO_MERGE`

**Rationale seuils différenciés** :
- `[fix]` petit seuil (30) : les fixes doivent être ciblés — si plus, c'est probablement un refactor ou feat déguisé
- `[refactor]` seuil plus large (80) : renommages, extractions de fonctions sont normaux à cette échelle
- `[perf]` compromise (50) : optimisations typiquement ciblées mais peuvent toucher quelques endroits

**Rationale limite de fichiers** : protection contre la fragmentation — un diff réparti sur 10 fichiers = risque caché même si le volume total est petit. Force l'IA à grouper ses changements logiquement.

**Stockage config** : `/root/sinse-workspace/tools/merge-to-main-config.json`

```json
{
  "thresholds": {
    "fix":      { "max_lines": 30, "max_files": 3 },
    "refactor": { "max_lines": 80, "max_files": 5 },
    "perf":     { "max_lines": 50, "max_files": 3 }
  }
}
```

**Évolution** : ces seuils sont dans un fichier `[chore]` auto-mergeable (si pas de fichier protégé). Ajustements post-S2 : après quelques semaines d'utilisation réelle, si trop de choses passent par l'IA arbitre inutilement, on augmente les seuils. Itération rapide possible.

### D32 — Workflow MERGE-REQUEST.md (2026-04-12, validé Sinse)

**Décision** : workflow MERGE-REQUEST.md adapté au contexte ACTUEL (sessions interactives uniquement), avec les 5 sous-décisions suivantes.

**Contexte clé** : on est 100% en sessions interactives aujourd'hui (Sinse est présent quand une IA tourne). Le mode "background tmux autonome" n'existe pas encore — Telegram/email/push notifications sont donc inutiles pour l'instant.

### 5A — Stockage : centralisé dans projects/

**Path** : `/root/sinse-workspace/projects/academie-ia/merge-requests/YYYY-MM-DD-HHMM-<branch>.md`

**Archive** (une fois approved/rejected) : `/root/sinse-workspace/projects/academie-ia/merge-requests/archive/`

**Rationale** : versionné git, cohérent avec D12, multi-requests naturels (fichiers distincts), trackable dans `make status`.

### 5B — Format du fichier

```markdown
# MERGE REQUEST — <branch> — <timestamp>

## Status
PENDING / APPROVED / REJECTED

## Request info
- Branch: <branch>
- Commit type: [<type>]
- Last commit: <SHA> "<message>"
- Created at: <timestamp>
- Files modified: <count>
- Lines changed: +<add> -<remove>

## Blocking reason
One of: RED_FILE_TOUCHED / TYPE_REQUIRES_HUMAN / ARBITER_NO_GO / TOO_LARGE / OTHER

## Details
<Human-readable explanation>

## Arbiter evaluation (if applicable)
DECISION: <GO|NO-GO>
REASON: <from arbiter>
ISSUES: <if NO-GO>

## Files changed
- path/to/file1.py (+10 -2)
- path/to/file2.svelte (+5 -0)

## Diff preview (first 100 lines)
`​``diff
<truncated git diff>
`​``

## Commands
- Approve: `merge-approve <branch>`
- Reject:  `merge-reject <branch> --reason "..."`
```

### 5C — Notification : stdout direct + fichier trace (pas Telegram)

Quand `merge-to-main` détermine HUMAN_REQUIRED :
1. **Crée le fichier** MERGE-REQUEST.md (trace permanente)
2. **Affiche dans stdout/stderr** un message structuré :
   ```
   🔴 MERGE REQUEST requires your approval

   File created: projects/academie-ia/merge-requests/2026-04-12-2345-claude.md

   Blocking reason: RED_FILE_TOUCHED (.env modified)
   Commit type: [chore]
   Branch: claude

   Summary:
   - 3 files modified (+45 -12 lines)
   - Including: .env, docker-compose.yml

   To approve: merge-approve claude
   To reject:  merge-reject claude --reason "..."

   The AI will now exit. Review and decide at your convenience.
   ```
3. **Exit 1** — l'IA rend la main, ne bloque pas

**Filets de sécurité additionnels** (anti-oubli) :
- `make status` affiche le count des PENDING merge requests
- Hook Stop (déjà actif dans `claude-settings.json`) affiche un rappel si count > 0 au prochain lancement de session

**Telegram / email / push notifs** : NON pour l'instant. Reporté en **Phase 4** si/quand on introduit le mode background tmux avec IAs autonomes.

### 5D — Bash tools `merge-approve` / `merge-reject`

**`merge-approve <branch>`** :
1. Lit `merge-requests/<date>-<branch>.md`
2. Vérifie Status == PENDING
3. Re-vérifie que main n'a pas divergé depuis (sinon alerte + abort)
4. Re-vérifie que la branche source n'a pas changé depuis (sinon alerte + abort)
5. Execute `git merge <branch>` vers main
6. Crée tag `deploy-YYYY-MM-DD-HHMM`
7. Push main + tag sur GitHub
8. Marque MERGE-REQUEST.md comme APPROVED (+timestamp approbation)
9. Déplace dans `merge-requests/archive/`

**`merge-reject <branch> --reason "..."`** :
1. Lit le fichier
2. Vérifie Status == PENDING
3. Marque comme REJECTED avec la raison
4. Déplace dans `merge-requests/archive/`
5. Note dans la branche source (commit `[chore]` dans la branche avec la raison de rejet) pour que l'IA sache qu'elle doit corriger

### 5E — Multi-requests

Fichiers distincts par `<timestamp>-<branch>.md` permettent de gérer plusieurs requests en parallèle sans conflit.

**Ordre de traitement** : au choix de Sinse (pas d'enforcement).

**Protection contre divergence** : `merge-approve` re-vérifie systématiquement que main n'a pas changé depuis la création de la request. Si main a bougé (parce qu'un autre merge a été approuvé entre temps), alerte + demande de refresh de la request.

**Bloc 4 du refactor COMPLÈTEMENT TERMINÉ ✅** — tous les 🟡 (B3 `/check`, E1 healthchecks, E2 gitleaks, G1 pre-commit hooks) sont tranchés via D22-D32. Plus l'Option E entière (auto-merge avec 12 types, arbiter, fichiers protégés, seuils, MERGE-REQUEST workflow).

### D33 — Contenu + placement slash commands `/pickup` et `/handoff` (2026-04-12, auto-validé après V2 révisée)

**Décision** : templates V2 télégraphiques anglais pour `/pickup` (11 étapes) et `/handoff` (7 étapes avec 3 outcomes explicites), placement via architecture P2 (source tracked git + script install).

**Templates validés** : voir conversation session (V2 après correction de 7 problèmes identifiés en auto-analyse).

**Corrections appliquées vs V1** :
1. Style télégraphique strict (D13)
2. Fallback graceful pour `docs-list` (pas encore créé en pré-S2)
3. Gestion CLAIMED continuation dans `/pickup` étape 9
4. Vérification branche safety dans `/pickup` étape 3
5. `merge-to-main` obligatoire dans `/handoff` étape 6
6. Reporting explicite des 3 outcomes MERGE-REQUEST (AUTO_MERGE / ARBITER_APPROVED / MERGE-REQUEST_CREATED)
7. Placement P2 tranché clairement

**Architecture P2 (placement)** :

```
/root/sinse-workspace/slash-commands/
├── pickup.md                         ← source tracked git
└── handoff.md                        ← source tracked git

/root/sinse-workspace/tools/
└── install-slash-commands            ← bash script (syncs source → targets)

Targets (user-level, installés par script) :
~/.claude/commands/
├── pickup.md                         ← copie directe du markdown
└── handoff.md                        ← copie directe du markdown
~/.gemini/commands/
├── pickup.toml                       ← converti MD → TOML (wrap prompt = """...""")
└── handoff.toml                      ← converti MD → TOML
```

**Script `install-slash-commands`** (fonctions) :
1. Lit fichiers source dans `/root/sinse-workspace/slash-commands/`
2. Copie directe vers `~/.claude/commands/` (markdown natif Claude Code)
3. Conversion simple MD → TOML pour `~/.gemini/commands/`
4. Check idempotent (skip si pas de diff)
5. Lancé manuellement après modif source (ou via post-commit hook optionnel)

**Migration en S2** :
- Créer les 2 fichiers source dans `slash-commands/`
- Créer le script `install-slash-commands`
- Lancer le script pour installer dans `~/.claude/commands/` et `~/.gemini/commands/`
- **Supprimer** `/opt/academia/.claude/commands/fin.md` (remplacé par `/handoff`)
- **Supprimer** `/opt/academia/.gemini/commands/fin.toml` (idem)

**Note WIP partiel** : si une IA veut sauvegarder du work-in-progress sans merger, elle N'utilise PAS `/handoff`. Elle fait juste `committer "[wip] ..."` + `git push` manuel. Le `/handoff` implique toujours "prêt à tenter merge".

**Bloc 5 du refactor TERMINÉ ✅** — 🟡 B1 + B2 tranchés via D33. Les anciens `/fin` (Claude et Gemini) sont supprimés en S2, remplacés par `/pickup` et `/handoff`.

### D34 — Tags git deploy + tool `rollback-to` (2026-04-12, validé Sinse)

**Décision** : système de tags deploy horodatés + bash tool `rollback-to` pour rollback rapide et safe.

### 34A — Format tag : `deploy-YYYY-MM-DD-HHMM`
Exemple : `deploy-2026-04-12-2345`. Lisible, chronologique, sortable alphabétiquement.

### 34B — Quand créer le tag
Auto-créé par :
- `merge-to-main` (à chaque auto-merge réussi, directe ou arbiter-approved)
- `merge-approve` (à chaque approbation humaine d'une MERGE-REQUEST)

**Pas de tag** pour les commits intermédiaires sur les branches IA (pas encore mergés).

### 34C — Rétention : tout garder
Pas de cleanup. Git gère les tags à l'échelle. Réévaluer à 500+ tags si besoin de cleanup.

### 34D — Bash tool `rollback-to`

**Emplacement** : `/root/sinse-workspace/tools/rollback-to`

**Usage** : `rollback-to <tag>` (ex: `rollback-to deploy-2026-04-12-2130`)

**Logique 11 étapes** :
1. Verify tag exists (else list recent deploy tags)
2. Must be on main branch (abort if not)
3. Fetch latest
4. Preview rollback (show commits + files affected)
5. Explicit confirmation (must type "ROLLBACK" in caps)
6. Create backup branch (`backup-before-rollback-<timestamp>`) — safety net
7. Revert commits via `git revert` (preserves history, NO force push)
8. Create rollback tag (`rollback-<timestamp>-from-<original>`)
9. Push main + tags (standard push, no force)
10. Run `smoke-test --deep` after rollback
11. Prompt Sinse to restart containers if needed (list affected services)

**Principes de safety** :
- **Confirmation explicite** : type "ROLLBACK" en majuscules (pas "yes")
- **Backup branch automatique** : si le rollback lui-même foire, on peut revert le revert via la branche backup
- **Pas de force push** : utilise `git revert` qui crée des commits d'annulation. Historique préservé, mauvais commits restent visibles pour debug post-mortem
- **Tag rollback tracé** : pour tracer qu'il y a eu un rollback
- **Smoke-test post-rollback** : vérifie que le rollback n'a pas cassé autre chose
- **Prompt restart containers** : rappelle mais ne fait pas automatiquement (trop risqué sans contexte)

**Classification** :
- Catégorie : bash tool maison (D10)
- Emplacement : `/root/sinse-workspace/tools/rollback-to`
- Protection : le tool lui-même est un fichier **ROUGE** (D30) — seul Sinse peut le modifier
- **Invocation** : Sinse uniquement, ou IA avec accord explicite Sinse (règle à ajouter dans AGENTS.md)

**Bloc 6 du refactor TERMINÉ ✅** — 🟡 E3 tranché via D34. Reste Bloc 7 (A7 + G2 exploration native Claude Code).

### D35 — Exploration native Claude Code : A7 + G2 (2026-04-12, validé Sinse)

### 35A — Memory native (A7) : Option D — refactor avec référence aux secrets

**Décision** : garder le contenu actuel de `~/.claude/projects/-opt-academie/memory/reference_dify_api.md`, mais :
1. Remplacer la clé admin Dify en dur par une référence : `ADMIN_KEY=$(cat /opt/academia-shared/secrets/dify-admin-key)`
2. Ajouter dans AGENTS.md la règle :
   > "Native Claude memory OK for non-sensitive references. Secrets MUST be by-reference (e.g., `$(cat /opt/shared/secrets/...)`)."
3. Auditer les autres fichiers memory (si existants) pour vérifier qu'il n'y a pas de secrets en clair

**Rationale** :
- Le contenu est utile (accès Dify API documenté, workspace IDs)
- On élimine le risque sécurité (pas de clé en clair dans un fichier non protégé)
- Cohérent avec D30 (secrets niveau ROUGE)
- Claude peut continuer à lire ce fichier pour les infos non-sensibles

**Migration en S2** :
1. Lire le fichier actuel
2. Remplacer la clé par la référence
3. Vérifier qu'il n'y a pas d'autres secrets dans memory native
4. Ajouter la règle dans AGENTS.md

### 35B — Subagents natifs (G2) : Option C — usage limité recherches read-only

**Décision** : autoriser l'usage des subagents natifs Claude Code (Task tool) uniquement pour des recherches read-only lourdes qui pollueraient le contexte principal.

**Règle à ajouter dans AGENTS.md** :
```
SUBAGENTS (Claude only)
Native Claude subagents (Task tool): OK for read-only research tasks that would pollute main context.

Rules:
- Read-only only (no file modifications)
- No commits from subagent
- No destructive commands
- Return structured summary to main context

Gemini/Codex: no equivalent, do research manually (acceptable tradeoff).
```

**Cas d'usage légitimes** :
- "Explore this large directory structure"
- "Find all files that import module X"
- Recherches documentaires longues

**Cas d'usage INTERDITS** :
- Subagent qui modifie des fichiers
- Subagent qui commit
- Subagent qui exécute des commandes destructrices

**Architecture** : on NE base PAS d'architecture sur les subagents (Gemini/Codex n'ont pas l'équivalent). C'est un outil ponctuel pour Claude, pas un pilier.

**Bloc 7 du refactor TERMINÉ ✅** — 🟡 A7 + G2 tranchés via D35. **TOUTES LES 18 PASTILLES JAUNES SONT DÉSORMAIS TRANCHÉES.**

### D36 — Ajustements post-audit redondances (2026-04-12, validé Sinse)

**Contexte** : audit redondances effectué après parcours des 18 pastilles jaunes. Résultat : pas de redondance majeure comme le `.lock`, mais quelques ajustements mineurs à formaliser.

### 36A — Règle update des fichiers contexte

**Ajouter dans AGENTS.md** :

```
CONTEXT FILES — who updates what, when

STATE.md:
- Updated at: merge-to-main success only (global project state)
- By: merge-to-main tool automatically
- Scope: project-wide facts (infra, users, stack, active features)

TODO.md:
- Updated during: session (each time AI claims/completes a task)
- By: AI via committer tool (CLAIMED ↔ OPEN ↔ DONE movements)
- Scope: task pool

HANDOFF-<agent>.md:
- Updated at: /handoff (end of session)
- By: AI, overwrites previous version
- Scope: current session recap (one per AI)

CHANGELOG.md:
- Updated during: session (when significant action happens)
- By: AI via `log <type> "<message>"` tool
- Scope: append-only action history
- Also updated: automatically by merge-to-main when merge completes

DECISIONS.md:
- Updated during: session (when important decision made)
- By: AI manually editing (append-only)
- Scope: rationale for choices, architectural decisions

No overlap intended. If you think two files should contain the same info, pick the one that matches the scope and link from the other if needed.
```

**Rationale** : évite le chevauchement potentiel entre STATE/TODO/HANDOFF identifié dans l'audit.

### 36B — `cly` wrapper : version complète Peter verbatim (pas de simplification)

**Décision** : adopter directement la version complète Peter (avec background title setter) plutôt qu'un simple alias shell.

**Rationale (Sinse)** : cohérent avec règle d'or #7 (plan v1.0 avant exécution, pas d'aller-retour). Le coût actuel (1 process qui sleep 0.5s en background) est négligeable (<0.01% CPU). La version complète est prête pour le futur multi-terminal sans migration.

**Emplacement** : `~/.config/zsh/claude-wrapper.zsh`, sourcé depuis `~/.zshrc`.

**Code verbatim** (déjà documenté en D section 2.3, dupliqué ici pour S2) :

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
    "$HOME/.claude/local/claude" --dangerously-skip-permissions "$@"
    local exit_code=$?
    kill $title_pid 2>/dev/null
    wait $title_pid 2>/dev/null
    _set_title "%~"
    return $exit_code
}

_set_title() { print -Pn "\e]2;$1\a" }
```

**Note** : adapter `$HOME/.claude/local/claude` au vrai path de claude sur cosmos (`/usr/local/bin/claude` d'après l'audit).

### 36C — Fichiers temporaires à archiver post-v1.0

Une fois le plan stabilisé en v1.0 et les Sessions S1+S2+S3 exécutées, les fichiers suivants deviennent obsolètes :
- `REFACTOR-PLAN.md`
- `REFACTOR-AUDIT.md`

**Action post-v1.0** : déplacer ces fichiers dans `projects/academie-ia/archive/refactor-workflow-2026-04-12/` pour préserver l'historique de la phase de refactor (référence future, audit trail).

### 36D — Anciens `/fin` suppression (confirmation)

Déjà prévu dans D33. Confirmation : `/opt/academia/.claude/commands/fin.md` et `/opt/academia/.gemini/commands/fin.toml` sont supprimés en S2.

**Audit redondances TERMINÉ ✅**. Pas de redondance majeure détectée. Le design est globalement sain.

### D37 — Résolution 10 gaps pre-v1.0 + structure v1.0 multi-fichiers (2026-04-12, validé Sinse)

**Contexte** : audit complet effectué avant stabilisation v1.0. 10 gaps identifiés (2 critiques, 3 importants, 5 mineurs) à traiter.

**Structure v1.0 — Option C hybride** :

```
/root/sinse-workspace/projects/academie-ia/refactor-v1.0/
├── README.md                           ← Index + overview + règles d'or
├── decisions.md                        ← 36 décisions organisées
├── architecture.md                     ← Vue AVANT/APRÈS complète
├── sessions/
│   ├── s1-securisation.md
│   ├── s2-refactor-archi.md
│   ├── s3-multi-ia-reel.md
│   └── s4-polish-optional.md
└── reference/
    ├── tools.md                        ← 15 bash tools
    ├── slash-commands.md               ← /pickup + /handoff
    ├── file-protection.md              ← ROUGE/ORANGE/VERT
    ├── disaster-recovery.md            ← DR + 4 scénarios
    └── workflow-rules.md               ← Template AGENTS.md
```

**REFACTOR-PLAN.md actuel (working, 1940+ lignes)** : archivé intégralement post-v1.0 dans `projects/academie-ia/archive/refactor-workflow-2026-04-12/REFACTOR-PLAN-working.md`. Source historique préservée.

**10 gaps résolus** :

### G1 — Passphrase Restic : triple stockage
1. `/opt/academia-shared/secrets/restic-passphrase` (chmod 600, root only)
2. Carnet papier offsite (Sinse écrit à la main, stocké hors cosmos)
3. Password manager Sinse (Bitwarden/1Password/KeePass)
Documenté dans `reference/disaster-recovery.md`.

### G2 — REFACTOR-PLAN trop gros : structure multi-fichiers Option C
Voir structure ci-dessus. Aucune perte d'info — découpage par thème/session.

### G3 — Tool `init-worktree` : 15ème bash tool
Fonctions :
- `git worktree add /opt/academia-worktrees/<agent> <branch>`
- Crée `.agent` file avec agent name
- Crée AGENTS.md pointer vers `/root/sinse-workspace/AGENTS.md`
- Symlinks vers `/opt/academia-shared/` pour les secrets
- Copy template `.claude/settings.local.json` avec permissions worktree-appropriées
- Premier `smoke-test --quick` dans le worktree
- Output : "Worktree <agent> ready at <path>"

### G4 — Dispatch CLAUDE.md → 6 docs projet
**Étape explicite S2.3.5** : Claude lit `/root/sinse-workspace/context/CLAUDE.md` + `/opt/academia/CLAUDE.md`, extrait et dispatche vers les 6 fichiers `docs/projects/academie-ia/*.md` selon le tableau D16. Pas de rédaction from scratch, extraction intelligente.

### G5 — Squelette disaster-recovery.md
**4 scénarios obligatoires** documentés avec procédures pas à pas :
1. **PG table drop** : restore depuis dump horaire (N2)
2. **Fichier workspace perdu** : restore depuis Restic (N3)
3. **VM cosmos crash** : restore depuis snapshot Proxmox (N1)
4. **NAS total cramage** : restore depuis Restic + Google Drive (N3 offsite)

Chaque scénario = étapes + commandes exactes + test validé S1.

### G6 — Liste exhaustive secrets : étape S2.1.5
Grep récursif sur patterns :
- `*key*`, `*secret*`, `*password*`, `*token*`
- `.env*`, `*.pem`, `*.crt`, `*_rsa*`, `*_ed25519*`
- Spécifiques : `dify_admin_key`, `encryption.key`, `anthropic-api-key`, `openai-api-key`

Dans : `/opt/academia/`, `/opt/litellm/`, `/opt/n8n/`, `~/.claude/`, `/root/sinse-workspace/`

Output dans un fichier de référence. Migration vers `/opt/academia-shared/secrets/`.

### G7 — Git hooks par repo : clarification D26
- `/root/sinse-workspace/.git/hooks/pre-commit` = **gitleaks uniquement** (pas de code actif, pas de smoke-test nécessaire)
- `/opt/academia/.git/hooks/pre-commit` = **gitleaks**
- `/opt/academia/.git/hooks/pre-push` = **smoke-test --deep**
- Worktrees : héritent via `git config core.hooksPath /opt/academia/.git/hooks` (ou équivalent)

### G8 — Checkpoints sessions : fichier `.session-progress`
Dans chaque worktree actif, un fichier `.session-progress` (gitignored) contient :
```
SESSION=S1
STEP=S1.3.2
TIMESTAMP=<unix>
LAST_ACTION=<description>
```

`/pickup` lit ce fichier en étape 5 bis. Si présent, propose de reprendre à STEP. Supprimé automatiquement par `/handoff` à la fin de la session.

### G9 — `sinse-quickstart.md` : créé en fin S2
Emplacement : `/root/sinse-workspace/docs/sinse-quickstart.md`
Langue : **français** (exception à D13 — ce fichier est pour Sinse)
Max 1 page, contient :
- Comment lancer une IA (cly)
- Commandes essentielles (make status, merge-approve, merge-reject, rollback-to, log, committer)
- Comment reviewer une MERGE-REQUEST
- Comment faire un rollback urgent
- Troubleshooting commun

### G10 — `AUDIT-TODO académie-ia` : créé en fin S3
Emplacement : `/root/sinse-workspace/projects/academie-ia/AUDIT-TODO.md`
Contient le squelette des 9 points listés dans D21 à traiter lors de l'audit complet du projet academie-IA post-refactor workflow.

**D37 TERMINÉE ✅. Pré-requis pour stabilisation v1.0 satisfaits.**

### 2026-04-12 — STABILISATION v1.0 ✅

**Version** : v0.3 → **v1.0**

**Livrable créé** : structure multi-fichiers `/root/sinse-workspace/projects/academie-ia/refactor-v1.0/`

```
refactor-v1.0/
├── README.md                       ← Index + overview + règles d'or
├── decisions.md                    ← 37 décisions organisées (D1-D37)
├── architecture.md                 ← Vue AVANT/APRÈS complète
├── sessions/
│   ├── s1-securisation.md         ← Checklist S1 + critères validation + troubleshooting
│   ├── s2-refactor-archi.md       ← Checklist S2 complète
│   ├── s3-multi-ia-reel.md        ← Checklist S3 complète
│   └── s4-polish-optional.md      ← Session optionnelle
└── reference/
    ├── tools.md                    ← 15 bash tools documentés
    ├── slash-commands.md           ← /pickup + /handoff verbatim
    ├── file-protection.md          ← ROUGE/ORANGE/VERT complet
    ├── disaster-recovery.md        ← 4 scénarios + procédures
    └── workflow-rules.md           ← Template AGENTS.md complet
```

**Règle d'or #7 activée** : à partir de maintenant, aucune modification du plan v1.0. Le refactor est prêt à être **exécuté** en Sessions S1 → S2 → S3 (+ S4 optionnel).

**Prochaine action** : Sinse lance Session 1 quand prêt.

**Archivage post-v1.0** : ce fichier `REFACTOR-PLAN.md` (working, 1940+ lignes) + `REFACTOR-AUDIT.md` seront archivés dans `projects/academie-ia/archive/refactor-workflow-2026-04-12/` en début de S2 (étape S2.2). Jusque-là, ils restent dans `/root/sinse-workspace/context/` pour référence immédiate.

---

## 4. Zones d'ombre à éliminer

### 4.1 Zone 1 — Patterns Peter (après recherche v2)

| # | Sujet | Statut | Résumé |
|---|-------|--------|--------|
| 1.1 | Pattern SDD | ✅ Résolu | Legacy, abandonné oct 2025 pour discussion itérative |
| 1.2 | Closed-loop validation et CI | 🟡 Partiel | Peter rejette TDD, écrit tests dans même contexte que feature |
| 1.3 | Contenu exact slash commands | ✅ Résolu | 12 commands fetched, `/handoff` et `/pickup` à copier |
| 1.4 | Pattern oracle détaillé | ✅ Résolu | Vrai npm package `@steipete/oracle`, CLI avec flags |
| 1.5 | Pattern "Make a note" | ✅ Résolu | Phrase naturelle, édite AGENTS.md en side effect |
| 1.6 | Context management long sessions | 🟡 Partiel | Auto-compact (233k tokens), pas de /clear manuel documenté |
| 1.7 | Protocole "never git revert" | 🔴 Gap | Pas documenté explicitement, inference seulement |
| 1.8 | Usage Claude + Codex parallèle | ✅ Résolu | Shift wholesale vers Codex, pas de routing par type |
| 1.9 | Tools maison (committer, oracle, peekaboo) | ✅ Résolu | Bash + Node.js + Swift, sources vérifiées |
| 1.10 | Gestion web context | ✅ Résolu | `gh` mandaté pour GitHub, WebFetch + Firecrawl sinon |

**Nouvelles zones Zone 1 découvertes** :

| # | Sujet | Statut |
|---|-------|--------|
| 1.11 | Pointer pattern AGENTS.md (1 canonical + pointers) | ✅ Résolu |
| 1.12 | docs-list pattern (alternative zero-dep à RAG) | ✅ Résolu |
| 1.13 | tmux multi-agents au lieu de subagents Claude | ✅ Résolu |
| 1.14 | Règle `gh` over web search pour GitHub URLs | ✅ Résolu |
| 1.15 | Style télégraphique strict pour AGENTS.md | ✅ Résolu |

**Gaps restants** (à combler si nécessaire) :
- Template exact de `spec.md` (taille : ~500 lignes confirmée)
- Routing rule explicite Claude vs Codex par task type
- Contenu de `/automerge` et `/massageprs`
- Protocole "never git revert" (inference seulement)

### 4.2 Zone 2 — Spécifiques à notre projet (à discuter ensemble)

| # | Sujet | Priorité |
|---|-------|----------|
| 2.1 | Multi-IA et `sys.user_id` Dify (qui est qui ?) | HAUTE |
| 2.2 | Rollback des chatflows Dify après modif | HAUTE |
| 2.3 | Gestion sessions Dify en multi-IA (nettoyage conversations test) | MOYENNE |
| 2.4 | Logs centralisés (6 sources aujourd'hui) | MOYENNE |
| 2.5 | Cohérence prod / worktrees (deploy post-merge) | HAUTE |
| 2.6 | Gestion secrets partagés en multi-IA | HAUTE |
| 2.7 | Tests des slash commands eux-mêmes | MOYENNE |
| 2.8 | Migration Postgres en multi-IA (schéma partagé) | HAUTE |
| 2.9 | Monitoring Postgres (pool, slow queries, disk) | BASSE |
| 2.10 | Rotation/audit des clés API | BASSE |
| 2.11 | Politique fichier `.lock` multi-IA | HAUTE |
| 2.12 | Communication humain ↔ IA (style, langue, longueur) | MOYENNE |
| 2.13 | Gestion dépendances npm/pip en multi-IA | MOYENNE |
| 2.14 | Génération curriculum (Sonnet vs Gemini vs Opus) | BASSE |
| 2.15 | Metrics business (dashboard d'usage) | BASSE |

### 4.3 Blocs de discussion (ordre proposé)

**Bloc A — CI / Validation** (critique pour YOLO)
Points : 1.2 + 2.4 + 2.7

**Bloc B — Layer collaboration** (cœur multi-IA)
Points : 1.3 + 1.4 + 1.5 + 1.6 + 1.9

**Bloc C — Gotchas stack** (spécifique Dify/n8n/PG)
Points : 2.1 + 2.2 + 2.3 + 2.5 + 2.8 + 2.11

**Bloc D — Polish et long terme** (Session 4)
Points : 1.1 + 1.7 + 1.8 + 1.10 + 2.6 + 2.9 + 2.10 + 2.12 + 2.13 + 2.14 + 2.15

---

## 5. TODO list structurée

### Légende

- `[OPEN]` à faire · `[DISCUSS]` nécessite décision · `[DECIDED]` tranché · `[DONE]` terminé
- `@sinse` action user · `@claude` action moi · `@both` on le fait ensemble en session

### Phase 0 — Préparation (hors session)

**P0.1 — Environnement client (Sinse)**
- [ ] Installer WSL2 sur Windows
- [ ] Installer Debian dans WSL
- [ ] Installer/configurer Windows Terminal
- [ ] Tester SSH vers cosmos depuis WSL Debian
- [DECIDED] Claude Code : continuer à l'utiliser sur cosmos (pas en local)

**P0.2 — Proxmox : inventaire**
- [ ] Inventaire disques/stockages Proxmox (à faire en début S1 via SSH)
- [DECIDED] Accès : SSH root (D6)

**P0.3 — Google Drive**
- [ ] Créer folder `/Backups/academie/` dans Google Drive
- [DISCUSS] Compte de service Google vs OAuth user
- [ ] Créer credentials API Google Drive (à faire en début S1 ensemble)

**P0.4 — Budget**
- [DECIDED] Full Opus 4.6 1M (D7)

### Session 1 — Sécurisation (3-4h)

**S1.1 — Backup N1 : Snapshots Proxmox**
- [ ] Configurer snapshots quotidiens VM cosmos
- [ ] Rétention 7d + 4w + 3m
- [ ] Stockage cible (à décider selon inventaire)
- [ ] Test snapshot manuel

**S1.2 — Backup N2 : Dumps PostgreSQL**
- [ ] Script `/opt/academia/scripts/pg-backup.sh`
- [ ] Cron horaire
- [ ] Destination `/opt/backups/postgres/`
- [ ] Rétention 24h + 7d + 4w
- [ ] Test dump manuel

**S1.3 — Backup N3 : Restic + Google Drive**
- [ ] Installer Restic + Rclone
- [ ] Configurer Rclone backend Google Drive
- [ ] Initialiser repo Restic
- [ ] Liste fichiers à backup (code + configs + secrets + dumps PG)
- [ ] Générer + stocker passphrase Restic (CRITIQUE)
- [ ] Script `restic-backup.sh` + cron 3h
- [ ] Premier backup manuel

**S1.4 — Tests de restore (CRITIQUE)**
- [ ] Test N2 : restore dump PG
- [ ] Test N3 : `restic restore latest --target /tmp/`
- [ ] Test N3 granulaire : 1 fichier seul
- [ ] Test N1 : rollback VM Proxmox (si faisable sans interruption)
- [ ] ✅ Validation : tous les tests passent

**S1.5 — Documentation**
- [ ] Créer `docs/disaster-recovery.md`
- [ ] Documenter chaque niveau de restore
- [ ] Lister tous les secrets critiques

**S1.6 — Smoke test minimal**
- [ ] Créer `scripts/smoke-test.sh`
- [ ] Tests : webapp, Dify, n8n, Postgres, LiteLLM
- [ ] Test en conditions normales + avec service down

**✅ Critère de validation S1** : Backups opérationnels + test restore passé + smoke-test OK

### Session 2 — Refactor archi + YOLO (4h)

**S2.1 — Activation YOLO**
- [ ] Créer alias `cly`
- [ ] Tester `--dangerously-skip-permissions`

**S2.2 — Structure worktrees**
- [DISCUSS] Nom final `/opt/academia/` vs `/opt/academia-prod/`
- [ ] Créer `/opt/academia-worktrees/`
- [ ] `git worktree add .../claude claude`
- [ ] Créer `/opt/academia-shared/` + déplacer secrets
- [ ] Symlinks shared → worktrees
- [ ] Fichier `.agent` par worktree
- [ ] Test session Claude depuis worktree

**S2.3 — Refactor fichiers contexte**
- [ ] Créer `AGENTS.md` (court, télégraphique)
- [ ] Découper CLAUDE.md → `docs/infra.md`, `teacher.md`, `webapp.md`, `litellm.md`, `n8n.md`, `postgres.md`, `taxonomies.md`, `cloudflare.md`
- [ ] Ajouter `read_when:` front-matter
- [ ] Symlink CLAUDE.md → AGENTS.md (ou supprimer)
- [ ] Restructurer `TODO.md` en sections par IA
- [ ] Renommer `HANDOFF.md` → `HANDOFF-claude.md`
- [ ] Améliorer `.lock` multi-IA

**S2.4 — Slash commands de base**
- [ ] `.claude/commands/start.md`
- [ ] `.claude/commands/fin.md`
- [ ] `.claude/commands/commit.md`
- [ ] `.claude/commands/deploy-teacher.md`
- [ ] `.claude/commands/changelog-webapp.md`
- [ ] `.claude/commands/merge.md` (+ tag deploy)
- [ ] Test `/start` + `/fin` sur session réelle

**S2.5 — Protocole destructif**
- [ ] Créer `docs/destructive-ops.md`
- [ ] Référencer depuis `AGENTS.md`

**✅ Critère de validation S2** : Worktree claude opérationnel, slash commands marchent, refactor contexte complet, YOLO activé sans casse

### Session 3 — Multi-IA réel (3h)

**S3.1 — Slash commands collaboration**
- [ ] `/oracle`
- [ ] `/review`
- [ ] `/handoff`
- [ ] `/archive-session`

**S3.2 — Dashboard make status**
- [ ] `scripts/status.sh`
- [ ] État worktrees (commits ahead, last activity)
- [ ] État prod (containers)
- [ ] État backups
- [ ] Alias shell `status`

**S3.3 — Introduction Gemini**
- [DISCUSS] Provider (AI Studio / Vertex / gemini-cli)
- [ ] API key Gemini
- [ ] Branche `gemini`
- [ ] Worktree `gemini`
- [ ] Test `/oracle` Claude → Gemini
- [ ] Test `/review` croisée

**S3.4 — Healthchecks**
- [ ] Vérifier healthchecks Docker existants
- [ ] Ajouter manquants
- [ ] Restart policies cohérentes

**✅ Critère de validation S3** : Claude + Gemini se parlent via `/oracle` et `/review`, `make status` fonctionne, healthchecks OK

### Session 4 — Polish (optionnelle, 2h)
- [ ] CLI-fication `profil_manager.py` → typer
- [ ] CLI-fication `update_teacher_chatflow.py` → typer
- [ ] Pre-commit hooks (gitleaks)
- [ ] Tests bout en bout webapp
- [ ] Tests API FastAPI
- [ ] Monitoring léger (alertes backup, containers)

---

## 6. Prochaines étapes immédiates

1. ✅ **Créer ce fichier REFACTOR-PLAN.md** (FAIT — v0.1)
2. 🟡 **Lancer recherche ciblée v2 Peter** (EN COURS, background)
3. ⏳ **Intégrer résultats recherche v2 dans Section 2** (après recherche)
4. ⏳ **Éliminer zones d'ombre Zone 1** avec les détails de la recherche
5. ⏳ **Discuter Bloc A** (CI / validation / logs) — bloquant Session 1
6. ⏳ **Discuter Bloc B** (layer collaboration) — bloquant Session 2
7. ⏳ **Discuter Bloc C** (gotchas stack) — bloquant Session 3
8. ⏳ **Stabiliser ce plan en v1.0** (tous les `[DISCUSS]` tranchés)
9. ⏳ **Lancer Session 1** (phase d'exécution)

---

## 7. Historique des décisions (append-only)

### 2026-04-11 — Session initiale refactor (discussion conceptuelle)

**Contexte** : Sinse veut refactor le workflow/workspace actuel inspiré par Peter Steinberger.

**Décisions tranchées** :
- D1 — Stratégie backup 4 niveaux (Proxmox + PG dumps + Restic/GDrive + Git)
- D2 — Architecture modèle C+ (worktrees isolés + patterns collaboration)
- D3 — Séquencement 3 sessions intenses
- D4 — WSL + Debian + Windows Terminal côté client
- D5 — Fichiers contexte refactorés (AGENTS.md + docs/ avec read_when:)
- D6 — Accès Proxmox via SSH root
- D7 — Full Opus 4.6 1M pour le refactor

**Zones d'ombre identifiées** : 25 points (10 Peter + 15 projet)

**Actions déclenchées** :
- Création de ce fichier REFACTOR-PLAN.md (v0.1)
- Recherche ciblée v2 sur Peter (d'abord échouée en background, relancée en foreground)

### 2026-04-11 (ter) — Audit infrastructure complet (v0.3)

**Contexte** : Sinse demande un audit complet de l'infra workflow/workspace actuelle avant qu'on continue. Il veut un tableau global avec ce qu'on a / Peter / décidé / zones d'ombres / idées potentielles.

**Méthode** : scan exhaustif `/root/sinse-workspace/`, `/opt/academia/`, `~/.claude/`. Lecture de tous les fichiers contexte + glob structure complète.

**Découvertes majeures** :
- ~30% du socle est déjà en place (slash commands, hooks, lock, branches, conventions, contexte structuré, symlink)
- `/opt/academia/CLAUDE.md` (9K) ET `/root/sinse-workspace/context/CLAUDE.md` (8K) sont DUPLIQUÉS — pile le problème que résout le pointer pattern (D8)
- Hook Stop déjà actif dans `claude-settings.json` (rappel commit)
- `/opt/academia/.claude/commands/fin.md` existe + `/opt/academia/.gemini/commands/fin.toml` existe
- Memory native Claude Code dans `~/.claude/projects/.../memory/` — non exploitée
- `DECISIONS.md` riche (70+ entries) — culture déjà ancrée

**Livrable** : `REFACTOR-AUDIT.md` créé avec 7 catégories (A-G), tableaux complets, statuts 🟢/🟡/⚪, et 30+ idées potentielles 🆕.

**Pastilles jaunes identifiées** : 18 items (7 doc + 3 slash + 1 tool + 1 archi + 3 sécu + 1 env + 2 hooks).

**Prochaine étape** : discuter les 18 pastilles jaunes une par une avec Sinse, dans un ordre logique. Une fois toutes tranchées + idées potentielles évaluées, on stabilise le plan en v1.0 et on lance Session 1.

### 2026-04-11 (bis) — Réception recherche v2 Peter (v0.2)

**Contexte** : recherche ciblée complétée (64 tool uses, sources vérifiées sur steipete.me et github.com/steipete).

**Révélation majeure** : Peter a **largement abandonné Claude Code pour Codex (GPT-5.2)** fin 2025. *"5x more done on one codex session than with claude."* Canonical actuel : `github.com/steipete/agent-scripts` (l'ancien `agent-rules` est archivé). Ses slash commands sont *"never found them too useful"*.

**Zones d'ombre Zone 1 résolues** : 8/10 ✅, 2/10 🟡. Nouvelles zones découvertes : pointer pattern AGENTS.md, docs-list script, tmux > subagents, règle `gh`, style télégraphique strict.

**Nouvelles décisions** :
- D8 — Pointer pattern AGENTS.md (1 canonical + pointers)
- D9 — Slash commands minimaux (4 au lieu de 10+)
- D10 — Tools maison en priorité (bash/python PATH-installed pour safety-critical)

**Updates Section 2** : enrichie en v2 avec toutes les sources verbatim (cly wrapper code, committer logic, `/handoff`/`/pickup` checklists, quotes Peter).

**Prochaine étape** : Discuter avec Sinse des ajustements du plan, notamment :
1. Validation du pointer pattern AGENTS.md (D8)
2. Validation de la réduction à 4 slash commands (D9)
3. Adoption du `committer` bash tool (D10)
4. Choix oracle : vrai npm package ou wrapper local LiteLLM
5. Puis attaquer le Bloc A (CI / validation / logs)
