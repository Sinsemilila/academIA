<script lang="ts">
  import { onMount } from 'svelte';

  let online = $state(true);

  onMount(() => {
    online = navigator.onLine;
    const goOnline = () => { online = true; };
    const goOffline = () => { online = false; };
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  });
</script>

{#if !online}
  <div class="fixed top-0 left-0 right-0 z-50 bg-lehrer text-black text-center text-sm py-2 font-medium">
    Connexion perdue — En attente de reconnexion...
  </div>
{/if}
