<script lang="ts">
  // Session 36 — 8-item mini-exam wizard.
  let {
    open = false,
    domain,
    onDone,
  } = $props<{
    open?: boolean;
    domain: string;
    onDone?: (payload: any) => void;
  }>();

  type Item = {
    id: string;
    type: 'fill' | 'choice' | 'transform' | 'produce_short';
    prompt: string;
    options?: string[];
    concept_code?: string;
  };
  let items = $state<Item[]>([]);
  let targetLevel = $state('');
  let idx = $state(0);
  let answers = $state<Record<string, string>>({});
  let loading = $state(true);
  let submitting = $state(false);
  let errorMsg = $state('');

  $effect(() => {
    if (open && items.length === 0 && !loading) loadExam();
  });

  $effect(() => {
    if (open && items.length === 0) loadExam();
  });

  async function loadExam() {
    loading = true;
    errorMsg = '';
    try {
      const tok = localStorage.getItem('token') ?? '';
      const r = await fetch(`/api/consolidation/mini-exam/start/${domain}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${tok}` },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      items = data.items;
      targetLevel = data.target_level;
      idx = 0;
      answers = {};
    } catch (e: any) {
      errorMsg = e?.message ?? 'Erreur de chargement';
    } finally {
      loading = false;
    }
  }

  function next() {
    if (idx < items.length - 1) idx += 1;
  }

  async function submit() {
    submitting = true;
    errorMsg = '';
    try {
      const tok = localStorage.getItem('token') ?? '';
      const r = await fetch(`/api/consolidation/mini-exam/submit/${domain}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({
          target_level: targetLevel,
          answers: items.map(it => ({ id: it.id, answer: answers[it.id] ?? '' })),
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      onDone?.(data);
    } catch (e: any) {
      errorMsg = e?.message ?? "Erreur d'envoi";
    } finally {
      submitting = false;
    }
  }

  function onKeyInput(e: KeyboardEvent) {
    if (e.key !== 'Enter' || e.shiftKey) return;
    e.preventDefault();
    if (!canNext || submitting) return;
    if (isLast) submit();
    else next();
  }

  let current = $derived(items[idx]);
  let progress = $derived(items.length ? Math.round(((idx + 1) / items.length) * 100) : 0);
  let canNext = $derived(current ? (answers[current.id] ?? '').trim().length > 0 : false);
  let isLast = $derived(items.length > 0 && idx === items.length - 1);
</script>

{#if open}
<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
  <div class="bg-surface text-text-primary border border-border-subtle rounded-2xl shadow-xl max-w-xl w-full p-6">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg font-semibold text-text-primary">Petit test de consolidation ({targetLevel || '…'})</h2>
      <span class="text-xs text-text-muted">{items.length ? `${idx + 1} / ${items.length}` : ''}</span>
    </div>

    {#if loading}
      <p class="text-text-secondary">Chargement des questions…</p>
    {:else if errorMsg}
      <p class="text-red-500 text-sm">{errorMsg}</p>
      <button class="mt-3 px-4 py-2 bg-elevated text-text-primary rounded-lg text-sm border border-border-subtle" onclick={loadExam}>Réessayer</button>
    {:else if current}
      <div class="h-1 bg-elevated rounded-full mb-4"><div class="h-1 bg-emerald-500 rounded-full" style="width: {progress}%"></div></div>
      <p class="text-text-primary text-sm leading-relaxed mb-4 whitespace-pre-wrap">{current.prompt}</p>

      {#if current.type === 'choice' && current.options}
        <div class="flex flex-col gap-2">
          {#each current.options as opt}
            <label class="flex items-center gap-2 cursor-pointer px-3 py-2 border rounded-lg hover:bg-elevated {answers[current.id] === opt ? 'border-emerald-500 bg-emerald-500/10' : 'border-border-subtle'}">
              <input type="radio" name={current.id} value={opt} bind:group={answers[current.id]} class="sr-only" />
              <span class="text-sm text-text-primary">{opt}</span>
            </label>
          {/each}
        </div>
      {:else if current.type === 'produce_short'}
        <textarea rows="3" class="w-full px-3 py-2 border border-border-subtle rounded-lg text-sm text-text-primary bg-elevated placeholder:text-text-muted"
                  bind:value={answers[current.id]} placeholder="Ta réponse… (Shift+Entrée pour nouvelle ligne)" onkeydown={onKeyInput}></textarea>
      {:else}
        <input type="text" class="w-full px-3 py-2 border border-border-subtle rounded-lg text-sm text-text-primary bg-elevated placeholder:text-text-muted"
               bind:value={answers[current.id]} placeholder="Ta réponse…" onkeydown={onKeyInput} autofocus />
      {/if}

      <div class="mt-5 flex justify-end gap-2">
        {#if isLast}
          <button class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                  onclick={submit} disabled={!canNext || submitting}>
            {submitting ? 'Envoi…' : 'Terminer le test'}
          </button>
        {:else}
          <button class="px-4 py-2 bg-teacher text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:brightness-110 transition-all"
                  onclick={next} disabled={!canNext}>Suivant</button>
        {/if}
      </div>
    {/if}
  </div>
</div>
{/if}
