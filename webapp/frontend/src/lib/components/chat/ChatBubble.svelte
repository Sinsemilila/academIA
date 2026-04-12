<script lang="ts">
  import { onMount } from 'svelte';
  import { marked } from 'marked';
  import { addToast } from '$lib/stores/toasts';
  import { userAppearance } from '$lib/stores/user';

  let { role, content, accentColor = '#3b82f6', streaming = false,
        agentFlag = '', agentName = '' } = $props<{
    role: 'user' | 'assistant';
    content: string;
    accentColor?: string;
    streaming?: boolean;
    agentFlag?: string;
    agentName?: string;
  }>();

  let mounted = $state(false);
  let showCopy = $state(false);
  let ua = $state({ initial: 'U', avatarColor: '#3b82f6', displayName: '' });

  onMount(() => {
    mounted = true;
    const unsub = userAppearance.subscribe(v => { ua = v; });
    return unsub;
  });

  // Configure marked
  marked.setOptions({ breaks: true, gfm: true });

  let htmlContent = $derived(
    role === 'assistant' ? marked.parse(content || '') as string : ''
  );

  async function copyMessage() {
    try {
      await navigator.clipboard.writeText(content);
      addToast({ type: 'info', message: 'Copi\u00E9 !' });
    } catch {
      addToast({ type: 'info', message: 'Copi\u00E9 !' });
    }
  }
</script>

<div
  class="flex {role === 'user' ? 'justify-end' : 'justify-start'} gap-2.5"
  class:bubble-enter={!mounted}
  onmouseenter={() => showCopy = true}
  onmouseleave={() => showCopy = false}
>
  <!-- Bot avatar (left) -->
  {#if role === 'assistant'}
    <div
      class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center overflow-hidden mt-1"
      style="background-color: {accentColor}18; border: 1.5px solid {accentColor}40"
    >
      {#if agentFlag}
        <img src={agentFlag} alt={agentName} class="w-5 h-5 object-contain" />
      {:else}
        <span class="text-xs font-semibold" style="color: {accentColor}">AI</span>
      {/if}
    </div>
  {/if}

  <div class="relative group max-w-[80%] sm:max-w-[72%]">
    {#if role === 'user'}
      <div
        class="px-4 py-2.5 rounded-2xl rounded-br-md text-sm leading-relaxed"
        style="background-color: {accentColor}20; border-left: 2px solid {accentColor}"
      >
        {content}
      </div>
    {:else}
      <div
        class="px-4 py-2.5 rounded-2xl rounded-bl-md bg-surface border border-border-subtle text-sm leading-relaxed markdown-body"
        class:streaming-bubble={streaming}
        style="border-left: 2px solid {accentColor}"
      >
        {@html htmlContent}{#if streaming}<span class="typing-cursor"></span>{/if}
      </div>
      <!-- Copy button -->
      {#if content && !streaming}
        <button
          onclick={copyMessage}
          class="absolute -bottom-5 left-2 flex items-center gap-1 px-2 py-0.5 rounded text-[10px]
                 text-text-muted hover:text-text-secondary bg-elevated border border-border-subtle
                 transition-all opacity-0 group-hover:opacity-100"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copier
        </button>
      {/if}
    {/if}
  </div>

  <!-- User avatar (right) -->
  {#if role === 'user'}
    <div
      class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center mt-1 text-xs font-semibold text-white"
      style="background-color: {ua.avatarColor}"
    >
      {ua.initial}
    </div>
  {/if}
</div>

<style>
  .bubble-enter {
    animation: fadeIn 150ms ease-out;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* Blinking cursor during streaming */
  .typing-cursor {
    display: inline-block;
    width: 2px;
    height: 1em;
    background-color: currentColor;
    margin-left: 1px;
    vertical-align: text-bottom;
    animation: blink 600ms steps(2) infinite;
  }
  @keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0; }
  }

  /* Smooth text reveal feel */
  .streaming-bubble :global(p:last-child),
  .streaming-bubble :global(li:last-child) {
    animation: textReveal 80ms ease-out;
  }
  @keyframes textReveal {
    from { opacity: 0.7; }
    to { opacity: 1; }
  }
</style>
