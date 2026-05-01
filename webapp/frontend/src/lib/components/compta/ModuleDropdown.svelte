<script lang="ts">
  // S57 — Maître Comptable dropdown α "Module en cours"
  // Phase 1 Mode B : Marie sélectionne le module Studi sur lequel elle bosse.
  // Valeur passée au chatflow Dify via dify_inputs.module_en_cours pour ancrage.

  interface Props {
    value: string;
    onChange: (newValue: string) => void;
  }

  let { value = $bindable('autre'), onChange }: Props = $props();

  const MODULES = [
    { group: 'BC1 — Travaux comptables courants et de clôture', items: [
      { v: 'bc1_1_objectifs', label: 'BC1.1 — Objectifs compta + profession' },
      { v: 'bc1_2_resultat_bilan', label: 'BC1.2 — Compte de résultat + bilan' },
      { v: 'bc1_3_ecritures_balance', label: 'BC1.3 — Écritures + balance' },
      { v: 'bc1_4_tva_mecanisme', label: 'BC1.4 — TVA mécanisme' },
      { v: 'bc1_5_factures', label: 'BC1.5 — Factures' },
      { v: 'bc1_6_operations_courantes', label: 'BC1.6 — Opérations courantes hors factures' },
      { v: 'bc1_7_facturation_electronique', label: 'BC1.7 — Facturation électronique 2026 + IA' },
      { v: 'bc1_8_rapprochement', label: 'BC1.8 — Rapprochement bancaire + suivi tiers' },
      { v: 'bc1_9_anomalies', label: 'BC1.9 — Anomalies' },
      { v: 'bc1_10_stocks_amort', label: 'BC1.10 — Variations stocks + amortissements' },
      { v: 'bc1_11_amort_fiscaux', label: 'BC1.11 — Amortissements fiscaux' },
      { v: 'bc1_12_depreciations', label: 'BC1.12 — Dépréciations + provisions' },
      { v: 'bc1_13_cessions', label: 'BC1.13 — Cessions immobilisations + VMP' },
      { v: 'bc1_14_inventaire', label: 'BC1.14 — Autres opérations inventaire' },
      { v: 'bc1_15_comptes_annuels', label: 'BC1.15 — Comptes annuels (bilan/CR/annexe)' },
      { v: 'bc1_16_affectation', label: 'BC1.16 — Affectation résultat' },
      { v: 'bc1_17_environnement_num', label: 'BC1.17 — Environnement numérique' },
      { v: 'bc1_18_sage_ligne_100', label: 'BC1.18 — Sage Ligne 100' },
    ]},
    { group: 'BC2 — Paie + déclarations fiscales', items: [
      { v: 'bc2_1_preparer_paie', label: 'BC2.1 — Préparer éléments paie' },
      { v: 'bc2_2_bulletins', label: 'BC2.2 — Bulletins paie (Sage v10)' },
      { v: 'bc2_3_tva_declaration', label: 'BC2.3 — Déclaration TVA (CA3 / CA12)' },
    ]},
    { group: 'BC3 — Accueil + travaux administratifs', items: [
      { v: 'bc3_1_ecrits_pro', label: 'BC3.1 — Écrits professionnels' },
      { v: 'bc3_2_classement_rgpd', label: 'BC3.2 — Classement + archivage + RGPD' },
      { v: 'bc3_3_communication', label: 'BC3.3 — Communication accueil' },
      { v: 'bc3_4_reportings_excel', label: 'BC3.4 — Reportings Excel' },
    ]},
    { group: 'Autre', items: [
      { v: 'autre', label: 'Autre / pas dans la liste' },
    ]},
  ];

  function handleChange(e: Event) {
    const newVal = (e.target as HTMLSelectElement).value;
    value = newVal;
    onChange(newVal);
  }
</script>

<div class="flex items-center gap-2 px-4 py-2 bg-elevated border-b border-border-subtle">
  <label for="module-en-cours" class="text-xs text-text-muted shrink-0">
    📚 Module en cours :
  </label>
  <select
    id="module-en-cours"
    {value}
    onchange={handleChange}
    class="text-xs bg-base border border-border-subtle rounded px-2 py-1 flex-1 max-w-[400px] focus:outline-none focus:border-teacher transition-colors"
  >
    {#each MODULES as group}
      <optgroup label={group.group}>
        {#each group.items as item}
          <option value={item.v}>{item.label}</option>
        {/each}
      </optgroup>
    {/each}
  </select>
</div>
