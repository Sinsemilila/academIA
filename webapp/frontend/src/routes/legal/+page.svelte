<svelte:head>
  <title>Mentions l&#233;gales — Acad&#233;mie-IA</title>
</svelte:head>

<div class="max-w-2xl mx-auto space-y-8 py-4">
  <div class="flex items-center gap-3">
    <a
      href="/"
      class="w-8 h-8 flex items-center justify-center rounded-lg bg-elevated text-text-secondary hover:text-text-primary hover:bg-border-subtle transition-all"
      aria-label="Retour"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </a>
    <h1 class="text-2xl font-semibold">Mentions l&#233;gales & Confidentialit&#233;</h1>
  </div>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <h2 class="font-semibold text-lg">&#201;diteur du site</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Acad&#233;mie-IA est un projet personnel d&#233;velopp&#233; et h&#233;berg&#233; par Sinse.
      <br />Contact : sinseproduction@gmail.com
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <h2 class="font-semibold text-lg">H&#233;bergement</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Le site est h&#233;berg&#233; sur une infrastructure auto-g&#233;r&#233;e en France (serveur personnel).
      L'acc&#232;s est s&#233;curis&#233; via Cloudflare (tunnel chiffr&#233; + Zero Trust).
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <h2 class="font-semibold text-lg">Donn&#233;es collect&#233;es</h2>
    <ul class="text-sm text-text-secondary leading-relaxed space-y-2 list-disc pl-5">
      <li>Nom d'utilisateur et mot de passe (chiffr&#233; bcrypt)</li>
      <li>Messages &#233;chang&#233;s avec les agents IA (pour la continuit&#233; p&#233;dagogique)</li>
      <li>Progression : scores, niveaux, streaks, XP, r&#233;sultats d'examens</li>
      <li>Adresse IP et informations d'appareil (pour la s&#233;curit&#233; des sessions)</li>
    </ul>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <h2 class="font-semibold text-lg">Utilisation des donn&#233;es</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Les donn&#233;es sont utilis&#233;es exclusivement pour le fonctionnement de la plateforme
      d'apprentissage. Elles ne sont ni vendues, ni partag&#233;es avec des tiers.
      Les conversations sont trait&#233;es par des mod&#232;les d'IA (Mistral, Groq) pour g&#233;n&#233;rer
      des r&#233;ponses p&#233;dagogiques.
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <h2 class="font-semibold text-lg">Conservation & Suppression</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Les donn&#233;es sont conserv&#233;es tant que le compte est actif.
      Pour supprimer ton compte et toutes les donn&#233;es associ&#233;es, contacte l'administrateur
      &#224; sinseproduction@gmail.com.
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-4">
    <h2 class="font-semibold text-lg">Droits (RGPD)</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Tu disposes d'un droit d'acc&#232;s, de rectification et de suppression de tes donn&#233;es.
      Pour exercer ces droits, exporte ou supprime ton compte directement depuis
      <a href="/settings/privacy" class="text-teacher hover:underline">Param&#232;tres &rarr; Confidentialit&#233;</a>,
      ou contacte sinseproduction@gmail.com.
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">En savoir plus</h2>
    <ul class="space-y-2 text-sm">
      <li>
        <a href="/legal/ia" class="text-teacher hover:underline inline-flex items-center gap-1.5">
          🤖 Mention IA &amp; sous-processeurs
        </a>
        <span class="text-text-muted ml-1">— quels mod&#232;les LLM, quelles donn&#233;es leur sont envoy&#233;es</span>
      </li>
      <li>
        <a href="/legal/mineurs" class="text-teacher hover:underline inline-flex items-center gap-1.5">
          👶 Mineurs (RGPD art. 8)
        </a>
        <span class="text-text-muted ml-1">— restriction &#8805;15 ans alpha + roadmap consentement parental</span>
      </li>
      <li>
        <a href="/settings/privacy" class="text-teacher hover:underline inline-flex items-center gap-1.5">
          🛡 Confidentialit&#233; &amp; RGPD
        </a>
        <span class="text-text-muted ml-1">— exporter ou supprimer ton compte</span>
      </li>
    </ul>
  </section>

  <p class="text-xs text-text-muted text-center">Derni&#232;re mise &#224; jour : avril 2026</p>
</div>
