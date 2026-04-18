<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { agents } from '$lib/config';

  let show = $state(false);
  let query = $state('');
  let selectedIndex = $state(0);
  let inputEl: HTMLInputElement;

  interface Command {
    id: string;
    label: string;
    icon: string;
    action: () => void;
    category: string;
  }

  const commands: Command[] = [
    // Pages
    { id: 'home', label: 'Home', icon: '\uD83C\uDFE0', action: () => goto('/'), category: 'Pages' },
    { id: 'stats', label: 'Statistiques', icon: '\uD83D\uDCCA', action: () => goto('/stats'), category: 'Pages' },
    { id: 'profile', label: 'Profil & R\u00e9glages', icon: '\u2699\uFE0F', action: () => goto('/profile'), category: 'Pages' },
    { id: 'changelog', label: 'Nouveaut\u00e9s', icon: '\uD83C\uDD95', action: () => goto('/changelog'), category: 'Pages' },
    { id: 'legal', label: 'Mentions l\u00e9gales', icon: '\uD83D\uDCC4', action: () => goto('/legal'), category: 'Pages' },
    // Agents
    ...agents.filter(a => a.available).map(a => ({
      id: `chat-${a.slug}`,
      label: `Chat ${a.name}`,
      icon: '\uD83D\uDCAC',
      action: () => goto(`/chat/${a.slug}`),
      category: 'Agents',
    })),
    // (Sprint 5: removed duplicate "Parler à Teacher" — covered by per-agent entries above)
  ];

  let filtered = $derived(
    query.length === 0
      ? commands
      : commands.filter(c =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.category.toLowerCase().includes(query.toLowerCase())
        )
  );

  function handleKeydown(e: KeyboardEvent) {
    // Open: Cmd+K or Ctrl+K
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      show = !show;
      if (show) {
        query = '';
        selectedIndex = 0;
        setTimeout(() => inputEl?.focus(), 10);
      }
      return;
    }

    // Shortcuts help
    if (e.key === '?' && !show && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
      e.preventDefault();
      show = true;
      query = '';
      selectedIndex = 0;
      setTimeout(() => inputEl?.focus(), 10);
      return;
    }

    if (!show) return;

    if (e.key === 'Escape') {
      show = false;
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, filtered.length - 1);
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
    }
    if (e.key === 'Enter' && filtered[selectedIndex]) {
      e.preventDefault();
      filtered[selectedIndex].action();
      show = false;
    }
  }

  // Group filtered by category
  let grouped = $derived(() => {
    const groups: Record<string, Command[]> = {};
    for (const cmd of filtered) {
      if (!groups[cmd.category]) groups[cmd.category] = [];
      groups[cmd.category].push(cmd);
    }
    return groups;
  });
</script>

<svelte:window onkeydown={handleKeydown} />

{#if show}
  <div class="fixed inset-0 z-[60] flex items-start justify-center pt-[15vh]">
    <!-- Backdrop -->
    <button class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={() => show = false} aria-label="Fermer"></button>

    <!-- Palette -->
    <div class="relative w-full max-w-md bg-surface border border-border-subtle rounded-xl shadow-2xl overflow-hidden">
      <!-- Input -->
      <div class="flex items-center gap-3 px-4 py-3 border-b border-border-subtle">
        <svg class="w-4 h-4 text-text-muted shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          bind:this={inputEl}
          bind:value={query}
          oninput={() => selectedIndex = 0}
          placeholder="Rechercher..."
          class="w-full bg-transparent text-sm text-text-primary placeholder-text-muted focus:outline-none"
        />
        <kbd class="text-[10px] text-text-muted bg-elevated px-1.5 py-0.5 rounded border border-border-subtle shrink-0">ESC</kbd>
      </div>

      <!-- Results -->
      <div class="max-h-72 overflow-y-auto py-2">
        {#if filtered.length === 0}
          <p class="text-sm text-text-muted text-center py-6">Aucun r&#233;sultat</p>
        {:else}
          {@const groups = grouped()}
          {#each Object.entries(groups) as [category, cmds], gi}
            <div class="px-3 py-1">
              <p class="text-[10px] font-medium text-text-muted uppercase tracking-wider px-2 mb-1">{category}</p>
              {#each cmds as cmd, ci}
                {@const globalIdx = filtered.indexOf(cmd)}
                <button
                  class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
                         {globalIdx === selectedIndex ? 'bg-elevated text-text-primary' : 'text-text-secondary hover:bg-elevated/50'}"
                  onclick={() => { cmd.action(); show = false; }}
                  onmouseenter={() => selectedIndex = globalIdx}
                >
                  <span class="text-base w-6 text-center">{cmd.icon}</span>
                  <span>{cmd.label}</span>
                </button>
              {/each}
            </div>
          {/each}
        {/if}
      </div>

      <!-- Footer -->
      <div class="px-4 py-2 border-t border-border-subtle flex items-center gap-4 text-[10px] text-text-muted">
        <span><kbd class="bg-elevated px-1 py-0.5 rounded border border-border-subtle">&#x2191;&#x2193;</kbd> Naviguer</span>
        <span><kbd class="bg-elevated px-1 py-0.5 rounded border border-border-subtle">&#x23CE;</kbd> Ouvrir</span>
        <span><kbd class="bg-elevated px-1 py-0.5 rounded border border-border-subtle">?</kbd> Aide</span>
      </div>
    </div>
  </div>
{/if}
