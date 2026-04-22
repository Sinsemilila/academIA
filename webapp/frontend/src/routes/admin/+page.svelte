<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { agents } from '$lib/config';
  import { currentDomain } from '$lib/stores/navigation';
  import { get } from 'svelte/store';
  import ModelBudgetBar from '$lib/components/admin/ModelBudgetBar.svelte';
  import JudgeBudgetBar from '$lib/components/admin/JudgeBudgetBar.svelte';

  const availableAgents = $derived(agents.filter(a => a.available));
  const initialDomain = get(currentDomain);

  // ── OpenAI gpt-4o-mini quota + fine-tuned model cost (footer) ──
  let tokenUsage = $state<any>(null);
  async function loadTokenUsage() {
    try { tokenUsage = await api.getTokenUsage(); } catch {}
  }

  // ── Session 44 B — 3-tier model budget waterfall ────────────
  let modelBudgets = $state<any>(null);
  async function loadModelBudgets() {
    try { modelBudgets = await api.adminModelBudgets(); } catch { modelBudgets = null; }
  }

  // ── Session 45 P4.5 — Oracle judge budget (Gemini chain 540 RPD) ──
  let judgeBudget = $state<any>(null);
  async function loadJudgeBudget() {
    try { judgeBudget = await api.adminJudgeBudget(); } catch { judgeBudget = null; }
  }

  // ── Prompt caching (global, windowed) ───────────────────────
  let cacheStats = $state<any>(null);
  let cacheHours = $state(24);
  let cacheLoading = $state(false);
  async function loadCacheStats() {
    cacheLoading = true;
    try { cacheStats = await api.adminCacheStats(cacheHours); } catch { cacheStats = null; }
    finally { cacheLoading = false; }
  }
  async function switchCacheWindow(hours: number) { cacheHours = hours; await loadCacheStats(); }

  function sparkPath(points: Array<{ bucket: string; cached_tokens: number; prompt_tokens: number }>): string {
    if (!points.length) return '';
    const w = 280, h = 60;
    const pcts = points.map(p => p.prompt_tokens > 0 ? (p.cached_tokens / p.prompt_tokens) * 100 : 0);
    const max = Math.max(100, ...pcts);
    const step = points.length > 1 ? w / (points.length - 1) : 0;
    return points.map((_, i) => {
      const x = i * step;
      const y = h - (pcts[i] / max) * h;
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }

  // ── Consolidation (per-block domain + window) ───────────────
  let consolidationDomain = $state<string>(initialDomain);
  let consolidationHours = $state(168);
  let consolidationStats = $state<any>(null);
  let consolidationLoading = $state(false);
  async function loadConsolidationStats() {
    consolidationLoading = true;
    try { consolidationStats = await api.adminConsolidationEvents(consolidationDomain, consolidationHours); }
    catch { consolidationStats = null; }
    finally { consolidationLoading = false; }
  }

  // ── Oracle (per-block agent + window) ───────────────────────
  let oracleAgent = $state<string>(initialDomain === 'es' ? 'maestro_es' : 'teacher_en');
  let oracleHours = $state(168);
  let oracleStats = $state<any>(null);
  let oracleLoading = $state(false);
  async function loadOracleStats() {
    oracleLoading = true;
    try { oracleStats = await api.adminOracleRuns(oracleAgent, oracleHours); }
    catch { oracleStats = null; }
    finally { oracleLoading = false; }
  }

  // ── Onboarding funnel (per-block domain + window) ───────────
  let funnelDomain = $state<string>(initialDomain);
  let funnelHours = $state(720);
  let funnelStats = $state<any>(null);
  let funnelLoading = $state(false);
  async function loadFunnelStats() {
    funnelLoading = true;
    try { funnelStats = await api.adminOnboardingFunnel(funnelDomain, funnelHours); }
    catch { funnelStats = null; }
    finally { funnelLoading = false; }
  }

  onMount(() => {
    loadTokenUsage(); loadCacheStats(); loadModelBudgets(); loadJudgeBudget();
    loadConsolidationStats(); loadOracleStats(); loadFunnelStats();
  });
</script>

<svelte:head>
  <title>Admin — AcademIA</title>
</svelte:head>

<div class="max-w-5xl mx-auto space-y-6">
  <div class="flex items-center justify-between flex-wrap gap-3">
    <h1 class="text-xl font-bold text-text-primary">Administration</h1>
    <a
      href="/admin/users"
      class="px-4 py-2 text-sm font-medium rounded-lg bg-elevated text-text-primary hover:bg-accent hover:text-white border border-border-subtle transition"
    >
      Manage users →
    </a>
  </div>

  <!-- HERO — Model budgets (3-tier waterfall) -->
  <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold text-text-primary">Model budgets</h2>
        <p class="text-xs text-text-muted">gpt-4o-mini → groq-standard → groq-snapshot · switch auto à 95% TPD</p>
      </div>
    </div>
    {#if !modelBudgets || !modelBudgets.tiers}
      <div class="skeleton h-24 rounded-lg"></div>
    {:else}
      <ModelBudgetBar
        tiers={modelBudgets.tiers}
        currentTier={modelBudgets.current_tier}
        currentSince={modelBudgets.current_since}
        totalRemaining={modelBudgets.total_remaining_today}
      />
    {/if}

    <!-- ft:gpt-4o-mini cost (sub-signal, payant, no quota) -->
    {#if tokenUsage}
      {@const ftModel = tokenUsage.models?.find((m: any) => m.name?.startsWith('ft:gpt-4o-mini'))}
      {#if ftModel}
        <div class="border-t border-border-subtle pt-3 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-text-secondary">ft:gpt-4o-mini-v3 (error analysis)</p>
            <p class="text-[10px] text-text-muted">Payant — pas de quota imposé</p>
          </div>
          <div class="text-right">
            <p class="text-sm font-mono">{Math.round(ftModel.tokens / 1000)}K tokens</p>
            <p class="text-[10px] text-text-muted">${ftModel.cost_usd.toFixed(4)}</p>
          </div>
        </div>
      {/if}
    {/if}
  </div>

  <!-- Oracle judge budget (Gemini chain 540 RPD cumulated) -->
  <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
    <div>
      <h2 class="text-sm font-semibold text-text-primary">Oracle judge budget</h2>
      <p class="text-xs text-text-muted">
        Chaîne Gemini κ=0.84 — LiteLLM cascade automatique quand 429. Reset 00:00 UTC.
      </p>
    </div>
    {#if !judgeBudget || !judgeBudget.tiers}
      <div class="skeleton h-24 rounded-lg"></div>
    {:else}
      <JudgeBudgetBar
        tiers={judgeBudget.tiers}
        totalUsed={judgeBudget.total_used}
        totalLimit={judgeBudget.total_limit}
        totalRemaining={judgeBudget.total_remaining}
        preflightCmd={judgeBudget.preflight_cmd}
      />
    {/if}
  </div>

  <!-- REGRESSION ROW — Consolidation + Oracle side-by-side -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <!-- Consolidation -->
    <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <h2 class="text-sm font-semibold text-text-primary">Consolidation CEFR events</h2>
          <p class="text-xs text-text-muted truncate">Trigger/decide events + mini-exam outcomes</p>
        </div>
        <div class="flex items-center gap-1 shrink-0">
          <select
            value={consolidationDomain}
            onchange={(e) => { consolidationDomain = (e.target as HTMLSelectElement).value; loadConsolidationStats(); }}
            class="px-1 py-0.5 text-xs rounded bg-elevated border border-border-subtle text-text-primary"
            title="Scope domaine"
          >
            {#each availableAgents as a (a.domain)}
              <option value={a.domain}>{a.lang}</option>
            {/each}
          </select>
          {#each [24, 168, 720] as h (h)}
            <button
              onclick={() => { consolidationHours = h; loadConsolidationStats(); }}
              class="px-1.5 py-0.5 text-[10px] rounded {consolidationHours === h ? 'bg-accent text-white' : 'bg-elevated text-text-muted hover:text-text-primary'}"
            >{h === 24 ? '24h' : h === 168 ? '7j' : '30j'}</button>
          {/each}
        </div>
      </div>
      {#if consolidationLoading}
        <div class="skeleton h-20 rounded-lg"></div>
      {:else if !consolidationStats || !consolidationStats.summary}
        <p class="text-xs text-text-muted italic">Aucune donnée.</p>
      {:else}
        {@const cs = consolidationStats.summary}
        {@const total = (cs.mini_exam_pass ?? 0) + (cs.mini_exam_fail ?? 0)}
        {@const passRate = total > 0 ? Math.round((cs.mini_exam_pass / total) * 100) : null}
        <div class="grid grid-cols-3 gap-2">
          <div class="bg-elevated rounded-lg p-2">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Events</p>
            <p class="text-base font-mono font-semibold text-text-primary">{cs.total ?? 0}</p>
            <p class="text-[10px] text-text-muted">{cs.pending ?? 0} pend · {cs.closed ?? 0} close</p>
          </div>
          <div class="bg-elevated rounded-lg p-2">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Mini-exam</p>
            <p class="text-base font-mono font-semibold text-text-primary">{cs.mini_exam_count ?? 0}</p>
            <p class="text-[10px] text-text-muted">{cs.mini_exam_pass ?? 0}✓ {cs.mini_exam_fail ?? 0}✗</p>
          </div>
          <div class="bg-elevated rounded-lg p-2">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Pass rate</p>
            <p class="text-base font-mono font-semibold {passRate === null ? 'text-text-muted' : passRate >= 70 ? 'text-teacher' : passRate >= 50 ? 'text-lehrer' : 'text-maestro'}">
              {passRate === null ? '—' : `${passRate}%`}
            </p>
          </div>
        </div>

        {#if consolidationStats.by_decision && consolidationStats.by_decision.length > 0}
          <details class="bg-elevated rounded-lg">
            <summary class="px-3 py-2 text-xs cursor-pointer text-text-muted">By decision ({consolidationStats.by_decision.length})</summary>
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-border-subtle text-text-muted">
                  <th class="text-left px-3 py-2 font-normal">Décision</th>
                  <th class="text-right px-3 py-2 font-normal">Count</th>
                  <th class="text-right px-3 py-2 font-normal">Avg</th>
                </tr>
              </thead>
              <tbody>
                {#each consolidationStats.by_decision as d (d.decision)}
                  <tr class="border-b border-border-subtle/50">
                    <td class="px-3 py-2 font-mono">{d.decision}</td>
                    <td class="px-3 py-2 text-right font-mono">{d.count}</td>
                    <td class="px-3 py-2 text-right font-mono text-text-muted">{d.avg_score ? d.avg_score + '%' : '—'}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </details>
        {/if}
      {/if}
    </div>

    <!-- Oracle V1 runs -->
    <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <h2 class="text-sm font-semibold text-text-primary">Oracle V1 runs</h2>
          <p class="text-xs text-text-muted truncate">oracle_run_log — pass/fail par dim</p>
        </div>
        <div class="flex items-center gap-1 shrink-0">
          <select
            value={oracleAgent}
            onchange={(e) => { oracleAgent = (e.target as HTMLSelectElement).value; loadOracleStats(); }}
            class="px-1 py-0.5 text-xs rounded bg-elevated border border-border-subtle text-text-primary"
            title="Agent"
          >
            <option value="teacher_en">teacher_en</option>
            <option value="maestro_es">maestro_es</option>
          </select>
          {#each [24, 168, 720] as h (h)}
            <button
              onclick={() => { oracleHours = h; loadOracleStats(); }}
              class="px-1.5 py-0.5 text-[10px] rounded {oracleHours === h ? 'bg-accent text-white' : 'bg-elevated text-text-muted hover:text-text-primary'}"
            >{h === 24 ? '24h' : h === 168 ? '7j' : '30j'}</button>
          {/each}
        </div>
      </div>
      {#if oracleLoading}
        <div class="skeleton h-20 rounded-lg"></div>
      {:else if !oracleStats || !oracleStats.summary}
        <p class="text-xs text-text-muted italic">Aucun run persisté.</p>
      {:else}
        {@const os_ = oracleStats.summary}
        <div class="grid grid-cols-3 gap-2">
          <div class="bg-elevated rounded-lg p-2">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Runs</p>
            <p class="text-base font-mono font-semibold text-text-primary">{os_.total_runs ?? 0}</p>
            <p class="text-[10px] text-text-muted">{os_.total_rows ?? 0} rows</p>
          </div>
          <div class="bg-elevated rounded-lg p-2">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Scenarios</p>
            <p class="text-base font-mono font-semibold text-text-primary">{os_.scenarios_touched ?? 0}</p>
          </div>
          <div class="bg-elevated rounded-lg p-2">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Dims</p>
            <p class="text-base font-mono font-semibold text-text-primary">{(oracleStats.by_dim ?? []).length}</p>
          </div>
        </div>

        {#if oracleStats.by_dim && oracleStats.by_dim.length > 0}
          <details class="bg-elevated rounded-lg" open>
            <summary class="px-3 py-2 text-xs cursor-pointer text-text-muted">By dim ({oracleStats.by_dim.length})</summary>
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-border-subtle text-text-muted">
                  <th class="text-left px-3 py-2 font-normal">Dim</th>
                  <th class="text-right px-3 py-2 font-normal">Tot</th>
                  <th class="text-right px-3 py-2 font-normal">✓</th>
                  <th class="text-right px-3 py-2 font-normal">✗</th>
                  <th class="text-right px-3 py-2 font-normal">%</th>
                </tr>
              </thead>
              <tbody>
                {#each oracleStats.by_dim as d (d.dim)}
                  <tr class="border-b border-border-subtle/50">
                    <td class="px-3 py-2 font-mono">{d.dim}</td>
                    <td class="px-3 py-2 text-right font-mono">{d.total}</td>
                    <td class="px-3 py-2 text-right font-mono text-teacher">{d.pass}</td>
                    <td class="px-3 py-2 text-right font-mono {d.fail > 0 ? 'text-maestro' : 'text-text-muted'}">{d.fail}</td>
                    <td class="px-3 py-2 text-right font-mono {d.pass_pct >= 80 ? 'text-teacher' : d.pass_pct >= 50 ? 'text-lehrer' : 'text-maestro'}">{d.pass_pct}%</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </details>
        {/if}

        {#if oracleStats.recent_runs && oracleStats.recent_runs.length > 0}
          <details class="bg-elevated rounded-lg">
            <summary class="px-3 py-2 text-xs cursor-pointer text-text-muted">Recent runs ({oracleStats.recent_runs.length})</summary>
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-border-subtle text-text-muted">
                  <th class="text-left px-3 py-2 font-normal">run_hash</th>
                  <th class="text-left px-3 py-2 font-normal">When</th>
                  <th class="text-left px-3 py-2 font-normal">Mode</th>
                  <th class="text-right px-3 py-2 font-normal">✓</th>
                  <th class="text-right px-3 py-2 font-normal">✗</th>
                </tr>
              </thead>
              <tbody>
                {#each oracleStats.recent_runs as r (r.run_hash)}
                  <tr class="border-b border-border-subtle/50">
                    <td class="px-3 py-2 font-mono">{r.run_hash.slice(0, 8)}</td>
                    <td class="px-3 py-2 font-mono text-text-muted">{r.started_at ? r.started_at.slice(0, 16).replace('T', ' ') : '—'}</td>
                    <td class="px-3 py-2 font-mono">{r.mode}</td>
                    <td class="px-3 py-2 text-right font-mono text-teacher">{r.pass_count}</td>
                    <td class="px-3 py-2 text-right font-mono {r.fail_count > 0 ? 'text-maestro' : 'text-text-muted'}">{r.fail_count}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </details>
        {/if}
      {/if}
    </div>
  </div>

  <!-- ONBOARDING FUNNEL — full width -->
  <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
    <div class="flex items-start justify-between gap-2">
      <div>
        <h2 class="text-sm font-semibold text-text-primary">Onboarding funnel</h2>
        <p class="text-xs text-text-muted">Step-by-step drop-off — client telemetry (sendBeacon)</p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <select
          value={funnelDomain}
          onchange={(e) => { funnelDomain = (e.target as HTMLSelectElement).value; loadFunnelStats(); }}
          class="px-1 py-0.5 text-xs rounded bg-elevated border border-border-subtle text-text-primary"
          title="Scope domaine"
        >
          {#each availableAgents as a (a.domain)}
            <option value={a.domain}>{a.lang}</option>
          {/each}
        </select>
        {#each [24, 168, 720] as h (h)}
          <button
            onclick={() => { funnelHours = h; loadFunnelStats(); }}
            class="px-1.5 py-0.5 text-[10px] rounded {funnelHours === h ? 'bg-accent text-white' : 'bg-elevated text-text-muted hover:text-text-primary'}"
          >{h === 24 ? '24h' : h === 168 ? '7j' : '30j'}</button>
        {/each}
      </div>
    </div>
    {#if funnelLoading}
      <div class="skeleton h-20 rounded-lg"></div>
    {:else if !funnelStats || !funnelStats.summary || (funnelStats.summary.sessions_started ?? 0) === 0}
      <p class="text-xs text-text-muted italic">Aucune session enregistrée.</p>
    {:else}
      {@const fs_ = funnelStats.summary}
      <div class="grid grid-cols-4 gap-3">
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Started</p>
          <p class="text-lg font-mono font-semibold text-text-primary">{fs_.sessions_started ?? 0}</p>
        </div>
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Completed</p>
          <p class="text-lg font-mono font-semibold text-teacher">{fs_.sessions_completed ?? 0}</p>
          <p class="text-[10px] text-text-muted">{fs_.completion_pct ?? 0}%</p>
        </div>
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Aborted</p>
          <p class="text-lg font-mono font-semibold {fs_.sessions_aborted > 0 ? 'text-maestro' : 'text-text-muted'}">{fs_.sessions_aborted ?? 0}</p>
        </div>
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">In-flight</p>
          <p class="text-lg font-mono font-semibold text-text-muted">{fs_.sessions_inflight ?? 0}</p>
        </div>
      </div>

      {#if funnelStats.by_step && funnelStats.by_step.length > 0}
        <div class="bg-elevated rounded-lg overflow-hidden">
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-border-subtle text-text-muted">
                <th class="text-left px-3 py-2 font-normal">#</th>
                <th class="text-left px-3 py-2 font-normal">Step</th>
                <th class="text-right px-3 py-2 font-normal">Entered</th>
                <th class="text-right px-3 py-2 font-normal">Dropped</th>
                <th class="text-right px-3 py-2 font-normal">→ next %</th>
              </tr>
            </thead>
            <tbody>
              {#each funnelStats.by_step as s (s.step_order)}
                <tr class="border-b border-border-subtle/50">
                  <td class="px-3 py-2 font-mono text-text-muted">{s.step_order}</td>
                  <td class="px-3 py-2 font-mono">{s.step_id ?? '—'}</td>
                  <td class="px-3 py-2 text-right font-mono">{s.entered}</td>
                  <td class="px-3 py-2 text-right font-mono {s.dropped_off > 0 ? 'text-maestro' : 'text-text-muted'}">{s.dropped_off}</td>
                  <td class="px-3 py-2 text-right font-mono {s.conversion_next_pct === null ? 'text-text-muted' : s.conversion_next_pct >= 80 ? 'text-teacher' : s.conversion_next_pct >= 50 ? 'text-lehrer' : 'text-maestro'}">
                    {s.conversion_next_pct === null ? '—' : `${s.conversion_next_pct}%`}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}

      {#if funnelStats.recent_aborts && funnelStats.recent_aborts.length > 0}
        <details class="bg-elevated rounded-lg">
          <summary class="px-3 py-2 text-xs cursor-pointer text-text-muted">Recent aborts ({funnelStats.recent_aborts.length})</summary>
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-border-subtle text-text-muted">
                <th class="text-left px-3 py-2 font-normal">When</th>
                <th class="text-left px-3 py-2 font-normal">Last step</th>
                <th class="text-right px-3 py-2 font-normal">#</th>
                <th class="text-right px-3 py-2 font-normal">Duration</th>
              </tr>
            </thead>
            <tbody>
              {#each funnelStats.recent_aborts as a (a.session_id)}
                <tr class="border-b border-border-subtle/50">
                  <td class="px-3 py-2 font-mono text-text-muted">{a.created_at ? a.created_at.slice(0, 16).replace('T', ' ') : '—'}</td>
                  <td class="px-3 py-2 font-mono">{a.step_id ?? '—'}</td>
                  <td class="px-3 py-2 text-right font-mono">{a.step_order ?? '—'}</td>
                  <td class="px-3 py-2 text-right font-mono text-text-muted">{a.duration_ms !== null ? `${Math.round(a.duration_ms / 1000)}s` : '—'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </details>
      {/if}
    {/if}
  </div>

  <!-- DIAGNOSTICS — collapsed by default -->
  <details class="bg-surface border border-border-subtle rounded-xl">
    <summary class="px-4 py-3 text-sm cursor-pointer text-text-secondary flex items-center justify-between">
      <span class="font-semibold">Prompt caching (OpenAI)</span>
      <span class="text-xs text-text-muted font-normal">cached / prompt tokens</span>
    </summary>
    <div class="p-4 space-y-3 border-t border-border-subtle">
      <div class="flex justify-end gap-1">
        {#each [24, 168, 720] as h (h)}
          <button
            onclick={() => switchCacheWindow(h)}
            class="px-2 py-1 text-xs rounded {cacheHours === h ? 'bg-accent text-white' : 'bg-elevated text-text-muted hover:text-text-primary'}"
          >{h === 24 ? '24h' : h === 168 ? '7j' : '30j'}</button>
        {/each}
      </div>

      {#if cacheLoading}
        <div class="skeleton h-20 rounded-lg"></div>
      {:else if !cacheStats || !cacheStats.summary}
        <p class="text-xs text-text-muted italic">Aucune donnée pour cette fenêtre.</p>
      {:else}
        {@const s = cacheStats.summary}
        {@const alerts = cacheStats.alerts ?? []}

        {#if alerts.length > 0}
          <div class="space-y-2">
            {#each alerts as a (a.code)}
              {@const color = a.level === 'critical' ? 'bg-maestro/20 border-maestro text-maestro'
                : a.level === 'warning' ? 'bg-lehrer/20 border-lehrer text-lehrer'
                : 'bg-elevated border-border-subtle text-text-muted'}
              <div class="rounded-lg border px-3 py-2 text-xs {color}">
                <p class="font-semibold uppercase tracking-wider mb-0.5">{a.level}</p>
                <p>{a.message}</p>
              </div>
            {/each}
          </div>
        {/if}
        <div class="grid grid-cols-3 gap-3">
          <div class="bg-elevated rounded-lg p-3">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Requêtes</p>
            <p class="text-lg font-mono font-semibold text-text-primary">{s.requests ?? 0}</p>
          </div>
          <div class="bg-elevated rounded-lg p-3">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Cache hit</p>
            <p class="text-lg font-mono font-semibold text-teacher">{s.cache_pct ?? 0}%</p>
            <p class="text-[10px] text-text-muted">{(s.cached_tokens ?? 0).toLocaleString()} / {(s.prompt_tokens ?? 0).toLocaleString()} tok</p>
          </div>
          <div class="bg-elevated rounded-lg p-3">
            <p class="text-[10px] uppercase tracking-wider text-text-muted">Économie ~</p>
            <p class="text-lg font-mono font-semibold text-text-primary">${((s.cached_tokens ?? 0) * 0.075 / 1_000_000).toFixed(3)}</p>
            <p class="text-[10px] text-text-muted">50% discount vs full input @ $0.15/1M</p>
          </div>
        </div>

        {#if cacheStats.by_hour && cacheStats.by_hour.length > 1}
          <div class="bg-elevated rounded-lg p-3">
            <p class="text-[10px] uppercase tracking-wider text-text-muted mb-2">Hit rate dans le temps</p>
            <svg viewBox="0 0 280 60" class="w-full h-16" preserveAspectRatio="none">
              <line x1="0" y1="30" x2="280" y2="30" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="2 2" />
              <path d={sparkPath(cacheStats.by_hour)} fill="none" stroke="currentColor" stroke-width="1.5" class="text-teacher" />
            </svg>
          </div>
        {/if}

        {#if cacheStats.by_model && cacheStats.by_model.length > 0}
          <div class="bg-elevated rounded-lg overflow-hidden">
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-border-subtle text-text-muted">
                  <th class="text-left px-3 py-2 font-normal">Modèle</th>
                  <th class="text-right px-3 py-2 font-normal">Req</th>
                  <th class="text-right px-3 py-2 font-normal">Prompt tok</th>
                  <th class="text-right px-3 py-2 font-normal">Cached tok</th>
                  <th class="text-right px-3 py-2 font-normal">Hit %</th>
                </tr>
              </thead>
              <tbody>
                {#each cacheStats.by_model as m (m.model)}
                  <tr class="border-b border-border-subtle/50">
                    <td class="px-3 py-2 font-mono">{m.model}</td>
                    <td class="px-3 py-2 text-right font-mono">{m.requests}</td>
                    <td class="px-3 py-2 text-right font-mono">{(m.prompt_tokens ?? 0).toLocaleString()}</td>
                    <td class="px-3 py-2 text-right font-mono">{(m.cached_tokens ?? 0).toLocaleString()}</td>
                    <td class="px-3 py-2 text-right font-mono {m.cache_pct >= 50 ? 'text-teacher' : m.cache_pct >= 20 ? 'text-lehrer' : 'text-text-muted'}">{m.cache_pct ?? 0}%</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {/if}
    </div>
  </details>
</div>
