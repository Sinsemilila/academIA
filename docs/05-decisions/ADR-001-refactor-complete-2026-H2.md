# ADR-001 — Refactor complet academia.petit-pont.com (2026-H2)

**Status** : Accepted
**Date** : 2026-04-23
**Decision-makers** : Sinse (solo-dev), Claude (assistant)
**Related** : `docs/decisions.md#18`

---

## Context

academia.petit-pont.com est une alpha SaaS d'apprentissage de langues (FR-natifs → EN/ES via chatbots Teacher/Maestro) hébergée sur Cosmos Server derrière Cloudflare. Stack : SvelteKit 2 + Svelte 5 runes, Tailwind v4, FastAPI, PostgreSQL, Docker, nginx, LiteLLM proxy. 141 comptes en DB, 1 user actif. Budget monétaire = **0€**.

Trois besoins convergents déclenchent ce refactor :
1. **Sécurité insuffisante pour ouvrir à des utilisateurs externes** : JWT stocké en `localStorage` côté frontend (vulnérable XSS), pas de CSP/HSTS, pas de DPIA, pas de migration Argon2id, pas de MFA, pas de PII scrubber avant envois LLM, pas d'audit isolation cross-user.
2. **Absence de design system cohérent** : ~20 composants hand-rolled sans tokens, typographie non formalisée, dark/light incohérent, pas de régression visuelle testée.
3. **Obligations légales à remplir avant 1er user externe** : DPIA CNIL, DPA OpenAI/Groq/Gemini, mention IA (AI Act EU art. 50 — deadline transparence 2 août 2026), Schrems II TIA, workflow DSAR, politique mineurs.

**Contrainte forte** : zéro dépense monétaire. Toute recommandation payante (pentest externe, Argos cloud, Sentry SaaS, Cloudflare Pro, validation juriste DPIA) est remplacée par une alternative gratuite self-hosted ou communautaire.

**Outcome visé** : site prêt pour **beta privée fermée gratuite** (5-10 testeurs trustés, non-payants) à fin Phase D. Ouverture publique payante différée au-delà, conditionnée au financement d'un pentest via premiers revenus.

## Décisions tranchées

| # | Décision | Statut |
|---|---|---|
| 1 | **JWT storage** | Vérifié : `localStorage` actuellement (`webapp/frontend/src/lib/api.ts:11-27`). Migration urgente vers cookie HttpOnly + sessions opaques Redis dès Phase A |
| 2 | **Cloudflare devant Cosmos** | Déjà en place (IPs 188.114.96.2 / 188.114.97.2 confirmées). Activation règles WAF managed + Bot Fight Mode en début Phase A |
| 3 | **Horizon 5-6 mois calendaires** | Validé, parallélisation refactor + pédago acceptée (60/40 par session ou alternance session entière) |
| 4 | **Pentest avant beta** | Option B : beta privée gratuite sans pentest externe. Auto-audit rigoureux. Pentest payant financé par premiers revenus post-beta |
| 5 | **i18n UI** | OUI par défaut (cible internationale future) — Paraglide-JS 2 maintenu dans le plan |
| 6 | **Politique mineurs** | Flow consentement parental implémenté (pas exclusion <15 ans) |
| 7 | **MFA scope** | TOTP pour tous les users (admin TOTP jour 1, users Phase A), WebAuthn/Passkeys Phase 2 post-beta |

## Principes directeurs

- **Pas de compromis "sous-dimensionné"** : stack SOTA 2026 adoptée (Bits UI, shadcn-svelte, OKLCH, WebAuthn prévus), pas de shortcuts liés au nombre d'users.
- **Compromis techniques réels maintenus** : Biome rejeté (pas de support `.svelte` stable en 2026), CSP report-only avant enforce (2 semaines), migration stores Svelte legacy en lazy (au toucher du fichier).
- **Parallélisation 60/40** : ~60% sessions refactor, ~40% sessions pédago.
- **Hofstadter ×2 assumé** : estimations calendaires réalistes 21-27 semaines (~5-6 mois).

## Phase A — Sécurité complète (5-6 semaines réalistes)

**KPI gate** : OWASP ZAP 0 critical/high · Mozilla Observatory A+ · Lighthouse security 100 · CSP enforce stable 7j · DPIA rédigée · 0 leak prompt injection CI.

- **A1 — Auth + sessions (~1.5 sem)** : migration JWT localStorage → cookie `HttpOnly + Secure + SameSite=Lax + __Host-` + sessions opaques Redis. CSRF double-submit. Révocation instantanée `/api/auth/logout-all-sessions`.
- **A2 — Argon2id (~0.5 sem)** : `CryptContext(["argon2", "bcrypt"], deprecated="auto")`, rehash-on-login auto, job cron force reset >90j inactivité.
- **A3 — Headers + CSP (~1 sem + 2 sem report-only)** : HSTS preload, CSP nonce SvelteKit, COOP/COEP/CORP, Permissions-Policy, Referrer-Policy. Endpoint collecte `/api/csp-report`. Enforce strict final puis soumission hstspreload.org.
- **A4 — MFA TOTP + WebAuthn scaffolding (~1 sem)** : `pyotp` backend, QR enrollment, admin activé jour 1. `simplewebauthn` libs en place, activation UI Phase 2.
- **A5 — LLM sécu (~1 sem)** : PII scrubber backend (regex + presidio-analyzer), audit isolation cross-user (tests CI prompt injection, 0 leak toléré), rate-limits per-user (slowapi), cost-runaway alerting per-user, logs LLM redaction + rotation 30j + chiffrement at-rest.
- **A6 — RGPD + AI Act + Schrems II (~1.5 sem)** : DPIA CNIL, registre traitements, DPA OpenAI/Groq/Gemini, TIA Schrems II, mention IA UI + CGU, workflow DSAR (export + delete), politique mineurs <15 (consentement parental double opt-in), banner cookies.
- **A7 — Infra + supply chain (~0.5 sem)** : DMARC/SPF/DKIM, Cloudflare WAF OWASP Core Rule Set + Bot Fight Mode, backups chiffrés age rotation 7/30/90j + restore testé mensuel, SBOM syft, Docker signing cosign, pip-audit + Dependabot, Docker hardening (non-root, read-only FS, drop caps).

## Phase B — Fondations visuelles (6-8 semaines réalistes)

**KPI gate** : Lighthouse perf ≥95/90 · INP p75 <200ms · axe-core 0 WCAG AA · bundle initial <80KB gzip · design tokens 100% · GlitchTip actif.

- **B1 — Tokens OKLCH + typo (~1 sem, parallèle A1-A2)** : Tailwind v4 `@theme` dark+light OKLCH, spacing/radius/motion/elevation scales, Inter (UI) + Source Serif 4 (L2) self-hosted subset+preload+Fontaine.
- **B2 — Bits UI + shadcn-svelte (~2.5 sem)** : adoption complète (Dialog, Combobox, Menu, Toast, Select, Checkbox, Radio, Tabs, Accordion, Popover, Tooltip, Toggle, Slider, Progress, Avatar, Badge, Card, Separator). Pinning strict versions pour éviter auto-upgrade bugs.
- **B3 — Images + PWA Workbox (~1 sem)** : `@sveltejs/enhanced-img` AVIF+WebP+srcset. Audit `sw.js` hand-written → Vite PWA + Workbox (NetworkOnly `/api/*`, SWR assets, NetworkFirst docs).
- **B4 — GlitchTip + bundle budget (~1 sem)** : GlitchTip 6 self-hosted (Docker), `@sentry/sveltekit` SDK, source maps CI, bundle gate CI <80KB initial / <30KB lazy.
- **B5 — Paraglide-JS 2 i18n (~0.5 sem)** : Vite plugin, strings FR + EN fallback, route `/[lang]/...` ou `Accept-Language`.
- **B6 — Forms + motion + state (~1 sem)** : Superforms v2 runes + Valibot pour QCM + chat, motion `svelte/transition` respectant `prefers-reduced-motion`, stores legacy → `.svelte.ts` runes lazy.

## Phase C — Refonte toutes pages (8-10 semaines réalistes)

**KPI gate** : Lost Pixel reviewed 100% · Playwright e2e 3 navigateurs × 2 thèmes verte · RGAA 100% · feature flag `?v2=1` éliminé.

- **C1 — Navigation globale (~1 sem)** : Sidebar, Header, CommandPalette sur tokens + Bits UI.
- **C2 — Pages publiques (~2 sem)** : Landing, login/signup/forgot, CGU/privacy/cookies/mentions/`security.txt`.
- **C3 — Onboarding QCM (~1.5 sem)** : OnboardingModal refonte, flow consentement parental mineurs, banner mention IA.
- **C4 — Chat Teacher/Maestro (~2.5 sem)** : ChatBubble sérif L2/sans L1, CEFR badges first-class, streaming SSE UX, system_consolidation bubbles. **Préserver** taxonomie erreurs CEFR + variable wiring Dify.
- **C5 — /admin + sous-routes (~2 sem)** : refacto ModelBudgetBar/JudgeBudgetBar/Consolidation/Oracle/Funnel sur tokens, résoudre 20 svelte-check errors baseline.
- **C6 — Lost Pixel + Playwright e2e (~1 sem)** : ~60 stories (familles × 2 thèmes × 3 breakpoints), 3 flows × 3 navigateurs × 2 thèmes, @axe-core/playwright.

## Phase D — Auto-audit sécu + correction (2-3 semaines réalistes)

**KPI gate** : OWASP ZAP full scan 0 critical/high · SSL Labs + Mozilla Observatory A+ · ASVS L2 checklist 100% ou justifié.

- **Outils gratuits** : OWASP ZAP baseline + full, nikto, testssl.sh, sqlmap (endpoints authentifiés), Mozilla Observatory, SSL Labs, Lighthouse.
- **Checklist OWASP ASVS L2** self-applied, documentée.
- **Responsible disclosure** : `/.well-known/security.txt` (RFC 9116), email `security@petit-pont.com`, politique publique.
- **Relecture amicale** : solliciter 2-3 contacts dev sécu (LinkedIn/Discord/forums) pour code review ad-hoc.
- **Remediation** toutes findings critical/high avant ouverture beta privée fermée.

## Parallélisation pédago

Sessions 46+ continuent en parallèle : Teacher EN structured output enum (P0), Phase 3 fault injection delta gating, Phase 4 gate-strict flip, Maestro ES catchup, Phase C-deep prompt reorder (Oracle-gated), curriculum_en.yaml sync DB.

Découpage : **60% refactor / 40% pédago**, ou alternance session entière selon contexte.

## Critical files to modify

**Phase A** :
- `webapp/backend/app/auth.py` — Argon2id + sessions Redis
- `webapp/backend/app/routers/auth_router.py` — cookies au lieu de tokens body
- `webapp/frontend/src/lib/api.ts` — retirer localStorage, `credentials: 'include'`
- `nginx/` — headers HSTS/CSP/COOP/COEP
- `webapp/backend/app/security/pii_scrubber.py` (nouveau)
- `webapp/backend/app/security/csp_report.py` (nouveau)
- `webapp/backend/app/routers/user_dsar_router.py` (nouveau)
- `docker-compose.yml` — GlitchTip
- `docs/99-runbooks/dpia.md` + `rgpd-registre.md` + `transfert-impact-assessment.md` (nouveaux)

**Phase B** :
- `webapp/frontend/src/app.css` + `tailwind.config.ts` — `@theme` OKLCH
- `webapp/frontend/src/lib/components/ui/*` — shadcn-svelte primitives
- `webapp/frontend/vite.config.ts` — enhanced-img, Paraglide, PWA
- `webapp/frontend/static/sw.js` — remplacement Workbox
- `webapp/frontend/src/lib/stores/*.ts` → `*.svelte.ts` lazy
- `package.json` — pinning strict Bits UI

**Phase C** :
- `webapp/frontend/src/routes/+layout.svelte` + components nav
- `webapp/frontend/src/routes/+page.svelte` (landing)
- `webapp/frontend/src/routes/login/` + `signup/` + `forgot-password/`
- `webapp/frontend/src/lib/components/onboarding/OnboardingModal.svelte`
- `webapp/frontend/src/lib/components/chat/*`
- `webapp/frontend/src/routes/admin/*`

**Phase D** :
- `webapp/frontend/static/.well-known/security.txt` (nouveau)
- `docs/99-runbooks/asvs-l2-checklist.md` (nouveau)
- `.github/workflows/security-audit.yml` (nouveau)

## Reusable existing assets

- Redis `redis-academie` container déjà dans stack (sessions opaques)
- sops + age déjà utilisés (chiffrement backups)
- LiteLLM proxy déjà en place (cost tracking per-model)
- Cloudflare déjà devant (activer WAF rules)
- passlib déjà installé (swap scheme seulement)
- Smoke-test `/root/sinse-tools/smoke-test` (étendre security checks)

## Verification

**Phase A** : `pytest webapp/backend/tests/test_auth.py` · `curl -I` headers · OWASP ZAP baseline · Mozilla Observatory · CI prompt injection tests · DSAR flow manuel.

**Phase B** : `pnpm build` + `vite-bundle-visualizer` <80KB · Lighthouse CI targets · axe-core + Playwright 0 violation.

**Phase C** : Lost Pixel review · Playwright full suite · RGAA audit manuel.

**Phase D** : OWASP ZAP full · SSL Labs · ASVS L2 review.

## Risques résiduels acceptés

- **Pas de pentest externe avant beta privée** : auto-audit + responsible disclosure + relecture amicale. Pentest dès 5 users payants.
- **DPIA self-applied non-validée juriste** : template CNIL strict + relecture RGPD réseau. Validation pro dès budget.
- **Cloudflare free tier limites** : pas de WAF custom, pas de bot management avancé. Upgrade si attaques sérieuses.
- **GlitchTip self-hosted mono-instance** : si serveur tombe, monitoring tombe avec. Acceptable en alpha.
- **Hofstadter ×2** : calendrier 21-27 sem peut glisser à 30+ si dettes techniques non-anticipées. Re-estimation fin chaque phase.

## Commit plan

Un commit par item A1..D, préfixé `[refactor-2026h2-<phase><item>]`. ADR committé en premier, pointer depuis `docs/decisions.md`. Cadence 1-2 commits/session refactor, revue KPI gate à fin phase.
