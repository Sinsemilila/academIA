<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let recap = $state<any>(null);
  let loading = $state(true);
  let isMonday = $state(new Date().getDay() === 1);
</script>

{#await api.getWeeklyRecap() then recap}
  {#if recap}
    <div class="bg-surface border border-border-subtle rounded-xl p-5 relative overflow-hidden">
      <!-- Accent bar — brighter on Monday -->
      <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teacher via-sensei to-professore {isMonday ? 'opacity-80' : 'opacity-40'}"></div>

      <div class="flex items-center gap-2 mb-3">
        <span class="text-lg">&#x1F4C5;</span>
        <h3 class="text-sm font-medium">R&#233;cap de la semaine</h3>
        {#if isMonday}
          <span class="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-teacher/20 text-teacher">Nouveau</span>
        {/if}
      </div>

      {#if recap.sessions > 0}
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
      {:else}
        <p class="text-sm text-text-secondary">Pas encore de session cette semaine. Lance-toi !</p>
      {/if}
    </div>
  {/if}
{/await}
