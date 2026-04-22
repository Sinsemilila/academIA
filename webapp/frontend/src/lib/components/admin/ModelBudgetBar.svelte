<script lang="ts">
  type Tier = {
    name: string;
    limit: number;
    used: number;
    pct: number;
    is_active: boolean;
    eta_exhaust_min: number | null;
  };

  let { tiers, currentTier, currentSince, totalRemaining } = $props<{
    tiers: Tier[];
    currentTier: string;
    currentSince: string | null;
    totalRemaining: number;
  }>();

  // Each tier segment width = tier.limit / Σ(limits). The "now" marker
  // position on a given tier = tier.used / tier.limit within that segment.
  // Segments are laid out in activation order (tier 1 leftmost).
  const totalCapacity = $derived(tiers.reduce((acc: number, t: Tier) => acc + t.limit, 0));
  const segments = $derived.by(() => {
    let offsetPct = 0;
    return tiers.map((t: Tier) => {
      const widthPct = (t.limit / totalCapacity) * 100;
      const innerFillPct = t.limit > 0 ? (t.used / t.limit) * 100 : 0;
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

  function fmtTokens(n: number): string {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M';
    if (n >= 1_000) return Math.round(n / 1_000) + 'K';
    return n.toString();
  }

  function fmtEta(min: number | null): string {
    if (min === null) return '—';
    if (min > 24 * 60) return 'jours restants';
    if (min >= 60) return `~${Math.round(min / 60)}h`;
    return `~${min}min`;
  }

  function fmtSince(iso: string | null): string {
    if (!iso) return 'depuis minuit';
    const d = new Date(iso);
    const diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) return 'à l\'instant';
    if (diff < 3600) return `depuis ${Math.floor(diff / 60)}min`;
    if (diff < 86400) return `depuis ${Math.floor(diff / 3600)}h`;
    return `depuis ${Math.floor(diff / 86400)}j`;
  }

  // Color per tier : OK (green) / warn (amber) / near-exhaust (red)
  function tierColor(pct: number): string {
    if (pct >= 95) return '#ef4444';  // maestro-ish red
    if (pct >= 70) return '#f59e0b';  // lehrer amber
    return '#10b981';                  // teacher green
  }

  const activeTier = $derived(tiers.find((t: Tier) => t.is_active) ?? tiers[0]);
</script>

<div class="space-y-3">
  <!-- Headline text -->
  <div class="flex items-end justify-between gap-3 flex-wrap">
    <div>
      <p class="text-[10px] uppercase tracking-wider text-text-muted">Tier actif</p>
      <p class="text-base font-mono font-semibold text-text-primary">
        {currentTier} <span class="text-xs text-text-muted font-normal">{fmtSince(currentSince)}</span>
      </p>
    </div>
    <div class="text-right">
      <p class="text-[10px] uppercase tracking-wider text-text-muted">ETA exhaust tier actif</p>
      <p class="text-base font-mono font-semibold {activeTier.pct >= 90 ? 'text-maestro' : activeTier.pct >= 70 ? 'text-lehrer' : 'text-teacher'}">
        {fmtEta(activeTier.eta_exhaust_min)}
      </p>
    </div>
    <div class="text-right">
      <p class="text-[10px] uppercase tracking-wider text-text-muted">Capacité restante</p>
      <p class="text-base font-mono font-semibold text-text-primary">{fmtTokens(totalRemaining)}</p>
    </div>
  </div>

  <!-- Stacked bar -->
  <div class="relative w-full h-5 bg-elevated rounded-full overflow-hidden">
    <svg viewBox="0 0 100 10" preserveAspectRatio="none" class="absolute inset-0 w-full h-full">
      {#each segments as s, i (s.name)}
        <!-- Segment background (muted) -->
        <rect
          x={s.offsetPct}
          y="0"
          width={s.widthPct}
          height="10"
          fill={s.is_active ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.03)'}
        />
        <!-- Segment fill (usage) -->
        <rect
          x={s.offsetPct}
          y="0"
          width={s.widthPct * s.innerFillPct / 100}
          height="10"
          fill={tierColor(s.pct)}
          opacity={s.is_active ? 1 : 0.6}
        />
        <!-- Segment divider -->
        {#if i > 0}
          <line
            x1={s.offsetPct}
            y1="0"
            x2={s.offsetPct}
            y2="10"
            stroke="rgba(0,0,0,0.4)"
            stroke-width="0.4"
          />
        {/if}
        <!-- Active-tier highlight ring -->
        {#if s.is_active}
          <rect
            x={s.offsetPct + 0.1}
            y="0.1"
            width={s.widthPct - 0.2}
            height="9.8"
            fill="none"
            stroke="white"
            stroke-width="0.3"
            stroke-opacity="0.6"
          />
        {/if}
      {/each}
    </svg>
  </div>

  <!-- Per-tier breakdown -->
  <div class="grid grid-cols-3 gap-2">
    {#each tiers as t (t.name)}
      <div class="bg-elevated rounded-lg p-2 {t.is_active ? 'ring-1 ring-accent' : ''}">
        <div class="flex items-baseline justify-between gap-1">
          <p class="text-[10px] uppercase tracking-wider text-text-muted truncate" title={t.name}>{t.name}</p>
          {#if t.is_active}
            <span class="text-[9px] font-semibold text-accent">ACTIF</span>
          {/if}
        </div>
        <p class="text-sm font-mono font-semibold {t.pct >= 95 ? 'text-maestro' : t.pct >= 70 ? 'text-lehrer' : 'text-teacher'}">
          {t.pct}%
        </p>
        <p class="text-[10px] text-text-muted font-mono">{fmtTokens(t.used)} / {fmtTokens(t.limit)}</p>
      </div>
    {/each}
  </div>
</div>
