<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { agents } from '$lib/config';
  import AgentFlag from '$lib/components/AgentFlag.svelte';
  import Tooltip from '$lib/components/Tooltip.svelte';
  import WeeklyRecap from '$lib/components/WeeklyRecap.svelte';

  let profile = $state<any>(null);
  let stats = $state({ sessions: 0, concepts: 0, minutes: 0 });
  let username = $state('');
  let loading = $state(true);

  // Concept popover state
  let showConceptPopover = $state(false);
  let conceptData = $state<any>(null);
  let conceptLoading = $state(false);
  let popoverRef = $state<HTMLElement | null>(null);

  // Derived concept stats
  let conceptScores = $derived(conceptData?.scores || {});
  let conceptKeys = $derived(conceptData?.concept_keys || []);
  let countMastered = $derived(conceptKeys.filter((k: string) => (conceptScores[k]?.score || 0) >= 80).length);
  let countMedium = $derived(conceptKeys.filter((k: string) => { const s = conceptScores[k]?.score || 0; return s >= 50 && s < 80; }).length);
  let countWeak = $derived(conceptKeys.filter((k: string) => { const s = conceptScores[k]?.score || 0; return s > 0 && s < 50; }).length);
  let countUntested = $derived(conceptKeys.filter((k: string) => (conceptScores[k]?.score || 0) === 0).length);

  // Top weakest concepts (non-zero, sorted ascending)
  let weakestConcepts = $derived(
    conceptKeys
      .filter((k: string) => { const s = conceptScores[k]?.score || 0; return s > 0 && s < 80; })
      .sort((a: string, b: string) => (conceptScores[a]?.score || 0) - (conceptScores[b]?.score || 0))
      .slice(0, 4)
  );

  function formatConceptName(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
  }

  function barColor(score: number): string {
    if (score >= 80) return 'bg-professore';
    if (score >= 50) return 'bg-lehrer';
    return 'bg-maestro';
  }

  async function toggleConceptPopover(e: MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (showConceptPopover) {
      showConceptPopover = false;
      return;
    }
    showConceptPopover = true;
    if (!conceptData) {
      conceptLoading = true;
      try {
        conceptData = await api.getConcepts('anglais');
      } catch { /* ignore */ }
      conceptLoading = false;
    }
  }

  function handleClickOutside(e: MouseEvent) {
    if (showConceptPopover && popoverRef && !popoverRef.contains(e.target as Node)) {
      showConceptPopover = false;
    }
  }

  // Agent groups for display
  const agentGroups = [
    { label: 'Langues', items: agents.filter(a => ['teacher','maestro','sensei','lehrer','professore'].includes(a.slug)) },
    { label: 'Tech', items: agents.filter(a => ['pymentor','cybermentor'].includes(a.slug)) },
  ];

  onMount(async () => {
    const [me, prof, st] = await Promise.all([
      api.me(),
      api.getProfile('anglais'),
      api.getWeeklyStats(),
    ]);
    username = me.display_name || me.username;
    profile = prof;
    stats = st;
    loading = false;
  });
</script>

<svelte:window onclick={handleClickOutside} />

<svelte:head>
  <title>Acad&#233;mie-IA</title>
</svelte:head>

{#if loading}
  <div class="max-w-4xl mx-auto space-y-8">
    <div class="skeleton h-8 w-56"></div>
    <div class="skeleton h-32 w-full"></div>
    <div class="grid grid-cols-3 gap-4">
      {#each Array(3) as _}<div class="skeleton h-20"></div>{/each}
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {#each Array(7) as _}<div class="skeleton h-24"></div>{/each}
    </div>
  </div>
{:else}
<div class="max-w-4xl mx-auto space-y-8">
  <!-- Greeting -->
  <h1 class="text-2xl font-semibold">
    Salut {username} &#x1F44B;
  </h1>

  <!-- Teacher card with concept popover -->
  {#if profile?.niveau}
    <div class="relative" bind:this={popoverRef}>
      <div
        class="bg-surface border border-border-subtle rounded-xl p-5 sm:p-6 cursor-pointer
               hover:border-teacher/40 transition-all"
        role="button"
        tabindex="0"
        onclick={toggleConceptPopover}
        onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggleConceptPopover(e as any); }}
      >
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <AgentFlag agent={agents[0]} size="md" />
            <div>
              <h2 class="font-semibold">Teacher &#183; Anglais</h2>
              <p class="text-sm text-text-secondary">Niveau {profile.niveau}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <!-- Expand indicator -->
            <svg
              class="w-4 h-4 text-text-muted transition-transform duration-200 {showConceptPopover ? 'rotate-180' : ''}"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            <a
              href="/chat/teacher"
              class="px-4 py-2 bg-teacher text-white text-sm font-medium rounded-lg
                     hover:brightness-110 transition-all"
              onclick={(e) => e.stopPropagation()}
            >
              Reprendre &#x2192;
            </a>
          </div>
        </div>
        <div class="w-full h-2 bg-elevated rounded-full overflow-hidden">
          <div
            class="h-full bg-teacher rounded-full animate-bar"
            style="width: {profile.progress_pct}%"
          ></div>
        </div>
        <div class="flex justify-between mt-2">
          <p class="text-xs text-text-muted">{profile.progress_pct}% vers le niveau suivant</p>
          <p class="text-xs text-text-muted">{profile.mastered}/{profile.total_expected} concepts</p>
        </div>
      </div>

      <!-- Concept popover dropdown -->
      {#if showConceptPopover}
        <div class="mt-1 bg-surface border border-border-subtle rounded-xl shadow-lg overflow-hidden
                    animate-slideDown z-50">
          {#if conceptLoading}
            <div class="p-6 text-center">
              <div class="inline-block w-5 h-5 border-2 border-teacher border-t-transparent rounded-full animate-spin"></div>
            </div>
          {:else if conceptData && conceptKeys.length > 0}
            <!-- 4 counters -->
            <div class="grid grid-cols-4 gap-px bg-border-subtle">
              <div class="bg-surface p-3 text-center">
                <p class="text-lg font-mono font-bold text-professore">{countMastered}</p>
                <p class="text-[9px] text-text-muted">ma&#238;tris&#233;</p>
              </div>
              <div class="bg-surface p-3 text-center">
                <p class="text-lg font-mono font-bold text-lehrer">{countMedium}</p>
                <p class="text-[9px] text-text-muted">en cours</p>
              </div>
              <div class="bg-surface p-3 text-center">
                <p class="text-lg font-mono font-bold text-maestro">{countWeak}</p>
                <p class="text-[9px] text-text-muted">faible</p>
              </div>
              <div class="bg-surface p-3 text-center">
                <p class="text-lg font-mono font-bold text-text-muted">{countUntested}</p>
                <p class="text-[9px] text-text-muted">non test&#233;</p>
              </div>
            </div>

            <!-- Weakest concepts -->
            {#if weakestConcepts.length > 0}
              <div class="px-4 pt-3 pb-1">
                <p class="text-[10px] font-medium text-text-muted uppercase tracking-wider mb-2">&#192; travailler</p>
              </div>
              <div class="divide-y divide-border-subtle">
                {#each weakestConcepts as key}
                  {@const score = conceptScores[key]?.score || 0}
                  <div class="px-4 py-2.5 flex items-center gap-3">
                    <div class="flex-1 min-w-0">
                      <p class="text-sm truncate">{formatConceptName(key)}</p>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      <div class="w-16 h-1.5 bg-elevated rounded-full overflow-hidden">
                        <div class="h-full rounded-full {barColor(score)}" style="width: {score}%"></div>
                      </div>
                      <span class="text-xs font-mono text-text-secondary w-8 text-right">{score}%</span>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="px-4 py-4 text-center">
                <p class="text-sm text-text-muted">
                  {countUntested > 0 ? 'Commence une session pour d\u00E9bloquer tes premiers concepts !' : 'Tous les concepts sont ma\u00EEtris\u00E9s \uD83C\uDF89'}
                </p>
              </div>
            {/if}

            <!-- Link to full concepts page -->
            <a
              href="/stats/concepts?domain=anglais"
              class="block px-4 py-3 text-center text-sm font-medium text-teacher
                     hover:bg-elevated transition-colors border-t border-border-subtle"
              onclick={(e) => e.stopPropagation()}
            >
              Voir tous les concepts &#x2192;
            </a>
          {:else}
            <div class="p-6 text-center">
              <p class="text-sm text-text-muted">Pas encore de donn&#233;es. Lance une session !</p>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {:else if profile?.onboarding_completed_at && !profile?.derniere_session}
    <!-- Post-diagnostic bilan — diagnosed but no session yet -->
    <div class="bg-surface border border-teacher/30 rounded-xl p-6 sm:p-8">
      <div class="flex items-center gap-3 mb-4">
        <AgentFlag agent={agents[0]} size="md" />
        <div>
          <h2 class="font-semibold text-lg">Diagnostic termin&#233;</h2>
          <p class="text-xs text-text-muted">Niveau provisoire &mdash; s'affinera au fil des sessions</p>
        </div>
      </div>
      <div class="flex items-center gap-3 mb-5">
        <span class="px-3 py-1.5 bg-teacher/10 text-teacher font-bold text-xl rounded-lg">{profile.niveau}</span>
        <span class="text-xs text-text-muted border border-border-subtle rounded px-2 py-0.5">provisoire</span>
      </div>
      {#if profile.details_par_competence}
        <div class="grid grid-cols-3 gap-3 mb-5">
          {#each Object.entries(profile.details_par_competence) as [skill, level]}
            <div class="bg-elevated rounded-lg p-3 text-center">
              <p class="text-xs text-text-muted capitalize">{skill}</p>
              <p class="font-mono font-semibold text-sm mt-1">{level}</p>
            </div>
          {/each}
        </div>
      {/if}
      {#if profile.points_forts}
        <div class="mb-3">
          <p class="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">Points forts</p>
          <p class="text-sm text-text-secondary">{profile.points_forts}</p>
        </div>
      {/if}
      {#if profile.lacunes}
        <div class="mb-5">
          <p class="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">&#192; travailler</p>
          <p class="text-sm text-text-secondary">{profile.lacunes}</p>
        </div>
      {/if}
      <a href="/chat/teacher" class="inline-block px-5 py-2.5 bg-teacher text-white text-sm font-medium rounded-lg hover:brightness-110 transition-all">
        Commencer ma premi&#232;re session &#x2192;
      </a>
    </div>
  {:else}
    <!-- Empty state — no diagnostic yet -->
    <div class="bg-surface border border-border-subtle rounded-xl p-8 text-center">
      <p class="text-4xl mb-3">&#x1F393;</p>
      <h2 class="font-semibold text-lg mb-2">Bienvenue sur Acad&#233;mie-IA !</h2>
      <p class="text-sm text-text-secondary mb-4">En quelques minutes, Teacher va &#233;valuer ton niveau d'anglais et cr&#233;er ton programme personnalis&#233;.</p>
      <a href="/chat/teacher" class="inline-block px-5 py-2.5 bg-teacher text-white text-sm font-medium rounded-lg hover:brightness-110 transition-all">
        Commencer &#x2192;
      </a>
    </div>
  {/if}

  <!-- Weekly stats -->
  <div class="grid grid-cols-3 gap-3 sm:gap-4">
    <Tooltip text="Sessions cette semaine">
      <div class="bg-surface border border-border-subtle rounded-xl p-3 sm:p-4 text-center w-full">
        <p class="text-xl sm:text-2xl font-mono font-semibold">{stats.sessions}</p>
        <p class="text-[10px] sm:text-xs text-text-secondary mt-1">sessions</p>
      </div>
    </Tooltip>
    <Tooltip text="Concepts travaill&#233;s">
      <div class="bg-surface border border-border-subtle rounded-xl p-3 sm:p-4 text-center w-full">
        <p class="text-xl sm:text-2xl font-mono font-semibold">{stats.concepts}</p>
        <p class="text-[10px] sm:text-xs text-text-secondary mt-1">concepts</p>
      </div>
    </Tooltip>
    <Tooltip text="Temps estim&#233; de pratique">
      <div class="bg-surface border border-border-subtle rounded-xl p-3 sm:p-4 text-center w-full">
        <p class="text-xl sm:text-2xl font-mono font-semibold">{stats.minutes}</p>
        <p class="text-[10px] sm:text-xs text-text-secondary mt-1">minutes</p>
      </div>
    </Tooltip>
  </div>

  <!-- Weekly recap -->
  <WeeklyRecap />

  <!-- Agents by group -->
  <div class="space-y-6">
    <h2 class="text-lg font-semibold">Mes agents</h2>
    {#each agentGroups as group}
      <div>
        <p class="text-[10px] font-medium text-text-muted uppercase tracking-wider mb-2">{group.label}</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {#each group.items as agent}
            <a
              href={agent.available ? `/chat/${agent.slug}` : '#'}
              class="bg-surface border border-border-subtle rounded-xl p-4 text-center transition-all
                     {agent.available
                       ? 'hover:border-[var(--agent-color)] hover:scale-[1.02] cursor-pointer'
                       : 'opacity-40 cursor-not-allowed'}"
              style="--agent-color: {agent.colorHex}"
            >
              <AgentFlag {agent} size="md" />
              <p class="font-medium text-sm mt-2">{agent.name}</p>
              <p class="text-xs text-text-muted mt-0.5">
                {agent.available ? agent.lang : 'Bient\u00F4t'}
              </p>
            </a>
          {/each}
        </div>
      </div>
    {/each}
  </div>
</div>
{/if}
