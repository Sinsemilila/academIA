# Session 4 — Polish (optionnelle)

> **Durée estimée** : 2h
> **Statut** : ⏳ Optionnelle (peut être sautée ou faite plus tard)
> **Livrable** : CLI-fication scripts + tests automatisés minimum + monitoring léger

---

## Objectif

Améliorations optionnelles du socle une fois que S1-S3 sont stables. **Peut être sautée** si on préfère passer directement aux features MVP v2 après S3. Sera probablement faite en même temps que l'audit académie-IA post-refactor.

---

## Prérequis

- [ ] Sessions S1, S2, S3 complètement validées
- [ ] Quelques jours d'utilisation réelle du nouveau workflow (pour identifier ce qui manque vraiment)
- [ ] 2h dispo

---

## Checklist (optionnelle, pas d'ordre strict)

### S4.1 — CLI-fication des scripts académie-IA (30 min)

Hors scope strict du refactor workflow (D21), mais peut être fait ici si on veut unifier :

- [ ] Convertir `/opt/academie/scripts/profil_manager.py` en CLI typer :
  ```python
  import typer
  app = typer.Typer()

  @app.command()
  def get(user: str, domain: str = "anglais"):
      """Récupère le profil d'un élève."""
      ...

  @app.command()
  def update(user: str, field: str, value: str):
      """Met à jour un champ du profil."""
      ...
  ```
- [ ] Convertir `update_teacher_chatflow.py` en CLI typer avec sous-commandes (`deploy`, `backup`, `rollback`)
- [ ] Créer aliases shell : `profil-manager`, `teacher-deploy`

### S4.2 — Tests automatisés minimum (45 min)

- [ ] Test bout en bout webapp :
  ```bash
  # Login test user → dashboard → envoyer message → check stats
  ```
- [ ] Test API FastAPI (endpoints critiques) :
  - POST /api/auth/login
  - GET /api/me/concepts
  - GET /api/me/streaks
- [ ] Test pipeline Teacher :
  - Envoyer une question au chatflow
  - Vérifier que la réponse a le format ❌✅💡
  - Vérifier le count des nœuds (28)
- [ ] Intégrer dans `smoke-test --deep` si concluant

### S4.3 — Monitoring léger (30 min)

- [ ] Alertes backup échoué :
  - Modifier `pg-backup` et `restic-backup` pour envoyer un message (email/Telegram/file marker) en cas de fail
- [ ] Alertes container down :
  - Cron toutes les 15 min : `smoke-test --quick --quiet || <notify>`
- [ ] Monitoring Postgres basique :
  - Query pour disk usage
  - Query pour slow queries (> 1s) si pg_stat_statements installé

### S4.4 — Hooks avancés (15 min)

- [ ] Pre-commit hook supplémentaire : `detect-secrets` en plus de gitleaks (double couche anti-secrets)
- [ ] Post-commit hook : ajouter automatiquement au CHANGELOG via `log` (si pas déjà fait par le slash command)
- [ ] Hook qui check la cohérence des fichiers CLAIMED dans TODO.md avant merge

### S4.5 — Documentation complémentaire (optionnel)

- [ ] `docs/git-workflow.md` : workflow git détaillé pour les nouveaux arrivants
- [ ] `docs/multi-ia-collaboration.md` : comment Claude, Gemini, Codex cohabitent
- [ ] `docs/troubleshooting.md` : problèmes communs + solutions

---

## Quand faire cette session ?

**Options** :

### Option A — Tout de suite après S3
Avantage : refactor complètement terminé d'un coup
Inconvénient : peut-être pas nécessaire tout de suite

### Option B — Après quelques semaines d'utilisation
Avantage : on sait ce qui manque vraiment
Inconvénient : le contexte se dilue

### Option C — Jamais (skip complètement)
Avantage : on passe direct aux features MVP v2 (admin page, XP triggers, flashcards)
Inconvénient : on ne fait pas de tests automatisés

**Recommandation** : **Option B** — attendre d'utiliser le nouveau workflow quelques semaines, identifier les vrais manques, puis faire S4 avec des priorités claires basées sur l'expérience réelle.

---

## Pas de critères de validation stricts

Cette session est optionnelle et à la carte. On pioche dans les sections ce qui semble le plus utile au moment où on la fait.
