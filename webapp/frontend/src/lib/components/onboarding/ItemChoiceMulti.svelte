<script lang="ts">
  let { item, value, onchange } = $props<{
    item: {
      prompt?: { fr: string };
      options?: Array<{ id: string; label_fr: string }>;
      min_selected?: number;
      max_selected?: number;
    };
    value: string[] | undefined;
    onchange: (v: string[]) => void;
  }>();

  const options = $derived(item.options ?? []);
  const selected = $derived(Array.isArray(value) ? value : []);
  const maxSel = $derived(item.max_selected ?? 99);
  const minSel = $derived(item.min_selected ?? 1);

  function toggle(id: string) {
    const isSel = selected.includes(id);
    let next: string[];
    if (isSel) {
      next = selected.filter((x) => x !== id);
    } else if (selected.length >= maxSel) {
      // Remove oldest, append new (sliding window)
      next = [...selected.slice(1), id];
    } else {
      next = [...selected, id];
    }
    onchange(next);
  }
</script>

<h3 class="text-lg font-medium mb-2 leading-snug">{item.prompt?.fr}</h3>
<p class="text-xs text-text-tertiary mb-5">
  Choisis {minSel === maxSel ? minSel : `${minSel}-${maxSel}`} {maxSel === 1 ? 'réponse' : 'réponses'}
</p>
<div class="flex flex-col gap-2">
  {#each options as opt}
    {@const isSel = selected.includes(opt.id)}
    <button
      type="button"
      onclick={() => toggle(opt.id)}
      class="p-4 rounded-lg border text-left transition flex gap-3 items-center
             {isSel
               ? 'border-teacher bg-teacher/10'
               : 'border-border-subtle hover:border-border-strong hover:bg-background-subtle'}"
    >
      <span class="w-5 h-5 rounded border-2 flex items-center justify-center shrink-0
                   {isSel ? 'border-teacher bg-teacher' : 'border-border-subtle'}">
        {#if isSel}<span class="text-white text-xs">✓</span>{/if}
      </span>
      <span class="text-sm">{opt.label_fr}</span>
    </button>
  {/each}
</div>
