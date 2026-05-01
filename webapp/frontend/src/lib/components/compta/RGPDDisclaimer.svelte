<script lang="ts">
  // S57 — Maître Comptable RGPD disclaimer Phase 1
  // Banner one-time visible 1ère ouverture chat compta. Marie peut dismiss.
  // localStorage 'maitre_comptable_rgpd_acked' empêche réaffichage.

  import { onMount } from 'svelte';

  let dismissed = $state(false);

  onMount(() => {
    if (typeof localStorage !== 'undefined' &&
        localStorage.getItem('maitre_comptable_rgpd_acked') === '1') {
      dismissed = true;
    }
  });

  function ack() {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('maitre_comptable_rgpd_acked', '1');
    }
    dismissed = true;
  }
</script>

{#if !dismissed}
  <div class="px-4 py-3 bg-warning-bg border-b border-warning-border">
    <div class="flex items-start gap-3">
      <svg class="w-5 h-5 text-warning-text shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
      </svg>
      <div class="flex-1 text-xs leading-relaxed">
        <p class="font-semibold text-warning-text mb-1">⚠️ Cas fictifs uniquement</p>
        <p class="text-text-secondary">
          Pour ta sécurité et celle des tiers, n'utilise QUE des cas fictifs / anonymisés.
          Ne saisis pas de vraies données d'entreprise (noms tiers, IBAN, numéros TVA réels,
          salaires nominatifs, numéros de sécurité sociale).
        </p>
      </div>
      <button
        type="button"
        onclick={ack}
        class="text-xs text-warning-text hover:text-text-primary px-2 py-1 rounded border border-warning-border transition-colors shrink-0 cursor-pointer"
        aria-label="Fermer le disclaimer"
      >
        Compris ✕
      </button>
    </div>
  </div>
{/if}
