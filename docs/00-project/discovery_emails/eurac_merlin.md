# Email Eurac Research — MERLIN

## Métadonnées

- **Destinataire principal** : Verena Lyding (verena.lyding@eurac.edu)
- **Cc** : Andrea Abel (andrea.abel@eurac.edu)
- **Site** : https://www.eurac.edu/en/institutes-centers/institute-for-applied-linguistics
- **MERLIN platform** : https://www.merlin-platform.eu
- **Objet** : Clarification license MERLIN + possible sous-corpus L1=français
- **Langue** : anglais (Eurac travaille en EN + IT + DE)

## Envoi

- **Date d'envoi** : ~2026-04 (à reconstituer)
- **Date de relance éventuelle (J+21)** : N/A (réponse reçue)
- **Réponse reçue** : 2026-05-05 par Egon W. Stemle (Eurac CLARIN Centre, pas Lyding/Abel direct)

## Réponse Stemle 2026-05-05 — synthèse

**Q1 Licence CC BY-SA 4.0** :
- ✅ Reuse permis hors usage académique (pas limité aux universités)
- Conditions : attribution + indication des changements + ShareAlike sur dérivés/redistribution
- ✅ Petite échelle éducatif (AcademIA actuel) : CC BY-SA suffit
- ⚠️ Si freemium/monétisé futur : **revoir ShareAlike obligations** sur derived/redistributed resources. Eurac propose de re-contacter pour discuter d'un arrangement licence différent si nécessaire.

**Q2 Sous-corpus L1=French** :
- ❌ Pas de release pré-packagée "L1=French" séparée
- ✅ Métadonnées corpus contiennent l'info L1 → extraction par filtre filename trivial
- **Pattern** : grep filenames `*-_French_-*.txt` dans `meta_ltext/german_metafn/` (et équivalent IT)
- **GitLab source** : https://gitlab.inf.unibz.it/commul/merlin-platform (tags alignés avec deposits CLARIN)
- **CLARIN release** = version stable citable long-terme : http://hdl.handle.net/20.500.12124/59

## Actions prises (2026-05-05, Session 60)

- Doc license confirmée dans [[multilang-italian-research]] (section MERLIN)
- Doc license confirmée dans [[multilang-german-research]] (section MERLIN)
- Pattern extraction L1=French documenté dans les deux research files
- Note ShareAlike pour future monétisation : à revisiter si pivot freemium

## Contenu

```
Dear Dr. Lyding, dear Dr. Abel,

I'm reaching out to ask a couple of questions about the MERLIN learner
corpus, which is central to a language-learning project I'm developing
(AcademIA — personal educational project for my family and close friends,
open-source-friendly, no commercial monetization at this stage).

AcademIA is a French-native tutor that covers Italian and German among other
languages. I rely on MERLIN-IT and MERLIN-DE to calibrate per-level error
weights via a Bayesian mixed-effects model — your 70-feature error-annotation
scheme is the richest open resource available for these languages.

Two quick questions:

1. The MERLIN CC BY-SA license is clear for academic use. For a small-scale
   educational project with no current monetization but potential future
   freemium transition, is the attribution requirement sufficient, or should
   I consider reaching out to EURAC for a complementary arrangement if the
   project grows?

2. Does MERLIN-IT or MERLIN-DE include a specifically tagged L1=French
   subcorpus that I could extract? This would help me calibrate FR→IT and
   FR→DE transfer patterns specifically, which is the population AcademIA
   serves.

I've downloaded the main CLARIN release, but I'd like to make sure I'm not
missing a more recent or more targeted release before building my pipeline.

Thank you for your time and for all the work that went into MERLIN — it's an
invaluable resource.

Best regards,
[First name / last name]
Independent developer, AcademIA
sinseproduction@gmail.com
```

## Notes pour Sinse

- Adapter la formule (1) selon le framing que tu préfères. L'idée est d'être
  transparent sur le statut actuel (non-commercial) + intention potentielle
- Verena Lyding est co-auteure du papier MERLIN 2014 et responsable plateforme
- Si elle ne répond pas, fallback vers `info@eurac.edu` ou formulaire contact
- Réponse positive = clarification + (peut-être) pointer vers LEONIDE ou KoKo
  qui sont leurs corpus multilingues plus récents
