<script lang="ts">
  // Session 36 — CEFR level + consolidation status indicator.
  let {
    niveau = null,
    status = 'provisoire',
    size = 'md',
  } = $props<{
    niveau?: string | null;
    status?: string;
    size?: 'sm' | 'md' | 'lg';
  }>();

  const labels: Record<string, string> = {
    provisoire: 'provisoire',
    calibration_en_cours: 'calibration…',
    'validé': 'validé ✓',
    stabilisation_volontaire: 'stabilisation',
    a_recalibrer: 'à recalibrer',
  };
  const colors: Record<string, string> = {
    provisoire: 'bg-amber-500/15 text-amber-600',
    calibration_en_cours: 'bg-blue-500/15 text-blue-600',
    'validé': 'bg-emerald-500/15 text-emerald-600',
    stabilisation_volontaire: 'bg-slate-500/15 text-slate-500',
    a_recalibrer: 'bg-orange-500/15 text-orange-600',
  };
  let label = $derived(labels[status] ?? 'provisoire');
  let color = $derived(colors[status] ?? colors.provisoire);
  let nivCls = $derived(size === 'lg' ? 'text-3xl font-bold' : size === 'sm' ? 'text-base font-semibold' : 'text-xl font-semibold');
  let badgeCls = $derived(size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-xs');
</script>

<div class="inline-flex flex-col items-start gap-0.5">
  {#if niveau !== null}
    <span class={nivCls}>{niveau ?? '—'}</span>
  {/if}
  <span class="font-medium rounded-full {badgeCls} {color}">{label}</span>
</div>
