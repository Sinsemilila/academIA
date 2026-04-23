# Roadmap — Flow consentement parental mineurs (RGPD art. 8)

**Status** : roadmap — implémentation prévue **post-beta publique** (≠ ADR-001 Phase B1 = design tokens OKLCH)
**Last updated** : 2026-04-23
**Auteur** : Sinse
**Related** : [`dpia.md`](dpia.md), ADR-001 décision #6

> **Note naming** : ADR-001 Phase B1 = design tokens OKLCH (fondations visuelles). Le flow mineurs est planifié pour la **phase d'ouverture publique payante**, distincte de toute phase ADR-001. Référez-vous à ce label "post-beta" partout dans la doc.

---

## Contexte

RGPD art. 8 : pour les services en ligne destinés à des mineurs, le consentement n'est licite que si l'enfant a au moins **16 ans**, ou — selon dérogation par État membre — un seuil compris entre 13 et 16 ans. **France : 15 ans** (Loi pour une République numérique, 2016).

Sous 15 ans, le consentement doit être donné **par le titulaire de l'autorité parentale**.

## Décision Phase A (alpha privée — Session 47, 2026-04-23)

**Defer le flow complet post-beta**. Mesures appliquées maintenant :

1. **Checkbox auto-attestation** au signup (ou validation admin pour comptes CLI) : "Je certifie avoir 15 ans ou plus, ou avoir l'autorisation de mon responsable légal pour utiliser ce service."
2. **Colonne PG `users.age_attestation_at TIMESTAMPTZ NULL`** — timestamp de l'attestation.
3. **Page `/legal/mineurs`** — page courte expliquant que le service est restreint ≥15 ans pour l'alpha, avec le flow consentement parental prévu pour la beta publique.
4. **Refus inscription** si checkbox non cochée (côté frontend + validation backend).

Rationale :
- Alpha privée fermée à ≤10 testeurs trustés, recrutés explicitement par Sinse (pas d'inscription publique anonyme).
- Pas d'infrastructure email transactionnelle disponible (Cloudflare Email Routing à configurer manuellement, pas de provider SMTP).
- Effort full flow ≈ 1.5 sem (table `parental_consents` + magic-link tokens + UI parent + email transactionnel + relance + révocation) — disproportionné face au risque réel actuel (0 inscription publique).
- Conformité RGPD acceptable pour une alpha **uniquement si l'auto-attestation est de bonne foi** et qu'aucun mineur <15 n'est invité.

## Roadmap post-beta — flow complet (~1.5 semaine)

### Étape 1 — modèle données

```sql
CREATE TABLE parental_consents (
  id              SERIAL PRIMARY KEY,
  user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
  child_birthdate DATE NOT NULL,
  parent_email    VARCHAR(255) NOT NULL,
  parent_name     VARCHAR(255),
  consent_token   VARCHAR(64) UNIQUE NOT NULL,
  consent_status  VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending | granted | revoked | expired
  granted_at      TIMESTAMPTZ,
  revoked_at      TIMESTAMPTZ,
  revoke_reason   TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  expires_at      TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days')
);
CREATE INDEX idx_parental_consents_user ON parental_consents(user_id);
CREATE INDEX idx_parental_consents_token ON parental_consents(consent_token);
CREATE INDEX idx_parental_consents_status ON parental_consents(consent_status);

ALTER TABLE users ADD COLUMN birthdate DATE;
ALTER TABLE users ADD COLUMN account_status VARCHAR(20) DEFAULT 'active';
-- account_status : active | pending_parental_consent | revoked_by_parent | self_suspended
```

### Étape 2 — UX inscription mineur

```
Inscription
  ↓
Saisie birthdate
  ↓
Si âge ≥15 → flow normal (checkbox attestation + création compte actif)
Si âge <15 → page "Consentement parental requis"
              ↓
              Saisie email parent + nom parent
              ↓
              Compte créé en `pending_parental_consent` (login bloqué)
              ↓
              Email parent : "Votre enfant <prénom> souhaite créer un compte sur AcademIA. [Lien magic 7j]"
              ↓
              Parent clique → page consentement (description finalité, données, droits)
                ↓
                Accept → compte `active`, email confirmation à child
                Refuse → compte `revoked_by_parent`, hard delete J+30
              ↓
              Si pas de réponse <7j → compte expiré, email rappel à parent + child
```

### Étape 3 — endpoints backend

- `POST /api/auth/signup-minor` — body `{username, email, birthdate, password, parent_email, parent_name}`. Création user `pending`, génération `consent_token`, envoi email parent.
- `GET /api/parental-consent/{token}` — affiche page consentement parent (no auth).
- `POST /api/parental-consent/{token}/grant` — parent accepte. Update user → `active`. Email confirmation child.
- `POST /api/parental-consent/{token}/revoke` — parent refuse ou retire ultérieurement. Update user → `revoked_by_parent`. Trigger hard delete J+30.
- Cron quotidien `expire_pending_consents.py` — purge tokens >7j sans réponse, email rappel + cleanup user pending.
- Cron quotidien `purge_revoked_users.py` — hard delete les comptes `revoked_by_parent` après 30j (grâce cas erreur parent).

### Étape 4 — UI parent

`/parental-consent/[token]/+page.svelte` — page standalone (pas dans le shell auth) :
- Identification enfant (prénom uniquement, pas d'autres données)
- Description finalité ("AcademIA est un service de tutorat IA pour l'apprentissage de langues...")
- Liste des données qui seront collectées
- Liste des sous-processeurs (OpenAI, Groq, Cloudflare)
- Droits du parent (révocation à tout moment via lien permanent)
- Boutons "Accepter" / "Refuser"
- Mention RGPD art. 8 + autorité légale

### Étape 5 — révocation parent ultérieure

`/parent-portal/[user_id]?token=<long_lived_revoke_token>` — page accessible via lien permanent (envoyé dans email confirmation accept) :
- Visualiser activité enfant (résumé : sessions, durée totale, agents utilisés — pas le contenu des conversations)
- Demander export des données enfant (déclenche `/api/me/export-data` côté child + envoi par email parent)
- Révoquer consentement → hard delete J+30

### Étape 6 — Infra email

Pré-requis avant post-beta :
- **Cloudflare Email Routing** configuré (`security@`, `dmarc-reports@`, `dsar@`, `parents@` → forwarding Sinse). Manuel TODO Sinse.
- **Provider SMTP transactionnel gratuit** (≤100 emails/jour) : choix entre [Resend](https://resend.com) free tier (3000/mois), [Brevo](https://www.brevo.com) free tier (300/jour), [Mailjet](https://www.mailjet.com) free tier (200/jour).
- **DKIM/SPF/DMARC** déjà en place (Phase A7 — DMARC `p=none` actuel, bump `quarantine` 2026-05-07).

### Étape 7 — Tests CI

- `tests/test_parental_consent_flow.py` : signup minor → consent token issued → grant → user active. Negative : token expiré, mauvais token, double grant.
- Test révocation : grant puis revoke → user `revoked_by_parent` → cron purge → 0 row.

### Étape 8 — Doc utilisateur

- `/legal/mineurs` mise à jour avec le flow réel, plus le placeholder "à venir".
- CGU mise à jour : section dédiée minors RGPD art. 8.

## Estimation effort total post-beta

| Étape | Effort |
|---|---|
| 1 — modèle données + migration | 0.5 j |
| 2 — UX inscription minor | 1 j |
| 3 — endpoints backend + crons | 2 j |
| 4 — UI parent consent | 1.5 j |
| 5 — UI parent portal révocation | 1 j |
| 6 — infra email transactionnelle | 0.5 j |
| 7 — tests CI | 1 j |
| 8 — doc | 0.5 j |
| **Total** | **~8 jours** = ~1.5 semaine focused |

## Blockers / pré-requis

- ✅ A1 sessions Redis (livré Session 46) — réutilisé pour reset session sur révocation
- ✅ A6 endpoints DSAR (Session 47) — `/api/me/delete-account` réutilisé pour purge `revoked_by_parent`

- ⚠️  Cloudflare Email Routing setup (manuel Sinse)
- ⚠️  Choix + intégration provider SMTP transactionnel
- ⚠️  Validation juridique du wording consentement (idéalement avis CNIL ou avocat ; à défaut, template CNIL "consentement parental" + auto-validation)

## Hors-scope post-beta

- **Vérification d'identité parentale forte** (carte d'identité, FranceConnect parent, etc.) — disproportionné pour un service éducatif gratuit, le double opt-in email est conforme aux recommandations CNIL pour ce type de service.
- **Consentement multilingue** (autres langues que FR) — différé à l'internationalisation post-beta.
