const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const AUTH_TOKEN_KEY = 'signalwatch_access_token';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  headers.set('Content-Type', 'application/json');
  const token = sessionStorage.getItem(AUTH_TOKEN_KEY);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || `Request failed: ${response.status}`);
  return response.status === 204 ? (undefined as T) : response.json();
}

export type Competitor = { id: number; name: string; website_url: string; enabled: boolean; status: string; feed_url: string | null; sitemap_url: string | null; last_checked_at: string | null; };
export type Overview = { total_competitors: number; online_competitors: number; offline_competitors: number; checking_competitors: number; articles_detected_today: number; average_detection_delay_seconds: number | null; fastest_detection_seconds: number | null; slowest_detection_seconds: number | null; within_five_minutes: number; over_five_minutes: number; failed_checks: number; };
export type Article = { id: number; competitor_id: number; title: string; url: string; published_at: string | null; detected_at: string; detection_delay_seconds: number | null; detection_method: string; author: string | null; extraction_status: string; };
export type MonitoringCheck = { id: number; competitor_id: number; started_at: string; completed_at: string | null; duration_ms: number | null; status: string; strategy: string; articles_found: number; new_articles_found: number; updated_articles: number; error_message: string | null; retry_count: number; };
export type Notification = { id: number; article_id: number; type: string; status: string; created_at: string; };
export type AuthResponse = { access_token: string; token_type: string };
export const api = { login: (email: string, password: string) => request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }), overview: () => request<Overview>('/api/analytics/overview'), competitors: () => request<Competitor[]>('/api/competitors'), createCompetitor: (data: { name: string; website_url: string; blog_url?: string; feed_url?: string; sitemap_url?: string; enabled?: boolean }) => request<Competitor>('/api/competitors', { method: 'POST', body: JSON.stringify(data) }), enableCompetitor: (id: number) => request<Competitor>(`/api/competitors/${id}/enable`, { method: 'POST' }), disableCompetitor: (id: number) => request<Competitor>(`/api/competitors/${id}/disable`, { method: 'POST' }), articles: () => request<Article[]>('/api/articles?limit=20'), checks: () => request<MonitoringCheck[]>('/api/monitoring/checks?limit=12'), notifications: () => request<Notification[]>('/api/notifications'), check: (id: number) => request(`/api/competitors/${id}/check`, { method: 'POST' }), analyze: (id: number) => request(`/api/competitors/${id}/analyze`, { method: 'POST' }) };
