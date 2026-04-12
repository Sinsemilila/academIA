// Theme store — syncs with DOM, localStorage, and DB
type Theme = 'dark' | 'light';
type ThemeListener = (theme: Theme) => void;

let currentTheme: Theme = 'dark';
const listeners: ThemeListener[] = [];

export function getTheme(): Theme {
  return currentTheme;
}

export function setTheme(theme: Theme) {
  currentTheme = theme;
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    // Update meta theme-color
    const mc = document.querySelector('meta[name="theme-color"]');
    if (mc) mc.setAttribute('content', theme === 'light' ? '#fafafa' : '#0a0a0a');
  }
  listeners.forEach(fn => fn(theme));
}

export function toggleTheme(): Theme {
  const next = currentTheme === 'dark' ? 'light' : 'dark';
  setTheme(next);
  return next;
}

export function initTheme() {
  if (typeof window === 'undefined') return;
  const stored = localStorage.getItem('theme') as Theme | null;
  if (stored) {
    currentTheme = stored;
  } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    currentTheme = 'light';
  }
  setTheme(currentTheme);
}

export function onThemeChange(fn: ThemeListener): () => void {
  listeners.push(fn);
  return () => {
    const idx = listeners.indexOf(fn);
    if (idx >= 0) listeners.splice(idx, 1);
  };
}
