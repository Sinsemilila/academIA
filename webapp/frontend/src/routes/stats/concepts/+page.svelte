<script lang="ts">
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { domainLabel as getDomainLabel } from '$lib/config';

  const levelLabels: Record<string, string> = {
    A1: 'Survie', A2: 'Quotidien', B1: 'Autonomie',
    B2: 'Aisance', C1: 'Ma\u00EEtrise', C2: 'Excellence',
  };

  // Sprint 5 D1: domain uses ISO codes ("en"/"es"/...)
  let domain = $derived(page.url.searchParams.get('domain') || 'en');
  let domainLabel = $derived(getDomainLabel(domain));

  let concepts = $state<any>(null);
  let loading = $state(true);
  let expandedConcept = $state<string | null>(null);

  let niveau = $derived(concepts?.niveau);
  let groups = $derived(concepts?.groups || {});
  let scores = $derived(concepts?.scores || {});
  let tips = $derived(concepts?.concept_tips || {});
  let conceptKeys = $derived(concepts?.concept_keys || []);
  let mastered = $derived(conceptKeys.filter((k: string) => (scores[k]?.score || 0) >= 80).length);
  let totalExpected = $derived(conceptKeys.length || 1);

  function conceptStatus(key: string): 'mastered' | 'medium' | 'weak' | 'untested' {
    const s = scores[key];
    if (!s || s.score === 0 || s.score === undefined) return 'untested';
    if (s.score >= 80) return 'mastered';
    if (s.score >= 50) return 'medium';
    return 'weak';
  }

  function statusIcon(status: string) {
    switch (status) {
      case 'mastered': return '\u2705';
      case 'medium':   return '\u26A1';
      case 'weak':     return '\uD83D\uDD34';
      case 'untested': return '\uD83C\uDD95';
      default: return '';
    }
  }

  function barColor(status: string) {
    switch (status) {
      case 'mastered': return 'bg-professore';
      case 'medium':   return 'bg-lehrer';
      case 'weak':     return 'bg-maestro';
      default:         return 'bg-border-subtle';
    }
  }

  function formatConceptName(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return "aujourd'hui";
    if (days === 1) return 'hier';
    return `il y a ${days}j`;
  }

  onMount(async () => {
    concepts = await api.getConcepts(domain);
    loading = false;
  });
</script>

<svelte:head>
  <title>Concepts {domainLabel} — Acad&#233;mie-IA</title>
</svelte:head>

{#if loading}
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="skeleton h-8 w-48"></div>
    <div class="skeleton h-16 w-full"></div>
    <div class="skeleton h-48 w-full"></div>
  </div>
{:else}
<div class="max-w-4xl mx-auto space-y-6">
  <!-- Header with back -->
  <div class="flex items-center gap-3">
    <a href="/stats" class="p-1.5 rounded-lg hover:bg-elevated transition-colors">
      <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </a>
    <div>
      <h1 class="text-2xl font-semibold">{domainLabel} — {niveau || '?'}</h1>
      <p class="text-sm text-text-secondary">{levelLabels[niveau] || ''}</p>
    </div>
  </div>

  {#if Object.keys(groups).length > 0}
    <!-- Summary counters -->
    <div class="grid grid-cols-4 gap-3">
      <div class="bg-surface border border-border-subtle rounded-xl p-3 text-center">
        <p class="text-xl font-mono font-bold text-professore">{mastered}</p>
        <p class="text-[10px] text-text-muted mt-0.5">ma&#238;tris&#233;</p>
      </div>
      <div class="bg-surface border border-border-subtle rounded-xl p-3 text-center">
        <p class="text-xl font-mono font-bold text-lehrer">{conceptKeys.filter((k: string) => { const s = scores[k]?.score || 0; return s >= 50 && s < 80; }).length}</p>
        <p class="text-[10px] text-text-muted mt-0.5">en cours</p>
      </div>
      <div class="bg-surface border border-border-subtle rounded-xl p-3 text-center">
        <p class="text-xl font-mono font-bold text-maestro">{conceptKeys.filter((k: string) => { const s = scores[k]?.score || 0; return s > 0 && s < 50; }).length}</p>
        <p class="text-[10px] text-text-muted mt-0.5">faible</p>
      </div>
      <div class="bg-surface border border-border-subtle rounded-xl p-3 text-center">
        <p class="text-xl font-mono font-bold">{conceptKeys.filter((k: string) => (scores[k]?.score || 0) === 0).length}</p>
        <p class="text-[10px] text-text-muted mt-0.5">non test&#233;</p>
      </div>
    </div>

    <!-- Concepts by module -->
    <div class="space-y-5">
      {#each Object.entries(groups) as [groupName, groupConcepts]}
        {@const gConcepts = groupConcepts as string[]}
        {@const gMastered = gConcepts.filter(k => (scores[k]?.score || 0) >= 80).length}

        <div class="bg-surface border border-border-subtle rounded-xl overflow-hidden">
          <div class="px-5 py-3 border-b border-border-subtle flex items-center justify-between">
            <h3 class="font-medium text-sm">{groupName}</h3>
            <div class="flex items-center gap-3">
              <span class="text-xs text-text-muted font-mono">{gMastered}/{gConcepts.length}</span>
              <div class="w-16 h-1.5 bg-elevated rounded-full overflow-hidden">
                <div
                  class="h-full bg-teacher rounded-full"
                  style="width: {gConcepts.length > 0 ? Math.round(gMastered / gConcepts.length * 100) : 0}%"
                ></div>
              </div>
            </div>
          </div>

          <div class="divide-y divide-border-subtle">
            {#each gConcepts as key}
              {@const status = conceptStatus(key)}
              {@const score = scores[key]?.score || 0}
              {@const lastSeen = scores[key]?.last_seen}
              {@const tip = tips[key]}
              {@const isExpanded = expandedConcept === key}
              <div>
                <button
                  class="w-full px-5 py-3 flex items-center gap-3 hover:bg-surface-hover/50 transition-colors text-left"
                  onclick={() => { expandedConcept = isExpanded ? null : key; }}
                >
                  <span class="text-base w-6 text-center">{statusIcon(status)}</span>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-sm truncate">{formatConceptName(key)}</span>
                      <span class="text-xs font-mono text-text-secondary ml-2 shrink-0">
                        {score > 0 ? score + '%' : '—'}
                      </span>
                    </div>
                    <div class="w-full h-1.5 bg-elevated rounded-full overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all duration-500 {barColor(status)}"
                        style="width: {score}%"
                      ></div>
                    </div>
                  </div>
                  {#if lastSeen}
                    <span class="text-[10px] text-text-muted shrink-0">{timeAgo(lastSeen)}</span>
                  {/if}
                  {#if tip}
                    <svg
                      class="w-3.5 h-3.5 text-text-muted shrink-0 transition-transform duration-200 {isExpanded ? 'rotate-180' : ''}"
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    ><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                  {/if}
                </button>
                {#if isExpanded && tip}
                  <div class="px-5 pb-3 pt-0 ml-9">
                    <div class="bg-elevated/60 rounded-lg p-3 space-y-2 text-xs leading-relaxed">
                      <p class="text-text-primary"><span class="text-text-muted">Rappel :</span> {tip.rule}</p>
                      {#if tip.mistake}
                        <p class="text-maestro"><span class="font-medium">Piege courant :</span> {tip.mistake}</p>
                      {/if}
                      {#if tip.example}
                        <p class="text-text-secondary italic">{tip.example}</p>
                      {/if}
                      {#if tip.advice}
                        <p class="text-teacher"><span class="font-medium">Conseil :</span> {tip.advice}</p>
                      {/if}
                    </div>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="bg-surface border border-border-subtle rounded-xl p-8 text-center">
      <p class="text-3xl mb-3">&#x1F4DA;</p>
      <p class="text-sm text-text-secondary">Pas encore de concepts. Commence une session !</p>
    </div>
  {/if}
</div>
{/if}
