# Refactor Workflow — Académie-IA — v1.0

> **Status** : ✅ Plan stabilisé en v1.0 (2026-04-12)
> **Source historique complète** : `projects/academie-ia/archive/refactor-workflow-2026-04-12/REFACTOR-PLAN-working.md`

---

## Quoi ?

Refactor complet du **socle workflow/workspace** inspiré par Peter Steinberger, adapté à la stack Académie-IA (Dify + n8n + Postgres + FastAPI + SvelteKit sur Proxmox).

## Pourquoi ?

**État avant le refactor** :
- Pas de filet de sécurité (backups limités à git)
- Pas de multi-IA opérationnel (Claude seul, Gemini/Codex prévus sans infra)
- Pas d'outillage workflow (aucun slash command custom, aucun CLI maison, aucun dashboard)
- Documentation monolithique (CLAUDE.md 500+ lignes dupliqué entre workspace et projet)
- Pas de mode YOLO sécurisé
- Protocoles début/fin recopiés manuellement dans chaque HANDOFF

## Objectifs v1.0

- ✅ **Backup 4-niveaux** robuste avec test de restore validé
- ✅ **Multi-IA collaboratif** (Claude + Gemini + futur Codex) via worktrees + arbiter cross-review
- ✅ **Mode YOLO** (`--dangerously-skip-permissions`) sécurisé
- ✅ **Slash commands réutilisables** remplaçant les protocoles recopiés
- ✅ **Documentation scalable** (AGENTS.md court + `docs/` détaillés avec `read_when:`)
- ✅ **Observability minimale** (smoke-test + dashboard + destructive-ops protocol)
- ✅ **Auto-merge Option E** — 12 types de commit + fichiers protégés + arbiter

---

## Les 8 règles d'or (à ne jamais violer)

1. **Backup avant tout** — zéro changement structurel tant que le test de restore n'est pas validé
2. **Prod intouchable** — academie.petit-pont.com doit continuer à fonctionner pendant tout le refactor
3. **Code produit intact** — on refactore l'infrastructure AUTOUR du code, pas le code lui-même
4. **Tester chaque brique avant la suivante** — valider worktree claude avant de créer worktree gemini
5. **Documenter les décisions en temps réel**
6. **Aucun changement destructif sans confirmation explicite** de Sinse, même en YOLO
7. **Plan v1.0 avant exécution. Une fois lancé, pas d'arrêt.** Mesure deux fois, coupe une fois
8. **Séparation stricte LLM workflow vs LLM projet** — abonnements personnels = workflow, LiteLLM = projet

---

## Navigation dans la doc

### Lecture priority — première session

1. **Ce README** (5 min)
2. **`architecture.md`** (10 min) — vue AVANT/APRÈS pour comprendre le big picture
3. **Le fichier de la session que tu démarres** (`sessions/s1-securisation.md` pour la première)

### Pour chercher un détail spécifique

| Tu cherches | Fichier |
|-------------|---------|
| Pourquoi on a choisi X ? | `decisions.md` |
| À quoi sert un bash tool ? | `reference/tools.md` |
| Quel est le contenu exact de `/pickup` ? | `reference/slash-commands.md` |
| Ce fichier est-il protégé pour le merge ? | `reference/file-protection.md` |
| Comment restaurer en cas de catastrophe ? | `reference/disaster-recovery.md` |
| Que mettre dans AGENTS.md ? | `reference/workflow-rules.md` |
| Quelle session vient après S1 ? | `sessions/s2-refactor-archi.md` |
| Comment documenter pour le portfolio ? | `sessions/s5-documentation-portfolio.md` |

---

## Status v1.0

| Phase | Statut | Livrable |
|-------|--------|----------|
| **Plan** | ✅ Stabilisé v1.0 | Ce dossier `refactor-v1.0/` |
| **Session 1 — Sécurisation** | 🟡 Prête à lancer | Backup 4 niveaux + test restore + smoke-test |
| **Session 2 — Refactor archi** | ⏳ Dépend S1 | Worktrees + AGENTS.md + slash commands + YOLO |
| **Session 3 — Multi-IA réel** | ⏳ Dépend S2 | Arbiter + dashboard + premier Gemini |
| **Session 4 — Polish** | ⏳ Optionnelle | CLI-fication + tests auto + hooks |
| **Session 5 — Documentation Portfolio** | ⏳ Dépend S1-S3 | README pro EN/FR + docs archi + decisions + GitHub Profile + demo |

---

## Les 36 décisions (D1-D36)

Toutes documentées dans `decisions.md`. Résumé ultra-court :

- **D1-D7** : Fondations (backup strategy, multi-IA model, sessions sequencing, WSL client, contexte files refactored, Proxmox SSH, Opus budget)
- **D8-D16** : Bloc 1 Fondation doc (pointer pattern, structure workspace, style telegraph EN, AGENTS.md content, native memory policy, docs granularity)
- **D17-D19** : Bloc 2 Organisation multi-IA fichiers (TODO CLAIMED, HANDOFF per IA, CHANGELOG format + log tool)
- **D20-D21** : Bloc 3 Outils (lock file suppression, profil_manager out of scope)
- **D22-D32** : Bloc 4 CI + Option E (Niveau 2, smoke-test, healthchecks, gitleaks, hooks, 12 commit types, arbiter, workflow/project separation, protected files, thresholds, MERGE-REQUEST)
- **D33** : Bloc 5 Slash commands (/pickup + /handoff content + P2 placement)
- **D34** : Bloc 6 Tags deploy + rollback-to
- **D35** : Bloc 7 Native memory + subagents policy
- **D36** : Audit redondances adjustments (context files rules, cly full version, archive temps)
- **D37** : Gaps pre-v1.0 (10 items : passphrase restic, multi-file structure, init-worktree, dispatch docs, DR scenarios, secrets list, git hooks per repo, checkpoints, sinse quickstart, audit-todo académie)

---

## Prochaine action

**Lancer Session 1 — Sécurisation**

→ Ouvrir : `sessions/s1-securisation.md`
→ Suivre la checklist dans l'ordre
→ Ne pas passer à S2 avant validation complète S1 (critères dans le fichier)

**Avant de lancer** :
- S'assurer d'avoir 3-4h de concentration dispo
- S'assurer d'avoir l'accès SSH Proxmox (D6)
- S'assurer d'avoir le compte Google Drive prêt (D1 niveau 3)
- Full Opus 4.6 1M disponible (D7)
