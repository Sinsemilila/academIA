<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import ItemLikert5 from './ItemLikert5.svelte';
  import ItemChoiceSingle from './ItemChoiceSingle.svelte';
  import ItemChoiceSingleRich from './ItemChoiceSingleRich.svelte';
  import ItemChoiceMulti from './ItemChoiceMulti.svelte';
  import ItemTextShort from './ItemTextShort.svelte';
  import ItemLikertGroup3 from './ItemLikertGroup3.svelte';

  let { domain, agentName = '', onComplete } = $props<{
    domain: string;
    agentName?: string;
    onComplete: () => void;
  }>();

  type Item = {
    id: string;
    order: number;
    block?: string;
    construct: string;
    format: string;
    required: boolean;
    conditional?: { rule: string; feature_flag?: string };
    prompt?: { fr: string };
    prompt_group?: { fr: string };
    placeholder_fr?: string;
    skip_label_fr?: string;
    options?: Array<{ id: string; label_fr: string }>;
    sub_items?: Array<{ id: string; prompt_fr: string }>;
    scale?: { labels_fr: string[]; values: number[] };
    sentence_to_translate?: { fr: string };
    min_chars?: number;
    max_chars?: number;
    min_selected?: number;
    max_selected?: number;
    db_variable: string;
  };

  let content = $state<any>(null);
  let step = $state(0); // 0 = intro, 1..N = items, N+1 = summary, N+2 = sending
  let answers = $state<Record<string, any>>({});
  let loading = $state(true);
  let submitting = $state(false);
  let error = $state<string | null>(null);
  let submitResult = $state<any>(null);

  const draftKey = $derived(`academie:qcm:draft:${domain}`);
  const sessionKey = $derived(`academie:onboarding:session:${domain}`);

  // Session 43 P5 — onboarding telemetry
  let sessionId = '';
  let completed = false;
  let lastLoggedStep = -1;

  function genUUID(): string {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
    // RFC4122 v4 fallback
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function currentStepId(): string {
    if (step === 0) return 'intro';
    if (step > 0 && step <= totalSteps) return visibleItems[step - 1]?.id ?? `step_${step}`;
    if (step === totalSteps + 1) return 'summary';
    return `step_${step}`;
  }

  onMount(async () => {
    try {
      content = await api.getOnboardingContent(domain);
      // Restore draft + telemetry session_id
      if (typeof window !== 'undefined') {
        sessionId = localStorage.getItem(sessionKey) || '';
        if (!sessionId) {
          sessionId = genUUID();
          localStorage.setItem(sessionKey, sessionId);
        }
        const raw = localStorage.getItem(draftKey);
        if (raw) {
          try {
            const parsed = JSON.parse(raw);
            if (parsed.answers && typeof parsed.step === 'number') {
              answers = parsed.answers;
              step = parsed.step;
            }
          } catch {}
        }

        // Abort beacon : fires when the tab closes/reloads before complete.
        // sendBeacon works during unload where fetch() is unreliable.
        const onBeforeUnload = () => {
          if (completed || !sessionId) return;
          const payload = JSON.stringify({
            session_id: sessionId,
            domain,
            event: 'abort',
            step_id: currentStepId(),
            step_order: step,
            total_steps: totalSteps,
          });
          if (navigator.sendBeacon) {
            const blob = new Blob([payload], { type: 'application/json' });
            navigator.sendBeacon('/api/telemetry/onboarding-event', blob);
          }
        };
        window.addEventListener('beforeunload', onBeforeUnload);
      }
    } catch (e: any) {
      error = e?.message ?? 'Erreur de chargement du questionnaire';
    } finally {
      loading = false;
    }
  });

  // Log step_enter on each step change (dedup on lastLoggedStep).
  $effect(() => {
    if (loading || !content || !sessionId) return;
    if (step === lastLoggedStep) return;
    lastLoggedStep = step;
    api.postOnboardingTelemetry({
      session_id: sessionId,
      domain,
      event: 'step_enter',
      step_id: currentStepId(),
      step_order: step,
      total_steps: totalSteps,
    });
  });

  // Filter visible items (conditional ones skipped if rule fails)
  const visibleItems = $derived.by(() => {
    if (!content?.items) return [] as Item[];
    return (content.items as Item[]).filter((it) => {
      if (!it.conditional) return true;
      // Only support the one rule we ship in v1
      if (it.conditional.rule === 'max(cefr_comprehension, cefr_production) >= B1') {
        const c = answers['cefr_comprehension'];
        const p = answers['cefr_production'];
        const order = ['A1','A2','B1','B2','C1','C2'];
        if (!c || !p) return false;
        return order.indexOf(c) >= 2 || order.indexOf(p) >= 2;
      }
      return true;
    });
  });

  const totalSteps = $derived(visibleItems.length);
  const currentItem = $derived(step >= 1 && step <= totalSteps ? visibleItems[step - 1] : null);
  const isIntro = $derived(step === 0);
  const isSummary = $derived(step === totalSteps + 1);

  function persistDraft() {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(draftKey, JSON.stringify({ step, answers }));
    } catch {}
  }

  function clearDraft() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(draftKey);
  }

  $effect(() => {
    if (!loading && content) persistDraft();
  });

  function currentItemValid(): boolean {
    if (!currentItem) return true;
    const v = answers[currentItem.db_variable] ?? answers[currentItem.id];
    if (!currentItem.required) return true;
    if (currentItem.format === 'text_short') {
      const s = (v ?? '').toString().trim();
      const min = currentItem.min_chars ?? 0;
      return s.length >= min;
    }
    if (currentItem.format === 'choice_multi') {
      const arr = Array.isArray(v) ? v : [];
      const min = currentItem.min_selected ?? 1;
      return arr.length >= min;
    }
    if (currentItem.format === 'likert_group_3') {
      const obj = (v && typeof v === 'object') ? v : {};
      return (currentItem.sub_items ?? []).every((si) => typeof obj[si.id] === 'number');
    }
    return v !== undefined && v !== null && v !== '';
  }

  function next() {
    if (!currentItemValid()) return;
    step++;
  }

  function prev() {
    if (step > 0) step--;
  }

  function keyFor(it: Item) {
    // For single-value items, store under db_variable for easy lookup.
    // For group items (FLA), store the full object under db_variable.
    return it.db_variable || it.id;
  }

  function updateAnswer(it: Item, value: any) {
    answers = { ...answers, [keyFor(it)]: value };
  }

  async function submit() {
    if (!content) return;
    submitting = true;
    error = null;
    try {
      const universal_block = {
        self_efficacy: answers['self_efficacy'],
        mindset: answers['mindset'],
        goal_text: (answers['goal_text'] ?? '').toString().trim(),
        autonomy_pref: answers['autonomy_pref'],
        engagement_pattern: answers['engagement_pattern'],
      };
      const domain_level: any = {
        cefr_comprehension: answers['cefr_comprehension'],
        cefr_production: answers['cefr_production'],
      };
      if (typeof answers['probe_answer'] === 'string' && answers['probe_answer'].trim().length > 0) {
        domain_level.probe_answer = answers['probe_answer'];
      } else {
        domain_level.probe_answer = null;
      }
      const domain_motivation = {
        ideal_l2_self_tags: answers['ideal_l2_self_tags'] ?? [],
        fla_items_raw: answers['fla_items_raw'] ?? {},
      };
      const payload = { universal_block, domain_level, domain_motivation };
      const res = await api.submitLearnerProfile(domain, payload);
      submitResult = res;
      completed = true;
      api.postOnboardingTelemetry({
        session_id: sessionId,
        domain,
        event: 'complete',
        step_id: 'summary',
        step_order: step,
        total_steps: totalSteps,
      });
      if (typeof window !== 'undefined') localStorage.removeItem(sessionKey);
      clearDraft();
      // Small delay so user sees the summary once before chat opens
      setTimeout(() => onComplete(), 1200);
    } catch (e: any) {
      error = e?.message ?? 'Erreur d\u2019envoi';
    } finally {
      submitting = false;
    }
  }

  function progressPct() {
    if (totalSteps === 0) return 0;
    if (isIntro) return 0;
    if (isSummary) return 100;
    return Math.round(((step) / (totalSteps + 1)) * 100);
  }
</script>

<!-- Modal backdrop : no close button (bloquant) -->
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
     role="dialog" aria-modal="true" aria-labelledby="qcm-title">
  <div class="relative w-full max-w-2xl bg-surface border border-border-subtle rounded-2xl shadow-2xl overflow-hidden">
    {#if loading}
      <div class="p-12 text-center text-text-secondary">Chargement…</div>
    {:else if error && !content}
      <div class="p-8 text-center">
        <p class="text-red-400 mb-4">{error}</p>
      </div>
    {:else}
      <!-- Progress bar -->
      <div class="h-1 bg-background-subtle">
        <div class="h-full bg-teacher transition-all duration-300" style:width={`${progressPct()}%`}></div>
      </div>

      <div class="px-8 py-6 max-h-[80vh] overflow-y-auto">

        {#if isIntro}
          <!-- Intro screen -->
          <h2 id="qcm-title" class="text-2xl font-semibold mb-3">Avant de commencer avec {agentName || 'ton tuteur'}</h2>
          <p class="text-text-secondary mb-6">
            On a besoin de 2-3 minutes pour calibrer le tuteur à ta façon d'apprendre.
            Aucune bonne ou mauvaise réponse. Tes réponses sont stockées localement
            et utilisées pour personnaliser tes sessions.
          </p>
          <ul class="text-sm text-text-secondary space-y-2 mb-8">
            <li>• 8 questions rapides (90 s à 3 min)</li>
            <li>• Niveau auto-évalué en {content.language_display_fr ?? 'la langue cible'}</li>
            <li>• Motivation et style d'apprentissage</li>
          </ul>
          <div class="flex justify-end">
            <button
              onclick={() => (step = 1)}
              class="px-6 py-3 rounded-xl bg-teacher text-white font-medium hover:brightness-110 transition"
            >
              Commencer
            </button>
          </div>

        {:else if currentItem}
          <!-- Current item -->
          <div class="mb-2 text-xs uppercase tracking-wider text-text-tertiary">
            Question {step} / {totalSteps}
          </div>

          {#if currentItem.format === 'likert_5'}
            <ItemLikert5
              item={currentItem}
              value={answers[keyFor(currentItem)]}
              onchange={(v: any) => updateAnswer(currentItem, v)}
            />
          {:else if currentItem.format === 'choice_single'}
            <ItemChoiceSingle
              item={currentItem}
              value={answers[keyFor(currentItem)]}
              onchange={(v: any) => updateAnswer(currentItem, v)}
            />
          {:else if currentItem.format === 'choice_single_rich'}
            <ItemChoiceSingleRich
              item={currentItem}
              value={answers[keyFor(currentItem)]}
              onchange={(v: any) => updateAnswer(currentItem, v)}
            />
          {:else if currentItem.format === 'choice_multi'}
            <ItemChoiceMulti
              item={currentItem}
              value={answers[keyFor(currentItem)]}
              onchange={(v: any) => updateAnswer(currentItem, v)}
            />
          {:else if currentItem.format === 'text_short'}
            <ItemTextShort
              item={currentItem}
              probeHint={currentItem.id === 'lang_probe_discriminant_1' ? content.probe : undefined}
              value={answers[keyFor(currentItem)]}
              onchange={(v: any) => updateAnswer(currentItem, v)}
            />
          {:else if currentItem.format === 'likert_group_3'}
            <ItemLikertGroup3
              item={currentItem}
              value={answers[keyFor(currentItem)]}
              onchange={(v: any) => updateAnswer(currentItem, v)}
            />
          {/if}

          <div class="mt-8 flex justify-between items-center">
            <button
              onclick={prev}
              disabled={step === 1}
              class="px-4 py-2 text-sm text-text-secondary hover:text-text-primary disabled:opacity-30"
            >
              ← Précédent
            </button>
            <button
              onclick={next}
              disabled={!currentItemValid()}
              class="px-6 py-2 rounded-lg bg-teacher text-white font-medium hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Suivant →
            </button>
          </div>

        {:else if isSummary}
          <!-- Summary / submission screen -->
          <h2 class="text-2xl font-semibold mb-4">Ton profil est prêt</h2>
          {#if !submitting && !submitResult}
            <div class="space-y-3 text-sm text-text-secondary mb-6">
              <p>On va passer tes réponses au tuteur. Tu peux revenir en arrière si tu veux modifier quelque chose.</p>
            </div>
            {#if error}<p class="text-red-400 text-sm mb-4">{error}</p>{/if}
            <div class="flex justify-between items-center">
              <button onclick={prev} class="text-sm text-text-secondary hover:text-text-primary">
                ← Modifier
              </button>
              <button
                onclick={submit}
                class="px-6 py-3 rounded-xl bg-teacher text-white font-medium hover:brightness-110 transition"
              >
                Envoyer et démarrer
              </button>
            </div>
          {:else if submitting}
            <p class="text-text-secondary">Enregistrement…</p>
          {:else if submitResult}
            <div class="p-4 rounded-lg bg-background-subtle mb-4">
              <p class="text-sm text-text-secondary">Niveau estimé de départ :</p>
              <p class="text-2xl font-semibold">{submitResult.cefr_placement}</p>
              <p class="text-xs text-text-tertiary mt-1">Style tuteur : {submitResult.tutor_style}</p>
            </div>
            <p class="text-sm text-text-secondary">Le chat va s'ouvrir dans un instant…</p>
          {/if}
        {/if}

      </div>
    {/if}
  </div>
</div>
