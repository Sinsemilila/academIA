// Agent definitions — single source of truth.
// Sprint 5 D1: each agent has a `domain` field (ISO code matching backend _DOMAIN_REGISTRY).
// To add a new language: flip `available` to `true` + add the YAML data files + deploy.
export interface Agent {
  slug: string;
  name: string;
  lang: string;       // User-facing label (FR)
  domain: string;     // Backend DB domain string (ISO: "en", "es", ...)
  flagSrc: string;    // Path to flag image
  color: string;      // Tailwind class
  colorHex: string;   // Raw hex for dynamic styles
  available: boolean;
}

export const agents: Agent[] = [
  { slug: 'teacher',     name: 'Teacher',     lang: 'Anglais',    domain: 'en',       flagSrc: '/flags/gb.png',     color: 'text-teacher',     colorHex: '#3b82f6', available: true  },
  { slug: 'maestro',     name: 'Maestro',     lang: 'Espagnol',   domain: 'es',       flagSrc: '/flags/es.png',     color: 'text-maestro',     colorHex: '#ef4444', available: true  },
  { slug: 'sensei',      name: 'Sensei',      lang: 'Japonais',   domain: 'ja',       flagSrc: '/flags/jp.png',     color: 'text-sensei',      colorHex: '#a855f7', available: false },
  { slug: 'lehrer',      name: 'Lehrer',      lang: 'Allemand',   domain: 'de',       flagSrc: '/flags/de.png',     color: 'text-lehrer',      colorHex: '#f59e0b', available: false },
  { slug: 'professore',  name: 'Professore',  lang: 'Italien',    domain: 'it',       flagSrc: '/flags/it.png',     color: 'text-professore',  colorHex: '#22c55e', available: false },
  { slug: 'pymentor',    name: 'PyMentor',    lang: 'Python',     domain: 'python',   flagSrc: '/flags/python.svg', color: 'text-pymentor',    colorHex: '#06b6d4', available: false },
  { slug: 'cybermentor', name: 'CyberMentor', lang: 'Cybersec',   domain: 'cybersec', flagSrc: '/flags/cyber.svg',  color: 'text-cybermentor', colorHex: '#ec4899', available: false },
];

/** User-facing label ("Anglais") for a domain. */
export function domainLabel(domain: string): string {
  return agents.find((a) => a.domain === domain)?.lang ?? domain;
}

// Sprint 5 Phase 5 — feature flag for QCM onboarding refonte.
// Activated 2026-04-20. Rollback : flip to `false` + rebuild academie-frontend (5 min).
export const QCM_ONBOARDING_ENABLED = true;
