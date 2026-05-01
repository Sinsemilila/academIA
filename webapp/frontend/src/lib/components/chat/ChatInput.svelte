<script lang="ts">
  let { onSend, disabled = false } = $props<{
    onSend: (message: string) => void;
    disabled?: boolean;
  }>();

  let input = $state('');
  let textarea: HTMLTextAreaElement;

  function handleSubmit(e: Event) {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    const text = input.trim();
    input = '';
    if (textarea) textarea.style.height = 'auto';
    onSend(text);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  function autoResize() {
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }
  }
</script>

<form onsubmit={handleSubmit} class="border-t border-border-subtle bg-surface p-3 flex gap-2 items-end">
  <textarea
    bind:this={textarea}
    bind:value={input}
    oninput={autoResize}
    onkeydown={handleKeydown}
    placeholder="Ecris ta reponse..."
    name="chat-message"
    id="chat-message"
    autocomplete="off"
    rows="1"
    class="flex-1 px-4 py-2.5 bg-elevated border border-border-subtle rounded-xl
           text-sm text-text-primary placeholder-text-muted resize-none
           focus:outline-none focus:border-teacher transition-colors"
  ></textarea>
  <button
    type="submit"
    disabled={disabled || !input.trim()}
    class="px-4 py-2.5 rounded-xl text-sm font-medium transition-all shrink-0
           {disabled || !input.trim()
             ? 'bg-elevated text-text-muted cursor-not-allowed'
             : 'bg-teacher text-white hover:brightness-110'}"
  >
    ➤
  </button>
</form>
