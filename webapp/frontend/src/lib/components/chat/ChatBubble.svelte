<script lang="ts">
  import { onMount } from 'svelte';
  import { marked } from 'marked';
  import DOMPurify from 'dompurify';
  import { addToast } from '$lib/stores/toasts';
  import { userAppearance } from '$lib/stores/user';

  let { role, content, accentColor = '#3b82f6', streaming = false,
        agentFlag = '', agentName = '', font = 'sans' } = $props<{
    role: 'user' | 'assistant' | 'system_consolidation';
    content: string;
    accentColor?: string;
    streaming?: boolean;
    agentFlag?: string;
    agentName?: string;
    /* Phase B1.4 — 'serif' marks the bubble as L2 (target language). Caller
       passes 'serif' for assistant messages of language-teaching agents
       (Maestro, Teacher, Sensei, etc.). User L1 messages stay 'sans'. */
    font?: 'sans' | 'serif';
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

  // Session 37 fix — extract `feedback` from <output>{JSON}</output> for display.
  // Teacher & Maestro always wrap their response in this envelope per
  // OUTPUT_SCHEMA_BLOCK (teacher_prompt.py). Without extraction, marked strips
  // the <output> tags but keeps the raw JSON text, exposing `reasoning`,
  // `tier_applied`, `error_codes` etc. to the learner — breaking the tutor UX.
  //
  // During streaming the closing tag may not have arrived yet; show an empty
  // bubble rather than exposing partial JSON. Once complete, extract feedback.
  // On malformed JSON or missing tags, fall back to the raw content.
  function extractFeedback(raw: string, isStreaming: boolean): string {
    if (!raw) return '';
    const openIdx = raw.indexOf('<output>');
    if (openIdx < 0) return raw; // plain text response (legacy or fallback)
    const closeIdx = raw.indexOf('</output>', openIdx);
    if (closeIdx < 0) {
      // Still streaming the JSON — hide partial until complete.
      if (isStreaming) return raw.slice(0, openIdx); // anything before <output> (usually empty)
      return raw; // stream ended with unclosed tag → show raw for debugging
    }
    const inner = raw.slice(openIdx + '<output>'.length, closeIdx).trim();
    const trailing = raw.slice(closeIdx + '</output>'.length).trim();
    // Strict JSON parse first — preferred path when LLM escapes quotes properly.
    try {
      const parsed = JSON.parse(inner);
      const fb = (parsed.feedback ?? '').toString();
      return (fb + (trailing ? '\n' + trailing : '')).trim() || raw;
    } catch {
      // Fallback: LLMs occasionally emit unescaped nested quotes in `feedback`,
      // breaking strict JSON (e.g. `"feedback": "…'¿Qué decir con "X"?'…"`).
      // Use a permissive regex that stops at the next top-level `,` followed by
      // a known schema key — tolerates inner quotes.
      const m = inner.match(
        /"feedback"\s*:\s*"([\s\S]*?)"\s*,\s*"(?:tier_applied|feedback_types|error_codes|dosage_check|silenced_for_spaced_retrieval|reasoning|observed_level)"/
      );
      if (m && m[1]) {
        // Decode common escapes (\n, \", \\) that JSON.parse would have handled.
        const fb = m[1]
          .replace(/\\n/g, '\n')
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, '\\');
        return (fb + (trailing ? '\n' + trailing : '')).trim();
      }
      return raw;
    }
  }

  let displayContent = $derived(
    role === 'assistant' ? extractFeedback(content || '', streaming) : content
  );

  let htmlContent = $derived(
    role === 'assistant' ? DOMPurify.sanitize(marked.parse(displayContent) as string) : ''
  );

  async function copyMessage() {
    try {
      await navigator.clipboard.writeText(role === 'assistant' ? displayContent : content);
      addToast({ type: 'info', message: 'Copi\u00E9 !' });
    } catch {
      addToast({ type: 'info', message: 'Copi\u00E9 !' });
    }
  }
</script>

{#if role === 'system_consolidation'}
  <!-- Session 37 — persistent consolidation event bubble. Styled as a
       horizontal timeline marker, centered, subtle green accent. -->
  <div class="flex justify-center" class:bubble-enter={!mounted}>
    <div class="px-3 py-1.5 text-xs italic text-text-secondary bg-surface/60
                border-l-2 border-green-500/70 rounded-md max-w-[92%]
                markdown-body">
      {@html DOMPurify.sanitize(marked.parse(content || '') as string)}
    </div>
  </div>
{:else}
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
        class="px-4 py-2.5 rounded-2xl rounded-bl-md bg-surface border border-border-subtle text-sm leading-relaxed markdown-body {font === 'serif' ? 'font-serif' : 'font-sans'}"
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
{/if}

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
