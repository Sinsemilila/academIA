# Webapp Academie-IA — Plan d'implementation

## Architecture cible
- Frontend : SvelteKit + Tailwind CSS + Geist font
- Backend : FastAPI (Python) — proxy Dify + auth + PostgreSQL
- Deploy : 2 conteneurs Docker sur cosmos (academie-net-bridge)
- Routing : academie.petit-pont.com → SvelteKit / /api → FastAPI

## Sprint 0 — Fondations ✅ DONE

### 0.1 Structure projet ✅
### 0.2 Docker ✅ (2 containers up on academie-net-bridge)
### 0.3 Routing ✅ (proxy /api/* via SvelteKit hooks.server.ts → FastAPI:8000, Cosmos config pending Sprint 2)
### 0.4 Design tokens ✅ (Geist fonts woff2, palette dark, agent accents via @theme)
### 0.5 Layout squelette ✅ (Sidebar, Header, 4 pages: /, /login, /chat/[agent], /stats)
### 0.6 Base de donnees ✅ (4 tables + user sinse id=1 admin)

---

## Sprint 1 — Auth + Dashboard ✅ DONE

### 1.1 FastAPI auth ✅
- auth.py (bcrypt + JWT 7j), auth_router.py (/login, /me, /users admin)
- profile_router.py (/profile/{domain}, /streak, /stats/weekly)
- Tested: login → JWT → /me → /profile/anglais → real data sinse B1

### 1.2 Login page ✅
- Login form → POST /api/auth/login → localStorage token → redirect /
- Layout: route guard (onMount check token, redirect /login if missing)

### 1.3 Dashboard données réelles ✅
- Profile card (niveau B1, 5% progress, 1/20 mastered)
- Weekly stats (8 sessions, 2 concepts, 120 min)
- Agent grid (Teacher actif, 6 autres grisés)
- Full API chain via SvelteKit proxy → FastAPI → PostgreSQL

---

## Sprint 2 — Chat ✅ DONE

### 2.1 FastAPI proxy Dify ✅
- chat_router.py : /chat/send (SSE streaming), /chat/conversations, /chat/messages
- dify_user_id mapping (users.dify_user_id → UUID Dify existant)
- Streak auto-update on each chat message
- Session tracking in user_sessions table

### 2.2 Chat UI ✅
- ChatBubble.svelte (markdown, accent border, fade-in animation)
- ChatInput.svelte (auto-resize textarea, Enter/Shift+Enter)
- TypingIndicator.svelte (3-dot bounce)

### 2.3 Page chat ✅
- /chat/[agent]/+page.svelte : full SSE streaming, conversation resume, new session
- ReadableStream parsing of Dify SSE events (message + message_end)
- Auto-scroll, empty state, agent not available state

### 2.4 Mode exam — deferred to Sprint 3 polish
- [ ] Header special exam avec barre progression
- [ ] Masquer sidebar concepts pendant exam

### Validated
- SSE stream: sinse → FastAPI → Dify API → Teacher chatflow → token-by-token response ✅
- Real profile: B1, present perfect, concepts selection ✅
- Conversations list from Dify API ✅
- Streak: 1 day / 1 session updated in DB ✅

---

## Sprint 3 — Stats + Progression

### 3.1 FastAPI endpoints stats
- [ ] GET /api/me/concepts : retourne scores_confiance detailles + concept_groups
- [ ] GET /api/me/history : retourne historique sessions (date, duree, concepts)
- [ ] GET /api/me/exams : retourne historique examens (dernier_examen JSONB)
- [ ] GET /api/me/xp : retourne XP total + rang + log recent

### 3.2 Page stats
- [ ] /stats/+page.svelte : layout stats
- [ ] Carte niveau : jauge circulaire ou barre, pourcentage, "Pret pour exam" si applicable
- [ ] Grille concepts : groupes par module, chaque concept = mini-barre + score + icone (check/eclair/new/horloge)
- [ ] Code couleur : vert >80, orange 50-80, rouge <50, gris non teste
- [ ] Historique sessions : liste scrollable (date, agent, concepts travailles)
- [ ] Historique examens : resultats par module (score, passed/failed)
- [ ] XP + rang + prochain rang
- [ ] Tester : page stats affiche donnees reelles sinse

---

## Sprint 4 — Gamification

### 4.1 Streak
- [ ] Logique FastAPI : a chaque POST /chat/send, verifier last_active_date
  - Si aujourd'hui → rien
  - Si hier → current_streak++, update longest si besoin
  - Sinon → current_streak = 1
- [ ] Header : badge 🔥 N visible partout (layout)
- [ ] Animation : flamme pulse quand streak augmente

### 4.2 XP
- [ ] Trigger : +50 apres 10 messages dans une session
- [ ] Trigger : +200 quand n8n scoring retourne passed=true (webhook ou poll)
- [ ] Trigger : +500 quand niveau_global change en DB
- [ ] Rang calcule depuis SUM(xp_log.amount)
- [ ] Toast notification discret "+50 XP" en bas a droite

### 4.3 Badges
- [ ] Table badges : liste fixe en code (pas en DB)
  - Perseverant : streak >= 10
  - Infatigable : streak >= 30
  - Premier exam : COUNT exams >= 1
  - Promotion : nb_examens_niveau (passed) >= 1
  - Polyglotte : COUNT DISTINCT agents >= 2
  - Perfectionniste : exam score >= 95
- [ ] GET /api/me/badges : retourne badges debloques + progres vers prochain
- [ ] Page profil : section badges (icones + noms, grises si pas debloques)
- [ ] Prochain badge : barre de progression sur le dashboard

---

## Sprint 5 — Polish + Mobile

### 5.1 Responsive
- [ ] Mobile : sidebar → hamburger menu (slide in/out)
- [ ] Mobile : chat = plein ecran, pas de sidebar concepts
- [ ] Mobile : dashboard = cartes empilees verticalement
- [ ] Mobile : stats = scroll vertical continu
- [ ] Tester sur ecran 375px (iPhone SE)

### 5.2 Animations
- [ ] Page transitions : crossfade SvelteKit (svelte/transition)
- [ ] Chat messages : fade-in + slide-up a l'arrivee
- [ ] Barres de progression : animate width on mount
- [ ] Compteurs : increment anime (XP, streak, scores)
- [ ] Cards : hover scale 1.02 subtle

### 5.3 Finitions
- [ ] Favicon + meta tags
- [ ] Error pages (404, 500)
- [ ] Loading states (skeleton screens)
- [ ] Empty states ("Pas encore de session")
- [ ] Toast system (notifications discretes)
- [ ] Dark/light toggle (optionnel, dark par defaut)

---

## Design reference

### Palette dark
- bg-base: #0a0a0a
- bg-surface: #141414
- bg-elevated: #1e1e1e
- border-subtle: #262626
- text-primary: #f5f5f5
- text-secondary: #a0a0a0
- text-muted: #525252

### Accents agents
- teacher: #3b82f6 (blue)
- maestro: #ef4444 (red)
- sensei: #a855f7 (purple)
- lehrer: #f59e0b (amber)
- professore: #22c55e (green)
- pymentor: #06b6d4 (cyan)
- cybermentor: #ec4899 (pink)

### Typo
- UI: Geist Sans (400, 500, 600)
- Mono: Geist Mono (stats, code)
- Body: 14px, Small: 12px, H3: 18px, H2: 20px, H1: 24px

### Gamification
- XP par session: +50
- XP exam reussi: +200
- XP promotion: +500
- Rangs: Debutant(0), Explorateur(200), Apprenti(500), Praticien(1500), Expert(5000), Maitre(15000)

### Dify API reference
- App key Teacher: REDACTED_DIFY_TEACHER_KEY
- Endpoint: http://dify-api:5001/v1/chat-messages
- Auth: Authorization: Bearer {app_key}
- Body: { inputs: {}, query: "...", user: "user_{id}", response_mode: "streaming", conversation_id: "" }
- Response: SSE stream (event: message/message_end, answer: token delta)
- Conversations: GET /v1/conversations?user=user_{id}
- Messages: GET /v1/messages?user=user_{id}&conversation_id=X
