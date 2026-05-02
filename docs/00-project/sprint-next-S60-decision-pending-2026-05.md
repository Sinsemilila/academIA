---
title: Sprint S60 — décision pending (5 options)
status: draft
last_reviewed: 2026-05-02
owner: sinse
type: plan
---

# Sprint S60 — décision pending

> **Context** : sprint Maître Comptable P0+P1 locked S59 commit `71e4762`.
> Prochaine session = à choisir parmi 5 options classées ROI immédiat.
> À lire au `/pickup` S60.

## État cumul fin S59 (2026-05-02)

| Projet | Investi | Status | Reste |
|---|---|---|---|
| **Maître Comptable P0+P1** | ~30h S57-S59 | ✅ locked | P2 Mode A ~5-8j, P3+ ~15-20j |
| **Maestro ES MVP** | ~16h S56 | ✅ Wave 2-4 authorized | iter prompt sliding |
| **Teacher EN** | ~30h S40-S55 | ✅ baseline 18-19/26 stable | P0.1 structured output enum backlog |
| **Wave 2 IT essential** | ~5h prep S52 | 🟡 prep done, build pending | ~5-7j |
| **Wave 3 DE / 4 JP-RU** | ~5h prep S52 | 🟡 prep done, build pending | ~5-7j chacun |
| **Eisenday V2** | dormant ~4j | 🟡 dormant | Sinse decide |

## 5 options Sprint S60

### Option 1 — ⏸ Wait Marie 3-5j puis Maître Comptable P2 (recommandé split-mode)

- Pourquoi : data-driven decision pattern S59 auto-test évite scope creep
- Risque si attaqué maintenant : Mode A Lessons designé sans signal Marie usage réel
- Effort : sliding monitor + ~5-8j P2 ensuite

### Option 2 — 🌍 Wave 2 IT Phase 1 (~5-7j) — high ROI

- Prep faite S52 : `vault/knowledge/projects/academia-ia/multilang-italian-research.md` + 230KB research CILS/MERLIN/VALICO/Pienemann
- Pattern oracle réutilisable Maestro ES S56
- Acquisition livres Sinse fait (Profile Italian + Pienemann + CILS)
- Scope : `curriculum_it.json` mirror ES + `rules_it.py` + 8 fewshots IT + oracle 24-31 + Tier 1-6 RE-MEASURE
- Cible : κ Opus ≥0.85, ≥50% golden pass
- Risque : pas natif IT → cross-check via vault research + LLM judges multilingual

### Option 3 — 💰 Microentreprise launch prep (~1-2 semaines)

- Pourquoi : Marie pilote → si valide en 2-4 sem, monétiser
- Concurrents : Le Club Comptable 15€/mois (compta) + Nomad Education FREE (langues)
- Différenciation : IA Lyster scaffolds + multi-domaine (unique)
- Scope : ADR-018 RGPD SaaS + pricing + CGV + Stripe + /pricing page + landing refonte
- Risque : prématuré sans validation Marie ≥1 sem

### Option 4 — 🛠 Maître Comptable P2 Mode A Lessons BC1.4 TVA MVP (~5-8j)

- Reste sur lancée Maître Comptable
- Couvre autre moitié formation Studi (lessons guidées vs Q&A side-chat)
- Scope : clone Dify chatflow Mode A + scenarios YAML Cas Studi + frontend route + UX combo A+B+E
- Risque : sans data Marie Mode B, peut-être pas le bon angle pédago

### Option 5 — 💤 Eisenday V2 (dormant)

- Sinse decide momentum (pas de TODO actif visible)
- Cohérent anti-doc-théâtre L42 si pas relancé en S60-S61

## 🏆 Reco split-mode (à valider Sinse)

**Active fork** : Wave 2 IT Phase 1 (~5-7j) — high ROI, prep faite, oracle pattern, marché langues > compta long-term

**Passive fork** : monitor Marie organique sliding 3-5j → si pattern hallu résiduelle révélé, jump-fix A1 extension (~30 min) intersession Wave 2

**Defer** :
- Microentreprise launch jusqu'à validation Marie ≥1 sem usage
- Maître Comptable P2 Mode A jusqu'à data Marie collectée
- Eisenday — Sinse decide indépendamment

## Décision Sinse

À renseigner au `/pickup` S60 :

```
[ ] Option 1 — Wait Marie + Mode A
[ ] Option 2 — Wave 2 IT (recommandé)
[ ] Option 3 — Microentreprise launch
[ ] Option 4 — Maître Comptable P2 direct
[ ] Option 5 — Eisenday V2
[ ] Combo split-mode (Option 2 active + Marie monitor passif)
[ ] Autre :
```

---

*Doc draft S59 fin pour reprise S60. Si décision prise, archive ce doc dans `_legacy/` ou supersede par `sprint-XYZ-2026-05.md` proper.*
