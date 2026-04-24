<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { currentAgent } from '$lib/stores/navigation';

  onMount(() => {
    const agent = $currentAgent || 'teacher';
    goto(`/chat/${agent}`, { replaceState: true });
  });
</script>

<div class="flex items-center justify-center min-h-[60vh] text-[var(--text-muted)] text-sm">
  Redirection…
</div>
