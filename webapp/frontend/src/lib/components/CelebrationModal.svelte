<script lang="ts">
  /**
   * Reusable celebration modal — used for:
   * - Badge unlock
   * - Level promotion
   * - Streak milestone (7, 30, 100 days)
   */

  let {
    show = $bindable(false),
    type = 'badge',
    icon = '',
    title = '',
    subtitle = '',
    accentColor = '#3b82f6',
  }: {
    show: boolean;
    type: 'badge' | 'levelup' | 'streak';
    icon: string;
    title: string;
    subtitle: string;
    accentColor?: string;
  } = $props();

  let confettiPieces = $state<{ left: number; delay: number; duration: number; color: string; size: number }[]>([]);

  $effect(() => {
    if (show) {
      // Generate confetti
      const colors = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#a855f7', '#ec4899', '#06b6d4'];
      confettiPieces = Array.from({ length: 40 }, () => ({
        left: Math.random() * 100,
        delay: Math.random() * 0.5,
        duration: 1.5 + Math.random() * 2,
        color: colors[Math.floor(Math.random() * colors.length)],
        size: 4 + Math.random() * 8,
      }));

      // Auto-close after 4s
      const t = setTimeout(() => { show = false; }, 4000);
      return () => clearTimeout(t);
    }
  });
</script>

{#if show}
  <div class="fixed inset-0 z-[70] flex items-center justify-center">
    <!-- Backdrop -->
    <button
      class="absolute inset-0 bg-black/60 backdrop-blur-sm"
      onclick={() => show = false}
      aria-label="Fermer"
    ></button>

    <!-- Confetti -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      {#each confettiPieces as piece}
        <div
          class="absolute top-0 rounded-sm confetti-piece"
          style="
            left: {piece.left}%;
            animation-delay: {piece.delay}s;
            animation-duration: {piece.duration}s;
            background: {piece.color};
            width: {piece.size}px;
            height: {piece.size}px;
          "
        ></div>
      {/each}
    </div>

    <!-- Card -->
    <div class="relative z-10 celebration-enter">
      <div
        class="bg-surface border border-border-subtle rounded-2xl p-8 text-center max-w-sm mx-4 shadow-2xl"
        style="box-shadow: 0 0 60px {accentColor}33, 0 0 120px {accentColor}11"
      >
        <!-- Icon -->
        <div class="mb-4">
          {#if type === 'levelup'}
            <div class="w-20 h-20 mx-auto rounded-2xl bg-teacher/15 flex items-center justify-center text-4xl glow-icon" style="--glow-color: {accentColor}">
              {icon}
            </div>
          {:else if type === 'streak'}
            <div class="text-6xl streak-bounce">{icon}</div>
          {:else}
            <div class="text-5xl badge-spin">{icon}</div>
          {/if}
        </div>

        <!-- Text -->
        <h2 class="text-xl font-bold mb-1">{title}</h2>
        <p class="text-sm text-text-secondary">{subtitle}</p>

        <!-- Close button -->
        <button
          onclick={() => show = false}
          class="mt-5 px-6 py-2 bg-elevated text-text-secondary text-sm rounded-lg hover:text-text-primary hover:bg-border-subtle transition-all"
        >
          Continuer
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes confetti-fall {
    0% { transform: translateY(-20px) rotate(0deg); opacity: 1; }
    100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
  }
  .confetti-piece {
    animation: confetti-fall 2s ease-out forwards;
  }

  @keyframes celebration-scale {
    0% { transform: scale(0.7); opacity: 0; }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); opacity: 1; }
  }
  .celebration-enter {
    animation: celebration-scale 0.4s ease-out forwards;
  }

  @keyframes glow-icon-pulse {
    0%, 100% { box-shadow: 0 0 20px var(--glow-color, #3b82f6); }
    50% { box-shadow: 0 0 40px var(--glow-color, #3b82f6), 0 0 60px var(--glow-color, #3b82f6); }
  }
  .glow-icon {
    animation: glow-icon-pulse 1.5s ease-in-out infinite;
  }

  @keyframes badge-spin-in {
    0% { transform: scale(0) rotate(-180deg); }
    70% { transform: scale(1.2) rotate(10deg); }
    100% { transform: scale(1) rotate(0deg); }
  }
  .badge-spin {
    animation: badge-spin-in 0.6s ease-out forwards;
  }

  @keyframes streak-bounce {
    0% { transform: scale(0); }
    50% { transform: scale(1.3); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); }
  }
  .streak-bounce {
    animation: streak-bounce 0.5s ease-out forwards;
  }
</style>
