# i18n placeholder — FR-only v1

Decision D5 (Sinse, 2026-04-20) : v1 livre QCM en FR uniquement.
Les YAMLs sont déjà structurés i18n-ready (champs `prompt.fr`, `label_fr`,
`scale.labels_fr`, etc.). Pour ajouter une langue d'UI :

1. Pour chaque item, ajouter un sibling `prompt.en`, `label_en`, `scale.labels_en`.
2. Ajouter `locale_default: en` à l'overlay concerné, ou laisser le
   LocaleResolver côté front basculer via `navigator.language`.
3. Mettre à jour les overlays `probe_judge_*_v1` prompts si le matching
   pattern diffère par langue d'UI (rare — le contenu de traduction reste
   dans la langue cible).

**Aucune clé à traduire pour v1.**
