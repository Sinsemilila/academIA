---
description: Session end — save state, commit, push
---

Session end. Execute in order.

## 1. Pre-check
- `smoke-test --deep`
- Fail → STOP + fix before continuing.

## 2. Update state
- `/opt/academie/TODO.md`: mark completed tasks as DONE.
- `/opt/academie/CHANGELOG.md`: append via `log <type> "<message>"` tool.
- **Docs consistency check**: for each structural change this session (schema, architecture, pedagogy rules, infra), verify the corresponding `docs/*.md` was updated in the same session. If not, update `last_reviewed` OR flip `status: needs-review`. For new architectural decisions, create `docs/05-decisions/ADR-NNN-<slug>.md` from template.

## 3. Update SESSION.md
**Prepend** (don't overwrite) a new session block at the top of `/opt/academie/SESSION.md`, after the header line.
Keep previous sessions below.

**Rotation** : SESSION.md ne contient que les **3 dernières sessions**. Après avoir prepended la nouvelle, si le fichier contient >3 sessions, déplacer la plus ancienne (celle en bas) vers le haut de `SESSION_ARCHIVE.md` (aussi newest-on-top). L'archive n'est jamais lue au pickup mais reste disponible pour consultation manuelle.
```
---

## Session N — YYYY-MM-DD

### Done
- bullet list of what was accomplished

### Next
- bullet list of suggested next steps

### Gotchas
- bullet list of risks/issues (if any, omit section if none)
```

## 4. Vault auto-writes (v0.2 Claude-as-vault-cognition)

Vault path racine : `/root/sinse-vault/`

### 4.1 Daily log — append session block
Cible : `/root/sinse-vault/daily/YYYY-MM-DD.md`

- Si fichier inexistant ce jour → créer avec frontmatter :
  ```yaml
  ---
  created: YYYY-MM-DD
  type: daily
  tags: [daily]
  ai_summary: "Sessions du YYYY-MM-DD"
  ---

  # Daily YYYY-MM-DD
  ```
- Append (à la fin du fichier) un bloc session :
  ```markdown
  ## Session N — HH:MM-HH:MM [project]

  ### Done
  - bullets

  ### Decisions
  - bullets (avec lock LXX si nouveau lock acté)

  ### Gotchas
  - bullets (omit section si vide)

  ### Commits
  - `<sha>` `[type] msg` (project-or-repo)
  ```
- Plusieurs sessions le même jour → blocs successifs ordonnés chronologiquement.

### 4.2 Hot snapshot — overwrite intégral
Cible : `/root/sinse-vault/hot.md`

- **Overwrite complet** (le fichier est par design transient, regénéré à chaque /handoff).
- Frontmatter mis à jour (`updated: YYYY-MM-DD`, `session: "Session N — résumé"`, `ai_summary` 1-2 phrases).
- Body ≤500 mots cross-projet : workspace global, réalisations clés Session N, locks accumulés (totalcount), roadmap macro 4 horizons (P0/P1/P2/P3), smoke status fin session, next session pickup pointer.
- Doit lire seul (un nouveau Claude au /pickup doit comprendre le contexte sans autre fichier).

### 4.3 Log chronological — append one-liner
Cible : `/root/sinse-vault/log.md`

Append (avant le marker `---` final) une ligne dans le bloc ` ``` ` :
```
YYYY-MM-DD HH:MM [project] One-liner what happened.
```
Newest at bottom. Append-only.

### 4.4 Inbox drafts (conditionnel)
Cible : `/root/sinse-vault/inbox/<slug>.md`

- **Si** la session a révélé :
  - Pattern récurrent (≥2 occurrences sessions distinctes), OR
  - Pattern non-trivial (≥10 min debug réel), OR
  - Pattern probably cross-projet émergent (apprentissage techno réutilisable type Svelte runes, OKLCH tokens, GlitchTip self-host, CF Tunnel+Access patterns)
  - **non encore documenté** dans `vault/knowledge/`
- → draft un fichier `inbox/<slug>.md` avec frontmatter `type: knowledge`, `status: draft`, `project: cross-project|<projet>`, `tags: [3-5 from canonical taxonomy]`, `ai_summary: "..."`. Body court = pattern + reproduction + résolution + notes.
- Sinse review mensuel et promote vers `vault/knowledge/<topic>.md` via skill `/promote`.
- **Skip filler still applies** — bar = "utile debug futur OR pattern récurrent probable", pas trivia.

Cohérent `~/.claude/projects/-root/memory/feedback_skill_routing.md` inbox draft policy.

### 4.5 Failures + gotchas consolidation (NEW v0.2.1)

Au moment du `/handoff`, scanner la section `### Gotchas` du SESSION block
just-prepended (Section 3) :

Pour chaque gotcha listé :

- **Si command verbatim error** (format `cmd | error message verbatim`) :
  → invoque `/log-failure <cmd> | <error>` (per-projet `vault/projects/<projet>/failures.md` append-only L34 strict format)
- **Si pattern atomique projet** (symptôme + solution + why) :
  → propose append à `<projet>/docs/99-runbooks/gotchas.md` format atomique §2 (cohérent `vault/meta/conventions/failure-log-and-gotchas.md`)
- **Si trivial / typo / one-shot** (skip bar = "info utile pour debug futur") :
  → skip explicit

Output récap ligne :
```
🔻 Failures+gotchas consolidation : N failures logged, M gotchas atomiques append, K skipped trivial.
```

Cohérent L33-L42 (Sinse audit mensuel humain pas auto-promote, Claude consolidate in-loop pour capture max signal post-fix L36).

## 5. Commit + push (project + vault)

### 5.1 Project (/opt/academie)
- `committer "[<type>] <message>" <files...>` pour project code
- `committer "[docs] Session handoff" <files...>` pour workspace state (SESSION.md, TODO.md, CHANGELOG.md, docs/)
- `git -C /opt/academie push origin main`

### 5.2 Vault (/root/sinse-vault)
- `git -C /root/sinse-vault add daily/ hot.md log.md inbox/ projects/*/failures.md`
- `git -C /root/sinse-vault commit -m "[handoff] Session N — <slug 5-mot project>"`
- `git -C /root/sinse-vault push origin main`

Si rien dans vault diff (cas rare, session pas trackée) → skip vault commit.

## 6. Confirmation
One-line confirmation only.

**Anti-doc-théâtre auto-check** : si Sessions N, N-1, N-2, N-3 ont **0 skill
invoqué** (`/log-failure`, `/safepoint`, `/decision`) ET **0 inbox draft créé**
→ flag dans confirmation : `⚠️ Pipeline learning asleep — escalate root cause review`.
Cohérent `~/.claude/CLAUDE.md` § SKILLS & LEARNING PIPELINE.
