<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { setTheme, getTheme } from '$lib/stores/theme';
  import { addToast } from '$lib/stores/toasts';

  const AVATAR_COLORS = [
    '#3b82f6', '#ef4444', '#a855f7', '#f59e0b',
    '#22c55e', '#06b6d4', '#ec4899', '#8b5cf6',
    '#f97316', '#14b8a6',
  ];
  const GOAL_OPTIONS = [5, 10, 15, 20, 30, 45, 60];

  let settings = $state<any>(null);
  let sessions = $state<any[]>([]);
  let loading = $state(true);

  // Edit states
  let displayName = $state('');
  let avatarColor = $state('#3b82f6');
  let theme = $state<'dark' | 'light'>('dark');
  let dailyGoal = $state(15);
  let savingProfile = $state(false);
  let centresInteret = $state('');
  let styleCorrection = $state('');

  const STYLE_OPTIONS = [
    { value: '', label: 'Par d\u00E9faut' },
    { value: 'direct', label: 'Direct' },
    { value: 'encourageant', label: 'Encourageant' },
    { value: 'humour', label: 'Avec humour' },
  ];

  // Password states
  let currentPw = $state('');
  let newPw = $state('');
  let confirmPw = $state('');
  let pwError = $state('');
  let savingPw = $state(false);

  onMount(async () => {
    const [s, sess] = await Promise.all([
      api.getSettings(),
      api.getActiveSessions(),
    ]);
    settings = s;
    sessions = sess?.sessions || [];
    if (s) {
      displayName = s.display_name || '';
      avatarColor = s.avatar_color || '#3b82f6';
      theme = s.theme || 'dark';
      dailyGoal = s.daily_goal_minutes || 15;
      centresInteret = s.centres_interet || '';
      styleCorrection = s.style_correction || '';
    }
    loading = false;
  });

  async function saveProfile() {
    savingProfile = true;
    await api.updateProfile({
      display_name: displayName || undefined,
      avatar_color: avatarColor,
      theme,
      daily_goal_minutes: dailyGoal,
      centres_interet: centresInteret || undefined,
      style_correction: styleCorrection || undefined,
    });
    setTheme(theme);
    window.dispatchEvent(new CustomEvent('profile-updated', {
      detail: { avatar_color: avatarColor, display_name: displayName, daily_goal_minutes: dailyGoal },
    }));
    addToast({ type: 'info', message: 'Profil mis \u00e0 jour' });
    savingProfile = false;
  }

  async function savePassword() {
    pwError = '';
    if (newPw.length < 6) { pwError = '6 caract\u00E8res minimum'; return; }
    if (newPw !== confirmPw) { pwError = 'Les mots de passe ne correspondent pas'; return; }
    savingPw = true;
    try {
      await api.changePassword(currentPw, newPw);
      addToast({ type: 'info', message: 'Mot de passe mis \u00e0 jour' });
      currentPw = ''; newPw = ''; confirmPw = '';
    } catch (e: any) {
      pwError = e.message;
    }
    savingPw = false;
  }

  async function revokeSession(id: number) {
    await api.revokeSession(id);
    sessions = sessions.filter(s => s.id !== id);
    addToast({ type: 'info', message: 'Session r\u00e9voqu\u00e9e' });
  }

  async function revokeAll() {
    await api.revokeAllSessions();
    sessions = [];
    addToast({ type: 'info', message: 'Toutes les sessions r\u00e9voqu\u00e9es' });
  }

  function formatDate(iso: string): string {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString('fr-FR', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }
</script>

<svelte:head>
  <title>Profil — Academie-IA</title>
</svelte:head>

{#if loading}
  <div class="max-w-2xl mx-auto space-y-6">
    <div class="skeleton h-8 w-48"></div>
    {#each Array(3) as _}<div class="skeleton h-32 w-full"></div>{/each}
  </div>
{:else}
<div class="max-w-2xl mx-auto space-y-8">
  <h1 class="text-2xl font-semibold">Profil & R&#233;glages</h1>

  <!-- ── Account ─────────────────────────── -->
  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-5">
    <h2 class="font-semibold text-lg">Compte</h2>

    <div>
      <label for="username" class="block text-sm text-text-secondary mb-1">Nom d'utilisateur</label>
      <input id="username" type="text" value={settings?.username} disabled
        class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-text-muted text-sm cursor-not-allowed" />
    </div>

    <div>
      <label for="display_name" class="block text-sm text-text-secondary mb-1">Nom d'affichage</label>
      <input id="display_name" type="text" bind:value={displayName}
        class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-text-primary text-sm
               focus:outline-none focus:border-teacher transition-colors"
        placeholder="Ton pr&#233;nom ou pseudo" />
    </div>

    <!-- Avatar color -->
    <div>
      <label class="block text-sm text-text-secondary mb-2">Couleur de l'avatar</label>
      <div class="flex flex-wrap gap-2">
        {#each AVATAR_COLORS as color}
          <button
            class="w-9 h-9 rounded-full transition-all {avatarColor === color ? 'ring-2 ring-offset-2 ring-offset-base scale-110' : 'hover:scale-105'}"
            style="background-color: {color}; {avatarColor === color ? `ring-color: ${color}` : ''}"
            onclick={() => avatarColor = color}
          >
            {#if avatarColor === color}
              <svg class="w-4 h-4 mx-auto text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            {/if}
          </button>
        {/each}
      </div>
    </div>

    <!-- Theme -->
    <div>
      <label class="block text-sm text-text-secondary mb-2">Theme</label>
      <div class="flex gap-3">
        <button
          class="flex-1 px-4 py-2.5 rounded-lg border text-sm font-medium transition-all
                 {theme === 'dark' ? 'border-teacher bg-teacher/10 text-teacher' : 'border-border-subtle text-text-secondary hover:border-text-muted'}"
          onclick={() => { theme = 'dark'; setTheme('dark'); }}
        >
          &#x1F319; Sombre
        </button>
        <button
          class="flex-1 px-4 py-2.5 rounded-lg border text-sm font-medium transition-all
                 {theme === 'light' ? 'border-teacher bg-teacher/10 text-teacher' : 'border-border-subtle text-text-secondary hover:border-text-muted'}"
          onclick={() => { theme = 'light'; setTheme('light'); }}
        >
          &#x2600;&#xFE0F; Clair
        </button>
      </div>
    </div>

    <!-- Daily goal -->
    <div>
      <label class="block text-sm text-text-secondary mb-2">Objectif quotidien</label>
      <div class="flex flex-wrap gap-2">
        {#each GOAL_OPTIONS as opt}
          <button
            class="px-3 py-1.5 rounded-lg border text-sm font-mono transition-all
                   {dailyGoal === opt ? 'border-teacher bg-teacher/10 text-teacher' : 'border-border-subtle text-text-secondary hover:border-text-muted'}"
            onclick={() => dailyGoal = opt}
          >
            {opt} min
          </button>
        {/each}
      </div>
    </div>

    <!-- Centres d'interet -->
    <div>
      <label for="centres_interet" class="block text-sm text-text-secondary mb-1">Centres d'int&#233;r&#234;t</label>
      <input id="centres_interet" type="text" bind:value={centresInteret}
        class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-text-primary text-sm
               focus:outline-none focus:border-teacher transition-colors"
        placeholder="musique, cuisine, tech, cin&#233;ma..." />
      <p class="text-xs text-text-muted mt-1">Teacher utilisera tes centres d'int&#233;r&#234;t pour contextualiser les exercices.</p>
    </div>

    <!-- Style de correction -->
    <div>
      <label class="block text-sm text-text-secondary mb-2">Style de correction</label>
      <div class="flex flex-wrap gap-2">
        {#each STYLE_OPTIONS as opt}
          <button
            class="px-3 py-1.5 rounded-lg border text-sm transition-all
                   {styleCorrection === opt.value ? 'border-teacher bg-teacher/10 text-teacher' : 'border-border-subtle text-text-secondary hover:border-text-muted'}"
            onclick={() => styleCorrection = opt.value}
          >
            {opt.label}
          </button>
        {/each}
      </div>
      <p class="text-xs text-text-muted mt-1">Teacher adaptera son ton et sa fa&#231;on de te corriger.</p>
    </div>

    <button
      onclick={saveProfile}
      disabled={savingProfile}
      class="px-5 py-2 bg-teacher text-white text-sm font-medium rounded-lg
             hover:brightness-110 transition-all disabled:opacity-50"
    >
      {savingProfile ? 'Sauvegarde...' : 'Enregistrer'}
    </button>

    {#if settings?.created_at}
      <p class="text-xs text-text-muted">Compte cr&#233;&#233; le {formatDate(settings.created_at)}</p>
    {/if}
  </section>

  <!-- ── Password ────────────────────────── -->
  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <h2 class="font-semibold text-lg">S&#233;curit&#233;</h2>

    <div>
      <label for="current_pw" class="block text-sm text-text-secondary mb-1">Mot de passe actuel</label>
      <input id="current_pw" type="password" bind:value={currentPw}
        class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-text-primary text-sm
               focus:outline-none focus:border-teacher transition-colors" />
    </div>
    <div>
      <label for="new_pw" class="block text-sm text-text-secondary mb-1">Nouveau mot de passe</label>
      <input id="new_pw" type="password" bind:value={newPw}
        class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-text-primary text-sm
               focus:outline-none focus:border-teacher transition-colors" />
    </div>
    <div>
      <label for="confirm_pw" class="block text-sm text-text-secondary mb-1">Confirmer</label>
      <input id="confirm_pw" type="password" bind:value={confirmPw}
        class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-text-primary text-sm
               focus:outline-none focus:border-teacher transition-colors" />
    </div>

    {#if pwError}
      <p class="text-sm text-maestro">{pwError}</p>
    {/if}

    <button
      onclick={savePassword}
      disabled={savingPw || !currentPw || !newPw}
      class="px-5 py-2 bg-teacher text-white text-sm font-medium rounded-lg
             hover:brightness-110 transition-all disabled:opacity-50"
    >
      {savingPw ? 'Mise \u00E0 jour...' : 'Changer le mot de passe'}
    </button>
  </section>

  <!-- ── Active sessions ─────────────────── -->
  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="font-semibold text-lg">Sessions actives</h2>
      {#if sessions.length > 1}
        <button
          onclick={revokeAll}
          class="text-xs text-maestro hover:underline"
        >
          Tout r&#233;voquer
        </button>
      {/if}
    </div>

    {#if sessions.length === 0}
      <p class="text-sm text-text-muted">Aucune session active enregistr&#233;e.</p>
    {:else}
      <div class="space-y-2">
        {#each sessions as session}
          <div class="flex items-center justify-between bg-elevated rounded-lg px-4 py-3">
            <div>
              <p class="text-sm">{session.device || 'Appareil inconnu'}</p>
              <p class="text-xs text-text-muted">
                {session.ip || '—'} · {session.last_active ? formatDate(session.last_active) : '—'}
              </p>
            </div>
            <button
              onclick={() => revokeSession(session.id)}
              class="text-xs text-maestro hover:underline"
            >
              R&#233;voquer
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Footer -->
  <div class="text-center pt-2">
    <a href="/legal" class="text-xs text-text-muted hover:text-text-secondary transition-colors">
      Mentions l&#233;gales & Confidentialit&#233;
    </a>
  </div>
</div>
{/if}
