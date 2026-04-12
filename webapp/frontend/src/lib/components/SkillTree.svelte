<script lang="ts">
  /**
   * Skyrim-inspired constellation skill tree.
   * Each concept = a star. Groups = constellations connected by lines.
   * Mastered stars glow brightly, weak stars are dim, untested are faint.
   * Dual-theme: dark = deep space with glowing stars, light = blueprint with bright nodes.
   */
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  let concepts = $state<any>(null);
  let loading = $state(true);
  let hoveredNode = $state<{ key: string; score: number; name: string; x: number; y: number } | null>(null);
  let svgEl: SVGSVGElement;
  let viewBox = $state({ x: 0, y: 0, w: 800, h: 600 });

  // Pan/zoom state
  let isPanning = $state(false);
  let panStart = { x: 0, y: 0 };
  let viewBoxStart = { x: 0, y: 0 };

  onMount(async () => {
    concepts = await api.getConcepts();
    loading = false;
  });

  // Layout computation
  interface StarNode {
    key: string;
    name: string;
    score: number;
    status: 'mastered' | 'medium' | 'weak' | 'untested';
    x: number;
    y: number;
    group: string;
    groupIdx: number;
  }

  interface ConstellationLine {
    x1: number; y1: number; x2: number; y2: number;
    status1: string; status2: string;
  }

  function getStatus(score: number): 'mastered' | 'medium' | 'weak' | 'untested' {
    if (score >= 80) return 'mastered';
    if (score >= 50) return 'medium';
    if (score > 0) return 'weak';
    return 'untested';
  }

  function formatName(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  // Generate constellation layout
  let layout = $derived((() => {
    if (!concepts || !concepts.groups || Object.keys(concepts.groups).length === 0) {
      return { stars: [], lines: [], groups: [] };
    }

    const groups = concepts.groups as Record<string, string[]>;
    const scores = concepts.scores as Record<string, { score: number }>;
    const groupNames = Object.keys(groups);

    const stars: StarNode[] = [];
    const lines: ConstellationLine[] = [];
    const groupCenters: { name: string; cx: number; cy: number }[] = [];

    // Place each group as a constellation cluster
    const totalGroups = groupNames.length;
    const cols = Math.ceil(Math.sqrt(totalGroups));
    const rows = Math.ceil(totalGroups / cols);
    const cellW = 800 / cols;
    const cellH = 600 / rows;

    groupNames.forEach((gName, gi) => {
      const col = gi % cols;
      const row = Math.floor(gi / cols);
      const cx = cellW * col + cellW / 2;
      const cy = cellH * row + cellH / 2;
      groupCenters.push({ name: gName, cx, cy });

      const conceptKeys = groups[gName] as string[];
      const count = conceptKeys.length;

      // Arrange concepts in a constellation shape (circular with slight randomization)
      const radius = Math.min(cellW, cellH) * 0.32;
      const angleStep = (2 * Math.PI) / Math.max(count, 1);

      conceptKeys.forEach((key, ci) => {
        const angle = angleStep * ci - Math.PI / 2;
        // Slight variation for organic look
        const r = radius * (0.6 + 0.4 * ((ci * 7 + gi * 13) % 10) / 10);
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;

        const rawScore = scores[key]?.score || 0;

        stars.push({
          key,
          name: formatName(key),
          score: rawScore,
          status: getStatus(rawScore),
          x, y,
          group: gName,
          groupIdx: gi,
        });
      });

      // Connect concepts within group sequentially (constellation lines)
      const groupStars = stars.filter(s => s.group === gName);
      for (let i = 0; i < groupStars.length - 1; i++) {
        lines.push({
          x1: groupStars[i].x, y1: groupStars[i].y,
          x2: groupStars[i + 1].x, y2: groupStars[i + 1].y,
          status1: groupStars[i].status,
          status2: groupStars[i + 1].status,
        });
      }
      // Close the constellation loop if 3+ stars
      if (groupStars.length >= 3) {
        lines.push({
          x1: groupStars[groupStars.length - 1].x,
          y1: groupStars[groupStars.length - 1].y,
          x2: groupStars[0].x,
          y2: groupStars[0].y,
          status1: groupStars[groupStars.length - 1].status,
          status2: groupStars[0].status,
        });
      }
    });

    return { stars, lines, groups: groupCenters };
  })());

  let masteredCount = $derived(layout.stars.filter(s => s.status === 'mastered').length);
  let totalCount = $derived(layout.stars.length);
  let masteredPct = $derived(totalCount > 0 ? Math.round(masteredCount / totalCount * 100) : 0);

  function starRadius(status: string): number {
    switch (status) {
      case 'mastered': return 6;
      case 'medium': return 5;
      case 'weak': return 4;
      default: return 3;
    }
  }

  function starOpacity(status: string): number {
    switch (status) {
      case 'mastered': return 1;
      case 'medium': return 0.7;
      case 'weak': return 0.45;
      default: return 0.2;
    }
  }

  function lineOpacity(s1: string, s2: string): number {
    const o1 = starOpacity(s1);
    const o2 = starOpacity(s2);
    return Math.min(o1, o2) * 0.6;
  }

  function starColor(status: string): string {
    switch (status) {
      case 'mastered': return '#3b82f6';
      case 'medium': return '#f59e0b';
      case 'weak': return '#ef4444';
      default: return 'var(--color-star-dim)';
    }
  }

  // Pan handlers
  function onPointerDown(e: PointerEvent) {
    isPanning = true;
    panStart = { x: e.clientX, y: e.clientY };
    viewBoxStart = { x: viewBox.x, y: viewBox.y };
    (e.target as SVGSVGElement).setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!isPanning || !svgEl) return;
    const rect = svgEl.getBoundingClientRect();
    const scaleX = viewBox.w / rect.width;
    const scaleY = viewBox.h / rect.height;
    viewBox.x = viewBoxStart.x - (e.clientX - panStart.x) * scaleX;
    viewBox.y = viewBoxStart.y - (e.clientY - panStart.y) * scaleY;
  }

  function onPointerUp() {
    isPanning = false;
  }

  function onWheel(e: WheelEvent) {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.1 : 0.9;
    const rect = svgEl.getBoundingClientRect();
    const mx = ((e.clientX - rect.left) / rect.width) * viewBox.w + viewBox.x;
    const my = ((e.clientY - rect.top) / rect.height) * viewBox.h + viewBox.y;

    const newW = Math.max(200, Math.min(1600, viewBox.w * factor));
    const newH = Math.max(150, Math.min(1200, viewBox.h * factor));

    viewBox = {
      x: mx - (mx - viewBox.x) * (newW / viewBox.w),
      y: my - (my - viewBox.y) * (newH / viewBox.h),
      w: newW,
      h: newH,
    };
  }

  function handleStarHover(star: StarNode, e: MouseEvent) {
    hoveredNode = { key: star.key, score: star.score, name: star.name, x: e.clientX, y: e.clientY };
  }

  function resetView() {
    viewBox = { x: 0, y: 0, w: 800, h: 600 };
  }
</script>

{#if loading}
  <div class="skeleton h-80 w-full rounded-xl"></div>
{:else if layout.stars.length === 0}
  <div class="bg-surface border border-border-subtle rounded-xl p-8 text-center">
    <p class="text-3xl mb-3">&#x1F30C;</p>
    <p class="text-sm text-text-secondary">Pas encore de concepts. Commence une session pour voir ta constellation !</p>
  </div>
{:else}
  <div class="bg-star-bg border border-border-subtle rounded-xl overflow-hidden relative">
    <!-- Header -->
    <div class="absolute top-3 left-4 right-4 flex items-center justify-between z-10 pointer-events-none">
      <div>
        <h3 class="text-sm font-medium text-text-primary">Constellation {concepts?.niveau || ''}</h3>
        <p class="text-xs text-text-muted">{masteredCount}/{totalCount} · {masteredPct}%</p>
      </div>
      <button
        onclick={resetView}
        class="pointer-events-auto px-2 py-1 bg-elevated/80 backdrop-blur-sm text-[10px] text-text-muted rounded border border-border-subtle hover:text-text-secondary transition-colors"
      >
        Recentrer
      </button>
    </div>

    <!-- SVG Canvas -->
    <svg
      bind:this={svgEl}
      viewBox="{viewBox.x} {viewBox.y} {viewBox.w} {viewBox.h}"
      class="w-full cursor-grab active:cursor-grabbing"
      style="height: 400px; background: var(--color-star-bg)"
      onpointerdown={onPointerDown}
      onpointermove={onPointerMove}
      onpointerup={onPointerUp}
      onwheel={onWheel}
    >
      <defs>
        <!-- Star glow filter -->
        <filter id="glow-mastered" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feFlood flood-color="#3b82f6" flood-opacity="0.6" />
          <feComposite in2="blur" operator="in" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="glow-medium" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feFlood flood-color="#f59e0b" flood-opacity="0.4" />
          <feComposite in2="blur" operator="in" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="glow-weak" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feFlood flood-color="#ef4444" flood-opacity="0.3" />
          <feComposite in2="blur" operator="in" />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <!-- Background sparkles (tiny dim stars) -->
      {#each Array(30) as _, i}
        <circle
          cx={50 + (i * 137) % 700}
          cy={30 + (i * 89) % 540}
          r="0.8"
          fill="var(--color-star-dim)"
          opacity={0.3 + (i % 5) * 0.1}
        />
      {/each}

      <!-- Constellation lines -->
      {#each layout.lines as line}
        <line
          x1={line.x1} y1={line.y1}
          x2={line.x2} y2={line.y2}
          stroke="var(--color-star-dim)"
          stroke-width="1"
          opacity={lineOpacity(line.status1, line.status2)}
        />
      {/each}

      <!-- Group labels -->
      {#each layout.groups as g}
        <text
          x={g.cx} y={g.cy - Math.min(viewBox.w, viewBox.h) * 0.2 - 10}
          text-anchor="middle"
          fill="var(--color-text-muted)"
          font-size="11"
          font-weight="500"
          opacity="0.6"
        >{g.name}</text>
      {/each}

      <!-- Stars -->
      {#each layout.stars as star}
        {@const r = starRadius(star.status)}
        {@const filter = star.status === 'mastered' ? 'url(#glow-mastered)'
                       : star.status === 'medium' ? 'url(#glow-medium)'
                       : star.status === 'weak' ? 'url(#glow-weak)' : 'none'}
        <g class="star-node" style="cursor: pointer">
          <!-- Glow halo for mastered -->
          {#if star.status === 'mastered'}
            <circle
              cx={star.x} cy={star.y} r={r * 2.5}
              fill={starColor(star.status)}
              opacity="0.08"
              class="star-pulse"
            />
          {/if}
          <circle
            cx={star.x} cy={star.y} r={r}
            fill={starColor(star.status)}
            opacity={starOpacity(star.status)}
            {filter}
            onmouseenter={(e) => handleStarHover(star, e)}
            onmouseleave={() => hoveredNode = null}
          />
        </g>
      {/each}
    </svg>

    <!-- Legend -->
    <div class="absolute bottom-3 left-4 flex items-center gap-3 text-[10px] text-text-muted">
      <span class="flex items-center gap-1">
        <span class="w-2 h-2 rounded-full bg-teacher"></span> Maitrise
      </span>
      <span class="flex items-center gap-1">
        <span class="w-2 h-2 rounded-full bg-lehrer"></span> En cours
      </span>
      <span class="flex items-center gap-1">
        <span class="w-2 h-2 rounded-full bg-maestro"></span> Faible
      </span>
      <span class="flex items-center gap-1">
        <span class="w-2 h-2 rounded-full opacity-30" style="background: var(--color-text-muted)"></span> Non teste
      </span>
    </div>

    <!-- Zoom hint -->
    <div class="absolute bottom-3 right-4 text-[10px] text-text-muted">
      Scroll pour zoomer · Glisser pour naviguer
    </div>
  </div>

  <!-- Hover tooltip -->
  {#if hoveredNode}
    <div
      class="fixed z-50 pointer-events-none px-3 py-2 bg-elevated border border-border-subtle rounded-lg shadow-lg text-xs"
      style="left: {hoveredNode.x + 12}px; top: {hoveredNode.y - 10}px"
    >
      <p class="font-medium text-text-primary">{hoveredNode.name}</p>
      <p class="text-text-secondary">
        Score : <span class="font-mono">{hoveredNode.score > 0 ? hoveredNode.score : 'Non teste'}</span>
      </p>
    </div>
  {/if}
{/if}

<style>
  @keyframes star-glow-pulse {
    0%, 100% { opacity: 0.08; }
    50% { opacity: 0.15; }
  }
  .star-pulse {
    animation: star-glow-pulse 3s ease-in-out infinite;
  }
  .bg-star-bg {
    background-color: var(--color-star-bg);
  }
</style>
