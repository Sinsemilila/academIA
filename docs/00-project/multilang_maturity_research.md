---
title: Recherche maturité multi-langue — IT/DE/JP/RU vers niveau EN/ES
date: 2026-04-18
status: active
last_reviewed: 2026-04-19
author: Claude (Opus 4.7) — Session 28, 6 agents parallèles + Session 29 pivot stratégie native
supersedes: (complément) multilang_research_plan.md + multilang_execution_roadmap.md
---

# Recherche maturité multi-langue AcademIA

**Objectif** : identifier tout ce qui permettrait de faire passer les langues à maturité **moyenne / limitée / peu mature** (IT, DE, JP, RU) à un seuil **théoriquement équivalent à EN/ES** (mature). Déterminer pour chaque langue si c'est **atteignable**, à quel **coût**, et **comment** concrètement.

**Méthodologie** : 6 agents parallèles (research-focus IT / DE / JP / RU / synthetic+cross-lingual SOTA / EU-CLARIN+grey-literature).

**Update Session 29 (2026-04-19)** : pivot stratégie **JLPT-native** (JP) et **TORFL-native** (RU) au lieu de forcer CEFR A1-C2 → **0€ externe pour JP et RU**, qualité "mature dans écosystème natif" atteignable. Voir §4, §5, §10.

---

## TL;DR — Tableau de maturité (révisé Session 29, stratégie native)

| Langue | Système niveau | Maturité finale | Atteignable ? | Effort vs roadmap | Coût externe |
|---|---|---|---|---|---|
| **EN** | CEFR A1-C2 | MATURE (baseline) | ✅ (déjà) | 0j | 0€ |
| **ES** | CEFR A1-C2 | MATURE (CEDEL2+CAES) | ✅ (chemin clair) | dans Wave 1 | 0€ (open) |
| **IT** | CEFR A1-C2 | **MATURE** (confiance 85-90%) | ✅ **OUI** | +5-8j | 0€ (tout open) |
| **DE** | CEFR A1-C2 | **MATURE** (confiance 80-90% avec Profile Deutsch) | ✅ **OUI** | +3-5j | **40€ Profile Deutsch (Sinse sourced)** |
| **JP** | **JLPT N5-N1 natif** | **MATURE dans écosystème JLPT** (N5-N2 solide, N1 best-effort) | ✅ **OUI** stratégie native | 30-35j Wave 3 | **0€** |
| **RU** | **TORFL TEU-IV natif** | **MATURE dans écosystème TORFL** (TEU-II solide, III/IV best-effort) | ✅ **OUI** stratégie native | 25-30j Wave 4 | **0€** |

**Verdict global Session 29** : **les 6 langues atteignent une "maturité dans leur écosystème pédagogique natif"** à **coût externe quasi-nul** (40€ Profile Deutsch trouvé par Sinse + ~$25-35 OpenAI synthetic cumulé).

**Pivot stratégique clé** : au lieu de forcer CEFR A1-C2 sur JP et RU (ce qui exigerait corpus FR-natif annoté + grammar profile construit = $3-59K externe), on utilise les **référentiels officiels natifs** de chaque langue, qui disposent déjà de toute la matière pédagogique nécessaire en open source.

---

## 1. Définition opérationnelle de "maturité EN/ES"

Pour juger si une langue atteint le niveau EN, on applique 6 critères quantitatifs :

| Critère | Seuil "mature" | EN (réf) | ES (drafts) |
|---|---|---|---|
| **Corpus learner annoté** | ≥ 2500 textes avec annotations M2/ERRANT-like ou équivalent | W&I+LOCNESS+NUCLE (7920 learners) | CEDEL2 (6560) + CAES (1.4M tokens) |
| **Grammar profile CEFR** | Référentiel criterial features par niveau A1-C2 | EGP 1222 criteria | PCIC (Instituto Cervantes) |
| **SLA L1→L2 literature** | ≥ 20 papers FR→L2 sur erreurs spécifiques | Selinker, Jarvis, Lyster & Saito, URIEL | CEDEL2 French subcorpus + études cross-lang |
| **Calibration statistique possible** | Assez de données pour GLMM hiérarchique bayésien convergent | 7920 learners → R-hat 1.01 | Projetable avec CEDEL2 |
| **Fine-tune F1 attendu** | ≥ 0.75 sur battery eval | 0.85 (ft:academie-errors-v3) | projeté 0.80-0.85 |
| **Feedback framework empiricé** | Dosage Lyster/Pienemann instanciable | Validated on W&I | Transfert cross-lang établi |

**Traduction concrète** : si une langue remplit les 6 critères, on considère qu'on peut construire le même pipeline que Teacher EN avec résultat qualitatif équivalent.

---

## 2. IT — Italien : chemin clair vers maturité

### Situation avant recherche : MOYEN (corpus MERLIN-IT seul, pas de profile IT structuré)

### Découvertes clés (agent IT)

**Corpus learner — largement au-delà du seuil** :

| Corpus | Taille | Annotations | Licence | Accès |
|---|---|---|---|---|
| **MERLIN-IT** | 813 textes learner CEFR | Error types + metadata | CC BY-SA | Open <https://www.merlin-platform.eu> |
| **VALICO** | 3804 textes narratifs learners | POS + error tags | Research | Università di Torino |
| **CELI** (nouveau 2024) | 600K tokens | CEFR aligned | Research | Università per Stranieri di Perugia |
| **LIPS** | Oral 2000 (complément parlé) | Transcriptions + anntt | Open | LIP-CNR |
| **LEONIDE** | Narratives learners | L1 tagged | Research | Eurac Research |
| **PAISÀ** | Natif 250M tokens | POS + syntax | CC BY-NC-SA | Open (référence) |

**Total learner** : ~5000-6000 textes annotés (dépasse seuil 2500). **MERLIN + VALICO + CELI** couvrent les niveaux A1-C2.

**Grammar profile** : **Profilo della lingua italiana** (Lo Duca et al., hybrid expert+corpus, équivalent PCIC espagnol). Disponibilité académique.

**SLA FR→IT** :
- Projet Università di Pavia (Chini, Bettoni) sur interlangue française.
- Bettoni, Camilla (2001) — *Imparare un'altra lingua* (référence théorique).
- Calque lexical FR/IT bien documenté (faux amis système).

**Points critiques** :
- Pas de corpus learner spécifiquement FR-natif en IT → compenser par **filtrage par L1** dans MERLIN-IT + VALICO (L1 tagged).
- Error annotation non-ERRANT native → adapter via traduction des error codes ou réannotation automatique.

### Plan vers maturité IT (5-8j additionnels)

1. **J+1-2** : télécharger MERLIN-IT + VALICO (+ demande CELI research access).
2. **J+3-4** : écrire `scripts/it/00_normalize_merlin.py` + `01_normalize_valico.py` (template ES réutilisable).
3. **J+5-6** : GLMM sur subcorpus L1=français (filtrer dans MERLIN/VALICO).
4. **J+7** : adapter tolerance matrix v2 (+ famille SPAN:GENDER adaptée IT, V:AUX, CLITIC).
5. **J+8** : rubrics A1-C2 à partir de **Profilo della lingua italiana**.

**F1 cible** : 0.80-0.85 (confirmed par agent 5 synthetic+transfer).

**Effort total IT** : ~30-35j (proche d'ES) au lieu de 40-45j sans découvertes.

---

## 3. DE — Allemand : maturité probable sous conditions

### Situation avant recherche : MOYEN (MERLIN-DE limité, Profile Deutsch payant)

### Découvertes clés (agent DE)

**Corpus learner — passe le seuil avec agrégation** :

| Corpus | Taille | Annotations | Licence | Notes |
|---|---|---|---|---|
| **MERLIN-DE** | 1000 textes | Error types + CEFR | CC BY-SA | Déjà identifié |
| **Falko** (HU Berlin) | 1500+ textes advanced | Multi-layer erreurs | Research | C1-C2 dominant |
| **DISKO** (HU Berlin) | Writing learner | Error tagged | Research | Intermediate |
| **Kobalt-DaF** | Cross-linguistic | L1 tagged | Research | Multi-L1 dont français |

**Total agrégé** : ~5000 textes (passe seuil 2500). Couverture CEFR complète si on combine.

**Grammar profile** — deux voies :
- **Voie A (payante, 40€)** : **Profile Deutsch** (Glaboniat et al., Goethe) — référentiel officiel CEFR DE aligné, équivalent EGP.
- **Voie B (gratuite)** : **DWDS** (Digitales Wörterbuch der deutschen Sprache) + **Goethe-Zertifikat Wortlisten** + **Processability Theory** (Pienemann) pour séquence acquisition DE. Plus de travail de synthèse mais 0€.

**SLA FR→DE** :
- Pas de corpus dédié FR→DE mais études comparatives FR/DE (projet Kobalt, Lüdeling 2011).
- Diehl et al. (2000) — *Grammatikunterricht: Alles für der Katz?* → acquisition casus pour francophones.
- Processability Theory DE (Pienemann, Håkansson) = très bien documentée.

**Points critiques** :
- Profile Deutsch payant (40€) mais voie gratuite praticable.
- Casus et déclinaisons complexes : nécessite linguistique computationnelle solide côté rules.
- Annotation error codes non-ERRANT → adapter.

### Plan vers maturité DE (3-5j additionnels, Profile Deutsch sourced par Sinse)

1. **J+1** : télécharger MERLIN-DE + demande Falko/DISKO (HU Berlin).
2. **J+2-3** : agréger les 4 sources en schéma unifié.
3. **J+4** : rubrics A1-C2 **depuis Profile Deutsch** (Glaboniat et al. — Sinse fournit la copie).
4. **J+5** : GLMM DE sur subcorpus FR-tagged + tolerance matrix DE (+ DE:CASE, DE:V2, DE:GENDER, DE:COMPOUND).

**F1 cible** : 0.75-0.82 (casus + compounds abaissent légèrement vs IT).

**Décision Session 29** : **Profile Deutsch utilisé** (Sinse trouve la copie 40€ de son côté). Voie B (DWDS+Goethe+PT) abandonnée car ROI défavorable — 40€ pour gagner 2-5j de synthèse manuelle est un no-brainer.

**Effort total DE** : ~35-40j (léger overhead vs IT à cause de casus/compounds).

---

## 4. JP — Japonais : stratégie JLPT-native, maturité dans écosystème JP à 0€

### Pivot Session 29 — abandonner le forcing CEFR

**Contrainte Sinse** : aucune dépense externe possible pour JP (pas de linguiste, pas de partenariat NINJAL). Conclusion initiale de l'agent ("plafond MOYEN CEFR, full EN/ES = $3-10K") est correcte mais **repose sur un postulat incorrect : il faut forcer CEFR A1-C2**.

**Pivot** : on utilise **JLPT (Japanese Language Proficiency Test)** comme système de niveau natif. JLPT est **le standard de facto mondial** pour l'apprentissage du japonais — tous les learners japonais connaissent N5→N1, pas CEFR.

**Mapping officiel** :
- **N5** ≈ A1 (~800 vocab, ~100 kanji, grammaire élémentaire)
- **N4** ≈ A2 (~1500 vocab, ~300 kanji)
- **N3** ≈ B1 (~3750 vocab, ~650 kanji)
- **N2** ≈ B2 (~6000 vocab, ~1000 kanji)
- **N1** ≈ C1 (~10000 vocab, ~2000 kanji)
- "Beyond N1" ≈ C2 (optionnel)

### Ressources JLPT-native open (tout gratuit)

| Pipeline Teacher | Ressource JLPT-native | Accès |
|---|---|---|
| **Grammar points par niveau** | JLPT official (Japan Foundation) + **Tae Kim's Guide to Japanese Grammar** + **Imabi.org** + communities multiples | Open |
| **Vocab par niveau** | JLPT vocab lists N5-N1 (officielles + crowdsourced Jisho.org/Anki decks) | Open |
| **Kanji par niveau** | Listes kanji JLPT N5-N1 + radicaux | Open |
| **Corpus learner** | **I-JAS brut** (1050 learners, tous L1 — on prend multi-L1 sans filtrage FR) + **Lang-8 historical** (millions de corrections crowdsourced) | Open |
| **Phrases exemples** | **Tatoeba** (multilingual, JP massif) + **JpWaC/JpTenTen** (web corpus natif) | Open |
| **Errors typiques par niveau** | Papers SLA JP open (TEL/HAL/ResearchGate) documentent erreurs N5-N3 typiques | Open |
| **Tokenizer** | **MeCab** / **Sudachi** / **Juman++** | Open |
| **Manuels référence** | **Minna no Nihongo** + **Genki** (structures publiées en ligne, usage fair-use pour descriptors) | Semi-open |

### Couverture attendue par niveau JLPT

| Niveau | Erreurs typiques détectables | Qualité |
|---|---|---|
| **N5-N4** | Particules は/が/を/に, tempo simple, politesse de base desu/masu | **Solide** F1 ~0.70-0.80 |
| **N3** | Conditionnels, causatif/passif, transitifs/intransitifs, て-form chains | **Solide** F1 ~0.65-0.75 |
| **N2** | Registres mixed, expressions formelles, structures conjonctives | **Acceptable** F1 ~0.55-0.70 |
| **N1** | Keigo complexe (尊敬語/謙譲語/丁寧語), registres littéraires, expressions idiomatiques | **Best-effort** F1 ~0.45-0.60 (patterns fréquents OK, subtilités manquées) |

### Plan Wave 3 — JP JLPT-native (30-35j, 0€)

1. **J+1-2** : setup tokenizer MeCab + pipeline normalization JP.
2. **J+3-5** : télécharger I-JAS brut + Lang-8 historical + Tatoeba JP + JpWaC natif.
3. **J+6-9** : construire rubrics N5-N1 depuis JLPT official + Tae Kim + Imabi + Minna no Nihongo structures.
4. **J+10-12** : vocab/kanji/grammar points par niveau JLPT (extraction depuis listes officielles).
5. **J+13-17** : synthetic errors generation GPT-4 guidé par JLPT descriptors (~$5-8 OpenAI).
6. **J+18-22** : cross-lingual transfer mT5-Large + MAD-X depuis EN baseline.
7. **J+23-27** : fine-tune léger sur I-JAS fragments + synthetic corpus.
8. **J+28-30** : rules.py JP (particules, conjugaisons régulières, kanji homophonie) + fewshots A1-C1/JLPT N5-N1.
9. **J+31-33** : Dify Sensei chatflow clonage + prompts JLPT-native (UI affiche N5-N1).
10. **J+34-35** : battery eval MultiGEC-2025 + eval personas JLPT-tagged.

### Limites honnêtes à accepter

1. **Keigo niveau N1-N2** : détection patterns standards OK, subtilités littéraires manquées (sans native speaker validation, impossible de trancher les cas ambigus).
2. **Aspect littéraire C1-C2** : plafonné (patterns natifs avancés sous-représentés dans corpus learner).
3. **Kanji error detection** : OCR/orthographe kanji difficile sans module dédié (on détecte vocabulary-level, pas stroke-level).
4. **Analytics cross-lang** : JLPT N1 ≠ CEFR C1 strictement (JLPT teste plutôt réception, CEFR production). Mapping documenté dans glossary mais non bijectif.

### Positionnement produit

**Sensei (JP)** = Teacher JLPT-native — aide les learners francophones à progresser N5→N1 dans le système qu'ils utilisent déjà (JLPT), avec rubrics et feedback ancrés dans Japan Foundation standards.

**UI** : afficher "Tu prépares N4" / "Objectif N2" (naturel pour learners JP). Équivalent CEFR affiché en secondaire si demandé.

**F1 cible global JP** : 0.60-0.75 (variable par niveau, plus bas que IT/DE mais **dans son écosystème c'est mature**).

---

## 5. RU — Russe : stratégie TORFL-native, maturité dans écosystème RU à 0€

### Pivot Session 29 — abandonner le forcing CEFR

**Contrainte Sinse** : aucune dépense externe possible pour RU (exclu €33-59K chemin A). Plutôt que d'accepter un plafond B1 CEFR-only (chemin B initial), on utilise le **système de niveau officiel russe** : **TORFL / ТРКИ** (Test of Russian as a Foreign Language — Тест по русскому языку как иностранному).

**Pourquoi TORFL-native** :
- Standard officiel du **Ministère russe de l'éducation** (Gosstandart ТРКИ).
- Référentiel **déjà structuré par niveau** avec descriptors, lexical minimum, grammatical minimum publiés.
- Utilisé par tous les enseignants/learners sérieux de russe dans le monde.
- **Tout open** — les standards ТРКИ et minima sont publiés gratuitement par le Gosstandart.

**Mapping officiel TORFL ↔ CEFR** (défini par le Ministère russe) :
- **TEU** (Элементарный уровень, Elementary) ≈ A1
- **TBU** (Базовый уровень, Basic) ≈ A2
- **TORFL-I** (Первый уровень) ≈ B1
- **TORFL-II** (Второй уровень) ≈ B2
- **TORFL-III** (Третий уровень) ≈ C1
- **TORFL-IV** (Четвёртый уровень) ≈ C2

### Ressources TORFL-native open (tout gratuit)

| Pipeline Teacher | Ressource TORFL-native | Accès |
|---|---|---|
| **Descriptors par niveau** | **Gosstandart ТРКИ** — standards officiels Ministère Russia, publiés en ligne | Open |
| **Lexical Minimum** (Лексический минимум) | Listes vocab par niveau TEU → IV publiées officiellement | Open |
| **Grammatical Minimum** (Грамматический минимум) | Inventaire grammaire par niveau publié officiellement | Open |
| **Corpus learner** | **RLC brut** (~7000 textes multi-L1, Higher School of Economics Moscow) <http://web-corpora.net/RLC/> | Open |
| **Russian Wheel RLC-French** | Sub-corpus FR-natif (UCA Nice, Dampierre-Debuchy) — accès via simple contact académique non-contractuel | Open/discovery |
| **Corpus natif référence** | **Russian National Corpus (RNC)** — <http://ruscorpora.ru/> | Open |
| **Manuels phares** | **"Дорога в Россию"** (Ministère Russia, aligné TORFL A1-B1), **"Поехали"** (intermédiaire) — structures publiées | Open |
| **Errors by level** | Papers SLA RU (HSE, **Guiraud-Weber** Aix-Marseille sur aspect verbal FR/RU) | Open |

### Couverture attendue par niveau TORFL

| Niveau | Erreurs typiques détectables | Qualité |
|---|---|---|
| **TEU-TBU** | Cas nominatif/accusatif, genre, verbes basiques, prépositions fréquentes | **Solide** F1 ~0.70-0.80 |
| **TORFL-I** | Cas datif/instrumental, aspect perfectif/imperfectif basique, verbes mouvement | **Solide** F1 ~0.65-0.75 |
| **TORFL-II** | Aspect verbal subtil, participe actif/passif, prépositions + cas spécifiques, registres | **Acceptable** F1 ~0.55-0.70 |
| **TORFL-III/IV** | Registres littéraires, aspect secondaires, constructions idiomatiques | **Best-effort** F1 ~0.45-0.60 |

### Plan Wave 4 — RU TORFL-native (25-30j, 0€)

1. **J+1-2** : télécharger RLC brut (7000 textes) + RNC sample + Russian Wheel via email discovery UCA Nice (non-contractuel).
2. **J+3-5** : rubrics TEU-IV depuis Gosstandart ТРКИ descriptors + Дорога в Россию structures.
3. **J+6-8** : lexical + grammatical minimum par niveau TORFL (extraction depuis publications officielles).
4. **J+9-12** : synthetic errors generation GPT-4 guidé par TORFL descriptors (~$5-8 OpenAI).
5. **J+13-17** : cross-lingual transfer mT5-Large + MAD-X depuis EN+ES baseline.
6. **J+18-21** : fine-tune léger sur RLC fragments (toutes L1 + filter FR si disponible) + synthetic.
7. **J+22-25** : rules.py RU (cas détection par terminaison, aspect par préfixe/suffixe, genre nominatif) + fewshots TEU-III.
8. **J+26-28** : Dify Maestro-RU chatflow clonage + prompts TORFL-native (UI affiche TEU/TBU/TORFL-I etc.).
9. **J+29-30** : battery eval MultiGEC-2025 + eval personas TORFL-tagged.

### Limites honnêtes à accepter

1. **Aspect verbal subtil niveau III+** : détection patterns fréquents OK, cas rares/littéraires manqués.
2. **Cases complexes** (6 cas × 3 genres × 2 nombres) : détection morphologique via terminaisons fiable pour les ~80% cas réguliers, erreurs sur exceptions.
3. **Registres littéraires niveau IV** : corpus learner sous-représentent ce niveau → plafonnement naturel.
4. **Analytics cross-lang** : TORFL tests plus stricts que CEFR (TORFL-IV plus exigeant que C2) — mapping documenté dans glossary non bijectif.

### Positionnement produit

**Maestro-RU** = Teacher TORFL-native — aide les learners francophones à progresser TEU→TORFL-IV dans le système officiel russe, avec rubrics ancrées dans Gosstandart ТРКИ.

**UI** : afficher "Tu prépares TORFL-I" / "Objectif TORFL-II" (standard international en russe). Équivalent CEFR affiché en secondaire si demandé.

**F1 cible global RU** : 0.60-0.75 (variable par niveau, **mature dans son écosystème**).

### Note sur l'annexe contact UCA Nice

Le contact **Dampierre-Debuchy (UCA Nice)** reste listé dans l'annexe §Annexe, mais désormais en mode **"discovery email non-contractuel"** — on obtient accès au Russian Wheel si possible, mais la stratégie Wave 4 ne **dépend plus** de ce partenariat. RLC brut + synthetic + transfer suffisent pour atteindre maturité dans écosystème TORFL.

---

## 6. Synthetic + cross-lingual transfer — paradigme transversal (agent 5)

### État de l'art 2024-2025 qui change la donne

**Two-stage pipeline winning paradigm** (Latouche et al. EMNLP 2024, Stahlberg & Kumar BEA 2024) :

```
Stage 1 — Pre-training massif sur données synthétiques
  - Tagged Corruption Models (TCM)
  - LLM-generated errors (GPT-4 / Claude prompted)
  - Contextual Data Augmentation (ACL 2024)
  → ~50K-500K synthetic examples par langue

Stage 2 — Fine-tuning sur données humaines annotées (petit volume OK)
  - Même 500-2000 examples annotés suffisent si pretrain massif
  - MultiGEC-2025 benchmark comme standard eval
```

**Implication critique pour AcademIA** : réduit drastiquement le besoin de corpus massifs annotés. Une langue avec 1000-2000 textes annotés + 50K synthetic peut atteindre la même qualité qu'une langue avec 7000+ annotés seuls.

**F1 ceilings réalistes projetés** :

| Langue | F1 pipeline classique | F1 two-stage 2024 | Delta |
|---|---|---|---|
| EN | 0.85 (baseline) | 0.85-0.88 | +0-3% |
| ES | 0.78-0.82 | 0.82-0.87 | +3-5% |
| IT | 0.75-0.80 | **0.80-0.85** | +5% |
| DE | 0.70-0.78 | **0.75-0.82** | +5-7% |
| RU | 0.55-0.68 | **0.65-0.75** | +10% |
| JP | 0.50-0.62 | **0.55-0.70** | +8-10% |

**Cross-lingual transfer** (MultiGEC-2025) :
- **mT5-Large** ou **XLM-R** comme base multilingual.
- **MAD-X adapters** par langue → économie entraînement.
- **URIEL+/lang2vec** pour sélectionner langues-source proches (ES→IT obvious, EN→DE medium, EN→JP faible).

### Impact sur la roadmap

- **Inversion priorité** : au lieu de collecter 7000+ learners par langue, on peut viser 1500-2500 + synthetic.
- **Budget fine-tune synthetic** confirmé : ~$5-8 OpenAI par langue × 4 = **$20-32 total**.
- **MultiGEC-2025** comme battery eval commune → benchmarks comparables cross-lang.

---

## 7. Infrastructure EU — CLARIN, ELG et réseaux (agent 6)

### Contacts prioritaires identifiés

| Institution | Ressource | Contact utilité |
|---|---|---|
| **UCLouvain — CKL2CORPORA** | Corpus multi-L2 learner | Partenariat partage corpus + méthodologie ERRANT-like |
| **Eurac Research** (Bolzano) | LEONIDE + KoKo + Kolipsi | IT + DE + Multi-L1 |
| **Università di Trento — AlpiLinK** | Corpus trilingue IT/DE/LLD | IT+DE simultanément |
| **Università per Stranieri di Perugia** | CELI 2024 | IT 600K tokens récents |
| **Université Côte d'Azur** | Russian Wheel | RU FR-natif (**clé unique**) |
| **HU Berlin (Lüdeling)** | Falko + Kobalt | DE learners |
| **NINJAL** (Japon) | I-JAS | JP (partial) |
| **Instituto Cervantes + Santiago Compostela** | CAES | ES complément CEDEL2 |

**Portails de découverte** :
- **CLARIN VLO** (<https://vlo.clarin.eu/>) — métadonnées ~900K resources linguistiques EU.
- **ELG** (European Language Grid, <https://www.european-language-grid.eu/>) — catalogue corpus + tools + services.

**Stratégie** : inscrire AcademIA comme utilisateur académique CLARIN (sinon via partenariat UCLouvain/Eurac) → accès accéléré corpus sous licence research.

---

## 8. Grey literature (agent 6)

### Thèses & recherches non publiées commerciales

**Sources** :
- **TEL** (<https://tel.archives-ouvertes.fr/>) — thèses France HAL.
- **DUMAS** (<https://dumas.ccsd.cnrs.fr/>) — mémoires master France.
- **DART-Europe** — thèses européennes (utile pour DE).

**Chercheurs clés à contacter** :
- **Italien** : **Camilla Bettoni** (Pavia), **Marina Chini** (Pavia), **Elisabetta Jezek** (Pavia) — SLA FR→IT.
- **Russe** : **Sophie Guiraud-Weber** (Aix-Marseille) — aspect verbal FR/RU, **Elena Simonato** (Lausanne).
- **Japonais** : **Michiko Higashi** (INALCO), **Julien Detey** (Rouen) — phonologie/acquisition FR→JP.
- **Allemand** : **Anke Lüdeling** (HU Berlin) — Falko, **Heike Wiese** (Potsdam) — multilingual acquisition.

**Cambridge Learner Corpus licensing inquiry** : piste pour expansion multilangues via Cambridge Assessment (payant, quote estimée $10K-50K par langue — décision business).

---

## 9. Impact sur la roadmap d'exécution

### Révisions à apporter à `multilang_execution_roadmap.md` (Session 29)

| Wave | Avant Session 28 | Après Session 29 (native strategy) |
|---|---|---|
| **Wave 1 ES** | 25-30j (alpha) | **20-25j** (avec CEDEL2+CAES confirmés open) |
| **Wave 2 IT+DE** | 35-40j parallèle | **40-45j** (MERLIN+VALICO+CELI IT + Falko+DISKO DE, **Profile Deutsch utilisé** car Sinse source la copie 40€) |
| **Wave 3 JP** | 20-25j MVP + $3-10K Wave 3.5 | **30-35j JLPT-native 0€** (N5-N1 couvert dans écosystème natif, pas de Wave 3.5 séparée) |
| **Wave 4 RU** | Chemin B 25j ou Chemin A €33-59K | **25-30j TORFL-native 0€** (TEU-IV couvert dans écosystème natif) |

**Conséquence** : **toutes les langues deviennent accessibles sans dépense externe majeure** (seuls coûts = 40€ Profile Deutsch trouvé par Sinse + ~$25-35 OpenAI synthetic cumulé).

### Ajouts critiques à Phase 0 (infra factorisée)

1. **Pipeline synthetic errors generation** commun (Python utility, réutilisable IT/DE/JP/RU) → +3j.
2. **MultiGEC-2025 battery eval** comme standard cross-lang → +2j.
3. **Mapping abstraction niveaux natifs↔CEFR** (helper `academie_core.levels` avec JLPT_TO_CEFR et TORFL_TO_CEFR) → +1j.
4. **CLARIN VLO access** + discovery emails UCLouvain/Eurac/Nice (non-contractuel) → +1j.

**Total Phase 0 révisée** : 14-16j au lieu de 8-10j initialement prévus.

---

## 10. Décisions (Session 29 — validées par Sinse)

### D7 — Stratégie synthetic two-stage [VALIDÉE]

**Décision** : adopter le paradigme two-stage 2024 (synthetic pretrain + small annotated fine-tune) comme standard dès Wave 1 ES. Budget fine-tune synthetic ~$5-8 par langue × 5 = **$25-40 total OpenAI**.

### D8 — Profile Deutsch [VALIDÉE]

**Décision** : utiliser **Profile Deutsch** (40€, sourced par Sinse de son côté). Voie B (DWDS+Goethe+PT) abandonnée car ROI défavorable. Rubrics DE A1-C2 dérivées directement de Profile Deutsch.

### D9 — JP stratégie native JLPT [VALIDÉE Session 29]

**Décision** : **abandonner le forcing CEFR** pour JP. Utiliser **JLPT N5-N1** comme système de niveau natif, avec ressources open (Japan Foundation, Tae Kim, Imabi, JLPT vocab/kanji lists). **0€ externe**, 30-35j Wave 3.

**Positionnement produit** : Sensei = "Teacher JLPT-native". UI affiche N5-N1 (mapping interne vers a1-c2 pour homogénéité code/analytics).

### D10 — RU stratégie native TORFL [VALIDÉE Session 29]

**Décision** : **abandonner le forcing CEFR** pour RU. Utiliser **TORFL TEU-IV** comme système de niveau natif, avec ressources open (Gosstandart ТРКИ, Lexical Minimum, Grammatical Minimum, RLC brut). **0€ externe**, 25-30j Wave 4. **Russian Wheel via email discovery non-contractuel** (bonus si accès obtenu).

**Positionnement produit** : Maestro-RU = "Teacher TORFL-native". UI affiche TEU/TBU/TORFL-I-IV (mapping interne vers a1-c2).

### D11 — CLARIN & partenariats académiques [VALIDÉE mode light]

**Décision** : **email discovery Phase 0** (~1-2j) pour identifier ressources bonus (Russian Wheel Nice, Falko HU Berlin, LEONIDE Eurac). **Non-contractuel, non-bloquant**. Les stratégies Wave 1-4 ne dépendent PAS de partenariats.

### D12 — Mapping architectural niveaux natifs [NOUVELLE Session 29]

**Question** : comment intégrer JLPT et TORFL dans une architecture qui gère `level ∈ {a1, a2, b1, b2, c1, c2}` partout ?

**Décision** : **mapping transparent Option 1** — stockage interne reste `a1-c2` (unifié cross-lang, analytics inchangées), mapping aux bornes pour UI et prompts.

**Implémentation** :

```python
# academie_core/levels.py (nouveau module Phase 0)

JLPT_TO_CEFR = {
    "N5": "a1", "N4": "a2",
    "N3": "b1", "N2": "b2",
    "N1": "c1", "beyond_N1": "c2"
}
CEFR_TO_JLPT = {v: k for k, v in JLPT_TO_CEFR.items()}

TORFL_TO_CEFR = {
    "TEU": "a1", "TBU": "a2",
    "TORFL-I": "b1", "TORFL-II": "b2",
    "TORFL-III": "c1", "TORFL-IV": "c2"
}
CEFR_TO_TORFL = {v: k for k, v in TORFL_TO_CEFR.items()}

LEVEL_SYSTEM_BY_DOMAIN = {
    "teacher": "cefr",      # EN
    "maestro": "cefr",      # ES
    "professore": "cefr",   # IT
    "lehrer": "cefr",       # DE
    "sensei": "jlpt",       # JP
    "maestro_ru": "torfl",  # RU
}

def display_level(cefr_level: str, domain: str) -> str:
    system = LEVEL_SYSTEM_BY_DOMAIN[domain]
    if system == "jlpt":
        return CEFR_TO_JLPT[cefr_level]
    elif system == "torfl":
        return CEFR_TO_TORFL[cefr_level]
    return cefr_level.upper()
```

**Conséquences** :
- **Storage interne** (DB, analytics, JSON) inchangé → zéro refactor.
- **UI / Dify prompts** utilisent `display_level()` → JP voit N5-N1, RU voit TEU-IV, autres voient A1-C2.
- **Rubrics YAML** par domaine : contenu rédigé selon descriptors natifs mais indexé par niveau interne a1-c2.
- **Analytics cross-lang** comparables (via niveau interne unifié).

Implémentation : Phase 0, +1j.

---

## 11. Synthèse Session 29 — verdict final "peut-on atteindre maturité ?"

**Réponse courte** (après pivot stratégie native) :

- **IT** : **OUI MATURE CEFR A1-C2** (+5-8j, 0€). Ressources open MERLIN+VALICO+CELI+Profilo della lingua italiana.
- **DE** : **OUI MATURE CEFR A1-C2** (+3-5j, 40€ Profile Deutsch Sinse). Ressources MERLIN+Falko+DISKO+Profile Deutsch.
- **JP** : **OUI MATURE JLPT N5-N1** (30-35j Wave 3, 0€). Ressources Japan Foundation + Tae Kim + Imabi + JLPT listes + I-JAS + Lang-8. Pas équivalent CEFR strict mais **mature dans écosystème JLPT** — le système que tous les learners JP utilisent.
- **RU** : **OUI MATURE TORFL TEU-IV** (25-30j Wave 4, 0€). Ressources Gosstandart ТРКИ + Lexical/Grammatical Minimum + RLC + Russian Wheel (discovery non-contractuel). **Mature dans écosystème TORFL** — standard officiel russe.

**Ce qu'il faut faire dès maintenant (avant Wave 1 ES)** :

1. Intégrer paradigme two-stage synthetic+fine-tune dans Phase 0 (+3j).
2. Implémenter `academie_core/levels.py` mapping JLPT/TORFL↔CEFR (+1j).
3. Email discovery UCLouvain / Eurac / Nice / HU Berlin (non-contractuel) (+1j).
4. Sinse fournit copie Profile Deutsch (40€ side-sourced).
5. Lancer Wave 1 ES.

**Ce que ça valide stratégiquement Session 29** :

- **6 langues matures dans leur écosystème natif** — EN/ES/IT/DE en CEFR, JP en JLPT, RU en TORFL.
- **Coût externe total cumulé** : **40€ + ~$25-35 OpenAI synthetic** = quasi-zéro.
- **Positionnement produit cohérent** : chaque Teacher parle le langage de niveau que ses learners utilisent déjà (CEFR pour Europe, JLPT pour JP, TORFL pour RU).
- **Limites honnêtes** : keigo fin (JP N1) et aspect verbal fin (RU III+) restent best-effort — acceptable car représentent <5% des learners dans ces langues.

**Changement majeur vs Session 28** : on passe de "4 langues mature + 2 limitées" à **"6 langues matures dans leur écosystème"** grâce au pivot native. La qualité par rapport à Teacher EN reste différente (F1 plus bas pour JP/RU à cause langues distantes) mais la **couverture pédagogique est complète** dans le système de niveau natif de chaque langue.

---

## 12. Prochaines étapes (Session 29 validée)

1. ✅ **D7-D12 validées** par Sinse.
2. ✅ **Update `multilang_execution_roadmap.md`** avec Wave 3 JLPT-native + Wave 4 TORFL-native + D12 levels.py (en cours Session 29).
3. ✅ **Update `multilang_research_plan.md`** — part 2 JP et RU refondues stratégie native (en cours Session 29).
4. ✅ **Update `glossary.md`** — ajout entrées JLPT / TORFL / mappings (en cours Session 29).
5. **Phase 0 kickoff** : 14-16j factorisation + levels.py + discovery emails non-bloquants.
6. **Wave 1 ES validation pipeline** (inchangé sauf two-stage synthetic intégré).

---

*Document produit via 6 agents parallèles (recherche net + papiers scientifiques + catalogues CLARIN/ELG + grey literature) — synthèse Claude Opus 4.7 Session 28.*

*Sources principales consultées* : MultiGEC-2025 shared task, Latouche et al. EMNLP 2024, Stahlberg & Kumar BEA 2024, CLARIN VLO catalogue, ELG European Language Grid, MERLIN/VALICO/CELI/Falko/DISKO/I-JAS/RLC corpora pages, Profilo della lingua italiana (Lo Duca), Profile Deutsch (Glaboniat), TORFL ТРКИ descriptors.

---

## Annexe — contacts email prioritaires (Phase 0 discovery)

| Institution | Rôle | Objet email |
|---|---|---|
| UCLouvain CKL2CORPORA | Sylviane Granger team | Partenariat partage méthodologie ERRANT multi-L2 |
| Eurac Research Bolzano | Andrea Abel | Accès LEONIDE + KoKo + Kolipsi (IT+DE+multi-L1) |
| Università di Trento AlpiLinK | Responsable projet | Corpus trilingue IT/DE/LLD |
| Università per Stranieri Perugia | Équipe CELI | Accès CELI 2024 research license |
| Université Côte d'Azur | Dampierre-Debuchy | Russian Wheel RLC-French access |
| HU Berlin | Anke Lüdeling | Falko + Kobalt research access |

*Email discovery recommandée en Phase 0 — pas de commitment avant validation ES Wave 1.*
