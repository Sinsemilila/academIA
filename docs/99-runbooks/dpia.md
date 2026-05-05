# DPIA — academia.petit-pont.com (auto-évaluation CNIL)

**Status** : v1 — auto-assessment alpha privée
**Last updated** : 2026-04-23
**Auteur** : Sinse (responsable de traitement)
**Révision** : annuelle minimum, ou à chaque changement majeur (nouveau sous-processeur LLM, ouverture publique, ajout de catégories de données)
**Related** : [`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`](../05-decisions/ADR-001-refactor-complete-2026-H2.md), [`rgpd-registre.md`](rgpd-registre.md), [`transfert-impact-assessment.md`](transfert-impact-assessment.md)

---

## 1. Description du traitement

### 1.1 Finalité
Tutorat IA personnalisé pour l'apprentissage de langues étrangères (français-natifs vers EN/ES, autres domaines à venir). Trois agents pédagogiques (Maestro, Teacher, Onboarding) interagissent en temps réel avec l'apprenant·e via une interface chat.

### 1.2 Base légale (RGPD art. 6)
- **Art. 6(1)(a)** — consentement explicite recueilli au moment de la création de compte (acceptation des CGU + politique de confidentialité).
- **Art. 6(1)(b)** — exécution du contrat de service (fourniture du tutorat).

### 1.3 Catégories de personnes concernées
- Apprenant·es adultes (≥15 ans pour la version alpha — voir [`minors-flow-roadmap.md`](minors-flow-roadmap.md) pour le flow mineurs prévu post-beta publique).
- Public actuel : 1 utilisateur actif (Sinse, dogfood). 141 comptes legacy en base (anciens tests, à purger lors de la beta).

### 1.4 Catégories de données collectées

| Catégorie | Exemples | Source | Stockage |
|---|---|---|---|
| **Identification** | username, email, display_name, avatar_color, theme | Saisie directe (signup ou admin CLI) | PG `users` |
| **Authentification** | password_hash (Argon2id), TOTP secret, recovery_codes | Saisie directe + génération | PG `users` + `user_totp` (secret in-memory only after enrollment) |
| **Profil pédagogique** | Niveau CEFR, motivation, anxiété langue (FLA), L1/L2, mode d'apprentissage | Onboarding QCM | PG `learner_profiles`, `profils_eleves`, `eleves` |
| **Conversations LLM** | Messages utilisateur, réponses tuteur, contexte conversationnel | Chat en temps réel | PG `conversations` + `messages` (schéma Dify) |
| **Télémétrie pédagogique** | Erreurs détectées, événements consolidation, snapshots session, XP, streaks | Calcul backend | PG `error_log`, `consolidation_events`, `snapshots_session`, `xp_log`, `streaks`, `spaced_retrieval_queue` |
| **Télémétrie produit** | Steps onboarding (start/abort/complete) | Frontend → backend | PG `onboarding_telemetry_events` |
| **Sessions actives** | Token opaque, IP, user_agent, dates | Login | Redis `session:*` (TTL 7j) |
| **Sécurité** | Violations CSP (anonymisé : IP SHA256 daily-salted) | Browser → backend | PG `csp_violations` |

**Aucune donnée sensible** au sens RGPD art. 9 (santé, religion, orientation sexuelle, etc.) collectée ni stockée. L'item FLA (anxiété en langue étrangère) est une auto-évaluation pédagogique non-clinique.

### 1.5 Durée de conservation
- **Compte actif** : illimitée (tant que l'utilisateur ne demande pas la suppression).
- **Suppression compte (DSAR delete)** : hard delete immédiat sur toutes les tables PG + Redis sessions + tables Dify (`conversations`, `messages`). Pas de période de grâce.
- **Logs applicatifs** : rotation 30 jours (Docker logs + nginx).
- **Backups chiffrés (restic)** : rotation 7/30/90j (cf. A7). Un compte supprimé peut subsister jusqu'à 90j dans les backups froids — documenté comme limitation acceptable, restauration manuelle uniquement sur incident infra.
- **CSP violations** : 90j (purge cron — *à mettre en place*).
- **Sessions Redis** : TTL sliding 7j.
- **Onboarding telemetry** : 365j puis purge (à mettre en place).

### 1.6 Destinataires (sous-processeurs)
Voir [`rgpd-registre.md`](rgpd-registre.md) pour la liste détaillée et les DPA. Synthèse :
- **OpenAI** (US — DPF) : LLM gpt-4o-mini, gpt-4.1-mini.
- **Groq** (US — DPF) : LLM Llama 3.3.
- **Google AI Studio** (US — DPF) : LLM Gemini Flash (judge Oracle uniquement, pas tutorat).
- **Cloudflare** (US/EU — DPF + SCC) : reverse proxy + WAF + Bot Fight + Page Shield. Pas de cookies tiers, pas d'analytics.

Pas d'analytics tiers (pas de Google Analytics, pas de Plausible, pas de Sentry SaaS — on utilisera GlitchTip self-hosted en Phase B4).

### 1.7 Transferts hors UE
Tous les LLM sous-processeurs sont basés aux US. Voir [`transfert-impact-assessment.md`](transfert-impact-assessment.md) (TIA Schrems II).

---

## 2. Évaluation des risques (méthodologie CNIL PIA-2)

### 2.1 Atteinte à la confidentialité

| Source de risque | Impact | Vraisemblance | Niveau | Mesures |
|---|---|---|---|---|
| **Vol cookie session** (XSS) | Vol session 7j max | Faible (CSP + cookies HttpOnly + Argon2id + MFA) | **Faible** | A1 sessions opaques Redis HttpOnly+Secure, A3 CSP enforce J+14, A4 MFA TOTP obligatoire admin |
| **Fuite PII vers LLM** | Exposition email/téléphone/IBAN/NIR à OpenAI/Groq | Moyen (apprenant·es peuvent saisir leur PII réelle dans messages) | **Moyen** | A5 PII scrubber regex avant envoi, placeholder `[EMAIL]`/`[PHONE]`/`[IBAN]`/`[NIR]`/`[CARD]` |
| **Cross-user leak via prompt injection** | User A obtient profil/conv de User B | Moyen (LLM-based isolation pas garantie) | **Moyen** | A5 tests CI cross-user isolation (4 scénarios), 0 leak toléré, gate strict |
| **Compromission base PG** | Exposition complète de la base | Faible (Cosmos Server isolé, accès SSH clé uniquement, backups chiffrés age) | **Moyen** (impact élevé, vraisemblance faible) | Argon2id A2, backup encrypted, accès admin via clé SSH + MFA, rotation passwords |
| **DDoS / scraping** | Indisponibilité service | Moyen | **Faible** | A7 Cloudflare WAF + Bot Fight + rate-limit per-user A5 (100r/m) |
| **Backup compromis** | Exposition snapshot froid d'un compte supprimé | Faible | **Faible** | restic chiffré age, passphrase dans `/opt/academia-shared/secrets/restic-passphrase` (root only), restore testé mensuel |

### 2.2 Atteinte à l'intégrité

| Source de risque | Mesures |
|---|---|
| **Modification non-autorisée d'un profil** | A1 CSRF double-submit, sessions Redis sliding TTL, MFA pour mutations sensibles (TOTP disable) |
| **Injection SQL** | Requêtes paramétrées (asyncpg/psycopg) partout, audit régulier |
| **Modification config admin** | Rôle `is_admin` boolean en DB, vérifié par `require_admin()` à chaque endpoint admin |

### 2.3 Atteinte à la disponibilité

| Source de risque | Mesures |
|---|---|
| **Perte sessions Redis (restart)** | Audit `appendonly` Redis (TODO Sinse), si désactivé = users déconnectés au restart (acceptable alpha) |
| **Perte DB PG** | Backups restic 7/30/90j, restore testé mensuel (TODO) |
| **Coupure Cloudflare** | Pas de bypass prévu actuellement (Cloudflare devant Cosmos), accepté car acteur tier 1 |

---

## 3. Mesures de sécurité

### 3.1 Mesures techniques (Phase A roadmap)
- ✅ **A1** — Sessions opaques Redis + cookies HttpOnly+Secure+SameSite + CSRF double-submit (commit `941299b`).
- ✅ **A2** — Argon2id silent rehash sur login (commit `435abcc`).
- ✅ **A3** — CSP report-only + COOP/CORP/Permissions-Policy. Flip enforce 2026-05-07.
- ✅ **A4** — MFA TOTP backend + UI (commits `69aba81`, `50deb82`). Admin obligatoire.
- ⚠️  **A5** — PII scrubber + cross-user isolation tests + rate-limit per-user. **Session 47 (en cours).**
- ⚠️  **A6** — RGPD docs + endpoints DSAR (export/delete). **Session 47 (ce document).**
- ✅ **A7** — Cloudflare WAF + Bot Fight + Page Shield + HSTS 1 an + DMARC `p=none`. Bump `quarantine` 2026-05-07.

### 3.2 Mesures organisationnelles
- **Solo-dev** (Sinse) : pas de partage de credentials, accès SSH par clé uniquement, MFA partout (GitHub, Cloudflare, OpenAI, Groq, Aegis pour TOTP self).
- **Backups** : chiffrement age, passphrase isolée hors repo.
- **CI/CD** : Dependabot + security-audit workflow (pip-audit + npm audit + Trivy + syft SBOM) hebdo (commit `4e7377b`).
- **Sources** : repo GitHub privé.

### 3.3 Droits des personnes (DSAR)
Voir [`rgpd-registre.md`](rgpd-registre.md) §4 pour le détail des endpoints. Synthèse :

| Droit | Modalité | Délai |
|---|---|---|
| **Accès / portabilité** (art. 15, 20) | `GET /api/me/export-data` (UI : `/settings/privacy`) → JSON complet downloadable | Immédiat |
| **Effacement** (art. 17) | `DELETE /api/me/delete-account` (UI : modal 2-step retype username) → hard delete imm. | Immédiat |
| **Rectification** (art. 16) | `PATCH /api/me/profile` (UI : `/settings`) | Immédiat |
| **Opposition / retrait consentement** (art. 21, 7(3)) | Effacement compte = retrait. Pas d'opt-in marketing (pas d'emailing). | Immédiat |
| **Limitation** (art. 18) | Email manuel à `dsar@petit-pont.com` (TODO Cloudflare Email Routing) | <30j |
| **Réclamation CNIL** | Lien CNIL fourni dans `/legal/privacy` | N/A |

---

## 4. Avis du DPO
Pas de DPO désigné (alpha solo-dev, hors seuils RGPD art. 37). Auto-évaluation par le responsable de traitement. Désignation prévue avant ouverture publique payante.

## 5. Validation
- ✅ Auto-assessment Sinse — 2026-04-23
- ⏳ Revue annuelle planifiée — 2027-04-23
- ⏳ Sollicitation CNIL en cas d'incident grave (art. 33-34)

## 6. Annexes
- [`rgpd-registre.md`](rgpd-registre.md) — Registre art. 30
- [`transfert-impact-assessment.md`](transfert-impact-assessment.md) — TIA Schrems II
- [`minors-flow-roadmap.md`](minors-flow-roadmap.md) — Roadmap consentement parental
- [`a1-sessions-redis.md`](a1-sessions-redis.md), [`a2-argon2id-migration.md`](a2-argon2id-migration.md), [`a3-csp-report-only.md`](a3-csp-report-only.md), [`a4-mfa-totp.md`](a4-mfa-totp.md), [`a7-infra-hardening.md`](a7-infra-hardening.md) — runbooks Phase A
