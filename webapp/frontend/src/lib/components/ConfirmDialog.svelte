<script lang="ts">
  let { show = $bindable(false), title = 'Confirmer', message = '', confirmLabel = 'Confirmer',
        cancelLabel = 'Annuler', destructive = false, onConfirm } = $props<{
    show: boolean; title?: string; message: string; confirmLabel?: string;
    cancelLabel?: string; destructive?: boolean; onConfirm: () => void;
  }>();

  function handleConfirm() {
    onConfirm();
    show = false;
  }
</script>

{#if show}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <button
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      onclick={() => show = false}
      aria-label="Fermer"
    ></button>

    <!-- Dialog -->
    <div class="relative bg-surface border border-border-subtle rounded-xl p-6 max-w-sm w-full shadow-xl">
      <h3 class="font-semibold text-lg mb-2">{title}</h3>
      <p class="text-sm text-text-secondary mb-6">{message}</p>
      <div class="flex gap-3 justify-end">
        <button
          onclick={() => show = false}
          class="px-4 py-2 text-sm text-text-secondary hover:text-text-primary border border-border-subtle rounded-lg transition-colors"
        >
          {cancelLabel}
        </button>
        <button
          onclick={handleConfirm}
          class="px-4 py-2 text-sm font-medium text-white rounded-lg transition-all hover:brightness-110
                 {destructive ? 'bg-maestro' : 'bg-teacher'}"
        >
          {confirmLabel}
        </button>
      </div>
    </div>
  </div>
{/if}
