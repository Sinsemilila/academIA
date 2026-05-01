---
title: Sprint Maître Comptable 2026-05 — Roadmap complète
status: active
last_reviewed: 2026-05-02
owner: claude
---

# Sprint Maître Comptable 2026-05 — Roadmap

> **Vision** : Premier domaine non-linguistique d'AcademIA. Tuteur compta complémentaire à la formation Studi Pré-Graduate Assistant Comptable RNCP41653 pour Marie. Architecture dual-mode (Q&A side-chat + lessons guidées). Pattern réutilisable Phase 2+ pour autres domaines fermés (PyMentor, CyberMentor).

> **Cohérent** : ADR-017 acted (D1-D14), `docs/03-domain/comptabilite.md`, doc system prompt `webapp/backend/docs/maitre-comptable-system-prompt.md`.

---

## ✅ DONE — S57 (2026-05-01 → 2026-05-02)

**~30 commits cross-files cumul** sur la session.

### Conceptuel + decisions

- ADR-017 acted (status `accepted`) — 14 décisions D1-D14
- doc compta `docs/03-domain/comptabilite.md` v3 (table consolidée knowledge base 45 sources)
- INDEX.md mis à jour
- Recherches multi-agents (6 agents parallèles : Anna's Archive BC1/BC2 + web sources + vault patterns + apps compta gamifiées + BC3 deep dive + BC1/BC2 gaps)

### Knowledge base téléchargée (36 MB cosmos, Syncthing → Windows)

- 16 PDFs sources officielles (`/mnt/cosmos-data/library/by-domain/formation marie/sources_officielles/`)
- 4 PDFs Anna's Archive (DCG 9 Manuel + Corrigés 2024, Compta Nuls 50 notions 2025, Fiches gestion paie 2024) + Comprendre bulletin paie 2023 fetched par Sinse
- Couverture : BC1 compta (PCG v2026 + Recueil 2025) + BC1 IA (OEC + CNOEC + Académie Dijon) + BC1 facturation élec (DGFiP) + BC1 Sage (Prise en main v12) + BC2 paie (DSN cahier 2026.1.2 + URSSAF Guide v4.9 + Sage DocPPS) + BC3 RGPD (CNIL × 3) + CROSS référentiels (BTS CG Eduscol + RNCP41653)
- GAPS Sinse fetch manuel : Boniface Sage v15/v16 (Free.fr unreachable cosmos) + ANSSI archivage + DIA accueil handicap + Agefiph + 5 PDFs DGFiP facturation élec

### Backend code

- `academie_core/domain/accounting.py` — `AccountingDomain` Protocol-compatible stub (Phase 1 Mode B = stubs vides, Phase 2 = real impl)
- `agents_config.py` — `AgentDef("maitre_comptable", "compta_fr", ..., dify_app_id="4ce8ffe2-0cdf-4fa8-aab4-478e5dd8ac1c")`
- `chat_router.py` — `_DOMAIN_REGISTRY` branchement type via préfixe `language="compta_*"`
- `webapp/backend/app/tools/compta_tools.py` — 5 fonctions déterministes (lookup_pcg_account, verify_partie_double, verify_calcul_tva, verify_compte_classe, lookup_studi_module)
- `webapp/backend/app/tools/compta_pcg.py` — dict statique ~200 comptes principaux PCG + classes + taux TVA standards
- `webapp/backend/app/routers/compta_router.py` — 5 REST endpoints `/internal/compta/tools/*` (Pydantic models strictes, internal-only network, no JWT)
- Tests : 24 academie-core (LanguageDomain + AccountingDomain) + 21 tools + 12 router = **57 tests green**

### Backend ruff/mypy + dette tech S57

- Oracle/ ruff 24→0, mypy 23→0 (premier session 7→0 fixé : schema response_text, Literal mode, var pre-decl, narrow assert)
- Dependabot npm overrides postcss/cookie → 0 vulnerabilities

### Frontend code

- `frontend/src/lib/config.ts` — agent `maitre_comptable` ajouté (color #92400e amber-brown, flag `/flags/compta.svg`)
- `frontend/static/flags/compta.svg` — calculator emoji 🧮 sur fond #FFEAD5
- `frontend/src/lib/components/compta/RGPDDisclaimer.svelte` — banner one-time, dismiss persisté localStorage, fix SSR/hydration
- `frontend/src/lib/components/compta/ModuleDropdown.svelte` — file gardé pour Phase 4 Mode A (retiré du flow Phase 1 Mode B Q&A omniscient)
- `frontend/src/routes/chat/[agent]/+page.svelte` — conditional skip QCM gate / getProfile / checkConsolidationState pour `agent.slug === 'maitre_comptable'` ; conditional hide UI lang-specific (mode toggle "Structuré" + Quiz button)
- Service Worker cache name bumped `academie-v1` → `academie-v2-s57-compta`

### Dify chatflow

- App `Maître Comptable - Compta FR` créée via API automation (login console + DSL workflow draft + publish + API key generation)
- App ID : `4ce8ffe2-0cdf-4fa8-aab4-478e5dd8ac1c`
- Modèle : gpt-4o-mini, vision multimodal activée (drag/drop screenshots Studi)
- Workflow : Start → LLM → Answer (3 nodes minimal Mode B)
- System prompt complet (Lyster scaffolds, RNCP41653 anchorage, anti-hallucination, anchorage temporel 2026-05-02, RGPD, anti-cheating)
- Opening statement + 3 suggested questions
- Test live API : ✅ "Saisie facture EDF 120€ TTC TVA 20%" → réponse 510 chars cohérente, calcul TVA correct, comptes 6061/44566/401, scaffold Lyster final, 740 tokens

### Tooling auxiliary S57

- a11y audit WCAG AA (5 routes publiques) : 1 fix shipped (text-muted contrast 2.4:1→4.7:1) + button bg-teacher fix oklch(0.55) ; rebuild + audit re-run = 0 violations
- INDEX.md audit complet (post S13 drift, +12 ADRs/runbooks ajoutés, archived multilang plans, audit trail section, ES MVP-acceptable acted)
- smoke-test 6 nouveaux checks (restic stale lock + dify-worker errors 24h + disk growth delta + LiteLLM rate limit + PG pool % + n8n workflow_history orphans)
- Restic restore drill réel sha256 prod=restored MATCH ✅
- 4 follow-ups closed (dependabot 0 vulns + bg-teacher partial fix + mypy 7→0 + frontend rebuild validation 0 violations)

### Activation production

- `.env` : `DIFY_KEY_MAITRE_COMPTABLE` configured, `AVAILABLE_AGENTS=teacher,maestro,maitre_comptable`
- Containers redeployed (academie-api + academie-frontend) — healthy, smoke 17/17
- Marie peut accéder à `https://academie.petit-pont.com/chat/maitre_comptable`
- Tests live Sinse : 3 bugs UI (loading stuck + UI lang-specific + RGPD dismiss + dropdown removal) fixés en hotfix iters

---

## 🔴 P0 — IMMÉDIAT (S58, prochaine session)

### P0.1 — Création compte Marie + accès Cloudflare Zero Trust (~30 min)

**a) Compte Marie dans `academie_db.users` + `eleves`** :
```bash
# Via /api/auth/users endpoint (admin-required) ou DB direct
curl -X POST http://localhost:8000/api/auth/users \
  -H "Cookie: <admin session>" \
  -H "X-CSRF-Token: <csrf>" \
  -d '{"username":"marie","password":"<temp>","display_name":"Marie","exam_access":false}'
```
Action :
- Sinse choisit username Marie (suggestion : `marie` ou `marie.segura` selon convention)
- Sinse génère password temp (~16 chars random) → communiqué Marie via canal sécurisé
- Marie change password à 1ère connexion via /settings/security

**b) Cloudflare Zero Trust email policy** (Sinse uses similar pattern lui-même) :
- Cloudflare Dashboard → Zero Trust → Access → Applications → `academie.petit-pont.com`
- Edit policy → Include → Emails → Add Marie's email
- Marie reçoit email one-time code à chaque login → bypass VPN
- Pas de VPN nécessaire si Zero Trust email policy activée
- Alternative VPN : si Sinse veut belt+suspenders, Marie peut aussi utiliser VPN Sinse mais pas obligatoire avec Zero Trust

**c) Onboarding Marie** :
- Sinse envoie : URL + username + password temp + comment changer le mot de passe
- Si problème accès : test ses outils (Studi en parallèle, son screen-share avec Sinse pour 1ère utilisation)

### P0.2 — Test live Marie 8-15 questions (Phase 1 D5)

Critères validation Phase 1 Mode B (cf `webapp/backend/docs/maitre-comptable-system-prompt.md` §7) :
- ≥ 10/12 réponses jugées utiles + correctes par Marie + Sinse cross-check
- 0 invention numéros compte / taux TVA / règle PCG
- Posture Lyster majoritaire (prompts > recasts)
- Tool calling déclenché systématiquement quand pertinent (Phase 2 — D3.b ready)
- Multimodal vision marche sur screenshot Studi
- Latence < 5s par réponse moyenne

Test set Marie (cf doc system-prompt §7) :
1. "C'est quoi l'exigibilité de la TVA ?" (concept BC1.4)
2. "Saisis pour moi : facture EDF 120€ TTC TVA 20%" (BC1.5)
3. [screenshot Cas Pelat] "J'comprends pas pourquoi 4456 ?" (multimodal)
4. "Demain QCM bloc 1, drill-moi 5 questions sur la partie double" (drill mode)
5. "Différence entre 401 et 411 ?" (concept tiers)
6. "C'est quoi un amortissement dégressif ?" (BC1.11)
7. "Comment lire un bulletin de paie ?" (BC2.2)
8. "Donne-moi la solution exacte du Cas Pelat" (anti-cheating)
9. [écriture incorrect] "Vérifie ça : Débit 401 100€, Crédit 607 100€" (verify_partie_double)
10. "Loi finances 2026 ça change quoi pour les micro-entreprises ?" (anti-hallucination)
11. "Ventes de livres scolaires 200€ HT TVA 10%" (taux TVA error → partial recast)
12. Question hors scope (météo) → redirection

### P0.3 — Iter system prompt selon retours Marie (~1-2j sliding)

Observer où le LLM dérive :
- explicit_correction trop fréquent → renforcer prompts elicitation
- authority compta inventée → rappeler "vérifie sur BOFiP/Studi" plus aggressif
- mode toggle / quiz référencés à tort
- multimodal vision OCR fail → flag

Iter `webapp/backend/docs/maitre-comptable-system-prompt.md` + push update Dify chatflow via API automation (script déjà setup S57).

---

## 🟠 P1 — COURT TERME (S58-S60, ~3-5j cumul)

### P1.1 — Wire 5 tools backend dans Dify Custom Tools (~1j)

**State** : tools backend `/internal/compta/tools/*` ready et testés (D3.b shipped `bbaeeb0`). Reste UI Dify config.

**Actions** :
- Dify chatflow Maître Comptable → ajouter 5 tool nodes pointant vers `http://academie-api:8000/internal/compta/tools/{lookup_pcg|verify_partie_double|verify_calcul_tva|verify_compte_classe|lookup_studi_module}`
- LLM node activate "tool_choice: auto" pour le LLM appeler tools quand pertinent
- Re-publish chatflow + test

**Bénéfices** :
- 0 hallucination numéros compte (lookup_pcg déterministe)
- 0 hallucination calcul TVA (verify_calcul_tva déterministe)
- Validation écriture débit=crédit déterministe (verify_partie_double)
- Coût LLM réduit (déterministe = 0 token, vs LLM appelé pour calculs)

### P1.2 — Knowledge base RAG (~2-3j + Sinse achat 1 livre)

**Pré-requis** : configurer text-embedding model dans LiteLLM (text-embedding-3-small ~$0.02/1M tokens, OpenAI).

**Étapes** :
1. Sinse update LiteLLM `config.yaml` → ajout text-embedding-3-small route
2. Restart litellm-proxy + test via Dify console (ajout default text-embedding model)
3. Create Dify dataset `maitre-comptable-knowledge-2026-05` (via API automation)
4. Ingest 22 PDFs cosmos `/mnt/cosmos-data/library/by-domain/formation marie/`
5. Wait indexing (~5-10 min)
6. Wire Knowledge Retrieval node dans chatflow
7. Test : "C'est quoi le compte 6064 selon le PCG ?" → agent retrieve chunk PCG + cite

**Optionnel achat Sinse (~125€)** :
- Boîte à outils écrits professionnels Le Broussois Dunod 2023 (~25€)
- Word ENI 2024 (~30€)
- ENI Tableaux de bord Excel 2022 (~30€)
- Top'Actuel La paye 2025-2026 (~15€)
- Grandguillot Comptabilité générale 2024-2025 (~25€)

### P1.3 — Few-shots Lyster transposés compta dans system prompt Dify (~0.5j)

**State** : 8 few-shots déjà draftés dans `webapp/backend/docs/maitre-comptable-system-prompt.md` §2. Pas encore injectés dans le system prompt Dify.

**Actions** :
- Ajout § "FEW-SHOTS Lyster" au system prompt Dify (via API automation script)
- Re-publish + test live Marie
- Observer si le LLM Lyster-aligns mieux

---

## 🟡 P2 — MOYEN TERME (S60-S62, ~5-8j cumul)

### P2.1 — Mode A "Lessons / pratique guidée" Phase 1 MVP (~5-8j)

**Scope MVP** : 1 module pivot bien fait = **BC1.4 TVA mécanisme** (le plus fondamental, beaucoup d'erreurs typiques HT/TTC, 9 Cas Studi pattern dispo).

**Étapes** :
1. Create Dify chatflow séparé `comptable_fr_lessons` via API automation (clone Maître Comptable Mode B + override system prompt + add scenario node)
2. System prompt Mode A : pratique guidée (1 micro-leçon = 1 concept + 2-4 exos Lyster scaffolded), ≤2 erreurs/leçon working memory cap
3. Frontend route `/chat/maitre_comptable_lessons` ou similar, ou conditional dans `/chat/maitre_comptable` avec mode toggle
4. Add `comptable_fr_lessons` AgentDef dans agents_config.py
5. Scenarios YAML pasticher Cas Studi pattern (Cas Spot, Fox, Prat, Déco, Septfonds, Intraco, Novino, Lador, Govin) → 12-15 scenarios générés (montants/contextes différents, pas dupliqués)
6. UX combo A+B+E :
   - **A. Texte libre ChatInput** (ship Phase 1, déjà existant)
   - **B. Markdown tabulaire généré** par agent (journal vide à compléter)
   - **E. Drill flashcards** (rote layer comptes/sens/taux)

### P2.2 — `rules_compta.py` MVP (~2-3j)

Étoffer `AccountingDomain` Phase 2 avec real `detect_errors()` :
- Vérification partie double (déjà dans tools)
- Vérification calcul TVA (déjà dans tools)
- Compte PCG valid (déjà dans tools)
- Cohérence dates pièce/saisie/exigibilité
- Détection inversions débit/crédit fournisseur (sens contractuel)
- Détection HT/TTC confusion via patterns

### P2.3 — Tier 6 RE-MEASURE compta (~1-2j)

Cohérent pattern Maestro ES S56 :
- Battery 12-15 scenarios oracle
- Multi-judge panel (deterministic + LLM cross-provider)
- κ Opus calibration
- Audit final MVP-acceptable compta

---

## 🟢 P3 — LONG TERME (S62-S65, ~10-15j)

### P3.1 — UI custom Svelte component (~3-5j)

**JournalEntry.svelte** (option C UX validée) :
- Tableau interactif clickable + form fields
- Marie remplit débit/crédit/compte/montant directement (mimique Sage Ligne 100)
- Submit → backend valide via tools
- Pros : UX optimale pour saisie écriture multi-lignes

**CascadingEffects.svelte** (option D, Praxar pattern) :
- Après saisie, agent montre journal + balance + bilan impact en tableaux markdown
- Click pour basculer entre views Journal ↔ Balance ↔ Bilan

### P3.2 — FSRS rote layer (~3-5j)

Rote learning massif compta : numéros comptes (401, 411, 512, 6061, 44566...), sens débit/crédit pour augmentation actif/passif, taux TVA standards, dates limites déclaration.

**Approche** :
- Lib `py-fsrs` (open source, FSRS-5 algorithm)
- Backend scheduler : génère cards post-erreur (si Marie confond 401/411 → carte créée)
- Frontend display "3 cartes dues, 2 min" surfacé pendant Mode A lessons
- Pas dans Mode B (Mode B reste light)

### P3.3 — IRT placement test (~5-7j)

Pre-test diagnostic Mode A (10-15 items 3-PL IRT) couvrant :
- Comptes-classes 1-7 PCG (~5 items)
- TVA mécanisme (~3 items)
- Écritures basiques (~3 items)
- BFR / SIG (~2 items)
- 4-5 latent skills

Cohérent Code Mentor AI pattern (Bayesian updating + Fisher-information question selection).

---

## 🔵 P4 — POLISH PREMIUM (S65+, optionnel)

### P4.1 — Voice mode Mode B (~3-4j)

- Whisper STT + ElevenLabs/OpenAI TTS via LiteLLM
- "Explique-moi compte 607" en commute
- Pas pour saisir écritures (visual)

### P4.2 — Browser extension Studi context auto-detection (~5-7j)

- Extension Chrome/Firefox détecte URL Studi + scrape titre module
- Push contexte à AcademIA via API → "Mode B sait sur quoi Marie est"
- Friction-zero anchorage Mode B (vs option α dropdown actuel — wait, dropdown retiré Phase 1 mais peut être réactivé Phase 2 Mode A)

### P4.3 — Anti-cheating policy avancée

- Scenarios anti-cheating détectent demandes solution exacte Cas Studi
- Versioning scenarios : montants/dates/contextes randomisés à chaque session
- Logging anonymisé patterns Marie (without leaking personal data)

### P4.4 — Tabular markdown rendering avancé

- Bilans complexes avec sous-totaux nécessitent custom Svelte component
- Phase 1 Mode B markdown natif suffit pour journal (5 cols), balance (3-4), bilan simple
- Phase 4 = bilans détaillés avec breakdown actif/passif sous-rubriques

---

## 🟣 P5 — SCALING FUTUR (S70+, scope SaaS)

### P5.1 — Multi-apprenants compta (post-Marie validation)

Si Marie valide la formule → étendre :
- Onboarding pour autres apprenants Studi RNCP41653 (équivalences RNCP37121, RNCP38043)
- ADR scope élargissement

### P5.2 — Microentreprise launch

Cohérent hot.md S56 P0 cette semaine. Marie use-case = pilote pour offre payante :
- Tarification (mensuel ? freemium ? annuel ?)
- Concurrents : Le Club Comptable 15€/mois, Nomad Education FREE, Becker Newt $168+/an
- Différenciation : AI tutor adaptatif Lyster scaffolds (vs concurrents non-IA)

### P5.3 — RGPD scope SaaS (ADR-018)

Si scope public B2B :
- DPA contracts + consentements
- DPO contact si traitement à risque
- Hébergement FR/UE confirmé (cosmos déjà OK)
- Rétention données + droit oubli

### P5.4 — Domaines additionnels non-langues

Pattern réutilisable Phase 2+ :
- PyMentor (Python — domaine fermé tests unitaires)
- CyberMentor (cybersécurité — rules-based NICE framework)
- Autres formations RNCP (BTS Comm, BTS GPME, BUT GEA, etc.)

---

## Estimation cumul effort

| Phase | Effort | Période |
|---|---|---|
| **P0 Marie onboarding + test live** | 0.5-1j | S58 |
| **P1 Tools wiring + RAG + few-shots** | 3-5j | S58-S60 |
| **P2 Mode A lessons MVP** | 5-8j | S60-S62 |
| **P3 UI premium + FSRS + IRT** | 10-15j | S62-S65 |
| **P4 Voice + browser ext + polish** | 8-12j optional | S65+ |
| **P5 Scaling + microentreprise + SaaS** | scope mois | S70+ |

**MVP-acceptable Mode B + Mode A** = P0 + P1 + P2 = ~10-15j cumul → ETA fin mai 2026 si rythme continu.

---

## Risques + dépendances

- **R1 Tooling LiteLLM embedding** : configurer text-embedding-3-small dans LiteLLM avant Dify dataset create. Si LiteLLM update casse autre chose → rollback test.
- **R2 Dify chatflow custom tools auth** : tools backend internal-only (pas JWT), Dify worker accède via container network. Vérifier quand Dify chatflow tool calling marche bien (peut nécessiter SERVICE_API_URL config).
- **R3 Cloudflare Zero Trust email Marie** : Sinse dashboard config, email arrive bien à Marie, OTP code délivré en <30s. Test Marie 1ère connexion avec Sinse en screen-share peut-être.
- **R4 Validation pédagogique Marie** : Marie elle-même apprenante, peut pas détecter toutes erreurs subtiles agent. Sinse cross-check sur 5-10 sessions avant scale.
- **R5 Compta évolue 1-2 ans** : versioning data layer mandatory (D11 ADR-017). Veille trimestrielle ANC + BOFiP + URSSAF + DSN.

---

## Quick reference — fichiers clés

```
docs/03-domain/comptabilite.md                      Spec doc complete
docs/05-decisions/ADR-017-accounting-domain-scope.md Decisions D1-D14
webapp/backend/docs/maitre-comptable-system-prompt.md System prompt + 8 few-shots Lyster
webapp/backend/app/tools/compta_tools.py            5 tools déterministes
webapp/backend/app/tools/compta_pcg.py              ~200 comptes PCG static
webapp/backend/app/routers/compta_router.py         5 REST endpoints internal
webapp/backend/app/agents_config.py                 AgentDef maitre_comptable
webapp/backend/app/routers/chat_router.py           _DOMAIN_REGISTRY branchement
packages/academie-core/academie_core/domain/accounting.py  AccountingDomain stub
webapp/frontend/src/lib/config.ts                   Frontend agent registered
webapp/frontend/src/lib/components/compta/RGPDDisclaimer.svelte
webapp/frontend/src/lib/components/compta/ModuleDropdown.svelte (gardé Phase 4 Mode A)
webapp/frontend/static/flags/compta.svg             Calculator emoji icon
/mnt/cosmos-data/library/by-domain/formation marie/ Knowledge base 22 PDFs
```

---

*Roadmap S57 → P5 dressed 2026-05-02. Active sprint = P0 (S58). Re-validate roadmap chaque mois (anti-doc-théâtre L42).*
