# Loom narration — AcademIA demo (5-7 min)

Outreach byproduct. Zero pressure, not polished : unedited, raw, shows the
product in real use. Target audience : FR-native candidates for EN/ES learner
testing.

## Before recording

- [ ] Clean browser window (Chrome incognito recommended, no bookmarks bar).
- [ ] Fresh user account to show the onboarding path end-to-end.
- [ ] Teacher domain set to EN (or switch between EN/ES during the demo).
- [ ] Close `/admin` tab for the main arc — show admin separately as a bonus.

## Arc — 5-7 minutes

### Opening (30 sec)
"Je vous montre AcademIA, un tuteur de langue adaptatif que je développe.
L'idée : un prof particulier virtuel calibré CEFR, qui s'adapte à ton
niveau et à tes patterns d'erreurs typiques de francophone."

### 1. QCM onboarding (1 min)
- Start fresh account, pick EN.
- Answer QCM honestly (or pretend A1).
- Point out : "L'onboarding prend 90 secondes, il sert à placer l'apprenant
  et détecter ses patterns L1. La vraie valeur arrive ensuite."

### 2. First conversation (2 min)
- Open chat. Read the welcome.
- Type a deliberately wrong-ish message : "Yesterday I go to the market"
- Receive the tutor response.
- Narrate : "Tu vois, pas de liste de corrections en rouge comme Duolingo.
  Le tuteur reformule naturellement, il marque `went`, et continue la
  conversation. C'est le pattern Lyster — 30 ans de recherche SLA."

### 3. The 3-strikes micro-lesson (1.5 min)
- Continue the convo with 2 more verb tense errors.
- Wait for turn ~7. When the tutor intègre une clarification past-tense :
  "Là, tu vois — après 3 échecs consécutifs sur la même famille d'erreur,
  AcademIA injecte une mini-leçon ciblée. Pas un pop-up. Pas un encart rouge.
  Le tuteur tisse naturellement la règle dans sa prochaine réponse."

### 4. Observed level + doctrine (1 min)
- Open dev tools → network tab → inspect the message JSON.
- "Chaque réponse émet un `observed_level` — l'apprenant est jugé A1 ou A2
  en temps réel, pas à partir d'un test figé. Quand 8 tours confirment un
  niveau, tu reçois un mini-exam pour valider."

### 5. Admin dashboard (bonus, 1 min)
- Switch to `/admin` tab.
- Show the "Prompt caching" section (Phase D v2).
- "Le dashboard suit le cache OpenAI — 97% de hit rate sur les prompts
  stables. Concrètement, ça divise par 2 le coût d'un turn après le premier."

### Close (20 sec)
"Je cherche 3 FR-natifs qui veulent tester sur 1-2 semaines et me donner du
feedback — learners EN ou ES débutants ou intermédiaires. DM si ça
t'intéresse."

## Post-recording

- [ ] Save Loom as "unlisted".
- [ ] Drop link in `docs/outreach/loom-links.md` (create if absent).
- [ ] Queue 3 personalised DMs (friends / Reddit / Discord) with the link.

## What to AVOID saying

- No mention of "priority concepts" architecture internals (even though
  they're running — the tutor never mentions them out loud, we don't either).
- No cost numbers that could be interpreted as pricing (we're pre-revenue).
- No unvalidated claims like "better than Duolingo" — let the demo show it.
