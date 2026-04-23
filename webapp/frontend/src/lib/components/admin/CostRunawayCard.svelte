<!--
  Refactor 2026-H2 Phase A5 — per-user cost runaway visibility.
  Renders /api/admin/cost-runaway-users : top 20 + outlier flag.
-->
<script lang="ts">
  type UserRow = {
    user_id: number;
    username: string;
    display_name: string | null;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    models_used: number;
    runaway: boolean;
  };

  let { data, window, onWindowChange } = $props<{
    data: {
      window: string;
      days: number;
      median_tokens: number;
      outlier_threshold: number;
      users: UserRow[];
      system_attributable_tokens: number;
      as_of: string;
    } | null;
    window: string;
    onWindowChange: (w: string) => void;
  }>();

  const WINDOWS = ['24h', '7d', '30d'];

  function fmtTokens(n: number): string {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'k';
    return String(n);
  }

  function pctOfMedian(n: number, median: number): string {
    if (median <= 0) return '—';
    return `${Math.round((n / median) * 100)}%`;
  }
</script>

<div class="space-y-3">
  <div class="flex items-end justify-between gap-3 flex-wrap">
    <div>
      <p class="text-[10px] uppercase tracking-wider text-text-muted">Top consumers (per-user)</p>
      <p class="text-xs text-text-muted">Outlier flag : > max(median × 5, 100K tokens) sur la fenêtre.</p>
    </div>
    <div class="flex items-center gap-1 shrink-0">
      {#each WINDOWS as w (w)}
        <button
          type="button"
          onclick={() => onWindowChange(w)}
          class="px-1.5 py-0.5 text-[10px] rounded {window === w ? 'bg-accent text-white' : 'bg-elevated text-text-muted hover:text-text-primary'}"
        >{w}</button>
      {/each}
    </div>
  </div>

  {#if !data}
    <div class="skeleton h-24 rounded-lg"></div>
  {:else}
    <div class="grid grid-cols-3 gap-2">
      <div class="bg-elevated rounded-lg p-2">
        <p class="text-[10px] uppercase tracking-wider text-text-muted">Median user</p>
        <p class="text-sm font-mono font-semibold text-text-primary">{fmtTokens(data.median_tokens)}</p>
      </div>
      <div class="bg-elevated rounded-lg p-2">
        <p class="text-[10px] uppercase tracking-wider text-text-muted">Runaway threshold</p>
        <p class="text-sm font-mono font-semibold text-text-primary">{fmtTokens(data.outlier_threshold)}</p>
      </div>
      <div class="bg-elevated rounded-lg p-2">
        <p class="text-[10px] uppercase tracking-wider text-text-muted">System (Oracle, etc.)</p>
        <p class="text-sm font-mono font-semibold text-text-primary">{fmtTokens(data.system_attributable_tokens)}</p>
      </div>
    </div>

    {#if data.users.length === 0}
      <p class="text-xs text-text-muted text-center py-4">
        Aucune télémétrie attribuable sur la fenêtre {window}.
      </p>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="text-left text-text-muted border-b border-border-subtle">
              <th class="py-1.5 font-normal">Utilisateur</th>
              <th class="py-1.5 font-normal text-right">Total</th>
              <th class="py-1.5 font-normal text-right">% médiane</th>
              <th class="py-1.5 font-normal text-right">Input</th>
              <th class="py-1.5 font-normal text-right">Output</th>
              <th class="py-1.5 font-normal text-right">Modèles</th>
            </tr>
          </thead>
          <tbody>
            {#each data.users as u (u.user_id)}
              <tr class="border-b border-border-subtle/50 {u.runaway ? 'bg-rose-500/5' : ''}">
                <td class="py-1.5">
                  {#if u.runaway}
                    <span class="inline-block mr-1" title="Outlier — vérifie abuse / runaway loop">⚠️</span>
                  {/if}
                  <span class="{u.runaway ? 'text-rose-300 font-semibold' : 'text-text-primary'}">{u.username}</span>
                  {#if u.display_name}
                    <span class="text-text-muted">— {u.display_name}</span>
                  {/if}
                </td>
                <td class="py-1.5 text-right font-mono {u.runaway ? 'text-rose-300 font-semibold' : 'text-text-primary'}">
                  {fmtTokens(u.total_tokens)}
                </td>
                <td class="py-1.5 text-right font-mono text-text-muted">
                  {pctOfMedian(u.total_tokens, data.median_tokens)}
                </td>
                <td class="py-1.5 text-right font-mono text-text-secondary">{fmtTokens(u.input_tokens)}</td>
                <td class="py-1.5 text-right font-mono text-text-secondary">{fmtTokens(u.output_tokens)}</td>
                <td class="py-1.5 text-right text-text-muted">{u.models_used}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    <p class="text-[10px] text-text-muted text-right">As of {new Date(data.as_of).toLocaleString('fr-FR')}</p>
  {/if}
</div>
