// Agent definitions — single source of truth
export interface Agent {
  slug: string;
  name: string;
  lang: string;
  flagSrc: string;    // Path to flag image
  color: string;      // Tailwind class
  colorHex: string;   // Raw hex for dynamic styles
  available: boolean;
}

export const agents: Agent[] = [
  { slug: 'teacher',     name: 'Teacher',     lang: 'Anglais',    flagSrc: '/flags/gb.png',     color: 'text-teacher',     colorHex: '#3b82f6', available: true  },
  { slug: 'maestro',     name: 'Maestro',     lang: 'Espagnol',   flagSrc: '/flags/es.png',     color: 'text-maestro',     colorHex: '#ef4444', available: false },
  { slug: 'sensei',      name: 'Sensei',      lang: 'Japonais',   flagSrc: '/flags/jp.png',     color: 'text-sensei',      colorHex: '#a855f7', available: false },
  { slug: 'lehrer',      name: 'Lehrer',      lang: 'Allemand',   flagSrc: '/flags/de.png',     color: 'text-lehrer',      colorHex: '#f59e0b', available: false },
  { slug: 'professore',  name: 'Professore',  lang: 'Italien',    flagSrc: '/flags/it.png',     color: 'text-professore',  colorHex: '#22c55e', available: false },
  { slug: 'pymentor',    name: 'PyMentor',    lang: 'Python',     flagSrc: '/flags/python.svg', color: 'text-pymentor',    colorHex: '#06b6d4', available: false },
  { slug: 'cybermentor', name: 'CyberMentor', lang: 'Cybersec',   flagSrc: '/flags/cyber.svg',  color: 'text-cybermentor', colorHex: '#ec4899', available: false },
];
