<script lang="ts">
  import { page } from '$app/state';
  import { onMount, tick } from 'svelte';
  import { api } from '$lib/api';
  import { agents, QCM_ONBOARDING_ENABLED } from '$lib/config';
  import AgentFlag from '$lib/components/AgentFlag.svelte';
  import ChatBubble from '$lib/components/chat/ChatBubble.svelte';
  import ChatInput from '$lib/components/chat/ChatInput.svelte';
  import TypingIndicator from '$lib/components/chat/TypingIndicator.svelte';
  import OnboardingModal from '$lib/components/onboarding/OnboardingModal.svelte';
  import MiniExamModal from '$lib/components/MiniExamModal.svelte';
  import ConsolidationDecisionModal from '$lib/components/ConsolidationDecisionModal.svelte';
  import AIBanner from '$lib/components/AIBanner.svelte';
  import RGPDDisclaimer from '$lib/components/compta/RGPDDisclaimer.svelte';
  import { toastXP, toastError, toastSuccess } from '$lib/stores/toasts';

  // Session 37 — extended role vocabulary to support persistent consolidation
  // system bubbles interleaved with Dify messages by timestamp.
  interface Message {
    role: 'user' | 'assistant' | 'system_consolidation';
    content: string;
    timestamp?: string;  // ISO8601 — set on consolidation events for merge ordering
  }

  const agent = $derived(agents.find(a => a.slug === page.params.agent));

  let messages = $state<Message[]>([]);
  let streaming = $state(false);
  let showTyping = $state(false);
  let conversationId = $state<string | null>(null);
  let messagesContainer: HTMLDivElement;
  let streamingIdx = -1;
  let loadingHistory = $state(true);

  // Timer (tracks current sitting, not total conversation)
  let sessionStartTime = $state<number | null>(null);
  let timerDisplay = $state('0:00');
  let timerInterval: ReturnType<typeof setInterval> | null = null;
  let lastActivity = $state(Date.now());

  // ── Mode toggle ──────────────────────────────────
  let currentMode = $state<string>('structure');
  let showModeModal = $state(false);
  let pendingMode = $state<string>('');

  // ── Quiz state ───────────────────────────────────
  let quizActive = $state(false);
  let quizQuestionNum = $state(0);
  let quizTotalQuestions = $state(10);
  let quizConcepts = $state<Array<{key: string, mode: string}>>([]);
  let quizWaitingForNext = $state(false);
  let showQuizConfirm = $state(false);
  let quizLoading = $state(false);

  // Extra inputs to send with next message
  let pendingInputs = $state<Record<string, string>>({});

  // QCM onboarding gate (Sprint 5 Phase 5) — blocks chat on 1st visit per domain.
  let showOnboardingModal = $state(false);

  // Session 36 — Consolidation modals (mini-exam + decision).
  let showMiniExamModal = $state(false);
  let showDecisionModal = $state(false);
  let decisionKind = $state<'upgrade' | 'downgrade' | 'validation'>('validation');
  let decisionMessage = $state('');
  let decisionQcmLevel = $state('');
  let decisionProposedLevel = $state('');

  async function checkConsolidationState() {
    if (!agent?.domain) return;
    try {
      const data = await api.consolidationState(agent.domain);
      if (data.niveau_status === 'calibration_en_cours' && data.pending) {
        // Open mini-exam if awaiting_user not yet set; else directly show decision
        if (data.pending.awaiting_user) {
          // Mini-exam already done, user has decision pending
          openDecisionFromPending(data.pending);
        } else {
          showMiniExamModal = true;
        }
      }
    } catch (e) {
      console.warn('Could not check consolidation:', e);
    }
  }

  function openDecisionFromPending(pending: any) {
    decisionQcmLevel = pending.qcm;
    decisionProposedLevel = pending.observed;
    const qi = ['A1','A2','B1','B2','C1','C2'].indexOf(pending.qcm);
    const oi = ['A1','A2','B1','B2','C1','C2'].indexOf(pending.observed);
    decisionKind = oi > qi ? 'upgrade' : 'downgrade';
    decisionMessage = pending.message ?? '';
    showDecisionModal = true;
  }

  function onMiniExamDone(data: any) {
    showMiniExamModal = false;
    if (data.outcome === 'awaiting_user_decision') {
      decisionQcmLevel = data.qcm_level;
      decisionProposedLevel = data.observed_level;
      const qi = ['A1','A2','B1','B2','C1','C2'].indexOf(data.qcm_level);
      const oi = ['A1','A2','B1','B2','C1','C2'].indexOf(data.observed_level);
      decisionKind = oi > qi ? 'upgrade' : 'downgrade';
      decisionMessage = data.message ?? '';
      showDecisionModal = true;
    } else if (data.outcome === 'auto_validate') {
      decisionKind = 'validation';
      decisionMessage = data.message ?? '';
      decisionQcmLevel = data.final_level;
      decisionProposedLevel = data.final_level;
      showDecisionModal = true;
      // Session 37 — backend already wrote the system bubble ; refresh thread
      // so it appears right after the decision modal acknowledges the outcome.
      if (conversationId) loadMessages(conversationId).catch(() => {});
    }
  }

  function onDecisionDecided() {
    showDecisionModal = false;
    // Session 37 — after decision closes, re-fetch messages + events so the
    // persistent system bubble appears immediately in the thread.
    if (conversationId) loadMessages(conversationId).catch(() => {});
  }

  async function loadChatState() {
    const isComptaAgent = agent?.slug === 'maitre_comptable';
    try {
      // S57 — skip getProfile pour Maître Comptable (compta_fr non valide ISO 2-letter, returns 422).
      if (!isComptaAgent) {
        const profile = await api.getProfile(agent?.domain ?? 'en');
        if (profile?.mode_apprentissage) {
          currentMode = profile.mode_apprentissage;
        }
      }
      const convos = await api.getConversations(agent!.slug);
      if (convos?.data?.length > 0) {
        const latest = convos.data[0];
        conversationId = latest.id;
        await loadMessages(latest.id);
      }
    } catch (e) {
      console.warn('Could not load conversations:', e);
    }
    loadingHistory = false;
    await tick();
    await scrollToBottom();
    timerInterval = setInterval(updateTimer, 1000);
  }

  onMount(async () => {
    if (!agent?.available) { loadingHistory = false; return; }

    // S57 — Maître Comptable (premier non-langue) : skip QCM gate + consolidation
    // (CEFR-language-specific). Mode B Phase 1 = chat direct sans placement test.
    const isComptaAgent = agent.slug === 'maitre_comptable';

    let gateSkipChat = false;
    if (QCM_ONBOARDING_ENABLED && !isComptaAgent) {
      try {
        const lp = await api.getLearnerProfile(agent.domain);
        if (!lp) {
          showOnboardingModal = true;
          loadingHistory = false;
          gateSkipChat = true;
        }
      } catch (e) {
        console.warn('Could not check learner profile:', e);
        // Fail-open: if the endpoint is down, don't block chat.
      }
    }

    if (!gateSkipChat) {
      await loadChatState();
      if (!isComptaAgent) {
        await checkConsolidationState();
      }
    }
  });

  async function onOnboardingComplete() {
    showOnboardingModal = false;
    loadingHistory = true;
    await loadChatState();
  }

  function updateTimer() {
    if (!sessionStartTime) return;
    const idle = Date.now() - lastActivity;
    if (idle > 120000) return;
    const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    timerDisplay = `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  async function loadMessages(convoId: string) {
    if (!agent) return;
    try {
      // Session 37 — fetch Dify messages + consolidation events in parallel,
      // then interleave by timestamp for a coherent chronological thread.
      const [data, events] = await Promise.all([
        api.getChatMessages(convoId, agent.slug),
        api.consolidationEvents(agent.domain).catch(() => []),
      ]);

      const threadEntries: Array<Message & { _ts: number }> = [];

      if (data?.data) {
        for (const m of data.data) {
          // Dify returns messages as {query, answer, created_at (epoch seconds)}.
          const ts = typeof m.created_at === 'number'
            ? m.created_at * 1000
            : Date.parse(m.created_at || '') || 0;
          threadEntries.push({
            role: 'user', content: m.query,
            timestamp: new Date(ts).toISOString(), _ts: ts,
          });
          // Assistant answer is emitted just after the user query ; nudge by 1ms
          // so it sorts after the user turn even on identical timestamps.
          threadEntries.push({
            role: 'assistant', content: m.answer,
            timestamp: new Date(ts + 1).toISOString(), _ts: ts + 1,
          });
        }
      }

      for (const ev of events) {
        const ts = Date.parse(ev.triggered_at) || 0;
        threadEntries.push({
          role: 'system_consolidation',
          content: ev.bubble_message,
          timestamp: ev.triggered_at,
          _ts: ts,
        });
      }

      threadEntries.sort((a, b) => a._ts - b._ts);
      messages = threadEntries.map(({ _ts, ...rest }) => rest);
    } catch (e) {
      console.warn('Could not load messages:', e);
    }
  }

  async function sendMessage(text: string) {
    if (!agent || streaming) return;

    if (!sessionStartTime) sessionStartTime = Date.now();
    lastActivity = Date.now();

    messages.push({ role: 'user', content: text });
    streaming = true;
    showTyping = true;
    await scrollToBottom();

    messages.push({ role: 'assistant', content: '' });
    streamingIdx = messages.length - 1;

    try {
      // Phase A1 — auth via cookie + CSRF double-submit (no Bearer token).
      const csrfMatch = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
      const csrfToken = csrfMatch ? decodeURIComponent(csrfMatch[1]) : '';

      // Build request body with optional extra inputs
      const body: Record<string, any> = {
        message: text,
        conversation_id: conversationId,
        agent: agent.slug,
      };
      // Quiz: always send context when active (even for answer messages)
      if (pendingInputs.mock_exam) {
        body.mock_exam = pendingInputs.mock_exam;
      } else if (quizActive && quizQuestionNum > 0) {
        const c = quizConcepts[quizQuestionNum - 1];
        if (c) body.mock_exam = `Q${quizQuestionNum}/${quizTotalQuestions}:${c.key}:${c.mode}`;
      }
      if (pendingInputs.mode_override) body.mode_override = pendingInputs.mode_override;
      pendingInputs = {}; // Clear after sending

      const res = await fetch('/api/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify(body),
      });

      if (res.status === 429) {
        toastError('Trop de messages. Attends un instant...');
        messages.pop();
        return;
      }
      if (!res.ok || !res.body) throw new Error('Stream failed');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.event === 'message' || event.event === 'agent_message') {
              showTyping = false;
              messages[streamingIdx].content += event.answer || '';
              await scrollToBottom();
            }

            if (event.event === 'message_end' || event.event === 'agent_message_end') {
              if (event.conversation_id && !conversationId) {
                conversationId = event.conversation_id;
              }
            }

            if (event.event === 'workflow_finished') {
              if (event.conversation_id && !conversationId) {
                conversationId = event.conversation_id;
              }
              const status = event.data?.status;
              if (status === 'failed' || status === 'error') {
                if (!messages[streamingIdx].content) {
                  messages[streamingIdx].content = `${agent?.name ?? 'L\'agent'} ne répond pas. Réessaie dans un instant.`;
                }
              } else if (!messages[streamingIdx].content) {
                const fallback = event.data?.outputs?.answer || '';
                if (fallback) {
                  showTyping = false;
                  messages[streamingIdx].content = fallback;
                  await scrollToBottom();
                }
              }
            }

            if (event.event === 'xp_earned') {
              toastXP(event.amount || 50);
              window.dispatchEvent(new CustomEvent('xp-update', { detail: event.amount || 50 }));
            }

            if (event.event === 'error') {
              console.error('Dify error:', event);
              if (!messages[streamingIdx].content) {
                messages[streamingIdx].content = 'Erreur de connexion. Réessaie.';
              }
            }
          } catch (e) { console.warn('SSE parse error:', e); }
        }
      }

      if (!messages[streamingIdx].content) {
        messages[streamingIdx].content = 'Pas de réponse. Réessaie.';
      }
    } catch (e) {
      console.error('Chat error:', e);
      messages[streamingIdx].content = 'Erreur de connexion. Réessaie.';
    } finally {
      streaming = false;
      showTyping = false;
      streamingIdx = -1;
      lastActivity = Date.now();

      // Quiz: after assistant responds, allow "Question suivante"
      if (quizActive && quizQuestionNum > 0 && quizQuestionNum <= quizTotalQuestions) {
        quizWaitingForNext = true;
      }

      // Session 37 — re-poll consolidation state after each turn. The backend
      // `_consolidation_post_turn` hook may have flipped niveau_status →
      // `calibration_en_cours` on turn N≥8 ; without this, the MiniExamModal
      // only appears on next page mount/refresh.
      if (!showMiniExamModal && !showDecisionModal) {
        checkConsolidationState().catch(() => {}); // best-effort, never blocks
      }
    }
  }

  async function scrollToBottom() {
    await tick();
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // ── Mode toggle ────────────────────────────────
  function openModeModal() {
    pendingMode = currentMode === 'structure' ? 'libre' : 'structure';
    showModeModal = true;
  }

  async function confirmModeChange() {
    showModeModal = false;
    try {
      await api.changeMode(pendingMode);
      currentMode = pendingMode;
      // Send override with next message so chatflow picks it up immediately
      pendingInputs = { ...pendingInputs, mode_override: pendingMode };
      toastSuccess(`Mode ${pendingMode === 'structure' ? 'structuré' : 'libre'} activé`);
    } catch (e) {
      toastError('Erreur lors du changement de mode');
    }
  }

  // ── Quiz ───────────────────────────────────────
  async function startQuiz() {
    showQuizConfirm = false;
    quizLoading = true;
    try {
      // Load concepts to build quiz plan
      if (!agent) return;
      const data = await api.getConcepts(agent.domain);
      if (!data?.concept_keys?.length) {
        toastError('Pas de concepts disponibles pour le quiz');
        quizLoading = false;
        return;
      }

      // Select 10 concepts, prioritizing weak > untested > medium > mastered
      const keys = data.concept_keys as string[];
      const scores = data.scores as Record<string, {score: number}>;
      const withScores = keys.map(k => ({
        key: k,
        score: typeof scores[k] === 'object' ? (scores[k]?.score ?? 0) : (scores[k] ?? 0),
      }));

      // Sort: untested first, then weak, then medium, then strong
      withScores.sort((a, b) => {
        const cat = (s: number) => s === 0 ? 0 : s < 50 ? 1 : s < 80 ? 2 : 3;
        const diff = cat(a.score) - cat(b.score);
        if (diff !== 0) return diff;
        return a.score - b.score;
      });

      const selected = withScores.slice(0, 10);
      quizConcepts = selected.map(s => ({
        key: s.key,
        mode: s.score === 0 ? 'DECOUVERTE' : s.score < 50 ? 'RENFORCEMENT' : s.score < 80 ? 'PRATIQUE' : 'MAINTIEN',
      }));

      quizTotalQuestions = quizConcepts.length;
      quizQuestionNum = 1;
      quizActive = true;
      quizWaitingForNext = false;

      // Send first quiz message
      const c = quizConcepts[0];
      pendingInputs = { mock_exam: `Q1/${quizTotalQuestions}:${c.key}:${c.mode}` };
      await sendMessage('Quiz ! Première question !');
    } catch (e) {
      toastError('Erreur lors du lancement du quiz');
    } finally {
      quizLoading = false;
    }
  }

  async function nextQuizQuestion() {
    quizWaitingForNext = false;
    quizQuestionNum++;

    if (quizQuestionNum > quizTotalQuestions) {
      // Bilan
      pendingInputs = { mock_exam: 'bilan' };
      await sendMessage('Voilà mon dernier essai ! Fais le bilan !');
      quizActive = false;
      quizQuestionNum = 0;
      return;
    }

    const c = quizConcepts[quizQuestionNum - 1];
    pendingInputs = { mock_exam: `Q${quizQuestionNum}/${quizTotalQuestions}:${c.key}:${c.mode}` };
    // Don't auto-send — let the user type their answer to the previous question first
    // Actually, this is triggered AFTER the assistant responded to the previous answer
    await sendMessage('Question suivante !');
  }

  function cancelQuiz() {
    quizActive = false;
    quizQuestionNum = 0;
    quizWaitingForNext = false;
    toastSuccess('Quiz terminé');
  }
</script>

<svelte:head>
  <title>{agent?.name || 'Chat'} — Academie-IA</title>
</svelte:head>

{#if !agent?.available}
  <div class="flex items-center justify-center h-[calc(100dvh-3.5rem)] -m-4 md:-m-6">
    <p class="text-text-muted">Cet agent n'est pas encore disponible.</p>
  </div>
{:else if showOnboardingModal}
  <OnboardingModal
    domain={agent.domain}
    agentName={agent.name}
    onComplete={onOnboardingComplete}
  />
{:else}
  <MiniExamModal open={showMiniExamModal} domain={agent.domain} onDone={onMiniExamDone} />
  <ConsolidationDecisionModal
    open={showDecisionModal}
    domain={agent.domain}
    message={decisionMessage}
    qcmLevel={decisionQcmLevel}
    proposedLevel={decisionProposedLevel}
    kind={decisionKind}
    onDecided={onDecisionDecided} />
  <div class="flex flex-col h-[calc(100dvh-3.5rem)] -m-4 md:-m-6">
    <!-- Chat header -->
    <div class="h-12 bg-surface border-b border-border-subtle flex items-center justify-between px-4">
      <div class="flex items-center gap-3">
        <AgentFlag {agent} size="sm" />
        <span class="font-medium text-sm">{agent.name}</span>
        {#if sessionStartTime}
          <span class="text-xs font-mono text-text-muted">{timerDisplay}</span>
        {/if}
      </div>

      <div class="flex items-center gap-1.5 sm:gap-2">
        {#if agent.slug !== 'maitre_comptable'}
        <!-- Quiz indicator (langue-specific) -->
        {#if quizActive}
          <span class="text-[10px] sm:text-xs font-mono bg-warning/20 text-warning-text px-1.5 sm:px-2 py-0.5 rounded">
            {quizQuestionNum}/{quizTotalQuestions}
          </span>
          <button
            onclick={() => cancelQuiz()}
            class="text-xs text-text-muted hover:text-danger-text transition-colors"
            title="Arrêter le quiz"
          >✕</button>
        {/if}

        <!-- Mode toggle pill (langue-specific) -->
        <button
          onclick={() => openModeModal()}
          class="flex items-center gap-1 sm:gap-1.5 text-[10px] sm:text-xs px-1.5 sm:px-2.5 py-1 rounded-full border transition-colors
                 {currentMode === 'structure'
                   ? 'border-info/30 bg-info/10 text-info-text hover:bg-info/20'
                   : 'border-success/30 bg-success/10 text-success-text hover:bg-success/20'}"
          title="Changer le mode d'apprentissage"
        >
          {#if currentMode === 'structure'}
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
            <span class="hidden sm:inline">Structuré</span>
          {:else}
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"/></svg>
            <span class="hidden sm:inline">Libre</span>
          {/if}
        </button>

        <!-- Quiz button (langue-specific) -->
        <button
          onclick={() => { showQuizConfirm = true; }}
          disabled={quizActive || streaming || quizLoading}
          class="flex items-center gap-1 sm:gap-1.5 text-[10px] sm:text-xs px-1.5 sm:px-2.5 py-1 rounded-full border transition-colors
                 border-accent/30 bg-accent/10 text-accent hover:bg-accent/20
                 disabled:opacity-40 disabled:cursor-not-allowed"
          title="Lancer un quiz rapide (10 questions)"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <span class="hidden sm:inline">Quiz</span>
        </button>
        {/if}

        <!-- Message count (hidden on mobile) -->
        {#if messages.length > 0 && !quizActive}
          <span class="hidden sm:inline text-[10px] text-text-muted font-mono">{messages.filter(m => m.role === 'user').length} msg</span>
        {/if}
      </div>
    </div>

    <!-- Quiz progress bar -->
    {#if quizActive}
      <div class="h-1 bg-surface-hover">
        <div
          class="h-full bg-warning transition-all duration-500"
          style="width: {(quizQuestionNum / quizTotalQuestions) * 100}%"
        ></div>
      </div>
    {/if}

    <!-- S57 — Maître Comptable : RGPD disclaimer (Phase 1 Mode B Q&A omniscient, pas de dropdown module) -->
    {#if agent.slug === 'maitre_comptable'}
      <RGPDDisclaimer />
    {/if}

    <!-- Messages -->
    <div
      bind:this={messagesContainer}
      class="flex-1 overflow-y-auto p-4 space-y-4"
    >
      {#if loadingHistory}
        <div class="flex items-center justify-center h-full">
          <div class="text-center text-text-muted">
            <div class="w-6 h-6 border-2 border-text-muted border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-xs">Chargement de la conversation...</p>
          </div>
        </div>
      {:else if messages.length === 0 && !streaming}
        <div class="flex items-center justify-center h-full">
          <div class="text-center text-text-muted">
            <div class="mb-4">
              <AgentFlag {agent} size="lg" />
            </div>
            <p class="text-sm">Dis bonjour pour commencer avec {agent.name}</p>
          </div>
        </div>
      {:else}
        {#each messages as msg, i}
          {#if msg.content}
            <ChatBubble
              role={msg.role}
              content={msg.content}
              accentColor={agent.colorHex}
              streaming={streaming && i === streamingIdx}
              agentFlag={agent.flagSrc}
              agentName={agent.name}
              font={msg.role === 'assistant' && ['en','es','ja','de','it'].includes(agent?.domain ?? '') ? 'serif' : 'sans'}
            />
          {/if}
        {/each}
      {/if}

      {#if showTyping}
        <TypingIndicator accentColor={agent.colorHex} agentFlag={agent.flagSrc} agentName={agent.name} />
      {/if}
    </div>

    <!-- Quiz "Next Question" button -->
    {#if quizWaitingForNext && !streaming}
      <div class="px-4 py-2 bg-surface border-t border-border-subtle flex justify-center">
        <button
          onclick={() => nextQuizQuestion()}
          class="px-4 py-2 bg-warning text-black text-sm font-medium rounded-lg hover:bg-warning/90 transition-colors"
        >
          {quizQuestionNum >= quizTotalQuestions ? 'Voir le bilan' : `Question ${quizQuestionNum + 1}/${quizTotalQuestions} →`}
        </button>
      </div>
    {/if}

    <!-- Input -->
    <ChatInput onSend={sendMessage} disabled={streaming || loadingHistory} />
  </div>

  <!-- AI Act art. 50 mention -->
  <AIBanner />


  <!-- Mode change modal -->
  {#if showModeModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => { showModeModal = false; }}>
      <div class="bg-surface border border-border-subtle rounded-xl shadow-2xl max-w-sm w-full mx-4 p-6" onclick={(e) => e.stopPropagation()}>
        <h3 class="text-lg font-semibold mb-4">Changer de mode ?</h3>

        <div class="space-y-3 mb-6">
          <div class="p-3 rounded-lg {currentMode === 'structure' ? 'bg-info/10 border border-info/30' : 'bg-surface-hover'}">
            <div class="flex items-center gap-2 mb-1">
              <svg class="w-4 h-4 text-info-text" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
              <span class="font-medium text-sm">Structuré</span>
              {#if currentMode === 'structure'}<span class="text-[10px] text-info-text ml-auto">actuel</span>{/if}
            </div>
            <p class="text-xs text-text-muted leading-relaxed">Examen de passage quand tu maitrises 80% du niveau. Progression par paliers valides.</p>
            {#if currentMode === 'libre'}<p class="text-[10px] text-info-text mt-1">Un examen te sera propose des que tu seras pret.</p>{/if}
          </div>

          <div class="p-3 rounded-lg {currentMode === 'libre' ? 'bg-success/10 border border-success/30' : 'bg-surface-hover'}">
            <div class="flex items-center gap-2 mb-1">
              <svg class="w-4 h-4 text-success-text" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"/></svg>
              <span class="font-medium text-sm">Libre</span>
              {#if currentMode === 'libre'}<span class="text-[10px] text-success-text ml-auto">actuel</span>{/if}
            </div>
            <p class="text-xs text-text-muted leading-relaxed">Pas d'examen impose. Concepts du niveau suivant introduits naturellement. Progression fluide.</p>
            {#if currentMode === 'structure'}<p class="text-[10px] text-success-text mt-1">Tu ne passeras plus d'examens de niveau. Tes scores continuent de progresser.</p>{/if}
          </div>
        </div>

        <div class="flex gap-3">
          <button onclick={() => { showModeModal = false; }} class="flex-1 px-4 py-2 text-sm rounded-lg bg-surface-hover hover:bg-border-subtle transition-colors">Annuler</button>
          <button onclick={() => confirmModeChange()} class="flex-1 px-4 py-2 text-sm rounded-lg bg-accent text-white hover:bg-accent/90 transition-colors">
            Passer en {pendingMode === 'structure' ? 'structuré' : 'libre'}
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Quiz confirm modal -->
  {#if showQuizConfirm}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => { showQuizConfirm = false; }}>
      <div class="bg-surface border border-border-subtle rounded-xl shadow-2xl max-w-sm w-full mx-4 p-6" onclick={(e) => e.stopPropagation()}>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-full bg-warning/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-warning-text" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div>
            <h3 class="font-semibold">Quiz rapide</h3>
            <p class="text-xs text-text-muted">~5 min • 10 questions</p>
          </div>
        </div>

        <div class="bg-surface-hover rounded-lg p-3 mb-4">
          <ul class="text-xs text-text-muted space-y-1.5">
            <li class="flex items-start gap-2"><span class="text-warning-text mt-0.5">✓</span> 10 questions sur tes concepts actuels</li>
            <li class="flex items-start gap-2"><span class="text-warning-text mt-0.5">✓</span> Feedback immédiat après chaque réponse</li>
            <li class="flex items-start gap-2"><span class="text-warning-text mt-0.5">✓</span> Bilan personnalisé à la fin</li>
            <li class="flex items-start gap-2"><span class="text-text-muted mt-0.5">•</span> Aucun impact sur ta progression — c'est un entraînement</li>
          </ul>
        </div>

        <div class="flex gap-3">
          <button onclick={() => { showQuizConfirm = false; }} class="flex-1 px-4 py-2 text-sm rounded-lg bg-surface-hover hover:bg-border-subtle transition-colors">Annuler</button>
          <button onclick={() => startQuiz()} class="flex-1 px-4 py-2 text-sm rounded-lg bg-warning text-black font-medium hover:bg-warning/90 transition-colors">
            {#if quizLoading}
              <span class="inline-block w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></span>
            {:else}
              C'est parti !
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
{/if}
