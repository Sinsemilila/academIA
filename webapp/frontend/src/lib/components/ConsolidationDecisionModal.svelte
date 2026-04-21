<script lang="ts">
  // Session 36 — Modal presenting the bienveillant choice after mini-exam.
  let {
    open = false,
    domain,
    message = '',
    qcmLevel = '',
    proposedLevel = '',
    kind = 'upgrade',
    onDecided,
  } = $props<{
    open?: boolean;
    domain: string;
    message?: string;
    qcmLevel?: string;
    proposedLevel?: string;
    kind?: 'upgrade' | 'downgrade' | 'validation';
    onDecided?: (payload: { choice: string }) => void;
  }>();

  let submitting = $state(false);
  let errorMsg = $state('');

  async function submit(choice: 'accept_new' | 'stay_current') {
    submitting = true;
    errorMsg = '';
    try {
      const tok = localStorage.getItem('token') ?? '';
      const r = await fetch(`/api/consolidation/decide/${domain}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ choice }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      onDecided?.({ choice });
    } catch (e: any) {
      errorMsg = e?.message ?? 'Erreur réseau';
    } finally {
      submitting = false;
    }
  }

  function ack() { onDecided?.({ choice: 'ack' }); }
</script>

{#if open}
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
  <div class="bg-surface text-text-primary border border-border-subtle rounded-2xl shadow-xl max-w-xl w-full p-6">
    <h2 class="text-lg font-semibold mb-3 text-text-primary">
      {#if kind === 'validation'}Niveau confirmé{:else if kind === 'upgrade'}Progression détectée{:else}Calibration du niveau{/if}
    </h2>
    <p class="text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">{message}</p>

    {#if errorMsg}
      <p class="mt-3 text-red-500 text-sm">{errorMsg}</p>
    {/if}

    <div class="mt-5 flex flex-wrap gap-3 justify-end">
      {#if kind === 'validation'}
        <button class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:brightness-110 transition-all"
                onclick={ack} disabled={submitting}>Super, on continue</button>
      {:else if kind === 'upgrade'}
        <button class="px-4 py-2 bg-elevated text-text-primary border border-border-subtle rounded-lg text-sm font-medium disabled:opacity-50 hover:brightness-110 transition-all"
                onclick={() => submit('stay_current')} disabled={submitting}>
          Rester en {qcmLevel} pour consolider
        </button>
        <button class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:brightness-110 transition-all"
                onclick={() => submit('accept_new')} disabled={submitting}>
          Passer en {proposedLevel}
        </button>
      {:else}
        <button class="px-4 py-2 bg-elevated text-text-primary border border-border-subtle rounded-lg text-sm font-medium disabled:opacity-50 hover:brightness-110 transition-all"
                onclick={() => submit('stay_current')} disabled={submitting}>
          Rester en {qcmLevel}
        </button>
        <button class="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:brightness-110 transition-all"
                onclick={() => submit('accept_new')} disabled={submitting}>
          Repartir sur {proposedLevel}
        </button>
      {/if}
    </div>
  </div>
</div>
{/if}
