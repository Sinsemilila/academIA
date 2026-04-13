<script lang="ts">
  import { page } from '$app/state';
  import { afterNavigate } from '$app/navigation';
  import { onMount } from 'svelte';
  import { agents } from '$lib/config';
  import { userAppearance } from '$lib/stores/user';
  import AgentFlag from '$lib/components/AgentFlag.svelte';

  let { collapsed = $bindable(false), isAdmin = false } = $props<{ collapsed?: boolean; isAdmin?: boolean }>();
  let accentColor = $state('#3b82f6');

  onMount(() => {
    const unsub = userAppearance.subscribe(v => { accentColor = v.avatarColor; });
    return unsub;
  });

  const nav = [
    { href: '/',          icon: '\uD83C\uDFE0', label: 'Home' },
    { href: '/chat/teacher', icon: '\uD83D\uDCAC', label: 'Chat' },
    { href: '/stats',     icon: '\uD83D\uDCCA', label: 'Stats' },
    { href: '/profile',   icon: '\u2699\uFE0F', label: 'Profil' },
  ];

  // Auto-close sidebar on mobile after navigation
  afterNavigate(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      collapsed = true;
    }
  });
</script>

<!-- Overlay mobile -->
{#if !collapsed}
  <button
    class="fixed inset-0 bg-black/50 z-30 lg:hidden backdrop-blur-sm"
    onclick={() => collapsed = true}
    aria-label="Fermer le menu"
  ></button>
{/if}

<aside
  class="fixed top-0 left-0 h-full z-40 bg-surface border-r border-border-subtle
         flex flex-col transition-all duration-200 ease-out
         {collapsed
           ? '-translate-x-full lg:translate-x-0 lg:w-16'
           : 'translate-x-0 w-44'}"
>
  <!-- Logo -->
  <div class="h-14 flex items-center border-b border-border-subtle {collapsed ? 'justify-center px-2' : 'px-4'}">
    {#if collapsed}
      <a href="/" class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white hover:brightness-110 transition-all"
        style="background-color: {accentColor}">
        A
      </a>
    {:else}
      <a href="/" class="text-lg font-semibold tracking-tight text-text-primary hover:text-teacher transition-colors">
        Academie
      </a>
    {/if}
  </div>

  <!-- Nav -->
  <nav class="flex-1 py-3 px-2 space-y-1">
    {#each nav as item}
      {@const active = item.href === '/'
        ? page.url.pathname === '/'
        : page.url.pathname.startsWith(item.href)}
      <a
        href={item.href}
        class="flex items-center gap-3 py-2 rounded-lg text-sm transition-colors
               {collapsed ? 'justify-center px-2' : 'px-3'}
               {active ? 'bg-elevated text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-elevated/50'}"
        title={collapsed ? item.label : ''}
      >
        <span class="text-base">{item.icon}</span>
        {#if !collapsed}
          <span>{item.label}</span>
        {/if}
      </a>
    {/each}
  </nav>

  <!-- Admin -->
  {#if isAdmin}
    {@const active = page.url.pathname.startsWith('/admin')}
    <div class="px-2">
      <a
        href="/admin"
        class="flex items-center gap-3 py-2 rounded-lg text-sm transition-colors
               {collapsed ? 'justify-center px-2' : 'px-3'}
               {active ? 'bg-elevated text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-elevated/50'}"
        title={collapsed ? 'Admin' : ''}
      >
        <span class="text-base">&#x2699;</span>
        {#if !collapsed}
          <span>Admin</span>
        {/if}
      </a>
    </div>
  {/if}

  <!-- Agents -->
  <div class="px-2 pb-4">
    {#if !collapsed}
      <div class="px-3 py-2 text-xs font-medium text-text-muted uppercase tracking-wider">
        Agents
      </div>
    {:else}
      <div class="w-8 h-px bg-border-subtle mx-auto mb-2"></div>
    {/if}
    <div class="space-y-1">
      {#each agents as agent}
        {@const active = page.url.pathname === `/chat/${agent.slug}`}
        <a
          href={agent.available ? `/chat/${agent.slug}` : '#'}
          class="flex items-center gap-3 py-2 rounded-lg text-sm transition-colors
                 {collapsed ? 'justify-center px-2' : 'px-3'}
                 {agent.available
                   ? active
                     ? 'bg-elevated text-text-primary'
                     : 'text-text-secondary hover:text-text-primary hover:bg-elevated/50'
                   : 'text-text-muted cursor-not-allowed opacity-40'}"
          title={collapsed ? agent.name : ''}
        >
          <AgentFlag {agent} size="sm" />
          {#if !collapsed}
            <span>{agent.name}</span>
          {/if}
        </a>
      {/each}
    </div>
  </div>
</aside>
