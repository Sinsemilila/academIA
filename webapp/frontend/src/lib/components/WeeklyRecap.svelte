<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let recap = $state<any>(null);
  let loading = $state(true);

  onMount(async () => {
    recap = await api.getWeeklyRecap();
    loading = false;
  });
</script>

{#if !loading && recap && recap.sessions > 0}
  <div class="bg-surface border border-border-subtle rounded-xl p-5 relative overflow-hidden">
    <!-- Subtle gradient accent -->
    <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teacher via-sensei to-professore opacity-40"></div>

    <div class="flex items-center gap-2 mb-3">
      <span class="text-lg">&#x1F4C5;</span>
      <h3 class="text-sm font-medium">R&#233;cap de la semaine</h3>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="text-center">
        <p class="text-xl font-mono font-bold">{recap.sessions}</p>
        <p class="text-[10px] text-text-muted mt-0.5">sessions</p>
      </div>
      <div class="text-center">
        <p class="text-xl font-mono font-bold">{recap.minutes}</p>
        <p class="text-[10px] text-text-muted mt-0.5">minutes</p>
      </div>
      <div class="text-center">
        <p class="text-xl font-mono font-bold text-lehrer">{recap.xp || 0}</p>
        <p class="text-[10px] text-text-muted mt-0.5">XP gagn&#233;s</p>
      </div>
      <div class="text-center">
        <p class="text-xl font-mono font-bold">{recap.streak || 0}&#x1F525;</p>
        <p class="text-[10px] text-text-muted mt-0.5">streak</p>
      </div>
    </div>
  </div>
{/if}
