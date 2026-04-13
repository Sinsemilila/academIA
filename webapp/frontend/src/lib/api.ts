const API_BASE = '/api';

class ApiClient {
  private token: string | null = null;
  private refreshToken: string | null = null;
  private refreshing: Promise<boolean> | null = null;

  setToken(t: string | null) {
    this.token = t;
    if (typeof window !== 'undefined') {
      if (t) localStorage.setItem('token', t);
      else localStorage.removeItem('token');
    }
  }

  setRefreshToken(t: string | null) {
    this.refreshToken = t;
    if (typeof window !== 'undefined') {
      if (t) localStorage.setItem('refresh_token', t);
      else localStorage.removeItem('refresh_token');
    }
  }

  loadToken(): string | null {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
      this.refreshToken = localStorage.getItem('refresh_token');
    }
    return this.token;
  }

  private async tryRefresh(): Promise<boolean> {
    if (!this.refreshToken) return false;

    // Deduplicate concurrent refresh calls
    if (this.refreshing) return this.refreshing;

    this.refreshing = (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        this.setToken(data.access_token);
        if (data.refresh_token) this.setRefreshToken(data.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        this.refreshing = null;
      }
    })();

    return this.refreshing;
  }

  private async fetch(path: string, options: RequestInit = {}): Promise<Response> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

    // Auto-refresh on 401 (except login/refresh endpoints)
    if (res.status === 401 && !path.includes('/auth/login') && !path.includes('/auth/refresh')) {
      const refreshed = await this.tryRefresh();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.token}`;
        res = await fetch(`${API_BASE}${path}`, { ...options, headers });
      }
    }

    if (res.status === 401) {
      this.setToken(null);
      this.setRefreshToken(null);
      if (typeof window !== 'undefined') window.location.href = '/login';
      throw new Error('Non authentifi\u00e9');
    }

    // Rate limit handling — emit event so UI can show feedback
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
  async login(username: string, password: string) {
    const res = await this.fetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Erreur de connexion');
    }
    const data = await res.json();
    this.setToken(data.access_token);
    if (data.refresh_token) this.setRefreshToken(data.refresh_token);
    return data;
  }

  async me() {
    const res = await this.fetch('/auth/me');
    if (!res.ok) throw new Error('Non authentifi\u00e9');
    return await res.json();
  }

  // ── Profile ───────────────────────────────
  async getProfile(domain: string = 'anglais') {
    const res = await this.fetch(`/profile/${domain}`);
    if (!res.ok) return null;
    return await res.json();
  }

  // ── Error Profile ─────────────────────────
  async getErrorProfile(domain: string = 'anglais') {
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
  async getWeeklyStats() {
    const res = await this.fetch('/stats/weekly');
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
  async getConcepts(domain: string = 'anglais') {
    const res = await this.fetch(`/me/concepts?domain=${domain}`);
    if (!res.ok) return { niveau: null, groups: {}, scores: {}, weights: {}, concept_keys: [] };
    return await res.json();
  }

  async getHistory(domain: string = 'anglais', limit: number = 20) {
    const res = await this.fetch(`/me/history?domain=${domain}&limit=${limit}`);
    if (!res.ok) return { sessions: [] };
    return await res.json();
  }

  async getExams(domain: string = 'anglais') {
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

  async getBadges(domain: string = 'anglais') {
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

  async updateProfile(data: { display_name?: string; avatar_color?: string; theme?: string; daily_goal_minutes?: number }) {
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

  async getRecommendation(domain: string = 'anglais') {
    const res = await this.fetch(`/me/recommendation?domain=${domain}`);
    if (!res.ok) return null;
    return await res.json();
  }

  async getDailyProgress() {
    const res = await this.fetch('/me/daily-progress');
    if (!res.ok) return { goal_minutes: 15, done_minutes: 0, pct: 0, completed: false };
    return await res.json();
  }

  async getWeeklyRecap(domain: string = 'anglais') {
    const res = await this.fetch(`/me/weekly-recap?domain=${domain}`);
    if (!res.ok) return null;
    return await res.json();
  }

  logout() {
    this.setToken(null);
    this.setRefreshToken(null);
    if (typeof window !== 'undefined') window.location.href = '/login';
  }
}

export const api = new ApiClient();
