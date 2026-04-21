<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { addToast, toastError } from '$lib/stores/toasts';
  import { agents, domainLabel } from '$lib/config';
  import { currentDomain } from '$lib/stores/navigation';
  import { get } from 'svelte/store';

  type AdminUser = {
    id: number;
    username: string;
    display_name: string | null;
    is_admin: boolean;
    exam_access: boolean;
    created_at: string | null;
    niveau: string | null;
    derniere_session: string | null;
    mode: string | null;
    current_streak: number;
    longest_streak: number;
    total_sessions: number;
    total_xp: number;
    online: boolean;
    last_seen: string | null;
  };

  let users = $state<AdminUser[]>([]);
  let loading = $state(true);
  let showCreateForm = $state(false);
  let newUsername = $state('');
  let newPassword = $state('');
  let creating = $state(false);
  let confirmDelete = $state<number | null>(null);
  let confirmReset = $state<string | null>(null);
  // Session 37 — per-username reset-domain selection (null = global wipe).
  // Default to current navigation domain for safety (admin usually resetting
  // the domain they're looking at).
  let resetDomain = $state<string | null>(get(currentDomain));
  const availableAgents = $derived(agents.filter(a => a.available));
  let tokenUsage = $state<any>(null);

  async function loadTokenUsage() {
    try {
      tokenUsage = await api.getTokenUsage();
    } catch {}
  }

  async function loadUsers() {
    try {
      users = await api.adminGetUsers();
    } catch {
      toastError('Acces admin requis');
      goto('/');
    } finally {
      loading = false;
    }
  }

  async function createUser() {
    if (!newUsername || !newPassword) return;
    creating = true;
    try {
      await api.adminCreateUser(newUsername, newPassword);
      addToast(`Utilisateur ${newUsername} cree`, 'success');
      newUsername = '';
      newPassword = '';
      showCreateForm = false;
      await loadUsers();
    } catch (e: any) {
      toastError(e.message || 'Erreur creation');
    } finally {
      creating = false;
    }
  }

  async function resetProfile(username: string) {
    try {
      await api.adminResetProfile(username, resetDomain);
      const scopeLabel = resetDomain
        ? `${domainLabel(resetDomain)} uniquement`
        : 'tous domaines + historique';
      addToast(`Profil ${username} réinitialisé (${scopeLabel})`, 'success');
      confirmReset = null;
      await loadUsers();
    } catch (e: any) {
      toastError(e.message || 'Erreur reset');
    }
  }

  async function deleteUser(userId: number) {
    try {
      await api.adminDeleteUser(userId);
      addToast('Utilisateur supprime', 'success');
      confirmDelete = null;
      await loadUsers();
    } catch (e: any) {
      toastError(e.message || 'Erreur suppression');
    }
  }

  function timeAgo(dateStr: string | null): string {
    if (!dateStr) return 'jamais';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (diff < 60) return 'maintenant';
    if (diff < 3600) return `il y a ${Math.floor(diff / 60)}min`;
    if (diff < 86400) return `il y a ${Math.floor(diff / 3600)}h`;
    return `il y a ${Math.floor(diff / 86400)}j`;
  }

  onMount(() => { loadUsers(); loadTokenUsage(); });
</script>

<svelte:head>
  <title>Admin — AcademIA</title>
</svelte:head>

<div class="max-w-5xl mx-auto space-y-6">
  <div class="flex items-center justify-between">
    <h1 class="text-xl font-bold text-text-primary">Administration</h1>
    <button
      onclick={() => showCreateForm = !showCreateForm}
      class="px-4 py-2 text-sm font-medium rounded-lg bg-accent text-white hover:opacity-90 transition"
    >
      + Nouvel utilisateur
    </button>
  </div>

  <!-- Token Usage -->
  {#if tokenUsage}
    {@const pct = tokenUsage.pct}
    {@const barColor = pct > 90 ? 'bg-maestro' : pct > 70 ? 'bg-lehrer' : 'bg-teacher'}
    {@const ftModel = tokenUsage.models?.find((m: any) => m.name?.startsWith('ft:gpt-4o-mini'))}
    {@const sourceLabel = tokenUsage.source === 'litellm' ? 'Source : LiteLLM (réel)' : 'Source : estimation locale'}
    {@const sourceColor = tokenUsage.source === 'litellm' ? 'text-text-muted' : 'text-lehrer'}
    <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
      <div>
        <div class="flex items-center justify-between mb-2">
          <div>
            <h2 class="text-sm font-semibold">GPT-4o-mini &mdash; Quota journalier</h2>
            <p class="text-xs text-text-muted">Mod&#232;le actif : {tokenUsage.model}</p>
          </div>
          <div class="text-right">
            <p class="text-lg font-mono font-semibold" title="Affichage avec marge de sécurité +{tokenUsage.safety_margin_pct ?? 10}% pour rester ≥ OpenAI dashboard. Source brute : {tokenUsage.tokens_raw ? Math.round(tokenUsage.tokens_raw / 1000) + 'K' : 'n/a'}.">{Math.round(tokenUsage.tokens / 1000)}K <span class="text-sm text-text-muted font-normal">/ {Math.round(tokenUsage.limit / 1000)}K</span></p>
            <p class="text-xs text-text-muted">{pct}%{tokenUsage.safety_margin_pct ? ` (+${tokenUsage.safety_margin_pct}% safety)` : ''}</p>
          </div>
        </div>
        <div class="w-full h-2 bg-elevated rounded-full overflow-hidden">
          <div class="h-full {barColor} rounded-full transition-all" style="width: {Math.min(pct, 100)}%"></div>
        </div>
        {#if tokenUsage.exceeded}
          <p class="text-xs text-maestro mt-2">Quota d&#233;pass&#233; &mdash; fallback groq-standard actif</p>
        {/if}
        <p class="text-[10px] {sourceColor} mt-2 font-mono">{sourceLabel}</p>
      </div>

      {#if ftModel}
        <div class="border-t border-border-subtle pt-3 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold text-text-secondary">ft:gpt-4o-mini-v3 (error analysis)</p>
            <p class="text-[10px] text-text-muted">Payant — pas de quota imposé</p>
          </div>
          <div class="text-right">
            <p class="text-sm font-mono">{Math.round(ftModel.tokens / 1000)}K tokens</p>
            <p class="text-[10px] text-text-muted">${ftModel.cost_usd.toFixed(4)}</p>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  {#if showCreateForm}
    <div class="bg-surface border border-border-subtle rounded-xl p-4 space-y-3">
      <div class="flex gap-3">
        <input
          type="text"
          placeholder="Username"
          bind:value={newUsername}
          class="flex-1 px-3 py-2 rounded-lg bg-base border border-border-subtle text-sm text-text-primary"
        />
        <input
          type="password"
          placeholder="Mot de passe (min 8 car.)"
          bind:value={newPassword}
          class="flex-1 px-3 py-2 rounded-lg bg-base border border-border-subtle text-sm text-text-primary"
        />
        <button
          onclick={createUser}
          disabled={creating || !newUsername || newPassword.length < 8}
          class="px-4 py-2 text-sm font-medium rounded-lg bg-accent text-white hover:opacity-90 transition disabled:opacity-50"
        >
          {creating ? '...' : 'Creer'}
        </button>
      </div>
    </div>
  {/if}

  {#if loading}
    <div class="space-y-3">
      {#each Array(3) as _}<div class="skeleton h-16 rounded-xl"></div>{/each}
    </div>
  {:else}
    <div class="bg-surface border border-border-subtle rounded-xl overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border-subtle text-text-secondary text-left">
            <th class="px-4 py-3 font-medium">Utilisateur</th>
            <th class="px-4 py-3 font-medium hidden sm:table-cell">Niveau</th>
            <th class="px-4 py-3 font-medium hidden md:table-cell">Sessions</th>
            <th class="px-4 py-3 font-medium hidden md:table-cell">Streak</th>
            <th class="px-4 py-3 font-medium hidden lg:table-cell">XP</th>
            <th class="px-4 py-3 font-medium">Derniere connexion</th>
            <th class="px-4 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#each users as user (user.id)}
            <tr class="border-b border-border-subtle/50 hover:bg-base/50 transition">
              <td class="px-4 py-3">
                <div class="flex items-center gap-1.5">
                  {#if user.online}
                    <span class="w-2 h-2 rounded-full bg-green-400 shrink-0" title="En ligne"></span>
                  {/if}
                  <span class="font-medium text-text-primary">{user.display_name || user.username}</span>
                </div>
                <div class="text-xs text-text-muted">{user.username}{user.is_admin ? ' (admin)' : ''}</div>
              </td>
              <td class="px-4 py-3 hidden sm:table-cell">
                <span class="px-2 py-0.5 rounded text-xs font-semibold
                  {user.niveau ? 'bg-accent/20 text-accent' : 'bg-base text-text-muted'}">
                  {user.niveau || 'N/A'}
                </span>
              </td>
              <td class="px-4 py-3 hidden md:table-cell text-text-secondary">{user.total_sessions}</td>
              <td class="px-4 py-3 hidden md:table-cell text-text-secondary">{user.current_streak}j</td>
              <td class="px-4 py-3 hidden lg:table-cell text-text-secondary">{user.total_xp}</td>
              <td class="px-4 py-3 text-text-muted text-xs">
                {#if user.online}
                  <span class="text-green-400">en ligne</span>
                {:else}
                  {timeAgo(user.last_seen)}
                {/if}
              </td>
              <td class="px-4 py-3 text-right space-x-1">
                {#if confirmReset === user.username}
                  <select bind:value={resetDomain}
                    class="px-1 py-1 text-xs rounded bg-elevated border border-border-subtle text-text-primary"
                    title="Domaine à réinitialiser">
                    {#each availableAgents as a (a.domain)}
                      <option value={a.domain}>{a.lang}</option>
                    {/each}
                    <option value={null}>Tous (+ historique)</option>
                  </select>
                  <button onclick={() => resetProfile(user.username)}
                    class="px-2 py-1 text-xs rounded bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30">
                    Confirmer
                  </button>
                  <button onclick={() => confirmReset = null}
                    class="px-2 py-1 text-xs rounded text-text-muted hover:text-text-secondary">
                    Annuler
                  </button>
                {:else if confirmDelete === user.id}
                  <button onclick={() => deleteUser(user.id)}
                    class="px-2 py-1 text-xs rounded bg-red-500/20 text-red-400 hover:bg-red-500/30">
                    Confirmer suppr
                  </button>
                  <button onclick={() => confirmDelete = null}
                    class="px-2 py-1 text-xs rounded text-text-muted hover:text-text-secondary">
                    Annuler
                  </button>
                {:else}
                  <button onclick={() => { resetDomain = get(currentDomain); confirmReset = user.username; }}
                    title="Réinitialiser le profil (choix du domaine à l'étape suivante)"
                    class="px-2 py-1 text-xs rounded text-text-muted hover:text-yellow-400 hover:bg-yellow-500/10 transition">
                    Reset
                  </button>
                  {#if !user.is_admin}
                    <button onclick={() => confirmDelete = user.id}
                      title="Supprimer utilisateur"
                      class="px-2 py-1 text-xs rounded text-text-muted hover:text-red-400 hover:bg-red-500/10 transition">
                      Suppr
                    </button>
                  {/if}
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <div class="text-xs text-text-muted text-center">
      {users.filter(u => u.online).length} en ligne — {users.length} inscrits
    </div>
  {/if}
</div>
