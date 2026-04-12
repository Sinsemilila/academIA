<script lang="ts">
  import type { Agent } from '$lib/config';

  let { agent, size = 'md' } = $props<{
    agent: Agent;
    size?: 'sm' | 'md' | 'lg';
  }>();

  const sizes = {
    sm: 'w-7 h-7 rounded-lg',
    md: 'w-10 h-10 rounded-xl',
    lg: 'w-16 h-16 rounded-2xl',
  };
</script>

<span
  class="inline-flex items-center justify-center overflow-hidden shrink-0 {sizes[size]}"
  style="background-color: {agent.colorHex}15; border: 1px solid {agent.colorHex}30"
>
  <img
    src={agent.flagSrc}
    alt={agent.lang}
    class="w-[75%] h-auto object-contain rounded-sm"
  />
</span>
