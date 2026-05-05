// Sprint 5 D4 — Current agent + domain tracking across navigation.
// Domain values use ISO codes ("en", "es", ...) matching backend _DOMAIN_REGISTRY.
// l1_watch toggle stays per-domain (user can want hints for FR→ES but not FR→EN).

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

const STORAGE_KEY = 'academia:currentAgent';
const DEFAULT_AGENT = 'teacher';

function loadInitial(): string {
  if (!browser) return DEFAULT_AGENT;
  try {
    return localStorage.getItem(STORAGE_KEY) || DEFAULT_AGENT;
  } catch {
    return DEFAULT_AGENT;
  }
}

export const currentAgent = writable<string>(loadInitial());

if (browser) {
  currentAgent.subscribe((v) => {
    try {
      localStorage.setItem(STORAGE_KEY, v);
    } catch {
      // ignore localStorage full / disabled
    }
  });
}

// Map agent slug → backend DB domain string (ISO).
export const SLUG_TO_DOMAIN: Record<string, string> = {
  teacher: 'en',
  maestro: 'es',
  professore: 'it',
  lehrer: 'de',
  sensei: 'ja',
  // pymentor + cybermentor moved to sinse.petit-pont.com (Phase 5+ self-learn).
};

// Reverse map: domain → agent slug
export const DOMAIN_TO_SLUG: Record<string, string> = Object.fromEntries(
  Object.entries(SLUG_TO_DOMAIN).map(([k, v]) => [v, k])
);

export const currentDomain = derived(currentAgent, ($agent) =>
  SLUG_TO_DOMAIN[$agent] ?? 'en'
);

/** Return the first `available: true` agent (fallback 'teacher'). */
export function firstAvailableAgent(agents: Array<{ slug: string; available: boolean }>): string {
  return agents.find((a) => a.available)?.slug ?? DEFAULT_AGENT;
}
