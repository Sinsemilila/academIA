<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';

  type Status = { enrolled: boolean; enrolled_at?: string | null; recovery_codes_remaining: number };

  let status = $state<Status | null>(null);
  let loading = $state(false);
  let error = $state('');

  // Enrollment state
  let enrollmentStarted = $state(false);
  let secret = $state('');
  let qrDataUrl = $state('');
  let provisioningUri = $state('');
  let confirmCode = $state('');
  let recoveryCodes = $state<string[] | null>(null);

  // Disable state
  let disableMode = $state(false);
  let disablePassword = $state('');
  let disableCode = $state('');

  // A4b polish — regenerate recovery codes
  let regenMode = $state(false);
  let regenPassword = $state('');
  let regenCode = $state('');

  onMount(refreshStatus);

  async function refreshStatus() {
    try {
      status = await api.totpStatus();
    } catch (err: any) {
      error = err.message || 'Erreur de chargement';
    }
  }

  async function startEnrollment() {
    loading = true;
    error = '';
    try {
      const res = await api.totpEnrollStart();
      secret = res.secret;
      qrDataUrl = res.qr_data_url;
      provisioningUri = res.provisioning_uri;
      enrollmentStarted = true;
    } catch (err: any) {
      error = err.message || 'Erreur enrollment';
    } finally {
      loading = false;
    }
  }

  async function confirmEnrollment(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';
    try {
      const res = await api.totpEnrollConfirm(secret, confirmCode.trim());
      recoveryCodes = res.recovery_codes;
      await refreshStatus();
    } catch (err: any) {
      error = err.message || 'Code invalide';
    } finally {
      loading = false;
    }
  }

  function finishEnrollment() {
    enrollmentStarted = false;
    secret = '';
    qrDataUrl = '';
    provisioningUri = '';
    confirmCode = '';
    recoveryCodes = null;
  }

  async function doDisable(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';
    try {
      await api.totpDisable(disablePassword, disableCode.trim());
      disableMode = false;
      disablePassword = '';
      disableCode = '';
      await refreshStatus();
    } catch (err: any) {
      error = err.message || 'Disable impossible';
    } finally {
      loading = false;
    }
  }

  function copyRecoveryCodes() {
    if (!recoveryCodes) return;
    navigator.clipboard.writeText(recoveryCodes.join('\n'));
  }

  async function doRegen(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';
    try {
      const res = await api.totpRegenerateRecoveryCodes(regenPassword, regenCode.trim());
      recoveryCodes = res.recovery_codes;
      regenMode = false;
      regenPassword = '';
      regenCode = '';
      await refreshStatus();
    } catch (err: any) {
      error = err.message || 'Régénération impossible';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Sécurité — Academie-IA</title>
</svelte:head>

<div class="max-w-2xl mx-auto px-4 py-6 space-y-6">
  <header>
    <h1 class="text-2xl font-semibold tracking-tight">Sécurité du compte</h1>
    <p class="text-sm text-text-secondary mt-1">Authentification à deux facteurs (TOTP)</p>
  </header>

  {#if !status}
    <p class="text-sm text-text-muted">Chargement...</p>
  {:else if recoveryCodes}
    <!-- Recovery codes one-time display -->
    <div class="bg-surface border border-teacher rounded-xl p-6 space-y-4">
      <h2 class="text-lg font-semibold">⚠️ Codes de récupération</h2>
      <p class="text-sm text-text-secondary">
        Note ces 10 codes <strong>maintenant</strong>. Ils ne seront plus jamais affichés en clair.
        Chaque code n'est utilisable qu'une seule fois pour se connecter en cas de perte de ton appareil TOTP.
      </p>
      <div class="bg-elevated rounded-lg p-4 font-mono text-sm grid grid-cols-2 gap-2">
        {#each recoveryCodes as code}
          <div class="text-center py-1 bg-base rounded">{code}</div>
        {/each}
      </div>
      <div class="flex gap-2">
        <button
          onclick={copyRecoveryCodes}
          class="flex-1 py-2 text-sm bg-elevated border border-border-subtle rounded-lg hover:bg-surface transition-colors"
        >
          Copier
        </button>
        <button
          onclick={finishEnrollment}
          class="flex-1 py-2 text-sm bg-teacher text-white rounded-lg hover:brightness-110 transition-all"
        >
          J'ai noté les codes
        </button>
      </div>
    </div>
  {:else if enrollmentStarted}
    <!-- Enrollment in progress -->
    <div class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
      <h2 class="text-lg font-semibold">Configurer TOTP</h2>
      <ol class="list-decimal list-inside text-sm text-text-secondary space-y-2">
        <li>Ouvre ton application TOTP (Google Authenticator, 1Password, Aegis, Bitwarden, Raivo...)</li>
        <li>Scanne le QR code ci-dessous (ou colle l'URI / le secret manuellement)</li>
        <li>Entre le code à 6 chiffres affiché pour confirmer</li>
      </ol>

      <div class="flex flex-col items-center gap-4 py-4">
        <img src={qrDataUrl} alt="QR code TOTP" class="w-56 h-56 bg-white p-2 rounded" />
        <details class="w-full">
          <summary class="text-xs text-text-muted cursor-pointer hover:text-text-secondary">
            Ne peut pas scanner ? Saisie manuelle
          </summary>
          <div class="mt-2 space-y-2 text-xs">
            <div>
              <span class="text-text-muted">Secret :</span>
              <code class="ml-2 font-mono break-all">{secret}</code>
            </div>
            <div>
              <span class="text-text-muted">URI :</span>
              <code class="ml-2 font-mono break-all">{provisioningUri}</code>
            </div>
          </div>
        </details>
      </div>

      <form onsubmit={confirmEnrollment} class="space-y-3">
        <div>
          <label for="confirm-code" class="block text-sm font-medium text-text-secondary mb-1.5">
            Code de confirmation
          </label>
          <input
            id="confirm-code"
            type="text"
            inputmode="numeric"
            bind:value={confirmCode}
            required
            pattern="[0-9]{'{6}'}"
            maxlength="6"
            autocomplete="one-time-code"
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg
                   text-text-primary text-sm font-mono tracking-widest text-center
                   focus:outline-none focus:border-teacher transition-colors"
            placeholder="123456"
          />
        </div>
        {#if error}<p class="text-sm text-maestro">{error}</p>{/if}
        <button
          type="submit"
          disabled={loading || confirmCode.length !== 6}
          class="w-full py-2.5 bg-teacher text-white text-sm font-medium rounded-lg
                 hover:brightness-110 transition-all disabled:opacity-50"
        >
          {loading ? 'Vérification...' : 'Activer TOTP'}
        </button>
      </form>
    </div>
  {:else if status.enrolled}
    <!-- Already enrolled -->
    <div class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <span class="inline-block w-2 h-2 bg-emerald-500 rounded-full"></span>
            TOTP actif
          </h2>
          {#if status.enrolled_at}
            <p class="text-xs text-text-muted mt-1">
              Activé le {new Date(status.enrolled_at).toLocaleDateString('fr-FR')}
            </p>
          {/if}
        </div>
      </div>
      <div class="text-sm text-text-secondary">
        <p>
          <strong>{status.recovery_codes_remaining}</strong> code{status.recovery_codes_remaining > 1 ? 's' : ''} de récupération restant{status.recovery_codes_remaining > 1 ? 's' : ''}.
        </p>
        {#if status.recovery_codes_remaining < 3}
          <p class="text-maestro mt-1">⚠️ Stock faible — régénère tes codes ci-dessous.</p>
        {/if}
      </div>

      {#if regenMode}
        <form onsubmit={doRegen} class="space-y-3 pt-4 border-t border-border-subtle">
          <p class="text-sm text-text-secondary">
            Génère 10 nouveaux codes (les anciens seront invalidés). Confirme avec ton mot de passe + un code TOTP (ou recovery).
          </p>
          <input type="password" bind:value={regenPassword} required placeholder="Mot de passe" autocomplete="current-password"
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-sm focus:outline-none focus:border-teacher" />
          <input type="text" inputmode="numeric" bind:value={regenCode} required placeholder="Code TOTP ou recovery" autocomplete="one-time-code"
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-sm font-mono text-center focus:outline-none focus:border-teacher" />
          {#if error}<p class="text-sm text-maestro">{error}</p>{/if}
          <div class="flex gap-2">
            <button type="button" onclick={() => { regenMode = false; regenPassword = ''; regenCode = ''; error = ''; }}
              class="flex-1 py-2 text-sm bg-elevated border border-border-subtle rounded-lg">Annuler</button>
            <button type="submit" disabled={loading}
              class="flex-1 py-2 text-sm bg-teacher text-white rounded-lg hover:brightness-110 disabled:opacity-50">
              {loading ? '...' : 'Régénérer'}
            </button>
          </div>
        </form>
      {:else if !disableMode}
        <div class="flex gap-3">
          <button onclick={() => regenMode = true} class="text-sm text-teacher hover:underline">
            Régénérer mes recovery codes
          </button>
          <span class="text-text-muted">·</span>
          <button onclick={() => disableMode = true} class="text-sm text-maestro hover:underline">
            Désactiver TOTP
          </button>
        </div>
      {:else}
        <form onsubmit={doDisable} class="space-y-3 pt-4 border-t border-border-subtle">
          <p class="text-sm text-text-secondary">
            Confirme ton mot de passe + un code TOTP (ou recovery) pour désactiver.
          </p>
          <input
            type="password"
            bind:value={disablePassword}
            required
            placeholder="Mot de passe"
            autocomplete="current-password"
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-sm focus:outline-none focus:border-teacher"
          />
          <input
            type="text"
            inputmode="numeric"
            bind:value={disableCode}
            required
            placeholder="Code TOTP ou recovery"
            autocomplete="one-time-code"
            class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-sm font-mono text-center focus:outline-none focus:border-teacher"
          />
          {#if error}<p class="text-sm text-maestro">{error}</p>{/if}
          <div class="flex gap-2">
            <button
              type="button"
              onclick={() => { disableMode = false; disablePassword = ''; disableCode = ''; error = ''; }}
              class="flex-1 py-2 text-sm bg-elevated border border-border-subtle rounded-lg"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={loading}
              class="flex-1 py-2 text-sm bg-maestro text-white rounded-lg hover:brightness-110 disabled:opacity-50"
            >
              {loading ? '...' : 'Désactiver'}
            </button>
          </div>
        </form>
      {/if}
    </div>
  {:else}
    <!-- Not enrolled — invite to enroll -->
    <div class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
      <h2 class="text-lg font-semibold">Activer la double authentification</h2>
      <p class="text-sm text-text-secondary">
        L'authentification à deux facteurs (2FA) ajoute une couche de sécurité supplémentaire à
        ton compte. À chaque connexion, après ton mot de passe, tu devras saisir un code à 6
        chiffres généré par une application TOTP installée sur ton téléphone.
      </p>
      <p class="text-sm text-text-secondary">
        Apps recommandées (gratuites, open-source) : <strong>Aegis</strong> (Android),
        <strong>Raivo</strong> (iOS), <strong>Bitwarden</strong>, <strong>1Password</strong>,
        Google Authenticator.
      </p>

      {#if error}<p class="text-sm text-maestro">{error}</p>{/if}

      <button
        onclick={startEnrollment}
        disabled={loading}
        class="px-4 py-2.5 bg-teacher text-white text-sm font-medium rounded-lg
               hover:brightness-110 transition-all disabled:opacity-50"
      >
        {loading ? 'Préparation...' : 'Activer 2FA'}
      </button>
    </div>
  {/if}

  <!-- A4b polish — Passkeys placeholder (WebAuthn Phase 2) -->
  <div class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3 opacity-70">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        🔑 Passkeys (WebAuthn)
      </h2>
      <span class="text-xs px-2 py-0.5 bg-elevated rounded-full text-text-muted">Bientôt</span>
    </div>
    <p class="text-sm text-text-secondary">
      Les Passkeys (WebAuthn) remplaceront le mot de passe + TOTP par une clé cryptographique
      stockée sur ton appareil (Touch ID, Windows Hello, clé YubiKey, etc.). Plus rapide,
      plus sûr, anti-phishing.
    </p>
    <p class="text-xs text-text-muted">
      Activation prévue Phase 2 post-beta (cf. ADR-001 décision #7).
    </p>
    <button disabled
      class="px-4 py-2 text-sm bg-elevated border border-border-subtle rounded-lg cursor-not-allowed text-text-muted"
      title="WebAuthn non activé">
      Ajouter une Passkey
    </button>
  </div>

  <p class="text-xs text-text-muted text-center pt-4">
    <a href="/" class="hover:text-text-secondary transition-colors">← Retour à l'accueil</a>
  </p>
</div>
