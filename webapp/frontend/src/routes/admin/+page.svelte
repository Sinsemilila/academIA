<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { addToast, toastError } from '$lib/stores/toasts';

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
      await api.adminResetProfile(username);
      addToast(`Profil ${username} reinitialise (A1)`, 'success');
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

  onMount(loadUsers);
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
                  <button onclick={() => resetProfile(user.username)}
                    class="px-2 py-1 text-xs rounded bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30">
                    Confirmer reset
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
                  <button onclick={() => confirmReset = user.username}
                    title="Reset profil A1"
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
