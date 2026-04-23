# B1 — Design tokens (refactor 2026-H2 Phase B1)

**Status** : livré Session 47 — tokens OKLCH + state semantics + L2 serif font
**Last updated** : 2026-04-23
**Related** : ADR-001 §"Phase B — Fondations visuelles" + roadmap B2-B6

Tokens définis dans `webapp/frontend/src/routes/layout.css` (Tailwind v4 `@theme` block). Dark theme = défaut, light theme via `[data-theme="light"]`. Switch piloté par `lib/stores/theme.ts` + `localStorage.theme` + bootstrap inline `app.html`.

---

## 1. Tokens couleur — agents (immutables dark/light)

| Token | OKLCH | ≈ hex sRGB | Usage |
|---|---|---|---|
| `--color-teacher`     | `oklch(0.623 0.188 259.815)` | `#3b82f6` | Teacher (anglais) — bleu |
| `--color-maestro`     | `oklch(0.637 0.208 25.331)`  | `#ef4444` | Maestro (espagnol) — rouge |
| `--color-sensei`      | `oklch(0.627 0.232 303.9)`   | `#a855f7` | Sensei (japonais) — violet |
| `--color-lehrer`      | `oklch(0.769 0.165 70.080)`  | `#f59e0b` | Lehrer (allemand) — orange |
| `--color-professore`  | `oklch(0.723 0.192 149.579)` | `#22c55e` | Professore (italien) — vert |
| `--color-pymentor`    | `oklch(0.715 0.126 215.221)` | `#06b6d4` | PyMentor (Python) — cyan |
| `--color-cybermentor` | `oklch(0.656 0.212 354.308)` | `#ec4899` | CyberMentor — rose |

Tailwind expose : `bg-teacher`, `text-maestro`, `border-sensei`, `bg-lehrer/20` (alpha modifier), etc.

## 2. Tokens couleur — neutrals (variants dark/light)

| Token | Dark | Light | Usage |
|---|---|---|---|
| `--color-base`           | `oklch(0.145 0 0)` | `oklch(0.985 0 0)` | Background page (`html`) |
| `--color-surface`        | `oklch(0.191 0 0)` | `oklch(1 0 0)`     | Cards, panels |
| `--color-elevated`       | `oklch(0.235 0 0)` | `oklch(0.967 ...)` | Hover states, inputs |
| `--color-border-subtle`  | `oklch(0.269 0 0)` | `oklch(0.928 ...)` | Borders cards/inputs |
| `--color-text-primary`   | `oklch(0.970 0 0)` | `oklch(0.210 ...)` | Texte normal |
| `--color-text-secondary` | `oklch(0.706 0 0)` | `oklch(0.551 ...)` | Texte sous-titre / hint |
| `--color-text-muted`     | `oklch(0.439 0 0)` | `oklch(0.714 ...)` | Texte désactivé / labels |

## 3. Tokens couleur — state semantics (B1.2 nouveau)

Convention sémantique (jamais utiliser raw `bg-emerald-500/10` ou `text-rose-300` à la place) :

| Token | OKLCH | Sémantique |
|---|---|---|
| `--color-success` + variants | `oklch(0.696 0.170 162.480)` (vert) | Validation, état OK, success message |
| `--color-warning` + variants | `oklch(0.769 0.188 70.080)` (orange) | Attention non-bloquante, action requise |
| `--color-danger` + variants  | `oklch(0.628 0.258 29.234)` (rouge) | Suppression, erreur, opération destructive |
| `--color-info` + variants    | `oklch(0.623 0.214 259.815)` (bleu) | Information neutre, état actif/sélectionné |

Variants exposés (chacun en `-bg`, `-border`, `-text`) :
- `bg-success`, `bg-success/N` (alpha N), `bg-success-bg` (preset 10%)
- `border-success`, `border-success/N`, `border-success-border` (preset 30%)
- `text-success`, `text-success-text` (variante L bumpée pour contrast dark/light tuné)

**Anti-patterns à NE PAS commettre** :
- ❌ `bg-emerald-500/10` (raw palette) → ✅ `bg-success/10`
- ❌ `text-rose-300` → ✅ `text-danger-text`
- ❌ `border-amber-500/40` → ✅ `border-warning/40`

## 4. Tokens couleur — specialized

Cf. `layout.css` pour `--color-code-bg/border` (Markdown blocks), `--color-overlay/shadow` (modals/tooltips), `--color-heatmap-{empty,low,mid,high,max}` (ActivityHeatmap), `--color-star-{glow,dim,bg}` (CelebrationModal).

## 5. Tokens font

| Token | Source | Usage |
|---|---|---|
| `--font-sans`  | Geist Variable, self-hosted | UI principale (texte, boutons, labels), L1 (français — texte de l'apprenant) |
| `--font-mono`  | Geist Mono Variable, self-hosted | Code, tokens techniques, recovery codes TOTP |
| `--font-serif` | Source Serif 4 Variable, self-hosted | **L2** : texte en langue cible enseignée (anglais Teacher, espagnol Maestro, etc.). Branche dans `ChatBubble.svelte` via prop `font="serif"` quand `role === 'assistant'` ET `agent.domain ∈ {en, es, ja, de, it}` |

Fonts preloaded dans `app.html` : Geist + Source Serif 4 (latin subset).

## 6. Spacing / radius / shadow

**Pas de tokens custom — Tailwind defaults gardés** (decision Session 47, ADR-001 §B1).

- Spacing : `p-0` à `p-96` (échelle Tailwind 0/0.5/1/.../96) en multiples de 0.25rem
- Radius : `rounded-sm/md/lg/xl/2xl/3xl/full` (Tailwind defaults)
- Shadow : `shadow-sm/md/lg/xl/2xl` (Tailwind defaults)

Si besoin futur d'un custom 4pt grid, redéfinir dans `@theme` — mais évaluer le coût refactor (tout le code utilise les valeurs Tailwind).

---

## TODO opportuniste — fichiers restant à migrer state semantics

Sweep B1.3 a couvert les 2 plus gros offenders (`chat/[agent]` 31 + `settings/privacy` 27 = 58 / 65 occurrences). Restent **~7 occurrences** dans 7 fichiers, à migrer **au touch** (pas de chantier dédié) :

| Fichier | Action |
|---|---|
| `lib/components/AIBanner.svelte` | `bg-amber-500/10 border-amber-500/30 text-amber-400` → `bg-warning/10 border-warning/30 text-warning-text` |
| `lib/components/LevelBadge.svelte` | Mapping CEFR colors — garder palette directe (A1=red, B1=blue, C1=green) ou introduire `--color-cefr-A1/B1/C1` ? À discuter Session 48 |
| `lib/components/MiniExamModal.svelte` | `bg-amber-*` → `bg-warning-*` |
| `lib/components/ConsolidationDecisionModal.svelte` | Mixed amber/blue/emerald → state tokens |
| `lib/components/onboarding/OnboardingModal.svelte` | Idem |
| `lib/components/admin/CostRunawayCard.svelte` | `bg-rose-500/5 text-rose-300 font-semibold` → `bg-danger/5 text-danger-text font-semibold` |
| `routes/admin/users/+page.svelte` | Mixed |
| `routes/settings/security/+page.svelte` | 1 occurrence `text-amber-400` (déjà couvert par tokens introduits dans les fichiers édités cette session) |
| `lib/components/chat/ChatBubble.svelte` | `border-l-2 border-green-500/70` (consolidation event marker) → `border-success/70` |

**Convention d'application** : à chaque PR qui touche un de ces fichiers pour autre chose, profiter du diff pour migrer aussi les palette → tokens. Ne pas créer de PR dédié sweep.

---

## Notes futures (Phase B2+)

- **OKLCH dérivés** : la nouvelle syntaxe CSS `oklch(from var(--color-teacher) calc(l + 0.10) c h)` permettra de générer auto les variants `--color-teacher-50/100/.../900` à la shadcn-svelte sans dupliquer les définitions. À utiliser quand on intègre shadcn-svelte (B2).
- **`color-mix(in oklch, A, B 50%)`** : pour des hover states ou disabled states perceptuellement justes (vs `bg-color/50` qui blend en sRGB). Préférer pour les states critiques.
- **Browser support** : `oklch()` requiert Chrome 111+ / Firefox 113+ / Safari 15.4+ (mai 2023). Acceptable pour audience 2026.
