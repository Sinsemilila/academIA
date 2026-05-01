---
title: AccountingDomain — Tuteur compta complémentaire formation Studi RNCP41653
status: draft
last_reviewed: 2026-05-01
owner: claude
---

# AccountingDomain (FR) — Tuteur complémentaire Studi Pré-Graduate Assistant Comptable

> **Status** : DRAFT conceptuel S57. Premier domaine non-linguistique d'AcademIA. Scope précisé via PDF programme Studi 2026-05-01. ADR-017 pending.

## 1. Apprenante & contexte

**Marie** — formation **Studi Pré-Graduate Assistant Comptable** :
- **Certification** : RNCP41653 (décision France Compétences 27/11/25, **tout neuf**), niveau 4 (Bac), partenariat académique Comptalia
- **Durée** : 380h sur 9 mois, 100% en ligne, IA intégrée Studi (= concurrence directe)
- **Format Studi** : cours écrits + vidéos + 10 000 classes virtuelles + ~111 "Cas Studi" exercices pratiques (Cas Vincent, Pelat, Tachet, Z, JP, Louis, Alpha, etc.)
- **Évaluation** : 3 mises situation pro (BC1 3 parties, BC2 2 parties, BC3 4 parties + vidéo 6-8 min) + 1 QCM/bloc 30-180min + étude cas QCM 45min
- **Pré-requis** : Diplôme niveau 3 (CAP/BEP) — Marie remplit
- **Logiciel cible Studi** : **Sage Ligne 100** (compta) + **Sage v10** (paie)

## 2. Positionnement de l'agent — NON-remplaçant, COMPLÉMENT

**Studi a déjà** : cours, vidéos, 111 cas, classes virtuelles, accompagnement pédagogique 24h ouvrées, Career Center.

**Agent AcademIA n'est PAS un substitute Studi**. Il est un **tuteur perso 24/7** qui :

| Use case agent | Pendant que Studi fait... |
|----------------|---------------------------|
| Récap d'un concept en 5 min | Le cours dure 45 min |
| Génère un cas similaire à "Cas Pelat" pour s'entraîner | Studi propose 1-2 cas, on en veut 5-10 |
| Explique "pourquoi cette écriture ?" quand le cours reste opaque | Forum Studi répond en 24h, agent en 30s |
| Prépare le QCM bloc N (drill flashcards-like) | Studi évalue à la fin |
| Simule l'étude de cas finale 45 min | Studi évalue 1 fois en juin/décembre |
| Coache la motivation (autodidacte = isolement) | Career Center est plus career, pas affectif |

**Différenciation** : pratique illimitée + feedback immédiat sur ses propres écritures + adapté à son rythme + posture pédagogique Lyster (prompts/scaffolds) vs explicit-correction Studi.

## 3. Proficiency scale — blocs RNCP41653 × niveau acquisition

Mapping réel formation Studi :

### Bloc 1 — Traiter les travaux comptables courants et de clôture

Sous-modules officiels (12 macro-thèmes) :
1. Découvrir objectifs compta + profession comptable
2. Compte de résultat + bilan (présentation + détail comptes)
3. Écritures comptables + balance comptable
4. **TVA** : mécanisme + comptabilisation (taux, déductibilité, fait générateur, intracom, import/export, avances/acomptes)
5. **Factures** : doit, avoir, frais de port, sous-traitance, acquisition immobilisations
6. Opérations courantes hors factures : effets de commerce, charges personnel comptabilisation, modes règlement
7. **Facturation électronique + IA comptable** (récent !)
8. Rapprochement bancaire + suivi tiers + trésorerie prévisionnelle
9. Identifier/corriger anomalies (manuel + IA)
10. Variations stocks + amortissements (linéaire, dégressif, par composants, par UO)
11. Amortissements fiscaux + dépréciations + provisions (créances douteuses, titres, PRC)
12. Cessions immobilisations/VMP + autres opérations inventaire (CCA/PCA, emprunts indivis, opérations hors zone €, subventions, livraisons à soi-même, IS) + comptes annuels (bilan/CR/annexe) + affectation résultat
13. **Sage Ligne 100** : ergonomie, paramétrage plan comptable, saisie, modèles, automatisation, rapprochement auto, lettrage, déclaration TVA, états comptables, gestion analytique, clôture exercice

### Bloc 2 — Préparer les éléments de paie et les déclarations fiscales

Sous-modules :
1. **Paie** : préparer éléments (gestion paie, temps travail, rémunération brute, congés payés, heures sup/comp, avantages nature, IJSS, cotisations, réductions)
2. **Bulletins** : paramétrer + éditer (salaire net/imposable, prélèvement source, net social) + **Sage v10** (création société, paramétrage établissement, fiches salariés, bulletins modèles, cotisations, déclarations sociales)
3. **TVA déclaration** : champ application/territorial, exigibilité, déductibilité, régularisations, régimes particuliers/imposition, modalités règlement, crédit TVA, **CA3** + **CA12**

### Bloc 3 — Gérer accueil + travaux administratifs courants

Sous-modules :
1. Écrits professionnels (rapport, compte-rendu, note synthèse/service, structuration, prise de notes manuelle/digitale, lecture rapide, relance clients, **Word**)
2. Classement + archivage + RGPD + IA pour organisation documentaire
3. Communication accueil physique/téléphonique (techniques reformulation, désamorçage conflit, secret/discrétion, accueil personnes en situation handicap)
4. Reportings (**Excel** : formules base, mise en forme, tris/filtres, graphiques, TCD, tableaux de bord)

### Bonus — IA appliquée comptabilité

Modules IA dédiés (prompting, automatisation, analyse données, correction). Marie sera **utilisatrice avertie de prompts** — implication : agent AcademIA peut **enseigner le meta-prompting** parallèle.

### Niveaux acquisition par bloc

```
N0 decouverte    : concept exposé, pas autonome (≈ pré-cours Studi)
N1 guide         : autonome avec aide ponctuelle (≈ post-cours, 1er cas réussi)
N2 autonome      : tâche routine sans aide (≈ 5+ cas réussis, cible certif)
N3 expert_assist : gestion exceptions + auto-vérif (≈ post-emploi 6 mois)
```

**Cible certif RNCP41653** = N2 sur BC1+BC2+BC3.

## 4. Scenarios oracle — leverage corpus Studi 111 cas

**Décision majeure** : NE PAS dupliquer les Cas Studi (copyright + pédago Studi). Mais :
- Apprendre la **structure** des Cas Studi (input pédagogique typique)
- Générer **cas-similaires-pas-identiques** (montants random, dates random, contextes similaires)
- Format scenario YAML compta :

```yaml
id: bc1_tva_facture_fournisseur_001
domain: compta_fr_studi_rncp41653
scenario_key:
  agent: comptable_fr
  bloc: BC1                                    # BC1 / BC2 / BC3
  level: N1
  module: bc1_factures                         # mapping macro-module Studi
  error_category: tva_calcul
turns:
  - role: learner
    text: |
      Facture EDF reçue 15/03/2026 :
      - Consommation HT : 250€
      - TVA 20% : 50€
      - Total TTC : 300€
      Saisie proposée :
        Débit 6061 : 300€
        Débit 4456 : 60€
        Crédit 401 EDF : 360€
    expected_errors: [COMPTA:TVA_BASE_ERR, COMPTA:HT_TTC_CONFUSION]
expected_dimensions:
  cf_move_set_valid:
    acceptable: [partial_recast, prompt_plus_remediation, metalinguistic]
    forbidden: [explicit_correction]   # learner a tenté le bon schéma
  technical_accuracy:
    correct_answer:
      Débit 6061: 250
      Débit 4456: 50
      Crédit 401: 300
    learner_answer_check: deterministic   # comparable rules-based
```

## 5. Error taxonomy — codes initial proposés

Aligné Studi syllabus :

```
# BC1 — Saisie courante
COMPTA:DEBIT_CREDIT_INVERSE
COMPTA:HT_TTC_CONFUSION              # base TVA mal calculée (très courant débutant)
COMPTA:COMPTE_MISCLASS               # ex 6064 vs 6067, 401 vs 411
COMPTA:TVA_TAUX_ERR                  # 5.5/10/20 mauvais
COMPTA:TVA_DECDED_CONFUSION          # collectée vs déductible
COMPTA:DATE_INCOHERENTE              # pièce vs saisie vs exigibilité
COMPTA:LIBELLE_MANQUANT_FAIBLE
COMPTA:NUMERO_PIECE_MANQUANT
COMPTA:RAPPROCH_BANCAIRE_INCOMPLET
COMPTA:LETTRAGE_MISMATCH

# BC1 — Inventaire/clôture
COMPTA:AMORT_TAUX_ERR                # linéaire/dégressif/UO
COMPTA:DEPRECIATION_REPRISE_OUBLIEE
COMPTA:CCA_PCA_INVERSION             # charges constatées d'avance vs produits
COMPTA:CESSION_VNC_MAUVAIS

# BC2 — Paie
PAIE:BRUT_BASE_ERR                   # SMIC/cotisations base
PAIE:HEURES_SUP_TAUX_ERR
PAIE:CONGES_INDEMNITE_ERR
PAIE:NET_SOCIAL_OUBLI                # mention obligatoire 2024+
PAIE:PRELEVEMENT_SOURCE_TAUX_ERR

# BC2 — TVA déclaration
TVA:CA3_LIGNE_ERR
TVA:CA12_REGIME_ERR                  # SI/RSI confusion
TVA:CREDIT_TVA_REPORT_OUBLIE

# BC3 — Bureautique / écrits
BUREAU:EXCEL_FORMULE_ERR
BUREAU:FORMAT_DOCUMENT_PRO
BUREAU:CONFIDENTIALITE_RGPD_RISK
```

~25 codes core MVP. Whitelist FP + tolerance_matrix par niveau (pattern S55-S56).

## 6. Gravity axes — adaptation cross-domaine

| Axe lang | Axe compta | Definition |
|----------|------------|-----------|
| linguistic | **technical** | violation règle PCG/normative pure |
| communicative | **fiscal_legal** | impact déclaratif (TVA fausse → pénalité fiscale, charges sociales mal calculées → URSSAF) |
| social_pragmatic | **professional** | convention métier (libellé, numéro, ordre) — irritate réviseur |

## 7. Feedback Lyster transferable + nouvelles moves

| Lyster move | Compta exemple |
|-------------|----------------|
| `recast` | "Le bon compte est 6064, pas 6061" |
| `partial_recast` | "Tu es bien en classe 6, mais le sous-compte ?" |
| `explicit_correction` | "Non, débit 401, crédit 512 — pas l'inverse" |
| `prompt_plus_remediation` | "Rappelle-toi la règle de la partie double, et regarde où ça part" |
| `metalinguistic` | "C'est une charge externe, donc classe 6 — sous-compte selon nature" |
| `clarification_request` | "Pourquoi tu as choisi ce compte ?" |

**Nouvelle move possible (à valider)** : `show_balance` — visualisation balance après écriture (forme pédagogique propre compta, cf manipulation tabulaire).

## 8. Différences fondamentales vs langues — implications archi

| Aspect | Langue | Compta Studi RNCP41653 |
|--------|--------|------------------------|
| Production libre | Oui | **Non** (réponse exacte) |
| Validation | LLM judge nécessaire | **80% déterministe** (débit=crédit, taux TVA, calcul correct) |
| Authority anchor | Multi-source | **Mono-source** : PCG (ANC 2014-03) + BOFiP fiscal + RNCP41653 référentiel |
| Native variance | Énorme | Quasi nulle |
| Coût Oracle | LLM panel cross-provider élevé | **Bas** (rules + LLM seulement sur ambigus) |
| Corpus pédago | À construire (curriculum/fewshots) | **111 Cas Studi déjà existants** (template, pas duplication) |
| Logiciel | Texte pur | **Sage UI à reproduire/simuler ?** (gros question UX) |

**Implications archi** :
- `AccountingDomain.detect_errors()` = rules-based first (déterministe), LLM backup
- LLM utile surtout pour : génération exercices contextualisés, feedback Lyster narratif, diagnostic profond ("pourquoi tu as choisi ce compte ?"), récap concept
- **UI/UX** : ChatInput texte pur insuffisant pour saisie compta. Tableau journal multi-lignes ? Plan de comptes navigable ? Mockup Sage ? **Open question UX critique.**

## 9. Authority anchor data sources

**P0 acquisition (Phase 1)** :
- ✅ **Programme Studi** PDF (acquired S57 — `library/by-domain/formation marie/`)
- **Référentiel RNCP41653 officiel** France Compétences (à fetch web)
- **PCG règlement ANC 2014-03** — anc.gouv.fr (PDF officiel)
- **BOFiP TVA** sections fondamentales — bofip.impots.gouv.fr (web scrape ciblé)

**P1 corpus pédagogique (Phase 2)** :
- Annales DCG UE9 (Introduction à la comptabilité) — sujets + corrigés type cas Studi
- Manuel Béatrice & Francis Grandguillot "Comptabilité générale" — référence pédago canon
- Manuel Foucher / Nathan / Hachette compta bac pro

**P2 outils (Phase 3)** :
- Captures écrans Sage Ligne 100 + Sage v10 (sous-réserve droits, ou via Marie partage écran)
- Cerfa CA3 / CA12 / DSN / bulletin paie modèle

## 10. Open questions Sinse

1. **Phase 1 MVP scope** : juste **BC1 modules 1-5** (compta de base : R/B + écritures + balance + TVA mécanisme + factures) ? Ça représente déjà ~60-80h Studi équivalent + ~30 Cas Studi à pasticher.
2. **UI/UX critique** : ChatInput suffit pour MVP (en mode "explique-moi" + scenarios texte) ? OU dès MVP on prévoit composant tableau journal compta ?
3. **Marie sur quel rythme Studi ?** Démarrage déjà ? Quel BC en cours ? → cale notre Phase 1 sur ce qu'elle aborde dans les semaines à venir.
4. **Tutorat synchrone** : tu veux que toi-aussi tu interviennes (3-way Sinse + Marie + agent), ou agent pure solo Marie ?
5. **Anti-cheating** : si elle pratique sur agent, elle pourrait potentiellement copier réponse pour Studi. Probablement un faux problème (Studi a ses propres cas), mais à acter explicit.
6. **Nom de l'agent** : "Maître", "Comptable", "Sage", autre ? Cohérence avec Teacher/Maestro/Sensei/Lehrer convention.

## 11. Plan implémentation tentatif (post ADR-017)

**Phase 1 MVP (~5-8j)** : BC1 modules 1-5 (compta base + écritures + balance + TVA mécanisme + factures)
- ADR-017 acted
- Competency map BC1 modules 1-5 N0-N1 (~20 concepts)
- Error taxonomy MVP : 10 codes core (DEBIT_CREDIT_INVERSE, HT_TTC_CONFUSION, COMPTE_MISCLASS, TVA_*, LIBELLE/NUMERO_PIECE)
- Scenarios oracle : 12-15 scenarios basés Cas Studi pattern (montants/contextes différents)
- Detection : 80% rules + 20% LLM ambigus
- Agent prompt "Comptable_FR" Lyster moves transposed
- Tier 6 RE-MEASURE : ≥10/15 pass + 0 false-positive critique
- UI : ChatInput texte first, format saisie écriture libre parsée

**Phase 2 (~10-15j)** : étendre BC1 modules 6-13 (rapprochement, amortissements, dépréciations, comptes annuels) + démarrage BC2 paie

**Phase 3 (~15-20j)** : finir BC2 + BC3 + composant UI tableau journal + intégration Sage simulation (si stratégique)

## 12. Risques

- **R1 — Sur-LLM-isation** : tentation appliquer pattern Maestro/Teacher LLM-heavy alors que compta = mostly déterministe. Cost + variance inutiles.
- **R2 — Authority anchor désynchro légale** : ANC + BOFiP évoluent (réforme TVA, factur élec 2026). Versioning data layer obligatoire.
- **R3 — UI/UX critique** : ChatInput texte pur peut être insuffisant pour saisie écriture multi-lignes. Composant journal custom probablement requis Phase 2.
- **R4 — Niveau formateur Claude** : Claude peut produire écritures techniquement fausses (PCG misclass, taux TVA obsolètes 2025+). **Validation formateur humaine OBLIGATOIRE pré-déploiement** (cohérent L141 5-layer pipeline solo-dev). Marie reviewer first?
- **R5 — Concurrence Studi IA-intégrée** : Studi a déjà IA dans formation (modules dédiés). Risque que Marie utilise Studi-IA suffisant et trouve agent AcademIA redondant. **Différenciation = format conversationnel intime + Lyster scaffolding pédago vs Studi IA générique.**

---

*S57 v2 — scope précisé après acquisition PDF programme Studi RNCP41653. Pending Sinse decisions section 10 + ADR-017 acted.*
