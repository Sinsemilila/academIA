<script lang="ts">
  import type { Snippet } from 'svelte';
  let { text = '', children } = $props<{ text: string; children: Snippet }>();
</script>

<span class="tooltip-container inline-flex">
  {@render children()}
  {#if text}
    <span class="tooltip-content">{text}</span>
  {/if}
</span>
