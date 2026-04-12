<script lang="ts">
  let { accentColor = '#3b82f6', agentFlag = '', agentName = '' } = $props<{
    accentColor?: string;
    agentFlag?: string;
    agentName?: string;
  }>();
</script>

<div class="flex justify-start gap-2.5 animate-fadeIn">
  <!-- Bot avatar -->
  <div
    class="w-8 h-8 rounded-full shrink-0 flex items-center justify-center overflow-hidden mt-1"
    style="background-color: {accentColor}18; border: 1.5px solid {accentColor}40"
  >
    {#if agentFlag}
      <img src={agentFlag} alt={agentName} class="w-5 h-5 object-contain" />
    {:else}
      <span class="text-xs font-semibold" style="color: {accentColor}">AI</span>
    {/if}
  </div>

  <div
    class="bg-surface border border-border-subtle px-4 py-3 rounded-2xl rounded-bl-md"
    style="border-left: 2px solid {accentColor}"
  >
    <span class="inline-flex gap-1.5 items-center">
      <span class="dot"></span>
      <span class="dot" style="animation-delay: 150ms"></span>
      <span class="dot" style="animation-delay: 300ms"></span>
    </span>
  </div>
</div>

<style>
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--color-text-muted);
    animation: bounce 1.2s ease-in-out infinite;
  }
  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-4px); }
  }
  .animate-fadeIn {
    animation: fadeIn 200ms ease-out;
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
</style>
