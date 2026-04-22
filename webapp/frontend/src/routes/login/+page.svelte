<script lang="ts">
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';

  let username = $state('');
  let password = $state('');
  let mfaCode = $state('');
  let step = $state<'creds' | 'mfa'>('creds');
  let error = $state('');
  let loading = $state(false);

  async function handleLogin(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';
    try {
      const res = await api.login(username, password);
      if (res.mfa_required) {
        step = 'mfa';
      } else {
        goto('/');
      }
    } catch (err: any) {
      error = err.message || 'Erreur de connexion';
    } finally {
      loading = false;
    }
  }

  async function handleMfa(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';
    try {
      await api.loginMfa(username, password, mfaCode.trim());
      goto('/');
    } catch (err: any) {
      error = err.message || 'Code invalide';
    } finally {
      loading = false;
    }
  }

  function backToCreds() {
    step = 'creds';
    mfaCode = '';
    error = '';
  }
</script>

<svelte:head>
  <title>Connexion — Academie-IA</title>
</svelte:head>

<div class="min-h-dvh flex items-center justify-center bg-base -m-4 md:-m-6">
  <div class="w-full max-w-sm px-6">
    <!-- Logo -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-semibold tracking-tight">Academie</h1>
      <p class="text-sm text-text-secondary mt-2">Plateforme d'apprentissage IA</p>
    </div>

    {#if step === 'creds'}
      <!-- Step 1 — Credentials -->
      <form onsubmit={handleLogin} class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
        <div>
          <label for="username" class="block text-sm font-medium text-text-secondary mb-1.5">
            Nom d'utilisateur
          </label>
          <input
            id="username"
            type="text"
            bind:value={username}
            required
            autocomplete="username"
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg
                   text-text-primary placeholder-text-muted text-sm
                   focus:outline-none focus:border-teacher transition-colors"
            placeholder="sinse"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-text-secondary mb-1.5">
            Mot de passe
          </label>
          <input
            id="password"
            type="password"
            bind:value={password}
            required
            autocomplete="current-password"
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg
                   text-text-primary placeholder-text-muted text-sm
                   focus:outline-none focus:border-teacher transition-colors"
            placeholder="••••••••"
          />
        </div>

        {#if error}
          <p class="text-sm text-maestro">{error}</p>
        {/if}

        <button
          type="submit"
          disabled={loading}
          class="w-full py-2.5 bg-teacher text-white text-sm font-medium rounded-lg
                 hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Connexion...' : 'Entrer'}
        </button>
      </form>
    {:else}
      <!-- Step 2 — MFA TOTP -->
      <form onsubmit={handleMfa} class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
        <div>
          <label for="mfa-code" class="block text-sm font-medium text-text-secondary mb-1.5">
            Code d'authentification
          </label>
          <p class="text-xs text-text-muted mb-2">
            Saisis le code à 6 chiffres affiché par ton application TOTP, ou un recovery code.
          </p>
          <input
            id="mfa-code"
            type="text"
            inputmode="numeric"
            bind:value={mfaCode}
            required
            autocomplete="one-time-code"
            autofocus
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg
                   text-text-primary placeholder-text-muted text-sm font-mono tracking-widest text-center
                   focus:outline-none focus:border-teacher transition-colors"
            placeholder="123456"
          />
        </div>

        {#if error}
          <p class="text-sm text-maestro">{error}</p>
        {/if}

        <button
          type="submit"
          disabled={loading || !mfaCode.trim()}
          class="w-full py-2.5 bg-teacher text-white text-sm font-medium rounded-lg
                 hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Vérification...' : 'Valider'}
        </button>

        <button
          type="button"
          onclick={backToCreds}
          class="w-full py-2 text-xs text-text-muted hover:text-text-secondary transition-colors"
        >
          ← Retour
        </button>
      </form>
    {/if}

    <p class="text-center mt-6">
      <a href="/legal" class="text-xs text-text-muted hover:text-text-secondary transition-colors">
        Mentions l&#233;gales
      </a>
    </p>
  </div>
</div>
