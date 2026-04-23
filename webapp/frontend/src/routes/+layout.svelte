<script lang="ts">
  import './layout.css';
  import { page } from '$app/state';
  import { afterNavigate, goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { initTheme } from '$lib/stores/theme';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Header from '$lib/components/Header.svelte';
  import Toasts from '$lib/components/Toasts.svelte';
  import ConnectionIndicator from '$lib/components/ConnectionIndicator.svelte';
  import CommandPalette from '$lib/components/CommandPalette.svelte';
  import KeyboardShortcuts from '$lib/components/KeyboardShortcuts.svelte';
  import CelebrationModal from '$lib/components/CelebrationModal.svelte';
  import { toastError } from '$lib/stores/toasts';
  import { userAppearance } from '$lib/stores/user';
  import { currentAgent } from '$lib/stores/navigation';

  let { children } = $props();

  // Desktop: sidebar open by default. Mobile: closed.
  let sidebarCollapsed = $state(typeof window !== 'undefined' ? window.innerWidth < 1024 : true);
  let user = $state<{ username: string; display_name: string; is_admin: boolean } | null>(null);
  let streak = $state(0);
  let xp = $state(0);
  let rankName = $state('');
  let dailyProgress = $state<{ goal_minutes: number; done_minutes: number; pct: number; completed: boolean } | null>(null);
  let ready = $state(false);
  let pageKey = $state(0);

  // Celebration state
  let showCelebration = $state(false);
  let celebrationType = $state<'badge' | 'levelup' | 'streak'>('badge');
  let celebrationIcon = $state('');
  let celebrationTitle = $state('');
  let celebrationSubtitle = $state('');

  const isLoginPage = $derived(page.url.pathname === '/login');
  const isLegalPage = $derived(page.url.pathname === '/legal');
  const isPublicPage = $derived(isLoginPage || isLegalPage);

  async function loadUser() {
    // Phase A1 — auth via cookie (HttpOnly, server-side). No JS-readable token.
    // api.me() will redirect to /login on 401 via the shared fetch wrapper.
    try {
      user = await api.me();
      const [streakData, xpData, dpData] = await Promise.all([
        api.getStreak(),
        api.getXp(),
        api.getDailyProgress(),
      ]);
      streak = streakData.current_streak;
      xp = xpData.total;
      rankName = xpData.rank.name;
      dailyProgress = dpData;
      // Populate shared user appearance store
      userAppearance.set({
        initial: (user.display_name || user.username || 'U').charAt(0).toUpperCase(),
        avatarColor: user.avatar_color || '#3b82f6',
        displayName: user.display_name || user.username || '',
      });
      ready = true;
    } catch {
      goto('/login');
    }
  }

  function handleXpUpdate(e: Event) {
    const prevRank = rankName;
    api.getXp().then(data => {
      xp = data.total;
      rankName = data.rank.name;
      // Check for rank-up celebration
      if (prevRank && data.rank.name !== prevRank) {
        celebrationType = 'levelup';
        celebrationIcon = '\u2B50';
        celebrationTitle = `Rang ${data.rank.name} !`;
        celebrationSubtitle = `Tu as atteint le rang ${data.rank.name}`;
        showCelebration = true;
      }
    });
  }

  function handleStreakMilestone(e: Event) {
    const detail = (e as CustomEvent).detail;
    if (detail?.streak && [7, 14, 30, 50, 100].includes(detail.streak)) {
      celebrationType = 'streak';
      celebrationIcon = '\uD83D\uDD25';
      celebrationTitle = `${detail.streak} jours de streak !`;
      celebrationSubtitle = 'Ta r\u00e9gularit\u00e9 est impressionnante';
      showCelebration = true;
    }
  }

  function handleRateLimited(e: Event) {
    const detail = (e as CustomEvent).detail;
    toastError(`Trop de requ\u00eates. R\u00e9essaie dans ${detail?.seconds || 60}s`);
  }

  function handleBadgeUnlock(e: Event) {
    const detail = (e as CustomEvent).detail;
    if (detail?.name) {
      celebrationType = 'badge';
      celebrationIcon = detail.icon || '\uD83C\uDFC6';
      celebrationTitle = `Badge d\u00e9bloqu\u00e9 !`;
      celebrationSubtitle = detail.name;
      showCelebration = true;
    }
  }

  function handleProfileUpdated(e: Event) {
    const detail = (e as CustomEvent).detail;
    if (user && detail) {
      if (detail.avatar_color) user = { ...user, avatar_color: detail.avatar_color };
      if (detail.display_name !== undefined) user = { ...user, display_name: detail.display_name };
      if (detail.daily_goal_minutes && dailyProgress) {
        dailyProgress = {
          ...dailyProgress,
          goal_minutes: detail.daily_goal_minutes,
          pct: Math.min(100, Math.round((dailyProgress.done_minutes / detail.daily_goal_minutes) * 100)),
          completed: Math.round((dailyProgress.done_minutes / detail.daily_goal_minutes) * 100) >= 100,
        };
      }
      // Sync shared user appearance store
      userAppearance.set({
        initial: (user.display_name || user.username || 'U').charAt(0).toUpperCase(),
        avatarColor: user.avatar_color || '#3b82f6',
        displayName: user.display_name || user.username || '',
      });
    }
  }

  // Sprint 5 D4: sync currentAgent store from URL on every navigation
  afterNavigate((nav) => {
    const agentParam = nav.to?.params?.agent;
    if (typeof agentParam === 'string' && agentParam) {
      currentAgent.set(agentParam);
    }
  });

  onMount(() => {
    initTheme();
    if (isPublicPage) {
      ready = true;
      return;
    }
    loadUser();
    window.addEventListener('xp-update', handleXpUpdate);
    window.addEventListener('streak-milestone', handleStreakMilestone);
    window.addEventListener('rate-limited', handleRateLimited);
    window.addEventListener('badge-unlock', handleBadgeUnlock);
    window.addEventListener('profile-updated', handleProfileUpdated);
    return () => {
      window.removeEventListener('xp-update', handleXpUpdate);
      window.removeEventListener('streak-milestone', handleStreakMilestone);
      window.removeEventListener('rate-limited', handleRateLimited);
      window.removeEventListener('badge-unlock', handleBadgeUnlock);
      window.removeEventListener('profile-updated', handleProfileUpdated);
    };
  });

  afterNavigate(() => {
    pageKey++;
    if (!isPublicPage && !user) {
      loadUser();
    }
  });
</script>

<Toasts />
<ConnectionIndicator />
<CommandPalette />
<KeyboardShortcuts />
<CelebrationModal
  bind:show={showCelebration}
  type={celebrationType}
  icon={celebrationIcon}
  title={celebrationTitle}
  subtitle={celebrationSubtitle}
/>

{#if isPublicPage}
  {@render children()}
{:else if ready && user}
  <div class="min-h-dvh bg-base flex">
    <Sidebar bind:collapsed={sidebarCollapsed} isAdmin={user.is_admin} />
    <div class="flex-1 flex flex-col transition-[margin] duration-200
                {sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-44'}">
      <Header
        {streak}
        {xp}
        {rankName}
        {dailyProgress}
        username={user.display_name || user.username}
        avatarColor={user.avatar_color || '#3b82f6'}
        onToggleSidebar={() => sidebarCollapsed = !sidebarCollapsed}
      />
      <main class="flex-1 p-4 md:p-6">
        {#key pageKey}
          <div class="page-transition">
            {@render children()}
          </div>
        {/key}
      </main>
      <footer class="py-2 text-center">
        <a href="/legal" class="text-[10px] text-text-muted hover:text-text-secondary transition-colors">Mentions l&#233;gales</a>
      </footer>
    </div>
  </div>
{:else}
  <!-- Loading skeleton -->
  <div class="min-h-dvh bg-base flex">
    <div class="hidden lg:block w-56 bg-surface border-r border-border-subtle shrink-0"></div>
    <div class="flex-1 flex flex-col">
      <div class="h-14 bg-surface border-b border-border-subtle"></div>
      <main class="flex-1 p-4 md:p-6">
        <div class="max-w-4xl mx-auto space-y-6">
          <div class="skeleton h-8 w-48"></div>
          <div class="skeleton h-32 w-full"></div>
          <div class="grid grid-cols-3 gap-4">
            {#each Array(3) as _}<div class="skeleton h-20"></div>{/each}
          </div>
        </div>
      </main>
    </div>
  </div>
{/if}
