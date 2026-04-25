# Académie-IA — Document de référence Claude Code

## Documentation & Contexte (Source de Vérité)
Ces fichiers sont situés dans le repo de contexte et doivent être consultés/mis à jour à chaque session :
- **Dossier Contexte :** `/root/sinse-workspace/context/`
- **État du projet :** `/root/sinse-workspace/context/STATE.md`
- **Tâches (TODO) :** `/root/sinse-workspace/context/TODO.md`
- **Historique (CHANGELOG) :** `/root/sinse-workspace/context/CHANGELOG.md`
- **Décisions :** `/root/sinse-workspace/context/DECISIONS.md`
- **Handoff :** `/root/sinse-workspace/context/HANDOFF.md`
- **Conventions :** `/root/sinse-workspace/context/conventions.md`

## Contexte du projet
Plateforme d'apprentissage de langues et domaines techniques augmentée par IA.
Auto-hébergée sur Proxmox/Debian, orchestrée par Docker et Dify.
Développeur solo : Sinse (sinseproduction@gmail.com)

## Architecture infrastructure

### Accès public
- NAS avec Proxmox → VM Debian (cosmos) → Docker
- Cloudflare Tunnel : academie.petit-pont.com
- Cosmos Cloud : reverse proxy + pare-feu (cosmos.petit-pont.com)
- Proxmox UI : pve.petit-pont.com

### Stack Docker (tous sur academie-net-bridge)
- **dify-web** (port 3000) — interface élève
- **dify-api** (port 5001) — backend
- **dify-worker** — tâches async Celery
- **dify-plugin-daemon** — stable depuis 04/04/2026
- **litellm-proxy** (port 4000) — gateway LLM
- **postgres-academie** (172.16.0.25:5432) — DB principale
- **redis-academie** — cache + broker
- **cosmos-server** — reverse proxy
- **n8n-academie** (port 5678, interne uniquement) — orchestrateur workflows
- Qdrant : SUPPRIMÉ
- Ollama : SUPPRIMÉ

### Fichiers clés
- LiteLLM config : /opt/litellm/config.yaml
- Scripts : /opt/academie/scripts/
- n8n data : /opt/n8n/data/
- n8n clé chiffrement : /opt/n8n/encryption.key
- profil_manager.py : lecture/écriture profils élèves PostgreSQL

## Base de données PostgreSQL
- Host : 172.16.0.25 (depuis l'hôte) / postgres-academie (depuis Docker)
- Port : 5432
- DB : academie_db
- User : sinse
- Password : [REDACTED — see /opt/academie-shared/secrets/]

### Tables créées
- eleves (id, username, created_at)
- profils_eleves (eleve_id, domaine, niveau_global, personnalite JSONB, scores_confiance JSONB, points_forts, lacunes, plan_sessions, derniere_session)
- snapshots_session (eleve_id, domaine, contenu, created_at)
- historique_sessions (eleve_id, domaine, resume_session, date_session)

## Pool LLM (LiteLLM)

### Modèles configurés (owner: sinse)
- gpt-4o-mini — OpenAI, payant — support CJK ✅
- groq-snapshot — Llama 3.1 8B, gratuit — snapshots session — support CJK ❌
- groq-standard — Llama 3.3 70B, gratuit — sessions courantes — support CJK ❌
- groq-qwen — Qwen 32B, gratuit — raisonnement + japonais — support CJK ✅
- mistral-small — Mistral Small, gratuit — support CJK ✅

### Règle de routage
- Sessions normales → groq-standard (fallback : mistral-small)
- Snapshots → groq-snapshot (Llama 8B, ultra rapide — fallback : mistral-small)
- Japonais / CJK → groq-qwen (fallback : mistral-small) — NE PAS utiliser groq-standard/snapshot
- Tâches complexes (examens, évaluations) → gpt-4o-mini (payant)
- Utilisateurs futurs : ajouter leurs clés dans /opt/litellm/config.yaml avec owner et tier

## Agents Dify configurés
- Teacher — Professeur d'anglais (principal, system prompt v2 complet)
- Maestro — Professeur d'espagnol
- Sensei — Professeur de japonais
- Lehrer — Professeur d'allemand
- Professore — Professeur d'italien
- PyMentor — Professeur de Python
- CyberMentor — Professeur de cybersécurité

### Modèle actif Teacher
- groq-standard (Llama 3.3 70B)
- Type : Chatflow (advanced-chat), app ID : 39565197-c9d1-4d5b-b66f-18925de236d9
- Nœud HTTP Request au démarrage → dify-profil-get → profil injecté via Jinja2 dans system prompt
- sys.user_id = UUID Dify du compte connecté (ex: 01225ee1... = sinse)

## Système de mémoire à deux niveaux

### Niveau 1 — Session (court terme)
Toutes les 10 interactions, groq-snapshot génère un résumé glissant.
Chaque snapshot intègre le précédent (chaîne cohérente).
Stocké dans snapshots_session.
À brancher : webhook dify-snapshot déclenché depuis Teacher.

### Niveau 2 — Long terme (entre sessions)
Profil pédagogique complet dans profils_eleves.
Injecté automatiquement via n8n (dify-profil-get) au démarrage de session Teacher.
Mis à jour en fin de session via dify-profil-update (à brancher).

### Identifiants élèves en DB
- sinse (id=1) : username "sinse", profil anglais C1 (test)
- UUID f3c0dab9... (id=4) : UUID Dify preview, profil anglais C1 (copié)
- UUID 01225ee1... (id=7) : UUID Dify compte sinse (production), profil anglais C1

## Stratégie pédagogique

### Curriculum
- Pas de RAG sur livres commerciaux
- Curriculum généré par Claude Sonnet (abonnement Pro Sinse)
- Stocké dans PostgreSQL
- Taxonomie définie par domaine avant génération

### Taxonomie anglais A1→C2 (définie)
- A1 : Survie — phrases correctes, salutations, questions simples
- A2 : Quotidien — présent simple/continu, passé, modaux de base
- B1 : Autonomie — present perfect, passif, conditionnels 1&2, phrasal verbs
- B2 : Aisance — conditionnel 3, mixed conditionals, modaux déduction, registres
- C1 : Maîtrise — idiomes, nominalisation, pragmatique, dialectes
- C2 : Excellence — registres multiples, rhétorique, indistinguable natif

### Autres domaines (taxonomie à définir)
- Espagnol, japonais, allemand, italien : CECRL A1→C2
- Python : capacités concrètes
- Cybersécurité : Débutant→Praticien→Expert
- Comptabilité, musique : à définir

## Features MVP v2

1. Onboarding en 3 temps (personnalisation → test adaptatif → synthèse)
2. Exercices génératifs contextualisés
3. Scores de confiance par concept (0-100 dans PostgreSQL)
4. Mode examen automatique (IA payante)
5. Détection de régression
6. Dashboard WebApp Dify (bouton "revoir mes lacunes")
7. Mode flashcard / révision espacée
8. Sensei personnalisable + adaptatif (personnalité fixe + humeur dynamique)
9. Rapport hebdomadaire personnel (élève uniquement, via n8n)
10. Mode "revoir mes lacunes" (déclenché manuellement par l'élève)

## n8n Workflows (http://127.0.0.1:5678)

| Workflow | Méthode | URL interne | Rôle |
|---|---|---|---|
| dify-profil-get | GET | http://n8n-academie:5678/webhook/dify-profil-get?username=X&domaine=Y | Retourne profil + dernier snapshot |
| dify-snapshot | POST | http://n8n-academie:5678/webhook/dify-snapshot | Résumé IA session → snapshots_session |
| dify-profil-update | POST | http://n8n-academie:5678/webhook/dify-profil-update | Mise à jour profils_eleves |

- Accès UI n8n : ssh -L 5678:127.0.0.1:5678 cosmos → http://localhost:5678
- dify-snapshot : Webhook → Code → LiteLLM (groq-snapshot) → Code → Postgres
- dify-profil-get : crée automatiquement l'élève si inconnu (ON CONFLICT DO NOTHING)

## Roadmap

- Phase 1 & 2 : ✓ Complètes (infra + stockage)
- Phase 3 : ✓ Complète — Teacher Chatflow opérationnel, onboarding validé
- Phase 4 : ✓ Complète — n8n déployé, 3 workflows en production, mémoire élève active
- Phase 5 : À faire — pool LLM complet (20 clés 5 users × 4 providers)
- Phase 6 : À faire — dashboard + features (flashcards, examen, lacunes)
- Phase 7 : ⬤ En cours — n8n déployé, rapports hebdo à implémenter
- Phase 8 : À faire — multi-domaines + web search conditionnel

## Prochaines étapes immédiates
1. Brancher dify-snapshot dans Teacher (toutes les 10 interactions)
2. Brancher dify-profil-update en fin de session Teacher
3. Activer facturation Google → ajouter gemini-flash et gemini-pro dans Dify
4. Générer curriculum anglais A1→C2 complet → stocker en DB
5. Appliquer system prompt v2 + Chatflow aux autres agents (Maestro, Sensei, etc.)

## Règle changelog webapp
Quand des fonctionnalités visibles par l'utilisateur sont ajoutées à la webapp :
1. Mettre à jour le fichier `/opt/academie/webapp/frontend/src/routes/changelog/+page.svelte` en ajoutant une nouvelle entrée (ou en complétant l'entrée du jour) dans le tableau `entries` avec : date, version, title, items[]
2. Bumper la constante `CHANGELOG_VERSION` dans `/opt/academie/webapp/frontend/src/lib/components/Header.svelte` pour que le badge "Nouveau" s'affiche
3. Cela inclut : nouvelles pages, nouveaux composants visuels, corrections UX, nouvelles features, changements de layout

## Notes importantes
- dify-plugin-daemon était instable, s'est stabilisé tout seul le 04/04/2026
- Mot de passe PostgreSQL changé : [REDACTED — see /opt/academie-shared/secrets/]
- Gemini : quota gratuit épuisé sans facturation activée (max ~10 req/jour)
- profil_manager.py testé et fonctionnel : save_profil + get_profil + format_profil_for_injection
- System prompt Teacher v2 validé : onboarding 3 temps, test adaptatif C1 atteint, format ❌✅💡
- dify-sandbox déployé le 05/04/2026 — nécessaire pour Jinja2 dans les LLM nodes
- dify-api/dify-worker recréés avec ADMIN_API_KEY_ENABLE=true (clé dans /opt/academie/.dify_admin_key)
- Accès API Dify : Authorization: Bearer <ADMIN_KEY> + X-WORKSPACE-ID: [REDACTED-WORKSPACE-ID]
- sys.user_id dans Dify Chatflow = UUID du compte Dify connecté (pas un username)
