<script lang="ts">
  let { item, value, onchange } = $props<{
    item: {
      prompt?: { fr: string };
      scale?: { labels_fr: string[]; values: number[] };
    };
    value: number | undefined;
    onchange: (v: number) => void;
  }>();
  const labels = $derived(item.scale?.labels_fr ?? []);
  const values = $derived(item.scale?.values ?? [1, 2, 3, 4, 5]);
</script>

<h3 class="text-lg font-medium mb-6 leading-snug">{item.prompt?.fr}</h3>
<div class="flex flex-col gap-2">
  {#each values as v, i}
    <button
      type="button"
      onclick={() => onchange(v)}
      class="flex items-center gap-3 p-3 rounded-lg border text-left transition
             {value === v
               ? 'border-teacher bg-teacher/10'
               : 'border-border-subtle hover:border-border-strong hover:bg-background-subtle'}"
    >
      <span class="w-6 h-6 rounded-full border-2 flex items-center justify-center
                   {value === v ? 'border-teacher bg-teacher' : 'border-border-subtle'}">
        {#if value === v}
          <span class="w-2 h-2 rounded-full bg-white"></span>
        {/if}
      </span>
      <span class="text-sm">{labels[i] ?? v}</span>
    </button>
  {/each}
</div>
