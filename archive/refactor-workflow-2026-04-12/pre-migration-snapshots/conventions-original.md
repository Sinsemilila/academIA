# Conventions — Workspace Sinse

## Règle fondamentale
Ce repo est la mémoire partagée entre toutes les IA travaillant avec Sinse.
Chaque IA lit ces fichiers au démarrage et les met à jour en fin de session.

## Fichiers et leur rôle
- conventions.md : ce fichier — règles immuables, ne jamais modifier sans validation humaine
- STATE.md : état exact du projet actif à l'instant T — toujours à jour
- TODO.md : tâches actives, priorités, blocages
- HANDOFF.md : message de transition entre sessions ou entre IA
- DECISIONS.md : log append-only des décisions importantes
- CHANGELOG.md : log append-only des features et tâches complétées

## Système de lock et branches

### Fichier lock
- Emplacement : /root/sinse-workspace/.lock
- Format : une ligne par IA active → `nom_ia:timestamp_unix`
- Exemple : `claude:1743854400`
- **NON tracké en git** (.gitignore) — évite conflits de merge et commits parasites
- Géré manuellement par chaque IA en début/fin de session

### Règle des branches
- Chaque IA travaille sur sa propre branche git : `claude`, `gemini`, etc.
- Jamais de commit direct sur `main`
- Le merge vers `main` se fait manuellement avec confirmation humaine

### Gestion des locks périmés
- Si une entrée dans .lock a plus de 24h, elle est considérée comme morte (crash)
- L'IA suivante peut la supprimer au démarrage

## Protocole de début de session (OBLIGATOIRE)
L'IA DOIT faire dans cet ordre :
1. `git fetch origin && git merge origin/main` — synchroniser avec le travail des autres IA
   → Si conflit : résoudre en gardant le meilleur des deux versions, puis continuer
2. Lire conventions.md
3. Lire STATE.md et TODO.md
4. Lire CHANGELOG.md — **vérifier que le TODO est cohérent avec le CHANGELOG**
   → Si une tâche du TODO est présente dans le CHANGELOG → la marquer [x] dans TODO
5. Ajouter son entrée dans .lock : `echo "nom_ia:$(date +%s)" >> .lock`
6. Confirmer à Sinse : "J'ai lu le contexte. Voici où on en est : [résumé en 3 lignes]"

## Protocole de fin de session (OBLIGATOIRE)
L'IA DOIT faire dans cet ordre :
1. Mettre à jour STATE.md avec ce qui a changé
2. Mettre à jour TODO.md (retirer complété, ajouter découvert)
3. Ajouter dans CHANGELOG.md si feature complétée — **vérifier d'abord l'absence de doublon**
4. Ajouter dans DECISIONS.md si décision importante — **vérifier d'abord l'absence de doublon**
5. Écrire HANDOFF.md **après avoir relu CHANGELOG.md en entier**
   → Le HANDOFF doit refléter TOUT le travail du jour (pas seulement la session en cours)
   → Ne jamais écrire "à faire" pour quelque chose déjà dans le CHANGELOG
6. Retirer son entrée du .lock
7. `git add -A && git commit -m "[NOM_IA] [DATE] — résumé en une ligne" && git push origin [branche]`
8. Puis /exit

## Règles CHANGELOG et DECISIONS (append-only)
- **Ne jamais supprimer** de contenu dans DECISIONS.md et CHANGELOG.md
- Si une entrée est fausse ou dupliquée → ajouter une ligne `[CORRECTION]` à la suite
- Format correction : `[DATE] [IA] — [CORRECTION] description du problème corrigé`

## Format DECISIONS.md
[DATE] [IA] — [décision] — [raison]
Exemple : 2026-04-05 Claude — Abandon API Flask au profit de n8n — déjà prévu roadmap

## Format CHANGELOG.md
[DATE] [IA] — [ce qui a été fait]
Exemple : 2026-04-05 Claude — Installation Claude Code sur VM cosmos

## Règles générales
- Ne jamais supprimer de contenu dans DECISIONS.md et CHANGELOG.md
- Toujours faire `git fetch origin && git merge origin/main` avant de commencer
- Toujours faire `git push origin [branche]` avant de terminer
- Si conflit git : résoudre en gardant le meilleur des deux, documenter la résolution
- Langue : français
