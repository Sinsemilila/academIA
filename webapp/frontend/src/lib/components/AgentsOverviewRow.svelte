<script lang="ts">
  import { agents } from '$lib/config';
  import { currentAgent } from '$lib/stores/navigation';
  import AgentFlag from '$lib/components/AgentFlag.svelte';

  // Row of compact cards for every available agent, with niveau + progress.
  // Source = backend /api/me/dashboard (merges profils_eleves + learner_profiles QCM fallback).
  //
  // Click behavior : selects the agent (updates store → detailed panels below reload).
  // Does NOT navigate to chat — use the dedicated "Reprendre" / "Commencer" buttons
  // in the detailed panel for that.

  let { agentsData = [] } = $props<{
    agentsData: Array<{
      domain: string;
      niveau: string | null;
      provisional: boolean;
      progress_pct: number;
      mastered: number;
      total_expected: number;
      sessions_this_week?: number;
      minutes_this_week?: number;
    }>;
  }>();

  let byDomain = $derived(Object.fromEntries(agentsData.map((a: any) => [a.domain, a])));
  let visibleAgents = $derived(agents.filter((a) => a.available));

  function selectAgent(slug: string) {
    currentAgent.set(slug);
  }

  function formatMinutes(m: number): string {
    if (m < 60) return `${m}min`;
    const h = Math.floor(m / 60);
    const rem = m % 60;
    return rem > 0 ? `${h}h${rem.toString().padStart(2, '0')}` : `${h}h`;
  }
</script>

{#if visibleAgents.length > 1}
  <div class="grid gap-3 {visibleAgents.length <= 2 ? 'sm:grid-cols-2' : 'sm:grid-cols-2 lg:grid-cols-3'}">
    {#each visibleAgents as agent}
      {@const data = byDomain[agent.domain]}
      {@const isActive = $currentAgent === agent.slug}
      <button
        type="button"
        onclick={() => selectAgent(agent.slug)}
        class="relative text-left bg-surface border rounded-xl p-4 transition-all w-full
               {isActive ? 'border-[var(--agent-color)] bg-[var(--agent-color)]/5 ring-1 ring-[var(--agent-color)]/30' : 'border-border-subtle hover:border-border-strong'}"
        style="--agent-color: {agent.colorHex}"
        aria-pressed={isActive}
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <AgentFlag {agent} size="sm" />
            <div>
              <p class="font-medium text-sm">{agent.name}</p>
              <p class="text-[10px] text-text-muted">{agent.lang}</p>
            </div>
          </div>
          {#if data?.niveau}
            <div class="text-right">
              <span class="font-mono font-semibold text-sm" style="color: {agent.colorHex}">{data.niveau}</span>
              {#if data.provisional}
                <p class="text-[9px] text-text-muted">provisoire</p>
              {/if}
            </div>
          {:else}
            <span class="text-[10px] text-text-muted">non démarré</span>
          {/if}
        </div>
        {#if data && !data.provisional && data.total_expected > 0}
          <div class="w-full h-1.5 bg-elevated rounded-full overflow-hidden mb-1">
            <div
              class="h-full rounded-full transition-all duration-500"
              style="width: {data.progress_pct}%; background-color: {agent.colorHex}"
            ></div>
          </div>
          <div class="flex justify-between text-[10px] text-text-muted">
            <span>{data.progress_pct}%</span>
            <span>{data.mastered}/{data.total_expected} concepts</span>
          </div>
        {/if}
        {#if data && ((data.sessions_this_week ?? 0) > 0 || (data.minutes_this_week ?? 0) > 0)}
          <div class="mt-2 pt-2 border-t border-border-subtle/50 flex justify-between text-[10px] text-text-muted">
            <span>{data.sessions_this_week ?? 0} session{(data.sessions_this_week ?? 0) > 1 ? 's' : ''} / 7j</span>
            <span class="font-mono">{formatMinutes(data.minutes_this_week ?? 0)}</span>
          </div>
        {/if}
      </button>
    {/each}
  </div>
{/if}
