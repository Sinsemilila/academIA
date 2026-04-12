<script lang="ts">
  /**
   * Lightweight SVG line chart for XP progression or concept scores over time.
   * No external dependencies — pure SVG rendering.
   */

  let {
    data = [],
    label = 'XP',
    color = 'var(--color-teacher)',
    height = 160,
  }: {
    data: { date: string; value: number }[];
    label?: string;
    color?: string;
    height?: number;
  } = $props();

  const WIDTH = 600;
  const PADDING = { top: 20, right: 20, bottom: 30, left: 45 };
  const chartW = WIDTH - PADDING.left - PADDING.right;
  const chartH = height - PADDING.top - PADDING.bottom;

  let hoveredIdx = $state<number | null>(null);

  // Computed path
  let maxVal = $derived(Math.max(...data.map(d => d.value), 1));
  let minVal = $derived(Math.min(...data.map(d => d.value), 0));
  let range = $derived(maxVal - minVal || 1);

  let points = $derived(data.map((d, i) => ({
    x: PADDING.left + (i / Math.max(data.length - 1, 1)) * chartW,
    y: PADDING.top + chartH - ((d.value - minVal) / range) * chartH,
    date: d.date,
    value: d.value,
  })));

  let linePath = $derived(points.length > 1
    ? 'M ' + points.map(p => `${p.x},${p.y}`).join(' L ')
    : '');

  let areaPath = $derived(points.length > 1
    ? linePath + ` L ${points[points.length - 1].x},${PADDING.top + chartH} L ${points[0].x},${PADDING.top + chartH} Z`
    : '');

  // Y axis ticks (4 levels)
  let yTicks = $derived((() => {
    const ticks = [];
    for (let i = 0; i <= 3; i++) {
      const val = minVal + (range * i / 3);
      ticks.push({
        value: Math.round(val),
        y: PADDING.top + chartH - (i / 3) * chartH,
      });
    }
    return ticks;
  })());

  // X axis labels (first, middle, last)
  let xLabels = $derived((() => {
    if (data.length === 0) return [];
    const fmt = (d: string) => new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    const labels = [];
    if (data.length >= 1) labels.push({ label: fmt(data[0].date), x: points[0]?.x || PADDING.left });
    if (data.length >= 3) {
      const mid = Math.floor(data.length / 2);
      labels.push({ label: fmt(data[mid].date), x: points[mid]?.x || PADDING.left + chartW / 2 });
    }
    if (data.length >= 2) labels.push({ label: fmt(data[data.length - 1].date), x: points[points.length - 1]?.x || PADDING.left + chartW });
    return labels;
  })());

  function handleMouseMove(e: MouseEvent) {
    const svg = (e.currentTarget as SVGSVGElement);
    const rect = svg.getBoundingClientRect();
    // Map mouse position to data index directly (simpler, more reliable)
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const idx = Math.round(pct * (data.length - 1));
    hoveredIdx = Math.max(0, Math.min(data.length - 1, idx));
  }
</script>

{#if data.length > 1}
  <div class="bg-surface border border-border-subtle rounded-xl p-5">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-medium">{label}</h3>
      {#if hoveredIdx !== null && points[hoveredIdx]}
        <div class="text-xs text-text-secondary">
          <span class="font-mono font-semibold" style="color: {color}">{points[hoveredIdx].value}</span>
          · {new Date(points[hoveredIdx].date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
        </div>
      {/if}
    </div>

    <svg
      viewBox="0 0 {WIDTH} {height}"
      class="w-full"
      style="height: {height}px; max-height: {height}px"
      onmousemove={handleMouseMove}
      onmouseleave={() => hoveredIdx = null}
    >
      <!-- Grid lines -->
      {#each yTicks as tick}
        <line
          x1={PADDING.left} y1={tick.y}
          x2={WIDTH - PADDING.right} y2={tick.y}
          stroke="var(--color-border-subtle)" stroke-width="1" stroke-dasharray="4,4"
        />
        <text
          x={PADDING.left - 8} y={tick.y + 4}
          text-anchor="end" fill="var(--color-text-muted)"
          font-size="10" font-family="var(--font-mono)"
        >{tick.value}</text>
      {/each}

      <!-- X labels -->
      {#each xLabels as xl}
        <text
          x={xl.x} y={height - 6}
          text-anchor="middle" fill="var(--color-text-muted)"
          font-size="10"
        >{xl.label}</text>
      {/each}

      <!-- Area fill -->
      {#if areaPath}
        <path d={areaPath} fill={color} opacity="0.08" />
      {/if}

      <!-- Line -->
      {#if linePath}
        <path d={linePath} fill="none" stroke={color} stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      {/if}

      <!-- Hover indicator -->
      {#if hoveredIdx !== null && points[hoveredIdx]}
        <line
          x1={points[hoveredIdx].x} y1={PADDING.top}
          x2={points[hoveredIdx].x} y2={PADDING.top + chartH}
          stroke="var(--color-text-muted)" stroke-width="1" opacity="0.3"
        />
        <circle
          cx={points[hoveredIdx].x} cy={points[hoveredIdx].y}
          r="4" fill={color} stroke="var(--color-surface)" stroke-width="2"
        />
      {/if}
    </svg>
  </div>
{/if}
