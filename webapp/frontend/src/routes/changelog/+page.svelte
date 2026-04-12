<script lang="ts">
  import { onMount } from 'svelte';

  const entries = [
    {
      date: '2026-04-07',
      version: '0.5',
      title: 'Quiz, mode et insights',
      items: [
        'Bouton Quiz dans le header du chat \u2014 10 questions rapides avec feedback imm\u00e9diat',
        'Toggle Mode (structur\u00e9/libre) dans le header du chat avec confirmation',
        'Barre de progression du quiz en temps r\u00e9el',
        'Insights personnalis\u00e9s par module sur la page concepts',
        'TTT (Test\u2192Teach\u2192Test) : transition d\u00e9terministe entre concepts',
        'Mod\u00e8les LLM bascul\u00e9s sur groq-standard (plus fiable)',
      ],
    },
    {
      date: '2026-04-07',
      version: '0.4',
      title: 'Chat enrichi & logique p\u00e9dagogique',
      items: [
        'Avatars dans le chat : bulle utilisateur color\u00e9e et drapeau de l\'agent',
        'Conversation persistante unique par agent \u2014 reprise automatique',
        'D\u00e9tection d\'absence : accueil diff\u00e9rent apr\u00e8s 1h, 1 jour ou 7 jours',
        'Curseur de saisie anim\u00e9 pendant la r\u00e9ponse de l\u2019agent',
        'Examen d\u00e9clench\u00e9 uniquement apr\u00e8s ma\u00eetrise suffisante des concepts du niveau',
        'Message clair quand l\u2019agent ne r\u00e9pond pas (au lieu du silence)',
        'Objectif quotidien visible en haut (anneau de progression)',
        'Agents regroup\u00e9s par domaine dans la sidebar (Langues / Tech)',
        'Couleur d\u2019avatar se met \u00e0 jour en temps r\u00e9el sans recharger la page',
        'Le \u00ab A \u00bb Acad\u00e9mie dans la sidebar prend la couleur de ton avatar',
        'Filet de s\u00e9curit\u00e9 snapshots automatique (cron horaire)',
        'Mentions l\u00e9gales accessibles depuis chaque page',
      ],
    },
    {
      date: '2026-04-07',
      version: '0.3',
      title: 'Outils, raccourcis & gamification avanc\u00e9e',
      items: [
        'Palette de commandes (Ctrl+K) pour naviguer rapidement',
        'Raccourcis clavier (Shift+?) avec liste compl\u00e8te',
        'Objectif quotidien personnalisable (5 \u00e0 60 min)',
        'R\u00e9sum\u00e9 hebdomadaire permanent sur le dashboard',
        'Modal de c\u00e9l\u00e9bration (confetti) pour les promotions de rang',
        'Graphique de progression XP sur 30 jours',
        'Page badges redessin\u00e9e avec ic\u00f4ne, description et barre de progression',
        'Timer de session avec pause automatique apr\u00e8s inactivit\u00e9',
        'R\u00e9visions espac\u00e9es : le syst\u00e8me privil\u00e9gie les concepts \u00e0 revoir',
        'Indicateur de connexion en temps r\u00e9el',
        'Page profil compl\u00e8te (couleur avatar, objectif, th\u00e8me, s\u00e9curit\u00e9)',
        'Page changelog, page mentions l\u00e9gales',
        'Navigation clavier dans les dialogs de confirmation',
      ],
    },
    {
      date: '2026-04-07',
      version: '0.2',
      title: 'Renforcement & installation',
      items: [
        'Application installable sur mobile et desktop (PWA)',
        'Mode sombre et clair avec bascule en haut \u00e0 droite',
        'Page hors-ligne si connexion perdue',
        'Anti-spam : limite de messages par minute',
        'Connexion s\u00e9curis\u00e9e avec token de rafra\u00eechissement automatique',
        'Responsive mobile complet (sidebar escamotable, tap \u00e0 l\'ext\u00e9rieur ferme)',
        'Drapeaux pays corrects sur Windows (plus d\u2019emoji texte)',
        'Chargement skeleton pendant les appels r\u00e9seau',
        'Page 404 et page d\u2019erreur',
      ],
    },
    {
      date: '2026-04-07',
      version: '0.1',
      title: 'Lancement Acad\u00e9mie-IA',
      items: [
        'Chat streaming avec Teacher \u2014 anglais adapt\u00e9 \u00e0 ton niveau',
        'Onboarding : diagnostic de niveau CECRL automatique (A1 \u2192 C2)',
        'Dashboard avec progression, concepts du niveau et stats de la semaine',
        'Syst\u00e8me XP, 9 badges et rangs (D\u00e9butant \u2192 Ma\u00eetre)',
        'Page stats : jauge de niveau, grille des concepts, historique des sessions',
        'R\u00e9sultats d\u2019examens de validation de niveau',
        'Header avec XP, streak de jours cons\u00e9cutifs et objectif',
        'Gestion du profil et r\u00e9glages',
      ],
    },
  ];

  const CHANGELOG_VERSION = entries[0].version;

  onMount(() => {
    localStorage.setItem('lastSeenChangelog', CHANGELOG_VERSION);
  });
</script>

<svelte:head>
  <title>Nouveaut&#233;s — Acad&#233;mie-IA</title>
</svelte:head>

<div class="max-w-2xl mx-auto space-y-8 py-4">
  <h1 class="text-2xl font-semibold">Nouveaut&#233;s</h1>

  {#each entries as entry, i}
    <section class="bg-surface border border-border-subtle rounded-xl p-6">
      <div class="flex items-center gap-3 mb-4">
        <span class="px-2.5 py-0.5 bg-teacher/10 text-teacher text-xs font-mono rounded-full">v{entry.version} — {entry.date}</span>
        <h2 class="font-semibold">{entry.title}</h2>
        {#if i === 0}
          <span class="px-2 py-0.5 bg-teacher text-white text-[10px] font-semibold rounded-full">Nouveau</span>
        {/if}
      </div>
      <ul class="space-y-2">
        {#each entry.items as item}
          <li class="flex items-start gap-2 text-sm text-text-secondary">
            <span class="text-professore mt-0.5">&#x2713;</span>
            <span>{item}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/each}
</div>
