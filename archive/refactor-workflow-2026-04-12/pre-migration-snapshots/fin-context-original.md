---
description: Protocole de fermeture — met à jour la doc et commit/push git
---

Protocole de fermeture. Exécute sans commenter chaque étape, juste fais-le :

1. Mets à jour **STATE.md**, **TODO.md**, **CHANGELOG.md**, **HANDOFF.md** dans `/root/sinse-workspace/context/` pour refléter l'état réel après cette session. Si une décision importante a été prise, ajoute-la dans **DECISIONS.md**.

2. Commit et push :
```
cd /root/sinse-workspace && git add -A && git commit -m "[Claude] $(date +%Y-%m-%d) — résumé en une ligne" && git push origin claude
```

3. Confirme avec une seule ligne : "✅ Pushé. Session fermée proprement."

Ne génère pas de rapport de session. Ne liste pas ce que tu as fait étape par étape. Juste : mettre à jour, committer, confirmer.
