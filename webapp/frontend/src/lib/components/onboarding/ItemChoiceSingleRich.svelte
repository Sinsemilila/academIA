<script lang="ts">
  let { item, value, onchange } = $props<{
    item: {
      prompt?: { fr: string };
      options?: Array<{ id: string; label_fr: string }>;
    };
    value: string | undefined;
    onchange: (v: string) => void;
  }>();
  const options = $derived(item.options ?? []);
</script>

<h3 class="text-lg font-medium mb-6 leading-snug">{item.prompt?.fr}</h3>
<div class="flex flex-col gap-2">
  {#each options as opt}
    <button
      type="button"
      onclick={() => onchange(opt.id)}
      class="p-4 rounded-lg border text-left transition flex gap-3 items-start
             {value === opt.id
               ? 'border-teacher bg-teacher/10'
               : 'border-border-subtle hover:border-border-strong hover:bg-background-subtle'}"
    >
      <span class="font-mono text-xs px-2 py-1 rounded bg-background-subtle text-text-secondary shrink-0">
        {opt.id}
      </span>
      <span class="text-sm">{opt.label_fr}</span>
    </button>
  {/each}
</div>
