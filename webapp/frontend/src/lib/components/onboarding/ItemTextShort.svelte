<script lang="ts">
  let { item, probeHint, value, onchange } = $props<{
    item: {
      prompt?: { fr: string };
      placeholder_fr?: string;
      min_chars?: number;
      max_chars?: number;
      skip_label_fr?: string;
      sentence_to_translate?: { fr: string };
    };
    probeHint?: { source_sentence_fr?: string } | undefined;
    value: string | undefined;
    onchange: (v: string) => void;
  }>();

  const maxChars = $derived(item.max_chars ?? 200);
  const minChars = $derived(item.min_chars ?? 0);
  const current = $derived(value ?? '');
  const sentence = $derived(item.sentence_to_translate?.fr ?? probeHint?.source_sentence_fr ?? '');

  function skip() {
    onchange('');
  }
</script>

<h3 class="text-lg font-medium mb-4 leading-snug">{item.prompt?.fr}</h3>
{#if sentence}
  <div class="mb-4 p-4 rounded-lg bg-background-subtle border border-border-subtle italic text-text-secondary">
    « {sentence} »
  </div>
{/if}

<textarea
  value={current}
  oninput={(e) => onchange((e.currentTarget as HTMLTextAreaElement).value)}
  placeholder={item.placeholder_fr ?? ''}
  maxlength={maxChars}
  rows="3"
  class="w-full p-3 rounded-lg border border-border-subtle bg-surface text-text-primary
         focus:outline-none focus:border-teacher resize-none"
></textarea>

<div class="flex justify-between items-center mt-2 text-xs text-text-tertiary">
  <span>
    {#if minChars > 0 && current.length < minChars}
      Minimum {minChars} caractères
    {:else}
      {current.length} / {maxChars}
    {/if}
  </span>
  {#if item.skip_label_fr}
    <button
      type="button"
      onclick={skip}
      class="text-text-tertiary underline hover:text-text-secondary"
    >
      {item.skip_label_fr}
    </button>
  {/if}
</div>
