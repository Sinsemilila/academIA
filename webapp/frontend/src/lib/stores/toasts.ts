// Enhanced toast notification store — supports undo, progress, countdown
let _id = 0;

export interface Toast {
  id: number;
  message: string;
  icon?: string;
  type?: 'xp' | 'badge' | 'info' | 'success' | 'error' | 'action';
  duration?: number;
  action?: { label: string; callback: () => void };
  progress?: boolean; // Shows a countdown bar
}

type Listener = (toasts: Toast[]) => void;
let toasts: Toast[] = [];
const listeners = new Set<Listener>();
const timers = new Map<number, ReturnType<typeof setTimeout>>();

function notify() {
  listeners.forEach(fn => fn([...toasts]));
}

export function subscribe(fn: Listener) {
  listeners.add(fn);
  fn([...toasts]);
  return () => listeners.delete(fn);
}

export function addToast(toast: Omit<Toast, 'id'>): number {
  const id = ++_id;
  const duration = toast.duration || 3000;
  toasts = [...toasts, { ...toast, id }];
  notify();
  const timer = setTimeout(() => {
    removeToast(id);
  }, duration);
  timers.set(id, timer);
  return id;
}

export function removeToast(id: number) {
  const timer = timers.get(id);
  if (timer) { clearTimeout(timer); timers.delete(id); }
  toasts = toasts.filter(t => t.id !== id);
  notify();
}

export function toastXP(amount: number) {
  addToast({
    message: `+${amount} XP`,
    icon: '\u2728',
    type: 'xp',
    duration: 3500,
  });
}

export function toastBadge(name: string, icon: string) {
  addToast({
    message: `Badge d\u00e9bloqu\u00e9 : ${name}`,
    icon,
    type: 'badge',
    duration: 5000,
  });
}

export function toastSuccess(message: string) {
  addToast({ message, type: 'success', icon: '\u2705', duration: 3000 });
}

export function toastError(message: string) {
  addToast({ message, type: 'error', icon: '\u274C', duration: 5000 });
}

export function toastAction(message: string, actionLabel: string, callback: () => void) {
  addToast({
    message,
    type: 'action',
    duration: 6000,
    progress: true,
    action: { label: actionLabel, callback },
  });
}
