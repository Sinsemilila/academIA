<script lang="ts">
  type Tier = {
    alias: string;
    label: string;
    rpd_limit: number;
    used: number;
    remaining: number;
    pct: number;
    is_active: boolean;
  };

  let { tiers, totalUsed, totalLimit, totalRemaining, preflightCmd } = $props<{
    tiers: Tier[];
    totalUsed: number;
    totalLimit: number;
    totalRemaining: number;
    preflightCmd: string;
  }>();

  const totalPct = $derived(totalLimit > 0 ? (totalUsed / totalLimit) * 100 : 0);

  function tierColor(pct: number): string {
    if (pct >= 95) return '#ef4444';
    if (pct >= 70) return '#f59e0b';
    return '#10b981';
  }

  // Segment widths proportional to each tier's RPD limit (so the 500-cap
  // tier visually dominates — matches real budget allocation).
  const segments = $derived.by(() => {
    let offsetPct = 0;
    return tiers.map((t: Tier) => {
      const widthPct = (t.rpd_limit / totalLimit) * 100;
      const innerFillPct = t.rpd_limit > 0 ? (t.used / t.rpd_limit) * 100 : 0;
      const seg = {
        ...t,
        offsetPct,
        widthPct,
        innerFillPct: Math.min(innerFillPct, 100),
      };
      offsetPct += widthPct;
      return seg;
    });
  });

  const activeTier = $derived(tiers.find((t: Tier) => t.is_active) ?? tiers[0]);
</script>

<div class="space-y-3">
  <div class="flex items-end justify-between gap-3 flex-wrap">
    <div>
      <p class="text-[10px] uppercase tracking-wider text-text-muted">Tier judge actif</p>
      <p class="text-base font-mono font-semibold text-text-primary">
        {activeTier.label} <span class="text-xs text-text-muted font-normal">({activeTier.alias})</span>
      </p>
    </div>
    <div class="text-right">
      <p class="text-[10px] uppercase tracking-wider text-text-muted">Total today</p>
      <p class="text-base font-mono font-semibold {totalPct >= 90 ? 'text-maestro' : totalPct >= 70 ? 'text-lehrer' : 'text-teacher'}">
        {totalUsed} / {totalLimit} RPD
      </p>
      <p class="text-[10px] text-text-muted font-mono">{totalRemaining} remaining</p>
    </div>
  </div>

  <div class="relative w-full h-5 bg-elevated rounded-full overflow-hidden">
    <svg viewBox="0 0 100 10" preserveAspectRatio="none" class="absolute inset-0 w-full h-full">
      {#each segments as s, i (s.alias)}
        <rect
          x={s.offsetPct}
          y="0"
          width={s.widthPct}
          height="10"
          fill={s.is_active ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.03)'}
        />
        <rect
          x={s.offsetPct}
          y="0"
          width={s.widthPct * s.innerFillPct / 100}
          height="10"
          fill={tierColor(s.pct)}
          opacity={s.is_active ? 1 : 0.6}
        />
        {#if i > 0}
          <line x1={s.offsetPct} y1="0" x2={s.offsetPct} y2="10"
                stroke="rgba(0,0,0,0.4)" stroke-width="0.4" />
        {/if}
        {#if s.is_active}
          <rect x={s.offsetPct + 0.1} y="0.1"
                width={s.widthPct - 0.2} height="9.8"
                fill="none" stroke="white" stroke-width="0.3" stroke-opacity="0.6" />
        {/if}
      {/each}
    </svg>
  </div>

  <div class="grid grid-cols-3 gap-2">
    {#each tiers as t (t.alias)}
      <div class="bg-elevated rounded-lg p-2 {t.is_active ? 'ring-1 ring-accent' : ''}">
        <div class="flex items-baseline justify-between gap-1">
          <p class="text-[10px] uppercase tracking-wider text-text-muted truncate" title={t.label}>{t.label}</p>
          {#if t.is_active}
            <span class="text-[9px] font-semibold text-accent">ACTIF</span>
          {/if}
        </div>
        <p class="text-sm font-mono font-semibold {t.pct >= 95 ? 'text-maestro' : t.pct >= 70 ? 'text-lehrer' : 'text-teacher'}">
          {t.pct}%
        </p>
        <p class="text-[10px] text-text-muted font-mono">{t.used} / {t.rpd_limit} RPD</p>
      </div>
    {/each}
  </div>

  <div class="text-[10px] text-text-muted font-mono bg-elevated rounded-lg px-3 py-2">
    Pre-flight CLI : <code class="text-text-secondary">{preflightCmd}</code>
  </div>
</div>
