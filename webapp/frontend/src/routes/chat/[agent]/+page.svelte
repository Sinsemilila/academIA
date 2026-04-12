<script lang="ts">
  import { page } from '$app/state';
  import { onMount, tick } from 'svelte';
  import { api } from '$lib/api';
  import { agents } from '$lib/config';
  import AgentFlag from '$lib/components/AgentFlag.svelte';
  import ChatBubble from '$lib/components/chat/ChatBubble.svelte';
  import ChatInput from '$lib/components/chat/ChatInput.svelte';
  import TypingIndicator from '$lib/components/chat/TypingIndicator.svelte';
  import { toastXP, toastError, toastSuccess } from '$lib/stores/toasts';

  interface Message {
    role: 'user' | 'assistant';
    content: string;
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

  onMount(async () => {
    if (!agent?.available) { loadingHistory = false; return; }
    try {
      // Load profile to get current mode
      const profile = await api.getProfile('anglais');
      if (profile?.mode_apprentissage) {
        currentMode = profile.mode_apprentissage;
      }

      const convos = await api.getConversations(agent.slug);
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
    return () => {
      if (timerInterval) clearInterval(timerInterval);
    };
  });

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
      const data = await api.getChatMessages(convoId, agent.slug);
      if (data?.data) {
        messages = data.data.map((m: any) => ([
          { role: 'user' as const, content: m.query },
          { role: 'assistant' as const, content: m.answer },
        ])).flat();
      }
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
      const token = api.loadToken();

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
          'Authorization': `Bearer ${token}`,
        },
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
                  messages[streamingIdx].content = 'Teacher ne répond pas. Réessaie dans un instant.';
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
          } catch { /* skip */ }
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
      const data = await api.getConcepts('anglais');
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
{:else}
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
        <!-- Quiz indicator -->
        {#if quizActive}
          <span class="text-[10px] sm:text-xs font-mono bg-amber-500/20 text-amber-400 px-1.5 sm:px-2 py-0.5 rounded">
            {quizQuestionNum}/{quizTotalQuestions}
          </span>
          <button
            onclick={() => cancelQuiz()}
            class="text-xs text-text-muted hover:text-red-400 transition-colors"
            title="Arrêter le quiz"
          >✕</button>
        {/if}

        <!-- Mode toggle pill -->
        <button
          onclick={() => openModeModal()}
          class="flex items-center gap-1 sm:gap-1.5 text-[10px] sm:text-xs px-1.5 sm:px-2.5 py-1 rounded-full border transition-colors
                 {currentMode === 'structure'
                   ? 'border-blue-500/30 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20'
                   : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20'}"
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

        <!-- Quiz button -->
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
          class="h-full bg-amber-500 transition-all duration-500"
          style="width: {(quizQuestionNum / quizTotalQuestions) * 100}%"
        ></div>
      </div>
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
            <ChatBubble role={msg.role} content={msg.content} accentColor={agent.colorHex} streaming={streaming && i === streamingIdx} agentFlag={agent.flagSrc} agentName={agent.name} />
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
          class="px-4 py-2 bg-amber-500 text-black text-sm font-medium rounded-lg hover:bg-amber-400 transition-colors"
        >
          {quizQuestionNum >= quizTotalQuestions ? 'Voir le bilan' : `Question ${quizQuestionNum + 1}/${quizTotalQuestions} →`}
        </button>
      </div>
    {/if}

    <!-- Input -->
    <ChatInput onSend={sendMessage} disabled={streaming || loadingHistory} />
  </div>

  <!-- Mode change modal -->
  {#if showModeModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => { showModeModal = false; }}>
      <div class="bg-surface border border-border-subtle rounded-xl shadow-2xl max-w-sm w-full mx-4 p-6" onclick={(e) => e.stopPropagation()}>
        <h3 class="text-lg font-semibold mb-4">Changer de mode ?</h3>

        <div class="space-y-3 mb-6">
          <div class="p-3 rounded-lg {currentMode === 'structure' ? 'bg-blue-500/10 border border-blue-500/30' : 'bg-surface-hover'}">
            <div class="flex items-center gap-2 mb-1">
              <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
              <span class="font-medium text-sm">Structuré</span>
              {#if currentMode === 'structure'}<span class="text-[10px] text-blue-400 ml-auto">actuel</span>{/if}
            </div>
            <p class="text-xs text-text-muted leading-relaxed">Examen de passage quand tu maîtrises 80% du niveau. Progression par paliers validés.</p>
          </div>

          <div class="p-3 rounded-lg {currentMode === 'libre' ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-surface-hover'}">
            <div class="flex items-center gap-2 mb-1">
              <svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"/></svg>
              <span class="font-medium text-sm">Libre</span>
              {#if currentMode === 'libre'}<span class="text-[10px] text-emerald-400 ml-auto">actuel</span>{/if}
            </div>
            <p class="text-xs text-text-muted leading-relaxed">Pas d'examen imposé. Concepts du niveau suivant introduits naturellement. Progression fluide.</p>
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
          <div class="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div>
            <h3 class="font-semibold">Quiz rapide</h3>
            <p class="text-xs text-text-muted">~5 min • 10 questions</p>
          </div>
        </div>

        <div class="bg-surface-hover rounded-lg p-3 mb-4">
          <ul class="text-xs text-text-muted space-y-1.5">
            <li class="flex items-start gap-2"><span class="text-amber-400 mt-0.5">✓</span> 10 questions sur tes concepts actuels</li>
            <li class="flex items-start gap-2"><span class="text-amber-400 mt-0.5">✓</span> Feedback immédiat après chaque réponse</li>
            <li class="flex items-start gap-2"><span class="text-amber-400 mt-0.5">✓</span> Bilan personnalisé à la fin</li>
            <li class="flex items-start gap-2"><span class="text-text-muted mt-0.5">•</span> Aucun impact sur ta progression — c'est un entraînement</li>
          </ul>
        </div>

        <div class="flex gap-3">
          <button onclick={() => { showQuizConfirm = false; }} class="flex-1 px-4 py-2 text-sm rounded-lg bg-surface-hover hover:bg-border-subtle transition-colors">Annuler</button>
          <button onclick={() => startQuiz()} class="flex-1 px-4 py-2 text-sm rounded-lg bg-amber-500 text-black font-medium hover:bg-amber-400 transition-colors">
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
