<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let days = $state<{ date: string; sessions: number; minutes: number }[]>([]);
  let loading = $state(true);
  let hoveredDay = $state<{ date: string; sessions: number; minutes: number; x: number; y: number } | null>(null);

  onMount(async () => {
    const data = await api.getHeatmap();
    days = data.days || [];
    loading = false;
  });

  function intensityClass(sessions: number): string {
    if (sessions === 0) return 'heatmap-empty';
    if (sessions === 1) return 'heatmap-low';
    if (sessions <= 3) return 'heatmap-mid';
    if (sessions <= 5) return 'heatmap-high';
    return 'heatmap-max';
  }

  function formatDate(d: string): string {
    return new Date(d).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' });
  }

  // Build weeks grid (columns = weeks, rows = days 0-6)
  let weeks = $derived((() => {
    if (days.length === 0) return [];
    const grid: (typeof days[0] | null)[][] = [];
    let currentWeek: (typeof days[0] | null)[] = [];

    // Pad start to align with Monday (weekday 1)
    const firstDate = new Date(days[0].date);
    const firstDay = (firstDate.getDay() + 6) % 7; // Mon=0
    for (let i = 0; i < firstDay; i++) currentWeek.push(null);

    for (const day of days) {
      currentWeek.push(day);
      if (currentWeek.length === 7) {
        grid.push(currentWeek);
        currentWeek = [];
      }
    }
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) currentWeek.push(null);
      grid.push(currentWeek);
    }
    return grid;
  })());

  let totalSessions = $derived(days.reduce((s, d) => s + d.sessions, 0));
  let activeDays = $derived(days.filter(d => d.sessions > 0).length);

  // Month labels
  let monthLabels = $derived((() => {
    if (weeks.length === 0) return [];
    const labels: { label: string; col: number }[] = [];
    let lastMonth = -1;
    for (let w = 0; w < weeks.length; w++) {
      const day = weeks[w].find(d => d !== null);
      if (day) {
        const month = new Date(day.date).getMonth();
        if (month !== lastMonth) {
          labels.push({
            label: new Date(day.date).toLocaleDateString('fr-FR', { month: 'short' }),
            col: w,
          });
          lastMonth = month;
        }
      }
    }
    return labels;
  })());

  function handleMouseEnter(day: typeof days[0], event: MouseEvent) {
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    hoveredDay = { ...day, x: rect.left + rect.width / 2, y: rect.top };
  }

  function handleMouseLeave() {
    hoveredDay = null;
  }
</script>

{#if loading}
  <div class="skeleton h-28 w-full"></div>
{:else}
  <div class="bg-surface border border-border-subtle rounded-xl p-5 overflow-hidden">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-medium">Activite</h3>
      <div class="flex items-center gap-3 text-xs text-text-muted">
        <span>{totalSessions} sessions</span>
        <span>{activeDays} jours actifs</span>
      </div>
    </div>

    <!-- Month labels -->
    <div class="overflow-x-auto">
      <div class="min-w-[680px]">
        <div class="flex gap-[2px] ml-7 mb-1">
          {#each monthLabels as m, i}
            {@const gap = i === 0 ? m.col : m.col - (monthLabels[i-1]?.col || 0)}
            <span
              class="text-[10px] text-text-muted"
              style="margin-left: {i === 0 ? m.col * 13 : (gap - 1) * 13}px"
            >{m.label}</span>
          {/each}
        </div>

        <!-- Grid -->
        <div class="flex gap-[3px]">
          <!-- Day labels -->
          <div class="flex flex-col gap-[3px] text-[10px] text-text-muted leading-[11px] pt-0">
            <span class="h-[11px]"></span>
            <span class="h-[11px] flex items-center">Mar</span>
            <span class="h-[11px]"></span>
            <span class="h-[11px] flex items-center">Jeu</span>
            <span class="h-[11px]"></span>
            <span class="h-[11px] flex items-center">Sam</span>
            <span class="h-[11px]"></span>
          </div>

          <!-- Weeks -->
          {#each weeks as week}
            <div class="flex flex-col gap-[3px]">
              {#each week as day}
                {#if day}
                  <div
                    class="w-[11px] h-[11px] rounded-[2px] {intensityClass(day.sessions)} cursor-pointer transition-transform hover:scale-125"
                    role="button"
                    tabindex="0"
                    onmouseenter={(e) => handleMouseEnter(day, e)}
                    onmouseleave={handleMouseLeave}
                  ></div>
                {:else}
                  <div class="w-[11px] h-[11px]"></div>
                {/if}
              {/each}
            </div>
          {/each}
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex items-center justify-end gap-1.5 mt-3 text-[10px] text-text-muted">
      <span>Moins</span>
      <div class="w-[11px] h-[11px] rounded-[2px] heatmap-empty"></div>
      <div class="w-[11px] h-[11px] rounded-[2px] heatmap-low"></div>
      <div class="w-[11px] h-[11px] rounded-[2px] heatmap-mid"></div>
      <div class="w-[11px] h-[11px] rounded-[2px] heatmap-high"></div>
      <div class="w-[11px] h-[11px] rounded-[2px] heatmap-max"></div>
      <span>Plus</span>
    </div>
  </div>

  <!-- Tooltip -->
  {#if hoveredDay}
    <div
      class="fixed z-50 pointer-events-none px-3 py-2 bg-elevated border border-border-subtle rounded-lg shadow-lg text-xs"
      style="left: {hoveredDay.x}px; top: {hoveredDay.y - 8}px; transform: translate(-50%, -100%)"
    >
      <p class="font-medium text-text-primary">{formatDate(hoveredDay.date)}</p>
      <p class="text-text-secondary">
        {hoveredDay.sessions} session{hoveredDay.sessions !== 1 ? 's' : ''}
        {#if hoveredDay.minutes > 0} · {hoveredDay.minutes} min{/if}
      </p>
    </div>
  {/if}
{/if}

<style>
  .heatmap-empty { background-color: var(--color-heatmap-empty); }
  .heatmap-low   { background-color: var(--color-heatmap-low); }
  .heatmap-mid   { background-color: var(--color-heatmap-mid); }
  .heatmap-high  { background-color: var(--color-heatmap-high); }
  .heatmap-max   { background-color: var(--color-heatmap-max); }
</style>
