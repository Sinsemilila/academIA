<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { addToast, toastError } from '$lib/stores/toasts';
  import { agents, domainLabel } from '$lib/config';
  import { currentDomain } from '$lib/stores/navigation';
  import { get } from 'svelte/store';

  type AdminUser = {
    id: number;
    username: string;
    display_name: string | null;
    is_admin: boolean;
    exam_access: boolean;
    created_at: string | null;
    niveau: string | null;
    derniere_session: string | null;
    mode: string | null;
    current_streak: number;
    longest_streak: number;
    total_sessions: number;
    total_xp: number;
    online: boolean;
    last_seen: string | null;
  };

  let users = $state<AdminUser[]>([]);
  let loading = $state(true);
  let showCreateForm = $state(false);
  let newUsername = $state('');
  let newPassword = $state('');
  let creating = $state(false);
  let confirmDelete = $state<number | null>(null);
  let confirmReset = $state<string | null>(null);
  // Session 37 — admin-wide domain filter. Drives both the "niveau" column
  // query (backend returns profils_eleves.niveau_global scoped to this domain)
  // AND the default of the per-user reset <select> when admin clicks Reset.
  let adminDomain = $state<string>(get(currentDomain));
  // resetDomain is initialized to adminDomain on Reset click (see button handler).
  let resetDomain = $state<string | null>(get(currentDomain));
  const availableAgents = $derived(agents.filter(a => a.available));
  let tokenUsage = $state<any>(null);

  // Phase D v2 — OpenAI prompt caching telemetry (Block 1.2 sidecar)
  let cacheStats = $state<any>(null);
  let cacheHours = $state(24);
  let cacheLoading = $state(false);

  async function loadTokenUsage() {
    try {
      tokenUsage = await api.getTokenUsage();
    } catch {}
  }

  async function loadCacheStats() {
    cacheLoading = true;
    try {
      cacheStats = await api.adminCacheStats(cacheHours);
    } catch {
      cacheStats = null;
    } finally {
      cacheLoading = false;
    }
  }

  async function switchCacheWindow(hours: number) {
    cacheHours = hours;
    await loadCacheStats();
  }

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

  async function loadUsers() {
    try {
      users = await api.adminGetUsers(adminDomain);
    } catch {
      toastError('Acces admin requis');
      goto('/');
    } finally {
      loading = false;
    }
  }

  async function switchAdminDomain(d: string) {
    adminDomain = d;
    loading = true;
    await loadUsers();
  }

  async function createUser() {
    if (!newUsername || !newPassword) return;
    creating = true;
    try {
      await api.adminCreateUser(newUsername, newPassword);
      addToast(`Utilisateur ${newUsername} cree`, 'success');
      newUsername = '';
      newPassword = '';
      showCreateForm = false;
      await loadUsers();
    } catch (e: any) {
      toastError(e.message || 'Erreur creation');
    } finally {
      creating = false;
    }
  }

  async function resetProfile(username: string) {
    try {
      await api.adminResetProfile(username, resetDomain);
      const scopeLabel = resetDomain
        ? `${domainLabel(resetDomain)} uniquement`
        : 'tous domaines + historique';
      addToast(`Profil ${username} réinitialisé (${scopeLabel})`, 'success');
      confirmReset = null;
      await loadUsers();
    } catch (e: any) {
      toastError(e.message || 'Erreur reset');
    }
  }

  async function deleteUser(userId: number) {
    try {
      await api.adminDeleteUser(userId);
      addToast('Utilisateur supprime', 'success');
      confirmDelete = null;
      await loadUsers();
    } catch (e: any) {
      toastError(e.message || 'Erreur suppression');
    }
  }

  function timeAgo(dateStr: string | null): string {
    if (!dateStr) return 'jamais';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (diff < 60) return 'maintenant';
    if (diff < 3600) return `il y a ${Math.floor(diff / 60)}min`;
    if (diff < 86400) return `il y a ${Math.floor(diff / 3600)}h`;
    return `il y a ${Math.floor(diff / 86400)}j`;
  }

  // Session 42 P3 — consolidation events admin analytics
  let consolidationStats = $state<any>(null);
  let consolidationLoading = $state(false);
  async function loadConsolidationStats() {
    consolidationLoading = true;
    try {
      consolidationStats = await api.adminConsolidationEvents(adminDomain, 168);
    } catch {
      consolidationStats = null;
    } finally {
      consolidationLoading = false;
    }
  }

  // Session 42 O2 — oracle runs admin analytics
  let oracleStats = $state<any>(null);
  let oracleLoading = $state(false);
  async function loadOracleStats() {
    oracleLoading = true;
    try {
      const oracleAgent = adminDomain === 'es' ? 'maestro_es' : 'teacher_en';
      oracleStats = await api.adminOracleRuns(oracleAgent, 168);
    } catch {
      oracleStats = null;
    } finally {
      oracleLoading = false;
    }
  }

  onMount(() => {
    loadUsers(); loadTokenUsage(); loadCacheStats();
    loadConsolidationStats(); loadOracleStats();
  });
</script>

<svelte:head>
  <title>Admin — AcademIA</title>
</svelte:head>

<div class="max-w-5xl mx-auto space-y-6">
  <div class="flex items-center justify-between flex-wrap gap-3">
    <h1 class="text-xl font-bold text-text-primary">Administration</h1>
    <div class="flex items-center gap-2">
      <label class="text-xs text-text-muted">Domaine affiché :</label>
      <select
        value={adminDomain}
        onchange={(e) => switchAdminDomain((e.target as HTMLSelectElement).value)}
        class="px-2 py-1 text-sm rounded bg-elevated border border-border-subtle text-text-primary"
        title="Filtre la colonne niveau + défaut du Reset"
      >
        {#each availableAgents as a (a.domain)}
          <option value={a.domain}>{a.lang}</option>
        {/each}
      </select>
      <button
        onclick={() => showCreateForm = !showCreateForm}
        class="px-4 py-2 text-sm font-medium rounded-lg bg-accent text-white hover:opacity-90 transition"
      >
        + Nouvel utilisateur
      </button>
    </div>
  </div>

  <!-- Token Usage -->
  {#if tokenUsage}
    {@const pct = tokenUsage.pct}
    {@const barColor = pct > 90 ? 'bg-maestro' : pct > 70 ? 'bg-lehrer' : 'bg-teacher'}
    {@const ftModel = tokenUsage.models?.find((m: any) => m.name?.startsWith('ft:gpt-4o-mini'))}
    {@const sourceLabel = tokenUsage.source === 'litellm' ? 'Source : LiteLLM (réel)' : 'Source : estimation locale'}
    {@const sourceColor = tokenUsage.source === 'litellm' ? 'text-text-muted' : 'text-lehrer'}
    <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
      <div>
        <div class="flex items-center justify-between mb-2">
          <div>
            <h2 class="text-sm font-semibold">GPT-4o-mini &mdash; Quota journalier</h2>
            <p class="text-xs text-text-muted">Mod&#232;le actif : {tokenUsage.model}</p>
          </div>
          <div class="text-right">
            <p class="text-lg font-mono font-semibold" title="Affichage avec marge de sécurité +{tokenUsage.safety_margin_pct ?? 10}% pour rester ≥ OpenAI dashboard. Source brute : {tokenUsage.tokens_raw ? Math.round(tokenUsage.tokens_raw / 1000) + 'K' : 'n/a'}.">{Math.round(tokenUsage.tokens / 1000)}K <span class="text-sm text-text-muted font-normal">/ {Math.round(tokenUsage.limit / 1000)}K</span></p>
            <p class="text-xs text-text-muted">{pct}%{tokenUsage.safety_margin_pct ? ` (+${tokenUsage.safety_margin_pct}% safety)` : ''}</p>
          </div>
        </div>
        <div class="w-full h-2 bg-elevated rounded-full overflow-hidden">
          <div class="h-full {barColor} rounded-full transition-all" style="width: {Math.min(pct, 100)}%"></div>
        </div>
        {#if tokenUsage.exceeded}
          <p class="text-xs text-maestro mt-2">Quota d&#233;pass&#233; &mdash; fallback groq-standard actif</p>
        {/if}
        <p class="text-[10px] {sourceColor} mt-2 font-mono">{sourceLabel}</p>
      </div>

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
    </div>
  {/if}

  <!-- Phase D v2 — OpenAI prompt caching (Block 1.2 sidecar) -->
  <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold text-text-primary">Prompt caching (OpenAI)</h2>
        <p class="text-xs text-text-muted">cached_tokens / prompt_tokens via LiteLLM callback → litellm_cache_stats</p>
      </div>
      <div class="flex gap-1">
        {#each [24, 168, 720] as h (h)}
          <button
            onclick={() => switchCacheWindow(h)}
            class="px-2 py-1 text-xs rounded {cacheHours === h ? 'bg-accent text-white' : 'bg-elevated text-text-muted hover:text-text-primary'}"
          >
            {h === 24 ? '24h' : h === 168 ? '7j' : '30j'}
          </button>
        {/each}
      </div>
    </div>

    {#if cacheLoading}
      <div class="skeleton h-20 rounded-lg"></div>
    {:else if !cacheStats || !cacheStats.summary}
      <p class="text-xs text-text-muted italic">Aucune donnée pour cette fenêtre.</p>
    {:else}
      {@const s = cacheStats.summary}
      {@const alerts = cacheStats.alerts ?? []}

      <!-- Phase D v3 alerts banner (Session 41) -->
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

  <!-- Session 42 P3 — Consolidation events analytics -->
  <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold text-text-primary">Consolidation CEFR events</h2>
        <p class="text-xs text-text-muted">7 derniers jours — domaine {adminDomain}. Événements trigger/decide de consolidation.</p>
      </div>
    </div>
    {#if consolidationLoading}
      <div class="skeleton h-20 rounded-lg"></div>
    {:else if !consolidationStats || !consolidationStats.summary}
      <p class="text-xs text-text-muted italic">Aucune donnée.</p>
    {:else}
      {@const cs = consolidationStats.summary}
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Total events</p>
          <p class="text-lg font-mono font-semibold text-text-primary">{cs.total ?? 0}</p>
          <p class="text-[10px] text-text-muted">{cs.pending ?? 0} pending · {cs.closed ?? 0} closed</p>
        </div>
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Mini-exam</p>
          <p class="text-lg font-mono font-semibold text-text-primary">{cs.mini_exam_count ?? 0}</p>
          <p class="text-[10px] text-text-muted">{cs.mini_exam_pass ?? 0} pass · {cs.mini_exam_fail ?? 0} fail · avg {cs.avg_mini_exam_score ?? 0}%</p>
        </div>
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Pass rate</p>
          <p class="text-lg font-mono font-semibold {(cs.mini_exam_pass ?? 0) + (cs.mini_exam_fail ?? 0) > 0 ? 'text-teacher' : 'text-text-muted'}">
            {((cs.mini_exam_pass ?? 0) + (cs.mini_exam_fail ?? 0)) > 0 ? Math.round((cs.mini_exam_pass / ((cs.mini_exam_pass ?? 0) + (cs.mini_exam_fail ?? 0))) * 100) : '—'}%
          </p>
        </div>
      </div>

      {#if consolidationStats.by_decision && consolidationStats.by_decision.length > 0}
        <div class="bg-elevated rounded-lg overflow-hidden">
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-border-subtle text-text-muted">
                <th class="text-left px-3 py-2 font-normal">Décision</th>
                <th class="text-right px-3 py-2 font-normal">Count</th>
                <th class="text-right px-3 py-2 font-normal">Avg score</th>
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
        </div>
      {/if}
    {/if}
  </div>

  <!-- Session 42 O2 — Oracle V1 runs analytics -->
  <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
    <div>
      <h2 class="text-sm font-semibold text-text-primary">Oracle V1 runs</h2>
      <p class="text-xs text-text-muted">7 derniers jours — agent {adminDomain === 'es' ? 'maestro_es' : 'teacher_en'}. oracle_run_log sidecar.</p>
    </div>
    {#if oracleLoading}
      <div class="skeleton h-20 rounded-lg"></div>
    {:else if !oracleStats || !oracleStats.summary}
      <p class="text-xs text-text-muted italic">Aucun run persisté.</p>
    {:else}
      {@const os_ = oracleStats.summary}
      <div class="grid grid-cols-3 gap-3">
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Runs</p>
          <p class="text-lg font-mono font-semibold text-text-primary">{os_.total_runs ?? 0}</p>
          <p class="text-[10px] text-text-muted">{os_.total_rows ?? 0} rows</p>
        </div>
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Scenarios touchés</p>
          <p class="text-lg font-mono font-semibold text-text-primary">{os_.scenarios_touched ?? 0}</p>
        </div>
        <div class="bg-elevated rounded-lg p-3">
          <p class="text-[10px] uppercase tracking-wider text-text-muted">Dims actifs</p>
          <p class="text-lg font-mono font-semibold text-text-primary">{(oracleStats.by_dim ?? []).length}</p>
        </div>
      </div>

      {#if oracleStats.by_dim && oracleStats.by_dim.length > 0}
        <div class="bg-elevated rounded-lg overflow-hidden">
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-border-subtle text-text-muted">
                <th class="text-left px-3 py-2 font-normal">Dim</th>
                <th class="text-right px-3 py-2 font-normal">Total</th>
                <th class="text-right px-3 py-2 font-normal">Pass</th>
                <th class="text-right px-3 py-2 font-normal">Fail</th>
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
        </div>
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
                <th class="text-left px-3 py-2 font-normal">sha</th>
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
                  <td class="px-3 py-2 font-mono text-text-muted">{r.sha || '—'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </details>
      {/if}
    {/if}
  </div>

  {#if showCreateForm}
    <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
      <div class="flex gap-3">
        <input
          type="text"
          placeholder="Username"
          bind:value={newUsername}
          class="flex-1 px-3 py-2 rounded-lg bg-base border border-border-subtle text-sm text-text-primary"
        />
        <input
          type="password"
          placeholder="Mot de passe (min 8 car.)"
          bind:value={newPassword}
          class="flex-1 px-3 py-2 rounded-lg bg-base border border-border-subtle text-sm text-text-primary"
        />
        <button
          onclick={createUser}
          disabled={creating || !newUsername || newPassword.length < 8}
          class="px-4 py-2 text-sm font-medium rounded-lg bg-accent text-white hover:opacity-90 transition disabled:opacity-50"
        >
          {creating ? '...' : 'Creer'}
        </button>
      </div>
    </div>
  {/if}

  {#if loading}
    <div class="space-y-3">
      {#each Array(3) as _}<div class="skeleton h-16 rounded-xl"></div>{/each}
    </div>
  {:else}
    <div class="bg-surface border border-border-subtle rounded-xl overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border-subtle text-text-secondary text-left">
            <th class="px-4 py-3 font-medium">Utilisateur</th>
            <th class="px-4 py-3 font-medium hidden sm:table-cell">Niveau <span class="text-xs text-text-muted font-normal">({domainLabel(adminDomain)})</span></th>
            <th class="px-4 py-3 font-medium hidden md:table-cell">Sessions</th>
            <th class="px-4 py-3 font-medium hidden md:table-cell">Streak</th>
            <th class="px-4 py-3 font-medium hidden lg:table-cell">XP</th>
            <th class="px-4 py-3 font-medium">Derniere connexion</th>
            <th class="px-4 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each users as user (user.id)}
            <tr class="border-b border-border-subtle/50 hover:bg-base/50 transition">
              <td class="px-4 py-3">
                <div class="flex items-center gap-1.5">
                  {#if user.online}
                    <span class="w-2 h-2 rounded-full bg-green-400 shrink-0" title="En ligne"></span>
                  {/if}
                  <span class="font-medium text-text-primary">{user.display_name || user.username}</span>
                </div>
                <div class="text-xs text-text-muted">{user.username}{user.is_admin ? ' (admin)' : ''}</div>
              </td>
              <td class="px-4 py-3 hidden sm:table-cell">
                <span class="px-2 py-0.5 rounded text-xs font-semibold
                  {user.niveau ? 'bg-accent/20 text-accent' : 'bg-base text-text-muted'}">
                  {user.niveau || 'N/A'}
                </span>
              </td>
              <td class="px-4 py-3 hidden md:table-cell text-text-secondary">{user.total_sessions}</td>
              <td class="px-4 py-3 hidden md:table-cell text-text-secondary">{user.current_streak}j</td>
              <td class="px-4 py-3 hidden lg:table-cell text-text-secondary">{user.total_xp}</td>
              <td class="px-4 py-3 text-text-muted text-xs">
                {#if user.online}
                  <span class="text-green-400">en ligne</span>
                {:else}
                  {timeAgo(user.last_seen)}
                {/if}
              </td>
              <td class="px-4 py-3 text-right space-x-1">
                {#if confirmReset === user.username}
                  <select bind:value={resetDomain}
                    class="px-1 py-1 text-xs rounded bg-elevated border border-border-subtle text-text-primary"
                    title="Domaine à réinitialiser">
                    {#each availableAgents as a (a.domain)}
                      <option value={a.domain}>{a.lang}</option>
                    {/each}
                    <option value={null}>Tous (+ historique)</option>
                  </select>
                  <button onclick={() => resetProfile(user.username)}
                    class="px-2 py-1 text-xs rounded bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30">
                    Confirmer
                  </button>
                  <button onclick={() => confirmReset = null}
                    class="px-2 py-1 text-xs rounded text-text-muted hover:text-text-secondary">
                    Annuler
                  </button>
                {:else if confirmDelete === user.id}
                  <button onclick={() => deleteUser(user.id)}
                    class="px-2 py-1 text-xs rounded bg-red-500/20 text-red-400 hover:bg-red-500/30">
                    Confirmer suppr
                  </button>
                  <button onclick={() => confirmDelete = null}
                    class="px-2 py-1 text-xs rounded text-text-muted hover:text-text-secondary">
                    Annuler
                  </button>
                {:else}
                  <button onclick={() => { resetDomain = adminDomain; confirmReset = user.username; }}
                    title="Réinitialiser le profil (choix du domaine à l'étape suivante)"
                    class="px-2 py-1 text-xs rounded text-text-muted hover:text-yellow-400 hover:bg-yellow-500/10 transition">
                    Reset
                  </button>
                  {#if !user.is_admin}
                    <button onclick={() => confirmDelete = user.id}
                      title="Supprimer utilisateur"
                      class="px-2 py-1 text-xs rounded text-text-muted hover:text-red-400 hover:bg-red-500/10 transition">
                      Suppr
                    </button>
                  {/if}
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <div class="text-xs text-text-muted text-center">
      {users.filter(u => u.online).length} en ligne — {users.length} inscrits
    </div>
  {/if}
</div>
