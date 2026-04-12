<script lang="ts">
  import { subscribe, removeToast, type Toast } from '$lib/stores/toasts';
  import { onMount } from 'svelte';

  let toasts = $state<Toast[]>([]);

  onMount(() => {
    return subscribe(t => { toasts = t; });
  });

  function typeClasses(toast: Toast): string {
    switch (toast.type) {
      case 'xp':      return 'bg-lehrer/15 border-lehrer/30 text-lehrer';
      case 'badge':    return 'bg-sensei/15 border-sensei/30 text-sensei';
      case 'success':  return 'bg-professore/15 border-professore/30 text-professore';
      case 'error':    return 'bg-maestro/15 border-maestro/30 text-maestro';
      case 'action':   return 'bg-surface border-teacher/30 text-text-primary';
      default:         return 'bg-surface border-border-subtle text-text-primary';
    }
  }
</script>

{#if toasts.length > 0}
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
    {#each toasts as toast (toast.id)}
      <div
        class="pointer-events-auto rounded-xl shadow-lg border backdrop-blur-sm
               animate-slide-in overflow-hidden {typeClasses(toast)}"
      >
        <div class="px-4 py-2.5 flex items-center gap-2">
          {#if toast.icon}
            <span class="text-lg">{toast.icon}</span>
          {/if}
          <span class="text-sm font-medium flex-1">{toast.message}</span>
          {#if toast.action}
            <button
              onclick={() => { toast.action?.callback(); removeToast(toast.id); }}
              class="text-xs font-semibold text-teacher hover:underline ml-2"
            >
              {toast.action.label}
            </button>
          {/if}
        </div>
        {#if toast.progress}
          <div class="h-0.5 bg-teacher/20">
            <div class="h-full bg-teacher toast-countdown" style="--duration: {toast.duration || 3000}ms"></div>
          </div>
        {/if}
      </div>
    {/each}
  </div>
{/if}

<style>
  @keyframes slide-in {
    from { opacity: 0; transform: translateX(100%) scale(0.95); }
    to { opacity: 1; transform: translateX(0) scale(1); }
  }
  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }
  @keyframes countdown {
    from { width: 100%; }
    to { width: 0%; }
  }
  .toast-countdown {
    animation: countdown var(--duration, 3000ms) linear forwards;
  }
</style>
