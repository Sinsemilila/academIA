<svelte:head>
  <title>Mention IA — Académie-IA</title>
</svelte:head>

<div class="max-w-2xl mx-auto space-y-6 py-4">
  <div class="flex items-center gap-3">
    <a
      href="/legal"
      class="w-8 h-8 flex items-center justify-center rounded-lg bg-elevated text-text-secondary hover:text-text-primary hover:bg-border-subtle transition-all"
      aria-label="Retour"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </a>
    <h1 class="text-2xl font-semibold">Mention IA & sous-processeurs</h1>
  </div>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Vous interagissez avec une IA</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Conformément à l'<strong>article 50 du règlement européen sur l'IA</strong> (AI Act),
      nous vous informons explicitement que les agents Maestro, Teacher et Onboarding
      d'Académie-IA sont des <strong>systèmes d'intelligence artificielle générative</strong>.
      Leurs réponses sont produites par des modèles de langage (LLM) et peuvent contenir
      des inexactitudes. L'évaluation pédagogique reste indicative.
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Quelles données sont envoyées aux LLM ?</h2>
    <ul class="text-sm text-text-secondary leading-relaxed space-y-2 list-disc pl-5">
      <li>Le texte de vos messages (après filtrage automatique des PII : email, téléphone, IBAN, NIR, carte bancaire — remplacés par des placeholders).</li>
      <li>Le contexte de votre profil pédagogique (niveau CEFR, langues, motivation) pour personnaliser la réponse.</li>
      <li>L'historique récent de la conversation pour assurer la continuité.</li>
    </ul>
    <p class="text-sm text-text-secondary leading-relaxed">
      <strong>Aucune donnée d'identification</strong> (nom, email, identifiant) n'est transmise aux LLM.
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Sous-processeurs</h2>
    <ul class="text-sm text-text-secondary leading-relaxed space-y-3">
      <li>
        <strong>OpenAI</strong> (US — DPF certifié) — modèles gpt-4o-mini / gpt-4.1-mini.
        Utilisé pour ~99% des appels chat. Opt-out training data activé.
        <a href="https://openai.com/policies/data-processing-addendum" class="underline" target="_blank" rel="noopener">DPA OpenAI ↗</a>
      </li>
      <li>
        <strong>Groq</strong> (US — DPF certifié) — modèle Llama 3.3 70B.
        Utilisé en fallback (~1% des appels). Pas de training data par défaut.
        <a href="https://groq.com/dpa/" class="underline" target="_blank" rel="noopener">DPA Groq ↗</a>
      </li>
      <li>
        <strong>Google AI Studio</strong> (US — DPF certifié) — Gemini Flash.
        Utilisé uniquement pour le judge interne (évaluation qualité), <strong>aucun message
        utilisateur n'est transmis à Google</strong>.
      </li>
      <li>
        <strong>Cloudflare</strong> (US/UE — DPF + SCC) — reverse proxy, WAF, protection DDoS.
        <a href="https://www.cloudflare.com/cloudflare-customer-dpa/" class="underline" target="_blank" rel="noopener">DPA Cloudflare ↗</a>
      </li>
    </ul>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Vos droits</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Vous pouvez à tout moment exporter ou supprimer la totalité de vos données depuis
      <a href="/settings/privacy" class="underline">Paramètres → Confidentialité</a>.
      Pour toute autre question RGPD, contactez sinseproduction@gmail.com.
    </p>
  </section>

  <p class="text-xs text-text-muted text-center">Dernière mise à jour : 2026-04-23</p>
</div>
