# Registre des activités de traitement (RGPD art. 30)

**Status** : v1 — auto-tenu par le responsable de traitement
**Last updated** : 2026-04-23
**Responsable de traitement** : Sinse (sinseproduction@gmail.com)
**Révision** : à chaque ajout/retrait de sous-processeur ou de catégorie de données
**Related** : [`dpia.md`](dpia.md), [`transfert-impact-assessment.md`](transfert-impact-assessment.md)

---

## 1. Identité du responsable

| Champ | Valeur |
|---|---|
| Nom | Sinse (responsable solo, alpha non-commerciale) |
| Contact RGPD | sinseproduction@gmail.com (à remplacer par `dsar@petit-pont.com` post Cloudflare Email Routing) |
| Statut | Personne physique — projet personnel auto-financé |
| DPO | Non désigné (hors seuils art. 37 RGPD) |
| Lieu de traitement principal | Cosmos Server (Hetzner / OVH — *à confirmer location*) |

## 2. Traitements

### 2.1 Traitement principal — "Tutorat IA langues"

| Champ | Valeur |
|---|---|
| **Finalité** | Fournir un service de tutorat IA personnalisé pour l'apprentissage de langues étrangères |
| **Base légale** | Consentement (art. 6(1)(a)) + exécution contrat (art. 6(1)(b)) |
| **Catégories de personnes** | Apprenant·es ≥15 ans (alpha — flow mineurs Phase B1) |
| **Catégories de données** | cf. [`dpia.md`](dpia.md) §1.4 — identification, auth, profil pédagogique, conversations, télémétrie |
| **Destinataires** | Sous-processeurs §3 ci-dessous |
| **Transferts hors UE** | OUI (US — DPF) — voir [`transfert-impact-assessment.md`](transfert-impact-assessment.md) |
| **Durée conservation** | Cf. [`dpia.md`](dpia.md) §1.5 |
| **Mesures sécurité** | Cf. [`dpia.md`](dpia.md) §3 |

### 2.2 Traitement secondaire — "Sécurité applicative" (CSP violations)

| Champ | Valeur |
|---|---|
| **Finalité** | Détecter les violations CSP et tentatives d'attaque XSS |
| **Base légale** | Intérêt légitime (art. 6(1)(f)) — sécurité du système |
| **Catégories de données** | URL violée, IP hashée SHA256 (sel quotidien rotaté), user_agent |
| **Destinataires** | Aucun — usage interne |
| **Transferts hors UE** | Non |
| **Durée conservation** | 90j puis purge cron (TODO) |

### 2.3 Traitement secondaire — "Télémétrie produit" (onboarding)

| Champ | Valeur |
|---|---|
| **Finalité** | Mesurer le funnel d'onboarding (drop-off par step) |
| **Base légale** | Intérêt légitime (art. 6(1)(f)) — amélioration UX |
| **Catégories de données** | Step IDs traversés, durées, abandon ou complétion. UUID de session navigateur (localStorage). Pas de PII directe. |
| **Destinataires** | Aucun |
| **Transferts hors UE** | Non |
| **Durée conservation** | 365j puis purge cron (TODO) |

---

## 3. Sous-processeurs

| Sous-processeur | Rôle | Pays | DPA / Garanties | Statut signature |
|---|---|---|---|---|
| **OpenAI L.L.C.** | LLM API (gpt-4o-mini, gpt-4.1-mini) — chat tutorat principal | US (DPF certifié) | DPA self-service [openai.com/policies/data-processing-addendum](https://openai.com/policies/data-processing-addendum) — opt-out training data activé via [Privacy Settings](https://platform.openai.com/account/data-controls) | ⚠️ **À signer (Sinse)** |
| **Groq Inc.** | LLM API (Llama 3.3 70B) — fallback tier 2 chat | US (DPF certifié) | DPA self-service [groq.com/dpa](https://groq.com/dpa/) — pas de training data Groq par défaut | ⚠️ **À signer (Sinse)** |
| **Google LLC** (AI Studio Gemini API) | LLM judge (Oracle pédagogique) — gemini-3-1-flash-lite, gemini-3-flash, gemini-2.5-flash | US (DPF certifié) | API consumer-tier — pas de DPA formel disponible. Risque accepté pour usage limité au judge Oracle (pas de PII utilisateur, uniquement output Teacher) | ✅ Acté (risque résiduel : aucun message learner ne transite par Gemini, seulement les outputs synthétiques du Teacher) |
| **Cloudflare Inc.** | Reverse proxy + WAF + Bot Fight Mode + Page Shield + HSTS + Email Routing (à venir) | US + UE (DPF + SCC) | DPA standard auto-accepté à l'inscription [cloudflare.com/cloudflare-customer-dpa](https://www.cloudflare.com/cloudflare-customer-dpa/) | ✅ Signé (acceptation TOS) |
| **GitHub Inc.** (Microsoft) | Hébergement code source (repo privé) — pas de PII utilisateur | US (DPF certifié) | DPA via TOS Microsoft enterprise | ✅ Signé |
| **Hetzner / OVH** *(à confirmer)* | Hébergeur serveur Cosmos | UE | DPA UE-native | ✅ |

**À ne pas oublier post-beta** : ajouter au registre tout nouveau sous-processeur (ex : Plausible si analytics, Resend/Postmark si email transactionnel, GlitchTip si auto-hébergé pas concerné).

---

## 4. Droits des personnes — modalités

| Droit | Endpoint / Procédure | Délai engagement |
|---|---|---|
| **Information** (art. 13-14) | Page `/legal/privacy` (TODO) + bannière mention IA `/legal/ia` (Phase A6) | Permanent |
| **Accès** (art. 15) | `GET /api/me/export-data` via `/settings/privacy` → JSON complet | Immédiat |
| **Rectification** (art. 16) | `PATCH /api/me/profile`, `PATCH /api/me/mode` via `/settings` | Immédiat |
| **Effacement** (art. 17) | `DELETE /api/me/delete-account` via `/settings/privacy` (modal 2-step + retype username) | Immédiat (hard delete) |
| **Limitation** (art. 18) | Email à `dsar@petit-pont.com` (TODO Cloudflare Email Routing) | <30j |
| **Portabilité** (art. 20) | Identique accès — JSON exportable | Immédiat |
| **Opposition** (art. 21) | Effacement compte = opposition totale (pas d'usage commercial des données, pas de profilage marketing) | Immédiat |
| **Réclamation CNIL** | Lien dans `/legal/privacy` : [cnil.fr/plaintes](https://www.cnil.fr/fr/plaintes) | N/A |
| **Retrait consentement** (art. 7(3)) | Effacement compte = retrait | Immédiat |

**Engagement réponse aux DSAR exceptionnels** : <30j (RGPD art. 12(3)). Suivi manuel par Sinse via boîte email dsar@.

---

## 5. Notifications de violation

Procédure en cas de violation de données personnelles (RGPD art. 33-34) :

1. **Détection** — alerte Cloudflare Notifications (DDoS / SSL / Page Shield / Tunnel down — TODO Sinse re-créer côté token), GlitchTip self-hosted (Phase B4), audit logs PG.
2. **Évaluation impact** sous 24h : nombre de personnes affectées, catégories de données, nature de la violation.
3. **Notification CNIL** sous 72h via [notifications.cnil.fr](https://notifications.cnil.fr) si risque pour les droits et libertés.
4. **Notification aux personnes concernées** sans délai si risque élevé (email à toutes les adresses concernées, mention sur le site).
5. **Documentation** dans ce registre §6 ci-dessous.

## 6. Journal des incidents

Aucun incident à ce jour. *(Format prévu : Date | Description | Personnes affectées | CNIL notifiée O/N | Mesures correctives)*

---

## 7. Conservation du registre

Ce document est versionné dans le repo Git du projet ([`docs/99-runbooks/rgpd-registre.md`](rgpd-registre.md)) et révisé à chaque changement. Historique = git log.
