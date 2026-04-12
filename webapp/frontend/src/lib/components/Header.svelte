<script lang="ts">
  import { api } from '$lib/api';
  import { getTheme, toggleTheme } from '$lib/stores/theme';

  let {
    streak = 0, xp = 0, rankName = '', username = '',
    avatarColor = '#3b82f6', dailyProgress = null, onToggleSidebar
  } = $props<{
    streak: number; xp: number; rankName: string; username: string;
    avatarColor: string; dailyProgress: { goal_minutes: number; done_minutes: number; pct: number; completed: boolean } | null;
    onToggleSidebar: () => void;
  }>();

  let showMenu = $state(false);
  let theme = $state(getTheme());
  let lastSeenChangelog = $state('');
  // Latest changelog version — bump when adding entries
  const CHANGELOG_VERSION = '0.5';
  let hasNewChangelog = $derived(lastSeenChangelog !== CHANGELOG_VERSION);

  import { onMount } from 'svelte';
  onMount(() => {
    lastSeenChangelog = localStorage.getItem('lastSeenChangelog') || '';
  });

  function handleToggleTheme() {
    theme = toggleTheme();
  }

  function logout() {
    api.logout();
  }
</script>

<svelte:window onclick={() => { if (showMenu) showMenu = false; }} />

<header class="h-14 bg-surface border-b border-border-subtle flex items-center justify-between px-4">
  <!-- Left: hamburger -->
  <div class="flex items-center gap-3">
    <button
      class="text-text-secondary hover:text-text-primary transition-colors"
      onclick={onToggleSidebar}
      aria-label="Menu"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
  </div>

  <!-- Right: theme + XP + streak + avatar -->
  <div class="flex items-center gap-3">
    <!-- Search shortcut -->
    <div class="tooltip-container hidden sm:flex">
      <button
        onclick={() => { window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })); }}
        class="flex items-center gap-2 px-2.5 py-1 bg-elevated border border-border-subtle rounded-lg text-text-muted hover:text-text-secondary transition-all text-xs"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <kbd class="text-[10px] font-mono">&#x2318;K</kbd>
      </button>
      <div class="tooltip-content">Palette de commandes</div>
    </div>

    <!-- Theme toggle -->
    <button
      onclick={handleToggleTheme}
      class="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:text-text-primary hover:bg-elevated transition-all"
      aria-label="Changer le theme"
    >
      {#if theme === 'dark'}
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      {:else}
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      {/if}
    </button>

    <!-- Daily goal ring -->
    {#if dailyProgress}
      <div class="tooltip-container">
        <div class="relative w-8 h-8">
          <svg class="w-8 h-8 -rotate-90" viewBox="0 0 32 32">
            <circle cx="16" cy="16" r="13" fill="none" stroke="var(--color-elevated)" stroke-width="2.5" />
            <circle cx="16" cy="16" r="13" fill="none"
              stroke="{dailyProgress.completed ? 'var(--color-professore)' : 'var(--color-teacher)'}"
              stroke-width="2.5"
              stroke-dasharray="{Math.PI * 26}"
              stroke-dashoffset="{Math.PI * 26 * (1 - dailyProgress.pct / 100)}"
              stroke-linecap="round"
              class="transition-all duration-700"
            />
          </svg>
          <span class="absolute inset-0 flex items-center justify-center text-[8px] font-mono font-bold">
            {dailyProgress.pct}
          </span>
        </div>
        <div class="tooltip-content">{dailyProgress.done_minutes}/{dailyProgress.goal_minutes} min — Objectif du jour</div>
      </div>
    {/if}

    <!-- XP badge -->
    <div class="tooltip-container">
      <div class="flex items-center gap-1.5 px-2.5 py-1 bg-elevated rounded-lg">
        <span class="text-xs font-mono font-semibold text-lehrer">{xp}</span>
        <span class="text-[10px] text-text-muted">XP</span>
      </div>
      <div class="tooltip-content">Points d'exp&#233;rience</div>
    </div>

    <!-- Streak -->
    {#if streak > 0}
      <div class="tooltip-container">
        <div class="flex items-center gap-1 text-sm">
          <span class="text-base">&#x1F525;</span>
          <span class="font-mono font-semibold">{streak}</span>
        </div>
        <div class="tooltip-content">Jours cons&#233;cutifs</div>
      </div>
    {/if}

    <!-- Avatar + dropdown -->
    <div class="relative">
      <button
        class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold text-white
               hover:brightness-110 transition-all"
        style="background-color: {avatarColor}"
        onclick={(e) => { e.stopPropagation(); showMenu = !showMenu; }}
      >
        {username.charAt(0).toUpperCase()}
      </button>

      {#if showMenu}
        <div class="absolute right-0 top-10 bg-surface border border-border-subtle rounded-xl shadow-lg py-1 min-w-[160px] z-50">
          <div class="px-3 py-2 border-b border-border-subtle">
            <p class="text-sm font-medium">{username}</p>
            <p class="text-[10px] text-text-muted">{rankName}</p>
          </div>
          <a
            href="/profile"
            class="block w-full px-3 py-2 text-left text-sm text-text-secondary hover:text-text-primary hover:bg-elevated transition-colors"
          >
            Profil & R&#233;glages
          </a>
          <a
            href="/changelog"
            class="flex items-center gap-2 w-full px-3 py-2 text-left text-sm text-text-secondary hover:text-text-primary hover:bg-elevated transition-colors"
          >
            Nouveaut&#233;s
            {#if hasNewChangelog}
              <span class="w-2 h-2 rounded-full bg-teacher"></span>
            {/if}
          </a>
          <button
            class="w-full px-3 py-2 text-left text-sm text-maestro hover:bg-elevated transition-colors"
            onclick={logout}
          >
            D&#233;connexion
          </button>
        </div>
      {/if}
    </div>
  </div>
</header>
