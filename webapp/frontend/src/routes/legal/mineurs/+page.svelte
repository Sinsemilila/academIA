<svelte:head>
  <title>Mineurs — Académie-IA</title>
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
    <h1 class="text-2xl font-semibold">Utilisation par les mineurs</h1>
  </div>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Restriction actuelle (alpha privée)</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Académie-IA est actuellement en <strong>alpha privée fermée</strong>.
      L'accès est restreint aux personnes <strong>âgées de 15 ans ou plus</strong>, ou
      autorisées à utiliser le service par leur responsable légal.
    </p>
    <p class="text-sm text-text-secondary leading-relaxed">
      Cette restriction est conforme à l'<strong>article 8 du RGPD</strong> et à la
      Loi pour une République numérique (France, 2016) qui fixe à 15 ans l'âge
      du consentement numérique autonome en France.
    </p>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Flow consentement parental — prévu pour la beta publique</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Lorsqu'Académie-IA ouvrira en beta publique, un flow complet de consentement parental
      sera mis en place pour les mineurs de moins de 15 ans :
    </p>
    <ul class="text-sm text-text-secondary leading-relaxed space-y-2 list-disc pl-5">
      <li>Saisie de la date de naissance lors de l'inscription</li>
      <li>Si âge inférieur à 15 ans : saisie de l'email d'un parent ou tuteur</li>
      <li>Envoi d'un email au parent avec un lien de consentement (validité 7 jours)</li>
      <li>Page d'information complète présentée au parent (finalité, données collectées, sous-processeurs, droits)</li>
      <li>Activation du compte uniquement après accord explicite du parent</li>
      <li>Possibilité pour le parent de révoquer le consentement à tout moment</li>
    </ul>
  </section>

  <section class="bg-surface border border-border-subtle rounded-xl p-6 space-y-3">
    <h2 class="font-semibold text-lg">Contact</h2>
    <p class="text-sm text-text-secondary leading-relaxed">
      Si vous êtes parent ou tuteur d'un mineur de moins de 15 ans qui souhaite utiliser
      Académie-IA, contactez sinseproduction@gmail.com — un compte avec consentement
      manuel pourra être créé en attendant la mise en place du flow automatisé.
    </p>
  </section>

  <p class="text-xs text-text-muted text-center">Dernière mise à jour : 2026-04-23</p>
</div>
