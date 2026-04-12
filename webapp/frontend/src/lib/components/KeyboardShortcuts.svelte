<script lang="ts">
  let show = $state(false);

  interface Shortcut {
    keys: string[];
    desc: string;
  }

  interface ShortcutGroup {
    title: string;
    shortcuts: Shortcut[];
  }

  const groups: ShortcutGroup[] = [
    {
      title: 'Navigation',
      shortcuts: [
        { keys: ['Ctrl', 'K'], desc: 'Palette de commandes' },
        { keys: ['?'], desc: 'Aide / raccourcis' },
        { keys: ['Esc'], desc: 'Fermer le dialogue' },
      ],
    },
    {
      title: 'Chat',
      shortcuts: [
        { keys: ['Enter'], desc: 'Envoyer le message' },
        { keys: ['Shift', 'Enter'], desc: 'Retour a la ligne' },
      ],
    },
    {
      title: 'General',
      shortcuts: [
        { keys: ['Ctrl', 'K'], desc: 'Recherche rapide' },
      ],
    },
  ];

  function handleKey(e: KeyboardEvent) {
    // Shift+? to toggle shortcuts modal (only when not in input)
    if (e.key === '/' && e.shiftKey && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
      e.preventDefault();
      show = !show;
    }
    if (e.key === 'Escape' && show) {
      show = false;
    }
  }

  export function toggle() { show = !show; }
</script>

<svelte:window onkeydown={handleKey} />

{#if show}
  <div class="fixed inset-0 z-[60] flex items-center justify-center">
    <button class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={() => show = false} aria-label="Fermer"></button>

    <div class="relative w-full max-w-md bg-surface border border-border-subtle rounded-xl shadow-2xl overflow-hidden mx-4">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-border-subtle">
        <div class="flex items-center gap-2">
          <span class="text-base">&#x2328;&#xFE0F;</span>
          <h2 class="font-semibold text-sm">Raccourcis clavier</h2>
        </div>
        <button
          onclick={() => show = false}
          class="text-text-muted hover:text-text-secondary transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="px-5 py-4 space-y-5 max-h-[60vh] overflow-y-auto">
        {#each groups as group}
          <div>
            <p class="text-[10px] font-medium text-text-muted uppercase tracking-wider mb-2">{group.title}</p>
            <div class="space-y-2">
              {#each group.shortcuts as shortcut}
                <div class="flex items-center justify-between">
                  <span class="text-sm text-text-secondary">{shortcut.desc}</span>
                  <div class="flex items-center gap-1">
                    {#each shortcut.keys as key}
                      <kbd class="px-2 py-0.5 text-[11px] font-mono bg-elevated border border-border-subtle rounded text-text-muted">
                        {key}
                      </kbd>
                    {/each}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>

      <!-- Footer -->
      <div class="px-5 py-3 border-t border-border-subtle">
        <p class="text-[10px] text-text-muted text-center">
          Appuie sur <kbd class="px-1 py-0.5 bg-elevated border border-border-subtle rounded text-[10px]">?</kbd> pour afficher cette aide
        </p>
      </div>
    </div>
  </div>
{/if}
