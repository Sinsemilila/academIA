<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';

  let username = $state('');
  let exporting = $state(false);
  let deleting = $state(false);
  let error = $state('');
  let success = $state('');

  // Delete modal state
  let showDeleteModal = $state(false);
  let deleteStep = $state<1 | 2>(1);
  let confirmInput = $state('');

  onMount(async () => {
    try {
      const me = await api.me();
      username = me.username;
    } catch {
      goto('/login');
    }
  });

  async function downloadExport() {
    exporting = true;
    error = '';
    success = '';
    try {
      const filename = await api.exportMyData();
      success = `Export téléchargé : ${filename}`;
    } catch (err: any) {
      error = err.message || 'Erreur export';
    } finally {
      exporting = false;
    }
  }

  function openDeleteModal() {
    showDeleteModal = true;
    deleteStep = 1;
    confirmInput = '';
    error = '';
  }

  function closeDeleteModal() {
    if (deleting) return;
    showDeleteModal = false;
  }

  async function confirmDelete() {
    if (confirmInput !== username) {
      error = 'Le nom d\'utilisateur ne correspond pas.';
      return;
    }
    deleting = true;
    error = '';
    try {
      await api.deleteMyAccount(confirmInput);
      // Account gone, cookies cleared by backend → redirect login
      if (typeof window !== 'undefined') {
        window.location.href = '/login?deleted=1';
      }
    } catch (err: any) {
      error = err.message || 'Suppression échouée';
      deleting = false;
    }
  }
</script>

<svelte:head>
  <title>Confidentialité — Académie-IA</title>
</svelte:head>

<div class="max-w-2xl mx-auto space-y-6 py-4">
  <div class="flex items-center gap-3">
    <a
      href="/profile"
      class="w-8 h-8 flex items-center justify-center rounded-lg bg-elevated text-text-secondary hover:text-text-primary hover:bg-border-subtle transition-all"
      aria-label="Retour"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </a>
    <h1 class="text-2xl font-semibold">Confidentialité & RGPD</h1>
  </div>

  {#if success}
    <div class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-sm text-emerald-300">
      {success}
    </div>
  {/if}
  {#if error}
    <div class="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-sm text-rose-300">
      {error}
    </div>
  {/if}

  <!-- Section : Mes données -->
  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Mes données</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Télécharge une copie complète de toutes les données associées à ton compte
      au format JSON : profil, conversations, scores, historique, sessions actives.
      Conforme RGPD <strong>art. 15 (accès)</strong> et <strong>art. 20 (portabilité)</strong>.
    </p>
    <button
      type="button"
      onclick={downloadExport}
      disabled={exporting}
      class="px-4 py-2 bg-blue-500/15 border border-blue-500/40 text-blue-200 text-sm font-medium rounded-lg hover:bg-blue-500/25 transition disabled:opacity-50"
    >
      {exporting ? 'Préparation…' : '⬇ Télécharger mes données'}
    </button>
    <p class="text-xs text-text-muted">
      Limite : 3 exports par 5 minutes. Le fichier exclut le hash de mot de passe et le secret TOTP.
    </p>
  </section>

  <!-- Section : Sous-processeurs -->
  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Sous-processeurs</h2>
    <p class="text-sm text-text-secondary">
      Tes données sont traitées par les fournisseurs suivants (tous certifiés DPF) :
    </p>
    <ul class="text-sm text-text-secondary space-y-1 list-disc pl-5">
      <li>OpenAI — modèles LLM principaux (~99% des appels chat)</li>
      <li>Groq — fallback LLM (~1% des appels)</li>
      <li>Cloudflare — reverse proxy + protection DDoS</li>
    </ul>
    <p class="text-sm text-text-secondary">
      <a href="/legal/ia" class="underline">Voir le détail des sous-processeurs et opt-outs ↗</a>
    </p>
  </section>

  <!-- Section : Mes droits -->
  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Mes droits</h2>
    <ul class="text-sm text-text-secondary space-y-1 list-disc pl-5">
      <li><strong>Accès & portabilité</strong> — bouton "Télécharger mes données" ci-dessus</li>
      <li><strong>Rectification</strong> — modifie ton profil dans <a href="/profile" class="underline">Profil</a></li>
      <li><strong>Effacement</strong> — supprime ton compte ci-dessous</li>
      <li><strong>Limitation, opposition, autres droits</strong> — contacte sinseproduction@gmail.com</li>
      <li><strong>Réclamation</strong> — <a href="https://www.cnil.fr/fr/plaintes" target="_blank" rel="noopener" class="underline">CNIL ↗</a></li>
    </ul>
  </section>

  <!-- Section : Suppression compte -->
  <section class="bg-surface border border-rose-500/30 rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg text-rose-300">Supprimer mon compte</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      <strong>Action irréversible.</strong> Cette opération supprime immédiatement
      et définitivement ton compte et toutes les données associées (profil,
      conversations, scores, sessions). Aucune récupération n'est possible.
    </p>
    <p class="text-xs text-text-muted">
      Recommandation : télécharge une copie de tes données avant suppression.
    </p>
    <button
      type="button"
      onclick={openDeleteModal}
      class="px-4 py-2 bg-rose-500/15 border border-rose-500/40 text-rose-200 text-sm font-medium rounded-lg hover:bg-rose-500/25 transition"
    >
      🗑 Supprimer mon compte
    </button>
  </section>
</div>

{#if showDeleteModal}
  <div
    role="dialog"
    aria-modal="true"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
  >
    <div class="bg-surface border border-border-subtle rounded-xl shadow-2xl max-w-md w-full p-6 space-y-4">
      {#if deleteStep === 1}
        <h3 class="text-lg font-semibold text-rose-300">Confirmer la suppression</h3>
        <div class="space-y-2 text-sm text-text-secondary">
          <p>Tu es sur le point de supprimer définitivement :</p>
          <ul class="list-disc pl-5 space-y-1">
            <li>Ton compte <strong>{username}</strong> et tes paramètres</li>
            <li>Toutes tes conversations avec les agents</li>
            <li>Ton profil pédagogique, scores, niveau CEFR, streaks, XP</li>
            <li>L'historique de tes sessions et de tes erreurs</li>
            <li>Ta configuration MFA si activée</li>
          </ul>
          <p class="pt-2 text-rose-300 font-medium">
            Cette opération est irréversible et immédiate.
          </p>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onclick={closeDeleteModal}
            class="px-4 py-2 text-sm rounded-lg bg-surface-hover text-text-secondary hover:bg-border-subtle transition"
          >
            Annuler
          </button>
          <button
            type="button"
            onclick={() => { deleteStep = 2; }}
            class="px-4 py-2 text-sm rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-200 hover:bg-rose-500/30 transition"
          >
            Je comprends, continuer
          </button>
        </div>
      {:else}
        <h3 class="text-lg font-semibold text-rose-300">Dernière confirmation</h3>
        <p class="text-sm text-text-secondary">
          Pour confirmer, retape exactement ton nom d'utilisateur :
          <code class="px-1.5 py-0.5 bg-elevated rounded text-text-primary">{username}</code>
        </p>
        <input
          type="text"
          bind:value={confirmInput}
          disabled={deleting}
          autocomplete="off"
          autocapitalize="off"
          spellcheck="false"
          placeholder="Retape ton nom d'utilisateur"
          class="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:border-rose-500/50"
        />
        {#if error}
          <p class="text-sm text-rose-300">{error}</p>
        {/if}
        <div class="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onclick={closeDeleteModal}
            disabled={deleting}
            class="px-4 py-2 text-sm rounded-lg bg-surface-hover text-text-secondary hover:bg-border-subtle transition disabled:opacity-50"
          >
            Annuler
          </button>
          <button
            type="button"
            onclick={confirmDelete}
            disabled={deleting || confirmInput !== username}
            class="px-4 py-2 text-sm rounded-lg bg-rose-500 text-black font-medium hover:bg-rose-400 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {deleting ? 'Suppression…' : 'Supprimer définitivement'}
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}
