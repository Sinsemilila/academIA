<script lang="ts">
  let { item, value, onchange } = $props<{
    item: {
      prompt_group?: { fr: string };
      sub_items?: Array<{ id: string; prompt_fr: string }>;
      scale?: { labels_fr: string[]; values: number[] };
    };
    value: Record<string, number> | undefined;
    onchange: (v: Record<string, number>) => void;
  }>();

  const subItems = $derived(item.sub_items ?? []);
  const values = $derived(item.scale?.values ?? [1, 2, 3, 4, 5]);
  const current = $derived((value && typeof value === 'object') ? value : {});

  function setOne(id: string, v: number) {
    onchange({ ...current, [id]: v });
  }
</script>

<h3 class="text-lg font-medium mb-6 leading-snug">{item.prompt_group?.fr}</h3>
<div class="flex flex-col gap-5">
  {#each subItems as si}
    <div>
      <p class="text-sm mb-2">{si.prompt_fr}</p>
      <div class="flex gap-1">
        {#each values as v}
          {@const isSel = current[si.id] === v}
          <button
            type="button"
            onclick={() => setOne(si.id, v)}
            aria-label={`${si.id} = ${v}`}
            class="flex-1 py-2 rounded text-sm border transition
                   {isSel
                     ? 'border-teacher bg-teacher/10 font-medium'
                     : 'border-border-subtle hover:border-border-strong hover:bg-background-subtle'}"
          >
            {v}
          </button>
        {/each}
      </div>
    </div>
  {/each}
  <div class="flex justify-between text-xs text-text-tertiary mt-2">
    <span>1 = pas d'accord</span>
    <span>5 = tout à fait d'accord</span>
  </div>
</div>
