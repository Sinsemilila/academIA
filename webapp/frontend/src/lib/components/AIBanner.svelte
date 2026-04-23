<!--
  AIBanner — Mention IA AI Act art. 50 (deadline 2026-08-02).
  Affiche une bannière dismissible une seule fois (localStorage flag) sur les
  pages d'interaction avec un système IA (chat principalement).
-->
<script lang="ts">
  import { onMount } from 'svelte';

  const STORAGE_KEY = 'academie_ai_banner_dismissed_v1';

  let dismissed = $state(true);

  onMount(() => {
    try {
      dismissed = localStorage.getItem(STORAGE_KEY) === '1';
    } catch {
      dismissed = false;
    }
  });

  function dismiss() {
    dismissed = true;
    try {
      localStorage.setItem(STORAGE_KEY, '1');
    } catch {}
  }
</script>

{#if !dismissed}
  <div
    class="fixed bottom-0 inset-x-0 z-40 bg-amber-500/10 border-t border-amber-500/30 backdrop-blur-md"
    role="status"
    aria-live="polite"
  >
    <div class="max-w-4xl mx-auto px-4 py-2 flex items-center gap-3 text-xs text-text-secondary">
      <svg class="w-4 h-4 text-amber-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="flex-1 leading-snug">
        Vous interagissez avec une <strong class="text-text-primary">intelligence artificielle</strong>.
        Vos messages sont transmis à des fournisseurs LLM tiers (OpenAI, Groq).
        <a href="/legal/ia" class="underline hover:text-amber-400">En savoir plus</a>
      </p>
      <button
        type="button"
        onclick={dismiss}
        class="shrink-0 w-7 h-7 rounded-md hover:bg-amber-500/20 flex items-center justify-center text-text-muted hover:text-text-primary transition"
        aria-label="Fermer la bannière"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  </div>
{/if}
