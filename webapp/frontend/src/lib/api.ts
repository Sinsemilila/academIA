const API_BASE = '/api';

// Refactor 2026-H2 Phase A1 — auth via opaque session cookie + CSRF
// double-submit. JWT localStorage logic supprimé. Cookie __Host-as_session
// (HttpOnly) lu automatiquement par le navigateur via credentials:'include'.
// Cookie csrf_token (JS-readable) lu ici et envoyé en header X-CSRF-Token
// sur toute mutation.
const MUTATION_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : null;
}

class ApiClient {
  private async fetch(path: string, options: RequestInit = {}): Promise<Response> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    const method = (options.method || 'GET').toUpperCase();
    if (MUTATION_METHODS.has(method)) {
      const csrf = getCookie('csrf_token');
      if (csrf) headers['X-CSRF-Token'] = csrf;
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (res.status === 401 && !path.includes('/auth/login')) {
      if (typeof window !== 'undefined') window.location.href = '/login';
      throw new Error('Non authentifi\u00e9');
    }

    if (res.status === 429) {
      const retryAfter = res.headers.get('Retry-After') || '60';
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('rate-limited', {
          detail: { seconds: parseInt(retryAfter, 10) || 60, path },
        }));
      }
      throw new Error(`Trop de requ\u00eates. R\u00e9essaie dans ${retryAfter}s`);
    }

    return res;
  }

  // ── Auth ──────────────────────────────────
  // Phase A1 — login response is { user } or { mfa_required, username }.
  // Session/CSRF cookies are set by the backend ; nothing to store JS-side.
  async login(username: string, password: string): Promise<{ mfa_required?: boolean; user?: any; username?: string }> {
    const res = await this.fetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erreur de connexion');
    }
    return await res.json();
  }

  async loginMfa(username: string, password: string, code: string) {
    const res = await this.fetch('/auth/login-mfa', {
      method: 'POST',
      body: JSON.stringify({ username, password, code }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Code MFA invalide');
    }
    return await res.json();
  }

  // ── TOTP MFA ──────────────────────────────
  async totpStatus() {
    const res = await this.fetch('/security/totp/status');
    if (!res.ok) throw new Error('TOTP status fetch failed');
    return res.json();
  }

  async totpEnrollStart() {
    const res = await this.fetch('/security/totp/enroll-start', { method: 'POST' });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Enrollment failed');
    }
    return res.json();
  }

  async totpEnrollConfirm(secret: string, code: string) {
    const res = await this.fetch('/security/totp/enroll-confirm', {
      method: 'POST',
      body: JSON.stringify({ secret, code }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Code invalide');
    }
    return res.json();
  }

  async totpDisable(password: string, code: string) {
    const res = await this.fetch('/security/totp/disable', {
      method: 'POST',
      body: JSON.stringify({ password, code }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Disable failed');
    }
    return true;
  }

  async me() {
    const res = await this.fetch('/auth/me');
    if (!res.ok) throw new Error('Non authentifi\u00e9');
    return await res.json();
  }

  // ── Profile ───────────────────────────────
  async getProfile(domain: string = 'en') {
    const res = await this.fetch(`/profile/${domain}`);
    if (!res.ok) return null;
    return await res.json();
  }

  // ── Dashboard (multi-agent overview) ──────
  async getDashboard() {
    const res = await this.fetch('/me/dashboard');
    if (!res.ok) return { agents: [] };
    return await res.json();
  }

  // ── Onboarding QCM (Sprint 5 Phase 5) ────
  async getOnboardingContent(domain: string) {
    const res = await this.fetch(`/onboarding/content/${domain}`);
    if (!res.ok) throw new Error('onboarding content unavailable');
    return await res.json();
  }

  async getLearnerProfile(domain: string) {
    const res = await this.fetch(`/learner-profile/${domain}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error('learner profile fetch failed');
    return await res.json();
  }

  async submitLearnerProfile(domain: string, payload: any) {
    const res = await this.fetch(`/learner-profile/${domain}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'submit failed');
    }
    return await res.json();
  }

  // Session 43 P5 — onboarding telemetry (un-authed, tolerant to failure).
  async postOnboardingTelemetry(event: {
    session_id: string;
    domain: string;
    event: 'step_enter' | 'complete' | 'abort';
    step_id?: string | null;
    step_order?: number | null;
    total_steps?: number | null;
  }) {
    try {
      await fetch(`${API_BASE}/telemetry/onboarding-event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event),
        keepalive: true,
      });
    } catch {
      // telemetry is best-effort; never break onboarding UX
    }
  }

  async patchLearnerProfile(domain: string, patch: any) {
    const res = await this.fetch(`/learner-profile/${domain}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    });
    if (!res.ok) throw new Error('patch failed');
    return await res.json();
  }

  // ── Error Profile ─────────────────────────
  async getErrorProfile(domain: string = 'en') {
    const res = await this.fetch(`/error-profile/${domain}`);
    if (!res.ok) return null;
    return await res.json();
  }

  // ── Streak ────────────────────────────────
  async getStreak() {
    const res = await this.fetch('/streak');
    if (!res.ok) return { current_streak: 0, longest_streak: 0, total_sessions: 0 };
    return await res.json();
  }

  // ── Stats ─────────────────────────────────
  async getWeeklyStats(domain: string = 'en') {
    const res = await this.fetch(`/stats/weekly?domain=${domain}`);
    if (!res.ok) return { sessions: 0, concepts: 0, minutes: 0 };
    return await res.json();
  }

  // ── Agents ────────────────────────────────
  async getAgents() {
    const res = await this.fetch('/agents');
    if (!res.ok) return [];
    return await res.json();
  }

  // ── Stats ─────────────────────────────────
  async getConcepts(domain: string = 'en') {
    const res = await this.fetch(`/me/concepts?domain=${domain}`);
    if (!res.ok) return { niveau: null, groups: {}, scores: {}, weights: {}, concept_keys: [] };
    return await res.json();
  }

  async getHistory(domain: string = 'en', limit: number = 20) {
    const res = await this.fetch(`/me/history?domain=${domain}&limit=${limit}`);
    if (!res.ok) return { sessions: [] };
    return await res.json();
  }

  async getExams(domain: string = 'en') {
    const res = await this.fetch(`/me/exams?domain=${domain}`);
    if (!res.ok) return { current_exam: null, last_exam: null, nb_exams: 0 };
    return await res.json();
  }

  // ── XP & Badges ───────────────────────────
  async getXp() {
    const res = await this.fetch('/me/xp');
    if (!res.ok) return { total: 0, rank: { name: 'Debutant', next_name: 'Explorateur', threshold: 0, next_threshold: 200 }, recent: [] };
    return await res.json();
  }

  async getHeatmap() {
    const res = await this.fetch('/me/heatmap');
    if (!res.ok) return { days: [] };
    return await res.json();
  }

  async getXpHistory() {
    const res = await this.fetch('/me/xp-history');
    if (!res.ok) return { data: [] };
    return await res.json();
  }

  async getBadges(domain: string = 'en') {
    const res = await this.fetch(`/me/badges?domain=${domain}`);
    if (!res.ok) return { badges: [] };
    return await res.json();
  }

  // ── Chat ──────────────────────────────────
  async getConversations(agent: string = 'teacher') {
    const res = await this.fetch(`/chat/conversations?agent=${agent}`);
    if (!res.ok) return { data: [] };
    return await res.json();
  }

  async getChatMessages(conversationId: string, agent: string = 'teacher') {
    const res = await this.fetch(`/chat/messages?conversation_id=${conversationId}&agent=${agent}`);
    if (!res.ok) return { data: [] };
    return await res.json();
  }

  // ── Mode ───────────────────────────────
  async changeMode(mode: string) {
    const res = await this.fetch('/me/mode', {
      method: 'PATCH',
      body: JSON.stringify({ mode }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erreur');
    }
    return await res.json();
  }

  // ── Settings ───────────────────────────
  async getSettings() {
    const res = await this.fetch('/me/settings');
    if (!res.ok) return null;
    return await res.json();
  }

  async updateProfile(data: {
    display_name?: string;
    avatar_color?: string;
    theme?: string;
    daily_goal_minutes?: number;
    centres_interet?: string;
    style_correction?: string;
    domain?: string;  // Sprint 5 D1: per-language personality scoping
  }) {
    const res = await this.fetch('/me/profile', { method: 'PATCH', body: JSON.stringify(data) });
    return await res.json();
  }

  async changePassword(currentPassword: string, newPassword: string) {
    const res = await this.fetch('/me/password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erreur');
    }
    return await res.json();
  }

  async getActiveSessions() {
    const res = await this.fetch('/me/sessions');
    if (!res.ok) return { sessions: [] };
    return await res.json();
  }

  async revokeSession(sessionId: number) {
    await this.fetch(`/me/sessions/${sessionId}`, { method: 'DELETE' });
  }

  async revokeAllSessions() {
    await this.fetch('/me/sessions', { method: 'DELETE' });
  }

  async getRecommendation(domain: string = 'en') {
    const res = await this.fetch(`/me/recommendation?domain=${domain}`);
    if (!res.ok) return null;
    return await res.json();
  }

  async getDailyProgress() {
    const res = await this.fetch('/me/daily-progress');
    if (!res.ok) return { goal_minutes: 15, done_minutes: 0, pct: 0, completed: false };
    return await res.json();
  }

  async getWeeklyRecap(domain: string = 'en') {
    const res = await this.fetch(`/me/weekly-recap?domain=${domain}`);
    if (!res.ok) return null;
    return await res.json();
  }

  // ── Admin ──────────────────────────────
  async adminGetUsers(domain?: string) {
    const qs = domain ? `?domain=${encodeURIComponent(domain)}` : '';
    const res = await this.fetch(`/admin/users${qs}`);
    if (!res.ok) throw new Error('Admin access denied');
    return await res.json();
  }

  async adminResetProfile(username: string, domain?: string | null) {
    // Session 37: domain-scoped reset. When domain is null/undefined → legacy
    // global wipe. When set → scope DELETE to that domain on per-domain tables
    // (profils_eleves, error_log, snapshots_session, learner_profiles,
    // consolidation_events, spaced_retrieval_queue).
    const qs = domain ? `?domain=${encodeURIComponent(domain)}` : '';
    const res = await this.fetch(`/admin/reset-profile/${username}${qs}`, { method: 'POST' });
    if (!res.ok) throw new Error('Reset failed');
    return await res.json();
  }

  async adminDeleteUser(userId: number) {
    const res = await this.fetch(`/admin/users/${userId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete failed');
    return await res.json();
  }

  async adminCacheStats(hours: number = 24) {
    const res = await this.fetch(`/admin/cache-stats?hours=${hours}`);
    if (!res.ok) throw new Error('Cache stats fetch failed');
    return await res.json();
  }

  async adminConsolidationEvents(domain: string = 'en', hours: number = 168) {
    const res = await this.fetch(`/admin/consolidation-events?domain=${encodeURIComponent(domain)}&hours=${hours}`);
    if (!res.ok) throw new Error('Consolidation events fetch failed');
    return await res.json();
  }

  async adminOracleRuns(agent: string = 'teacher_en', hours: number = 168) {
    const res = await this.fetch(`/admin/oracle-runs?agent=${encodeURIComponent(agent)}&hours=${hours}`);
    if (!res.ok) throw new Error('Oracle runs fetch failed');
    return await res.json();
  }

  async adminModelBudgets() {
    const res = await this.fetch('/admin/model-budgets');
    if (!res.ok) throw new Error('Model budgets fetch failed');
    return await res.json();
  }

  async adminJudgeBudget() {
    const res = await this.fetch('/admin/judge-budget');
    if (!res.ok) throw new Error('Judge budget fetch failed');
    return await res.json();
  }

  async adminCostRunawayUsers(window: string = '7d') {
    const res = await this.fetch(`/admin/cost-runaway-users?window=${encodeURIComponent(window)}`);
    if (!res.ok) throw new Error('Cost runaway fetch failed');
    return await res.json();
  }

  async adminOnboardingFunnel(domain: string = 'en', hours: number = 720) {
    const res = await this.fetch(`/admin/onboarding-funnel?domain=${encodeURIComponent(domain)}&hours=${hours}`);
    if (!res.ok) throw new Error('Onboarding funnel fetch failed');
    return await res.json();
  }

  async adminCreateUser(username: string, password: string) {
    const res = await this.fetch('/auth/users', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Creation failed');
    }
    return await res.json();
  }

  async getTokenUsage() {
    const res = await this.fetch('/chat/token-usage');
    if (!res.ok) return null;
    return await res.json();
  }

  // Session 37 — consolidation endpoints (auto-refresh on 401 via this.fetch)
  async consolidationState(domain: string) {
    const res = await this.fetch(`/consolidation/state/${domain}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async miniExamStart(domain: string) {
    const res = await this.fetch(`/consolidation/mini-exam/start/${domain}`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async miniExamSubmit(domain: string, targetLevel: string, answers: Array<{id: string; answer: string}>) {
    const res = await this.fetch(`/consolidation/mini-exam/submit/${domain}`, {
      method: 'POST',
      body: JSON.stringify({ target_level: targetLevel, answers }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async consolidationDecide(domain: string, choice: 'accept_new' | 'stay_current') {
    const res = await this.fetch(`/consolidation/decide/${domain}`, {
      method: 'POST',
      body: JSON.stringify({ choice }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async consolidationEvents(domain: string): Promise<Array<{
    triggered_at: string;
    final_level: string;
    user_decision: string;
    bubble_message: string;
  }>> {
    const res = await this.fetch(`/consolidation/events/${domain}`);
    if (!res.ok) return [];
    return await res.json();
  }

  async logout() {
    try {
      await this.fetch('/auth/logout', { method: 'POST' });
    } catch {
      // best-effort ; cookies cleared by backend, fall through to redirect
    }
    if (typeof window !== 'undefined') window.location.href = '/login';
  }

  async logoutAllSessions() {
    await this.fetch('/auth/logout-all-sessions', { method: 'POST' });
    if (typeof window !== 'undefined') window.location.href = '/login';
  }

  // ── DSAR (Phase A6) ───────────────────────
  async exportMyData() {
    const res = await this.fetch('/me/export-data');
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Export indisponible');
    }
    const blob = await res.blob();
    const cd = res.headers.get('Content-Disposition') || '';
    const match = cd.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : 'academie-export.json';
    if (typeof window !== 'undefined') {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }
    return filename;
  }

  async deleteMyAccount(confirmUsername: string) {
    const res = await this.fetch('/me/delete-account', {
      method: 'DELETE',
      body: JSON.stringify({ confirm_username: confirmUsername }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Suppression \u00e9chou\u00e9e');
    }
    return await res.json();
  }
}

export const api = new ApiClient();
