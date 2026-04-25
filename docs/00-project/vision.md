---
title: Vision produit AcademIA
status: authoritative
last_reviewed: 2026-04-15
owner: sinse + claude
---

# Vision produit AcademIA

## Produit

**AcademIA** : plateforme d'apprentissage adaptatif multi-domaines par IA, positionnée comme **complément à un cours** (pas substitut).

## Cible finale

**Ouvrir en SaaS public / freemium / B2B** à terme.

Timing non défini — le projet reste en phase familiale/proches (~20 users) tant que :
- la taxonomie d'erreur n'est pas scientifiquement calibrée
- l'architecture multi-domaine n'est pas éprouvée
- les besoins sécurité (credentials, auth, GDPR) ne sont pas adressés

## Segments utilisateurs

**Ado + adulte**, différenciation minimale. Objectif : produit unique avec personnalisation par profil (`profils_eleves.personnalite.centres_interet`, `style_correction`) plutôt qu'éditions distinctes par segment.

## Positionnement

**Complément à un cours** — pas un substitut autonome type Duolingo. Usage type :
- Un lycéen en cours d'anglais utilise Teacher pour pratiquer entre les cours
- Un étudiant en informatique utilise PyMentor pour consolider après un TP
- Un pro en reconversion utilise un agent dédié pour combler des lacunes spécifiques

Ce positionnement autorise des sessions moins gamifiées qu'un produit "hook retention" (Duolingo) et plus centrées sur le feedback qualité.

## Domaines prévus (roadmap long terme)

### Langues (priorité 1-2)

1. **Teacher EN** — anglais (current prod)
2. **Maestro ES** — espagnol (DELE A1→C2)
3. **Sensei JP** — japonais (JLPT N5→N1)
4. **Lehrer DE** — allemand (Goethe A1→C2)
5. **Professore IT** — italien (CILS A1→C2)

### Informatique (priorité 2-3)

6. **PyMentor** — Python
7. **CyberMentor** — cybersécurité (NICE framework)
8. Agents système/réseau (futur)

### Autres (priorité 3+)

9. Comptabilité (IFRS/GAAP à explorer)
10. Autres domaines techniques

## Philosophie pédagogique

Fondée sur la recherche scientifique en SLA (cf. [01-pedagogy/bibliography.md](../01-pedagogy/bibliography.md)) :

- **Graduation des erreurs par niveau** (Pienemann processability, Corder mistake vs error) — pas de scoring binaire
- **Feedback adaptatif** (Lyster & Ranta prompts > recasts) — pas de correction uniforme
- **Dosage respecté** (Sweller cognitive load, Cowan 4-item buffer) — pas de sur-correction
- **Protection de la motivation** (Krashen affective filter, Mueller & Dweck mindset) — pas de praise d'intelligence
- **L1-aware** (Selinker transfer, Stockwell hierarchy) — matrices d'erreur spécifiques à la paire L1→L2

## Philosophie économique

**Gratuit tant que familial** (cf. ADR-006 LiteLLM BYOK). Ouverture SaaS ne devra pas détruire cette promesse pour les proches : freemium avec pool BYOK préservé côté interne, paying tiers pour users publics.

## Philosophie technique

- **Monolithe tant qu'on est solo** (cf. ADR-001), microservices envisagés
- **Schema from day 1 multi-langue et multi-domaine** (cf. ADR-002)
- **Architecture hybride orchestrée** avec `academie-core` comme socle partagé (cf. ADR-004, ADR-005)
- **LLMs = force, pas autorité** : rules layer Python obligatoire (Pfau 2023 recall limité, Fang 2023 overcorrection)

## Non-goals explicites

- ❌ **Gamification forte à la Duolingo** — pas le focus (streaks, XP, badges existent mais restent secondaires)
- ❌ **Apps mobiles natives iOS/Android** — stratégie PWA (web + mobile via navigateur)
- ❌ **Self-hosting LLM à court terme** — cosmos n'a pas de GPU, pas de budget cloud GPU
- ❌ **Certification officielle** (diplôme CECRL, JLPT, etc.) — on est préparation/complément, pas examen validant
- ❌ **Communauté / social / peer learning** — pas prioritaire

## Principes produit

1. **Scientifique > intuitif** : chaque décision pédagogique doit pouvoir citer un paper ou un corpus
2. **Transparent > opaque** : l'utilisateur doit comprendre pourquoi il reçoit tel feedback, tel tier, tel niveau
3. **Sobre > spectaculaire** : pas d'animations, de confetti, de tambours — feedback direct et respectueux
4. **Progressif > brutal** : migration, refonte, évolution = toujours avec versioning et rollback possibles
