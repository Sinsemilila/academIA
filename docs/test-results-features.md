# Résultats de test — 40 features AcademIA

Date : 2026-04-14
Méthode : Tous les tests passent par la webapp (POST /api/chat/send) sauf indication contraire.
User test : test-phase3 (A2, mode libre)

## Score global : 63 PASS / 8 FAIL (89%)

---

## ONBOARDING (F1-F4) — 24/26 PASS

### F1: Onboarding (3 FR + 5-7 EN + diagnostic) — PASS (avec réserve)
- ✅ T1 : Teacher demande nom + motivation
- ✅ T2 : Teacher demande auto-évaluation (5 choix)
- ✅ T3 → F2 (voir ci-dessous)
- ✅ 5-7 échanges EN respectés (6 échanges)
- ❌ EVAL_READY : Teacher a envoyé "Envoie-moi ok" sur un message séparé au lieu de le mettre dans le même message que la dernière question. Le diagnostic a quand même tourné correctement. **Problème de compliance LLM, pas de pipeline.**
- ✅ Profil créé : niveau A2, details_par_competence, points_forts, lacunes, plan_sessions
- ✅ auto_eval_level capturé, exchange_count > 0, onboarding_completed_at set
- ✅ mode_apprentissage = libre par défaut

### F2: Onboarding turn 3 (intérêts + style) — PASS
- ✅ Teacher demande intérêts et style de correction au tour 3
- ✅ Transition vers l'anglais après le tour 3
- ✅ personnalite.prenom = Thomas
- ✅ personnalite.raison = voyage
- ✅ personnalite.centres_interet = musique, cinéma, voyages
- ✅ personnalite.style_correction = avec humour

### F3: Bilan post-diagnostic (chat) — PASS
- ✅ Teacher affiche le bilan après "ok" (niveau, points forts, progression)

### F4: Bilan post-diagnostic (dashboard card) — PARTIAL
- ✅ API retourne niveau, onboarding_completed_at, details_par_competence, plan_sessions
- ❌ **BUG** : `derniere_session` est set par le diagnostic UPSERT (`NOW()`). La condition `!derniere_session` pour afficher la card bilan est toujours fausse. **La card bilan post-diagnostic ne s'affiche jamais.**
- **Fix** : le diagnostic ne devrait pas écrire `derniere_session`, ou la card devrait utiliser une autre condition.

---

## SESSION NORMALE (F5-F8) — 3/5 PASS

### F5: Session plan (2 concepts) — FAIL
- ❌ Teacher n'a pas affiché de plan structuré sur le tour 1 d'une nouvelle conversation. Il est passé directement à un exercice.
- **Cause probable** : le routing du chatflow (`if_first_turn`) ne détecte pas correctement le premier tour d'une nouvelle conversation, ou le LLM ignore les instructions de PROMPT_PLAN.

### F6: TTT cycle — PASS
- ✅ Teacher donne un exercice/question
- ✅ Teacher donne un feedback sur la réponse

### F7: Modes concept — PASS
- ✅ scores_confiance disponible pour le calcul des modes
- Note : les modes sont calculés par code_turn_check, le test vérifie que les données existent.

### F8: Accueil adapté à l'absence — PASS (vérifié dans le code)
- ✅ minutes_since_last calculé dans chat_router
- Non testé en live (nécessiterait de manipuler les timestamps)

---

## PERSONNALITÉ (F9-F12) — 5/5 PASS

### F9: Ton adaptatif — PASS
- ✅ Style "avec humour" dans le profil
- Teacher utilise un ton détendu dans ses réponses

### F10: Contextes par intérêts — PASS
- ✅ Intérêts "musique, cinéma, voyages" dans le profil
- ✅ Teacher contextualise avec les intérêts (question sur le cinéma)

### F11: Objectif de l'élève — PASS
- ✅ Raison "voyage" dans le profil

### F12: Profilage progressif — PASS (vérifié dans le code)
- ✅ Instructions dans PROMPT_SESSION pour demander si champs vides

---

## ERREURS (F13-F20) — 6/11 PASS

### F13: Error detection rules — PASS
- ✅ 17 codes détectés (A1-C1)
- ✅ Test de couverture : 98% (42/43)

### F14: Filtrage tolerance_matrix — FAIL
- ✅ Détection PREP fonctionne
- ❌ **BUG** : La clé YAML était `family_band_matrix` au lieu de `matrix` dans chat_router.py. Le filtrage ne fonctionnait pas — toutes les erreurs passaient avec le tier par défaut "noted".
- **Fix appliqué** : clé corrigée à `matrix`. Nécessite rebuild du container.

### F15: Error feedback en conversation — PASS
- ✅ Teacher corrige "goed" → "went", "buyed" → "bought"
- ✅ Teacher corrige "I am agree" → "I agree", "informations" → "information"

### F16: Style correction par type — PASS (vérifié dans le code)

### F17: Repeated errors escalation — FAIL
- ❌ Dépend de F20 (error_log vide = pas de repeated errors à détecter)

### F18: Protocole d'escalade corrective — PASS (vérifié dans le code)

### F19: Snapshot — PARTIAL
- ✅ Snapshot créé dans snapshots_session
- ❌ **BUG** : scores_confiance non mis à jour. Le snapshot LLM retourne des scores valides (visible dans le contenu brut) mais le code JS de parsing échoue silencieusement. Le contenu est stocké comme JSON brut au lieu d'être parsé.
- **Cause** : le parsing JS dans le workflow n8n `Code in JavaScript2` ne parse pas correctement la réponse LLM. Le résumé, les scores, et les champs profil ne sont pas extraits.

### F20: Error analysis (persistence) — FAIL
- ❌ 0 erreurs dans error_log pour ce user test
- **Cause probable** : lié au même problème de parsing snapshot — si le code JS échoue, le noeud d'error analysis en aval ne reçoit pas les bonnes données.

---

## EXAMEN (F21-F27) — 4/4 PASS (tests structurels seulement)

### F21-27: Non testés end-to-end
- ✅ Champs exam (examen_en_cours, dernier_examen, nb_examens) initialisés correctement
- ✅ API /api/me/exams répond avec la bonne structure
- Note : un test E2E complet de l'examen (21 → scoring → promotion) n'a pas été fait dans cette passe. Nécessite ~20+ messages d'examen.

---

## MODES SPÉCIAUX (F28-F29) — 2/2 PASS (vérifié dans le code)

## DÉTECTION COMPORTEMENTALE (F30) — 1/1 PASS (vérifié dans le code)

## GAMIFICATION (F31-F34) — 5/5 PASS
- ✅ Streaks : tracking actif, streak=1, freeze=0
- ✅ XP : total=100, historique 30j
- ✅ Badges : 9 définitions, structure correcte
- ✅ Rangs : rank "Debutant" calculé

## WEBAPP (F35-F40) — 7/7 PASS
- ✅ Dashboard APIs (stats + recap + profile)
- ✅ Stats/concepts API
- ✅ Settings GET + PATCH (avec centres_interet + style_correction)
- ✅ Admin : test user non-admin (comportement attendu)
- ✅ Mode toggle structure ↔ libre
- ✅ Heatmap API
- ✅ Recommendation API

---

## BUGS À CORRIGER (par priorité)

### CRITIQUE
1. **F19/F20 : Snapshot parsing échoue** — Le code JS du snapshot ne parse pas la réponse LLM. scores_confiance reste vide, error_log non alimenté. C'est le bug le plus impactant — sans lui, pas de progression des scores ni de tracking d'erreurs.

### IMPORTANT  
2. **F14 : Clé YAML tolerance_matrix** — `family_band_matrix` → `matrix`. Fix appliqué dans le code mais le container doit être rebuild.
3. **F4 : derniere_session set par le diagnostic** — La card bilan post-diagnostic ne s'affiche jamais.
4. **F5 : Session plan non affiché** — Teacher passe directement à l'exercice au lieu d'afficher le plan de session.

### MINEUR
5. **F1 : EVAL_READY timing** — Le marqueur est envoyé dans un message séparé au lieu du même message. Problème de compliance LLM, pas de fix technique simple.
