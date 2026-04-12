<script lang="ts">
  import { page } from '$app/state';
</script>

<div class="min-h-[60dvh] flex items-center justify-center">
  <div class="text-center">
    <p class="text-6xl font-mono font-bold text-text-muted mb-4">{page.status}</p>
    <p class="text-text-secondary mb-6">
      {#if page.status === 404}
        Cette page n'existe pas.
      {:else}
        Une erreur est survenue.
      {/if}
    </p>
    <a
      href="/"
      class="inline-block px-4 py-2 bg-teacher text-white text-sm font-medium rounded-lg
             hover:brightness-110 transition-all"
    >
      Retour a l'accueil
    </a>
  </div>
</div>
