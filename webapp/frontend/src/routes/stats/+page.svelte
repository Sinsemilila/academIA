<script lang="ts">
  import { api } from '$lib/api';
  import { currentAgent, currentDomain } from '$lib/stores/navigation';
  import { domainLabel } from '$lib/config';
  import AgentsOverviewRow from '$lib/components/AgentsOverviewRow.svelte';
  import ProgressionGraph from '$lib/components/ProgressionGraph.svelte';

  const levelLabels: Record<string, string> = {
    A1: 'Survie', A2: 'Quotidien', B1: 'Autonomie',
    B2: 'Aisance', C1: 'Ma\u00EEtrise', C2: 'Excellence',
  };
  const levelOrder = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  const badgeIcons: Record<string, string> = {
    fire: '\uD83D\uDD25', star: '\u2B50', target: '\uD83C\uDFAF', rocket: '\uD83D\uDE80',
    gem: '\uD83D\uDC8E', books: '\uD83D\uDCDA', trophy: '\uD83C\uDFC6', sparkle: '\uD83C\uDF1F',
    diamond: '\uD83D\uDCA0',
  };
  function getBadgeIcon(key: string): string { return badgeIcons[key] || key; }

  let concepts = $state<any>(null);
  let exams = $state<any>(null);
  let xpData = $state<any>(null);
  let xpHistory = $state<{ date: string; value: number }[]>([]);
  let badgeData = $state<any>(null);
  let dashboardAgents = $state<any[]>([]);
  let loading = $state(true);

  let niveau = $derived(concepts?.niveau);
  let scores = $derived(concepts?.scores || {});
  let conceptKeys = $derived(concepts?.concept_keys || []);
  let mastered = $derived(conceptKeys.filter((k: string) => (scores[k]?.score || 0) >= 80).length);
  let totalExpected = $derived(conceptKeys.length || 1);
  let progressPct = $derived(Math.round(
    conceptKeys.reduce((sum: number, k: string) => sum + (scores[k]?.score || scores[k] || 0), 0) / totalExpected
  ));
  let nextLevel = $derived(niveau ? levelOrder[levelOrder.indexOf(niveau) + 1] || null : null);

  function formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  }

  async function loadForDomain(domain: string) {
    loading = true;
    const [c, e, x, b, xh, dash] = await Promise.all([
      api.getConcepts(domain),
      api.getExams(domain),
      api.getXp(),
      api.getBadges(domain),
      api.getXpHistory(),
      api.getDashboard(),
    ]);
    concepts = c;
    exams = e;
    xpData = x;
    badgeData = b;
    xpHistory = xh.data || [];
    dashboardAgents = dash.agents || [];
    loading = false;
  }

  // Reactively reload on agent/domain switch (via sidebar).
  $effect(() => {
    loadForDomain($currentDomain);
  });
</script>

<svelte:head>
  <title>Stats — Acad&#233;mie-IA</title>
</svelte:head>

{#if loading}
  <div class="max-w-4xl mx-auto space-y-8">
    <div class="skeleton h-8 w-48"></div>
    <div class="skeleton h-32 w-full"></div>
    <div class="skeleton h-24 w-full"></div>
    <div class="skeleton h-48 w-full"></div>
  </div>
{:else}
<div class="max-w-4xl mx-auto space-y-8">
  <h1 class="text-2xl font-semibold">Ma progression</h1>

  <!-- Multi-agent overview (all available agents) -->
  <AgentsOverviewRow agentsData={dashboardAgents} />

  <!-- Level card — clickable → concepts detail + Reprendre button -->
  {#if niveau}
    <div class="bg-surface border border-border-subtle rounded-xl p-6">
      <div class="flex items-center gap-4 mb-4">
        <div class="w-16 h-16 rounded-2xl bg-teacher/15 flex items-center justify-center text-2xl font-bold text-teacher">
          {niveau}
        </div>
        <div class="flex-1">
          <h2 class="font-semibold text-lg">{domainLabel($currentDomain)} — {levelLabels[niveau] || niveau}</h2>
          <p class="text-sm text-text-secondary">
            {mastered}/{totalExpected} concepts ma&#238;tris&#233;s
          </p>
        </div>
        <div class="flex items-center gap-3">
          {#if progressPct >= 80}
            <span class="px-3 py-1 bg-professore/15 text-professore text-xs font-medium rounded-full">
              Pr&#234;t pour l'examen {nextLevel}
            </span>
          {/if}
          <a href="/chat/{$currentAgent}"
             class="px-4 py-2 bg-teacher text-white text-sm font-medium rounded-lg hover:brightness-110 transition-all shrink-0">
            Reprendre &#x2192;
          </a>
        </div>
      </div>
      <div class="w-full h-3 bg-elevated rounded-full overflow-hidden">
        <div
          class="h-full bg-teacher rounded-full transition-all duration-700"
          style="width: {progressPct}%"
        ></div>
      </div>
      <div class="flex justify-between items-center mt-2">
        <p class="text-xs text-text-muted">{progressPct}% vers {nextLevel || 'la perfection'}</p>
        <a href="/stats/concepts?domain={$currentDomain}"
           class="text-xs text-teacher hover:underline">
          Voir les concepts &#x2192;
        </a>
      </div>
    </div>
  {:else}
    <div class="bg-surface border border-border-subtle rounded-xl p-6 text-center">
      <p class="text-text-secondary">Pas encore de niveau. Lance ta premi&#232;re session !</p>
      <a href="/chat/{$currentAgent}" class="inline-block mt-3 px-4 py-2 bg-teacher text-white text-sm font-medium rounded-lg hover:brightness-110 transition-all">
        Commencer
      </a>
    </div>
  {/if}

  <!-- XP & Rank -->
  {#if xpData}
    {@const rank = xpData.rank}
    {@const progressToNext = rank.next_threshold
      ? Math.round((xpData.total - rank.threshold) / (rank.next_threshold - rank.threshold) * 100)
      : 100}

    <div class="bg-surface border border-border-subtle rounded-xl p-6">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <span class="text-2xl">&#x2728;</span>
          <div>
            <h2 class="font-semibold">{rank.name}</h2>
            <p class="text-sm text-text-secondary">
              <span class="font-mono font-semibold text-lehrer">{xpData.total}</span> XP
            </p>
          </div>
        </div>
        {#if rank.next_name}
          <div class="text-right">
            <p class="text-xs text-text-muted">Prochain rang</p>
            <p class="text-sm font-medium">{rank.next_name}</p>
            <p class="text-xs text-text-muted font-mono">{rank.next_threshold} XP</p>
          </div>
        {/if}
      </div>
      <div class="w-full h-2 bg-elevated rounded-full overflow-hidden">
        <div
          class="h-full bg-lehrer rounded-full transition-all duration-700"
          style="width: {Math.min(progressToNext, 100)}%"
        ></div>
      </div>
    </div>
  {/if}

  <!-- XP Progression graph -->
  {#if xpHistory.length > 1}
    <ProgressionGraph data={xpHistory} label="Progression XP (30 jours)" color="var(--color-lehrer)" />
  {/if}

  <!-- Badges -->
  {#if badgeData?.badges}
    <div class="space-y-4">
      <h2 class="text-lg font-semibold">Badges</h2>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {#each badgeData.badges as badge}
          <div
            class="bg-surface border rounded-xl p-4 transition-all
                   {badge.unlocked
                     ? 'border-sensei/30 hover:scale-[1.02]'
                     : 'border-border-subtle opacity-50'}"
          >
            <div class="flex items-center gap-3 mb-2">
              <span class="text-2xl">{getBadgeIcon(badge.icon)}</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate">{badge.name}</p>
                <p class="text-[10px] text-text-muted">{badge.desc}</p>
              </div>
            </div>
            {#if !badge.unlocked && badge.threshold > 0}
              <div class="w-full h-1.5 bg-elevated rounded-full overflow-hidden">
                <div
                  class="h-full bg-sensei/50 rounded-full"
                  style="width: {Math.min(Math.round(badge.progress / badge.threshold * 100), 100)}%"
                ></div>
              </div>
              <p class="text-[10px] text-text-muted mt-1 font-mono">{badge.progress}/{badge.threshold}</p>
            {:else if badge.unlocked}
              <p class="text-[10px] text-sensei font-medium">&#x2705; D&#233;bloqu&#233;</p>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Last exam -->
  {#if exams?.last_exam}
    <div class="space-y-4">
      <h2 class="text-lg font-semibold">Dernier examen</h2>
      <div class="bg-surface border border-border-subtle rounded-xl p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <span class="text-xl">{exams.last_exam.passed ? '\uD83C\uDF89' : '\uD83D\uDCDA'}</span>
            <div>
              <p class="font-medium text-sm">
                {exams.last_exam.passed ? 'R\u00E9ussi' : '\u00C0 retenter'}
                {#if exams.last_exam.from && exams.last_exam.to}
                  — {exams.last_exam.from} &#x2192; {exams.last_exam.to}
                {/if}
              </p>
              {#if exams.last_exam.date}
                <p class="text-xs text-text-muted">{formatDate(exams.last_exam.date)}</p>
              {/if}
            </div>
          </div>
          <div class="text-right">
            <p class="text-2xl font-mono font-semibold {exams.last_exam.passed ? 'text-professore' : 'text-maestro'}">
              {exams.last_exam.score || '—'}
            </p>
            <p class="text-xs text-text-muted">/100</p>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
{/if}
