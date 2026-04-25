# Session 3 — Multi-IA réel (arbiter + Gemini + dashboard)

> **Durée estimée** : 3h
> **Statut** : ⏳ Dépend de S2 validée
> **Livrable** : arbiter fonctionnel + premier worktree Gemini + dashboard status + AUDIT-TODO académie-IA créé

---

## Objectif

Activer le vrai multi-IA : tester l'arbiter avec un cross-review Claude ↔ Gemini, créer le worktree Gemini, implémenter le dashboard `make status`, et préparer l'AUDIT-TODO pour le projet academie-IA post-refactor.

À la fin de cette session :
- ✅ Arbiter testé en réel (Claude → Gemini et Gemini → Claude)
- ✅ Worktree Gemini créé et fonctionnel
- ✅ Dashboard `status` opérationnel
- ✅ Healthchecks Docker existants renforcés/vérifiés
- ✅ Premier test merge-to-main avec chaque outcome (AUTO / ARBITER / HUMAN)
- ✅ Squelette `AUDIT-TODO.md` pour académie-IA créé

---

## Prérequis

- [ ] **Session 2 complètement validée** (12 critères)
- [ ] YOLO mode actif via cly
- [ ] 15 bash tools fonctionnels
- [ ] Premier `/pickup` et `/handoff` réussis en S2

---

## Checklist

### S3.0 — Préparation (5 min)

- [ ] Checkpoint : `echo "SESSION=S3\nSTEP=S3.0" > /root/.session-progress`
- [ ] `smoke-test --all` → tous verts
- [ ] Backup manuel de sécurité : `/root/sinse-workspace/tools/restic-backup`

### S3.1 — Slash commands collaboration (30 min)

Les slash commands `/pickup` et `/handoff` existent déjà (S2). On teste maintenant qu'ils fonctionnent vraiment avec les patterns de collaboration :

- [ ] Test `/pickup` sur un worktree frais → doit afficher summary en 5 lignes
- [ ] Test `/handoff` sur un changement mineur `[docs]` → doit auto-merger
- [ ] Vérifier qu'un tag `deploy-YYYY-MM-DD-HHMM` a été créé
- [ ] Test d'un commit `[feat]` → doit passer par l'arbiter (voir S3.2)

### S3.2 — Test arbiter en conditions réelles (45 min)

#### S3.2.1 — Test `arbiter` directement

- [ ] Créer un fake commit `[feat]` dans le worktree claude (change un fichier webapp non critique)
- [ ] Lancer manuellement : `arbiter --branch claude --type feat`
- [ ] Vérifier que l'arbiter utilise `gemini -p` (cross-review)
- [ ] Vérifier le format de sortie : `DECISION: GO/NO-GO` + `REASON:`
- [ ] Tester avec un vrai petit refactor → decision GO attendu
- [ ] Tester avec un changement bizarre (commenter une ligne critique) → decision NO-GO attendu ?

#### S3.2.2 — Intégration arbiter dans merge-to-main

- [ ] Vérifier que `merge-to-main` appelle bien arbiter pour les types appropriés (feat, hotfix, fix/refactor/perf majeurs)
- [ ] Test full workflow : commit [feat] + `/handoff` → merge-to-main → arbiter → (selon résultat) merge ou MERGE-REQUEST
- [ ] Tester le cas MERGE-REQUEST créée : `ls projects/academie-ia/merge-requests/`
- [ ] Tester `merge-approve claude` → merge vers main + tag deploy
- [ ] Tester `merge-reject claude --reason "test"` → déplacement dans archive

### S3.3 — Dashboard `status` (30 min)

Le stub a été créé en S2. On l'implémente proprement maintenant.

- [ ] Implémenter `status` bash tool :
  - État des worktrees (branch, commits ahead of main, last commit time)
  - État des containers prod (`docker ps` filtered)
  - État des backups (last Proxmox snapshot, last PG dump, last Restic backup)
  - Count des MERGE-REQUEST pending
  - CLAIMED tasks par IA (depuis TODO.md)
- [ ] Output en français (exception D13, pour lisibilité humaine)
- [ ] Test : `status` → doit afficher un tableau synthétique en 1 écran
- [ ] Alias shell : `alias s='status'` (optionnel)

### S3.4 — Healthchecks Docker (20 min)

D24 a dit : pas de modification des healthchecks Docker, le smoke-test fait tout. On vérifie que tous les `docker exec` et `curl` fonctionnent :

- [ ] `docker exec postgres-academie pg_isready -U sinse` → OK
- [ ] `docker exec redis-academie redis-cli ping` → PONG
- [ ] `curl -s http://localhost:5001/console/api/workspaces -H "Authorization: Bearer $(cat /opt/academie-shared/secrets/dify-admin-key)"` → 200/401
- [ ] `curl -s http://localhost:5678/healthz` → 200
- [ ] `curl -s http://localhost:4000/health` → JSON valide
- [ ] Les healthchecks natifs existants (`academie-api`, `academie-frontend`) : `docker inspect | grep -A5 Health`
- [ ] Si un check fail, debug et fix dans `smoke-test --deep`

### S3.5 — Création worktree Gemini (30 min)

#### S3.5.1 — Pré-requis Gemini CLI

- [ ] Vérifier Gemini CLI : `gemini --version` → v0.36.0 ou plus récent
- [ ] Vérifier authentification : `gemini auth status` (ou équivalent)
- [ ] Test one-shot : `gemini -p "Say hello in French"` → doit retourner une réponse

#### S3.5.2 — Création worktree

- [ ] Créer la branche gemini : `cd /opt/academie && git branch gemini`
- [ ] Créer le worktree : `init-worktree gemini`
- [ ] Vérifier la structure : `ls -la /opt/academie-worktrees/gemini/`
- [ ] Vérifier le fichier `.agent` : `cat /opt/academie-worktrees/gemini/.agent` → "gemini"
- [ ] Vérifier le pointer AGENTS.md

#### S3.5.3 — Premier test Gemini dans son worktree

- [ ] `cd /opt/academie-worktrees/gemini && gemini`
- [ ] Dans Gemini, taper `/pickup`
- [ ] Vérifier que Gemini lit correctement :
  - `/root/sinse-workspace/AGENTS.md`
  - `PROJECT.md`
  - `HANDOFF-gemini.md` (absent → première session)
  - `TODO.md` (liste OPEN tasks)
- [ ] Demander à Gemini de faire un petit changement `[docs]` (ex: ajouter une ligne à un README projet)
- [ ] Test `/handoff` depuis Gemini → doit auto-merger `[docs]` directement

### S3.6 — Test cross-review arbiter en situation réelle (30 min)

- [ ] Dans le worktree claude, faire un commit `[feat]` non-trivial
- [ ] Lancer `/handoff` → merge-to-main → arbiter
- [ ] L'arbiter appelle **gemini** pour reviewer le commit de **claude**
- [ ] Vérifier :
  - Les tokens sont consommés depuis l'abonnement Gemini Advanced de Sinse (pas d'API key)
  - La décision est retournée proprement
  - Le format de sortie est parsable
- [ ] Inverse : dans le worktree gemini, commit `[feat]` → `/handoff` → arbiter appelle **claude**
- [ ] Vérifier les tokens Claude Pro/Max

### S3.7 — Squelette AUDIT-TODO académie-IA (D37 G10, 15 min)

- [ ] Créer `/root/sinse-workspace/projects/academie-ia/AUDIT-TODO.md`
- [ ] Contenu : les 9 points de D21 en checklist
  1. [ ] Scripts `/opt/academie/scripts/` : CLI-fier ? déplacer ? grouper sous `tools/` projet ?
  2. [ ] `/opt/academie/CLAUDE.md` : confirmer suppression (remplacé par pointer vers AGENTS.md + PROJECT.md)
  3. [ ] `/opt/academie/.claude/` : adapter (settings, commands, hooks)
  4. [ ] `/opt/academie/.gemini/` : idem
  5. [ ] Symlinks : `/opt/academie/context` → adapter selon nouvelle structure
  6. [ ] `/opt/academie/curriculums/` : organiser ?
  7. [ ] `/opt/academie/api/`, `/opt/academie/webapp/` : référencer depuis `docs/`
  8. [ ] Fichiers d'accès (`.dify_admin_key`) : déplacer dans secrets partagés ?
  9. [ ] Worktrees academie : créer structure `/opt/academie-worktrees/{claude,gemini}/`
- [ ] Ajouter note "À traiter post-refactor workflow, priorité normale"
- [ ] Commit : `committer "[docs] Create AUDIT-TODO for academie-ia (D21, D37 G10)" AUDIT-TODO.md`

### S3.8 — Validation finale session (10 min)

- [ ] `status` → affiche tout proprement
- [ ] `smoke-test --all` → tous verts
- [ ] Les 2 worktrees claude + gemini fonctionnent
- [ ] L'arbiter a été testé dans les deux sens (claude → gemini et gemini → claude)
- [ ] Un premier merge auto + un premier merge via arbiter ont été réalisés
- [ ] Un premier test MERGE-REQUEST humaine + merge-approve a été réalisé
- [ ] **Supprimer** `/root/.session-progress`

---

## ✅ Critères de validation Session 3

1. ✅ Worktree Gemini opérationnel + premier `/pickup` réussi
2. ✅ Arbiter testé en conditions réelles (claude → gemini ET gemini → claude)
3. ✅ Dashboard `status` affiche un état complet
4. ✅ Tous les healthchecks via smoke-test passent
5. ✅ Au moins 1 merge AUTO_MERGE (type `[docs]` ou `[chore]`)
6. ✅ Au moins 1 merge ARBITER (type `[feat]` ou `[refactor]` majeur)
7. ✅ Au moins 1 MERGE-REQUEST + merge-approve testé
8. ✅ `AUDIT-TODO.md` académie-IA créé avec les 9 points D21
9. ✅ Multi-IA fonctionnel en parallèle (claude + gemini simultanés possibles)

---

## 🚨 Troubleshooting

### Gemini CLI ne trouve pas l'abonnement
- Vérifier l'auth : `gemini auth status`
- Relogger : `gemini auth login`

### Arbiter retourne un NO-GO non justifié
- Afficher le prompt envoyé : `arbiter --branch claude --type feat --verbose`
- Ajuster le prompt template si nécessaire dans `/root/sinse-workspace/tools/arbiter`

### merge-to-main ne crée pas de tag deploy
- Vérifier la logique git tag dans le tool
- Test manuel : `git tag test-deploy-$(date +%Y%m%d) && git tag --list | tail`

### Cross-review consomme trop de tokens abonnement
- Limiter le contexte envoyé à l'arbiter (juste le diff + 1 fichier de contexte)
- Ou : passer temporairement à `claude -p` pour économiser Gemini Advanced

---

## Prochaine session (optionnelle)

→ **`sessions/s4-polish-optional.md`** — Polish (CLI-fication + tests auto + hooks avancés)

Ou bien : **démarrer la Phase Post-Refactor** (audit académie-IA + features MVP v2).
