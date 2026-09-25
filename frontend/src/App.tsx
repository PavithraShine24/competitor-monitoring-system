import { Activity, Bell, BookOpen, CheckCircle2, ChevronRight, Clock3, LayoutDashboard, Plus, Radio, RefreshCw, Settings, ShieldAlert, SlidersHorizontal, XCircle } from "lucide-react";
import { FormEvent, ReactNode, useEffect, useState } from "react";
import { api, Article, AUTH_TOKEN_KEY, Competitor, MonitoringCheck, Notification, Overview } from "./api";
import Login from "./Login";

type View = "overview" | "articles" | "competitors" | "monitoring" | "analytics" | "notifications";

const formatDelay = (seconds: number | null) => {
  if (seconds === null) return "Unavailable";
  const total = Math.floor(seconds);
  if (total < 60) return `${total} seconds`;
  if (total < 3600) return `${Math.floor(total / 60)}m ${(total % 60).toString().padStart(2, "0")}s`;
  return `${Math.floor(total / 3600)}h ${(Math.floor(total / 60) % 60).toString().padStart(2, "0")}m`;
};

const time = (value: string | null) => value ? new Date(value).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Never";
const errorText = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;

function ViewState({ loading, error, empty, children }: { loading: boolean; error: string; empty: boolean; children: ReactNode }) {
  if (loading) return <div className="panel empty">Loading...</div>;
  if (error) return <div className="panel error" role="alert"><XCircle size={18} />{error}</div>;
  if (empty) return <div className="panel empty">No data available yet.</div>;
  return <>{children}</>;
}

function Stats({ overview }: { overview: Overview | null }) {
  const stats = overview ? [
    { label: "Competitors", value: overview.total_competitors, icon: Radio, accent: "blue" },
    { label: "Detected today", value: overview.articles_detected_today, icon: BookOpen, accent: "orange" },
    { label: "Avg. delay", value: formatDelay(overview.average_detection_delay_seconds), icon: Clock3, accent: "green" },
    { label: "Failed checks", value: overview.failed_checks, icon: ShieldAlert, accent: "red" },
  ] : [];
  return <section className="stats">{stats.map(({ label, value, icon: Icon, accent }) => <div className="stat" key={label}><div className={`stat-icon ${accent}`}><Icon size={18} /></div><div><span>{label}</span><strong>{value}</strong></div></div>)}</section>;
}

function DelaySplit({ overview }: { overview: Overview | null }) {
  const total = (overview?.within_five_minutes ?? 0) + (overview?.over_five_minutes ?? 0);
  return <div className="panel"><div className="panel-head"><div><p className="eyebrow">ATTENTION</p><h2>Delay split</h2></div><Activity size={18} className="muted" /></div><div className="split"><div><strong>{overview?.within_five_minutes ?? 0}</strong><span>≤ 5 minutes</span></div><div className="divider" /><div><strong className="orange-text">{overview?.over_five_minutes ?? 0}</strong><span>&gt; 5 minutes</span></div></div><div className="bar"><span style={{ width: `${total ? ((overview?.within_five_minutes ?? 0) / total) * 100 : 0}%` }} /></div><p className="note">Every delay is stored exactly. No late detection is hidden.</p></div>;
}

function ArticlesView({ articles, competitors, loading, error }: { articles: Article[]; competitors: Competitor[]; loading: boolean; error: string }) {
  const names = new Map(competitors.map((competitor) => [competitor.id, competitor.name]));
  return <ViewState loading={loading} error={error} empty={!articles.length}><section className="panel"><div className="panel-head"><div><p className="eyebrow">LIVE INVENTORY</p><h2>Articles</h2></div><BookOpen size={18} className="muted" /></div><div className="table-wrap"><table><thead><tr><th>Article</th><th>Competitor</th><th>Published</th><th>Detected</th><th>Delay</th><th>Method</th><th>URL</th></tr></thead><tbody>{articles.map((article) => <tr key={article.id}><td><strong>{article.title || "Untitled"}</strong><small>{article.author || "Author unavailable"}</small></td><td>{names.get(article.competitor_id) || `Competitor #${article.competitor_id}`}</td><td>{time(article.published_at)}</td><td>{time(article.detected_at)}</td><td><span className={article.detection_delay_seconds !== null && article.detection_delay_seconds > 300 ? "delay late" : "delay"}>{formatDelay(article.detection_delay_seconds)}</span></td><td><span className="method">{article.detection_method}</span></td><td><a className="article-link" href={article.url} target="_blank" rel="noreferrer">Open</a></td></tr>)}</tbody></table></div></section></ViewState>;
}

function MonitoringView({ checks, competitors, loading, error }: { checks: MonitoringCheck[]; competitors: Competitor[]; loading: boolean; error: string }) {
  const names = new Map(competitors.map((competitor) => [competitor.id, competitor.name]));
  return <ViewState loading={loading} error={error} empty={!checks.length}><section className="panel"><div className="panel-head"><div><p className="eyebrow">CHECK HISTORY</p><h2>Monitoring</h2></div><Activity size={18} className="muted" /></div><div className="history">{checks.map((check) => <div className="history-row monitoring-row" key={check.id}><span className={`dot ${check.status}`} /><strong>{names.get(check.competitor_id) || `#${check.competitor_id}`}</strong><span>{check.strategy}</span><span>{time(check.started_at)}</span><span>{check.new_articles_found} new{check.updated_articles > 0 ? ` · ${check.updated_articles} updated` : " articles"}</span><span>{check.duration_ms ? `${check.duration_ms}ms` : "Running"}</span>{check.error_message && <small className="error-text">{check.error_message}</small>}</div>)}</div></section></ViewState>;
}

function CompetitorsView({ competitors, loading, error, busy, onAdd, onAction }: { competitors: Competitor[]; loading: boolean; error: string; busy: number | null; onAdd: () => void; onAction: (id: number, kind: "check" | "enable" | "disable") => void }) {
  return <ViewState loading={loading} error={error} empty={!competitors.length}><section className="panel"><div className="panel-head"><div><p className="eyebrow">MONITORING FLEET</p><h2>Competitors</h2></div><button className="primary" type="button" onClick={onAdd}><Plus size={16} />Add competitor</button></div><div className="competitor-list">{competitors.map((competitor) => <div className="competitor" key={competitor.id}><div className="favicon">{competitor.name.slice(0, 1).toUpperCase()}</div><div className="competitor-name"><strong>{competitor.name}</strong><small>{competitor.website_url}</small></div><span className={`status ${competitor.status}`}>{competitor.status}</span><span className="last-check">{time(competitor.last_checked_at)}</span><button className="ghost competitor-toggle" type="button" disabled={busy === competitor.id} onClick={() => onAction(competitor.id, competitor.enabled ? "disable" : "enable")}>{busy === competitor.id ? "Working..." : competitor.enabled ? "Disable" : "Enable"}</button><button className="icon-button" title="Check now" disabled={busy === competitor.id} onClick={() => onAction(competitor.id, "check")}>{busy === competitor.id ? <RefreshCw className="spin" size={16} /> : <CheckCircle2 size={16} />}</button></div>)}</div></section></ViewState>;
}

function NotificationsPanel({ notifications, loading, error }: { notifications: Notification[]; loading: boolean; error: string }) {
  return <ViewState loading={loading} error={error} empty={!notifications.length}><section className="panel notifications-panel"><div className="panel-head"><div><p className="eyebrow">ACTIVITY</p><h2>Notifications</h2></div><Bell size={18} className="muted" /></div><div className="notification-list">{notifications.map((notification) => <div className="notification-row" key={notification.id}><div className="notification-icon"><Bell size={16} /></div><div className="notification-details"><strong>{notification.type}</strong><span>Article #{notification.article_id}</span></div><span className={`status ${notification.status}`}>{notification.status}</span><time>{time(notification.created_at)}</time></div>)}</div></section></ViewState>;
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(AUTH_TOKEN_KEY));
  const [selectedView, setSelectedView] = useState<View>("overview");
  const [isCompetitorFormOpen, setIsCompetitorFormOpen] = useState(false);
  const [competitorName, setCompetitorName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [blogUrl, setBlogUrl] = useState("");
  const [feedUrl, setFeedUrl] = useState("");
  const [sitemapUrl, setSitemapUrl] = useState("");
  const [isSubmittingCompetitor, setIsSubmittingCompetitor] = useState(false);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [checks, setChecks] = useState<MonitoringCheck[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState("");
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const authenticate = (accessToken: string) => { sessionStorage.setItem(AUTH_TOKEN_KEY, accessToken); setToken(accessToken); };
  const logout = () => { sessionStorage.removeItem(AUTH_TOKEN_KEY); setToken(null); setOverview(null); setCompetitors([]); setArticles([]); setChecks([]); };
  const refresh = async () => { setDataLoading(true); try { setError(""); const [o, c, a, h] = await Promise.all([api.overview(), api.competitors(), api.articles(), api.checks()]); setOverview(o); setCompetitors(c); setArticles(a); setChecks(h); } catch (e) { setError(errorText(e, "API unavailable")); } finally { setDataLoading(false); } };
  useEffect(() => { if (!token) return; refresh(); const id = window.setInterval(refresh, 15000); return () => window.clearInterval(id); }, [token]);
  useEffect(() => { if (!token || selectedView !== "notifications") return; setNotificationsLoading(true); setNotificationsError(""); api.notifications().then(setNotifications).catch((e) => setNotificationsError(errorText(e, "Unable to load notifications."))).finally(() => setNotificationsLoading(false)); }, [token, selectedView]);
  const action = async (id: number, kind: "check" | "enable" | "disable") => { setBusy(id); try { await (kind === "check" ? api.check(id) : kind === "enable" ? api.enableCompetitor(id) : api.disableCompetitor(id)); await refresh(); } catch (e) { setError(errorText(e, "Action failed")); } finally { setBusy(null); } };
  const resetCompetitorForm = () => { setCompetitorName(""); setWebsiteUrl(""); setBlogUrl(""); setFeedUrl(""); setSitemapUrl(""); setIsCompetitorFormOpen(false); };
  const submitCompetitor = async (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); if (!competitorName.trim() || !websiteUrl.trim()) { setError("Competitor name and website URL are required."); return; } setIsSubmittingCompetitor(true); setError(""); try { await api.createCompetitor({ name: competitorName.trim(), website_url: websiteUrl.trim(), ...(blogUrl.trim() && { blog_url: blogUrl.trim() }), ...(feedUrl.trim() && { feed_url: feedUrl.trim() }), ...(sitemapUrl.trim() && { sitemap_url: sitemapUrl.trim() }) }); resetCompetitorForm(); await refresh(); } catch (e) { setError(errorText(e, "Unable to add competitor.")); } finally { setIsSubmittingCompetitor(false); } };
  if (!token) return <Login onAuthenticated={authenticate} />;
  const navItems: [View, string, typeof LayoutDashboard][] = [["overview", "Overview", LayoutDashboard], ["competitors", "Competitors", Radio], ["articles", "Articles", BookOpen], ["monitoring", "Monitoring", Activity], ["analytics", "Analytics", SlidersHorizontal], ["notifications", "Notifications", Bell]];
  const commonProps = { loading: dataLoading, error };
  return <div className="shell"><aside><div className="brand"><span className="brand-mark">S</span><div><strong>Signalwatch</strong><small>content intelligence</small></div></div><nav>{navItems.map(([view, label, Icon]) => <button type="button" className={selectedView === view ? "active" : ""} key={view} onClick={() => setSelectedView(view)}><Icon size={17} />{label}</button>)}</nav><button className="settings" type="button" onClick={logout}><Settings size={17} />Log out</button></aside><main><header><div><p className="eyebrow">OPERATIONS CENTER</p><h1>{navItems.find(([view]) => view === selectedView)?.[1] || "Overview"}</h1><p className="subhead">A live view of what your market is publishing and how quickly you catch it.</p></div><button className="refresh" type="button" onClick={refresh} disabled={dataLoading}><RefreshCw size={16} />{dataLoading ? "Refreshing..." : "Refresh"}</button></header>{error && selectedView === "overview" && <div className="error" role="alert"><XCircle size={18} />{error}</div>}{selectedView === "overview" && <><Stats overview={overview} /><section className="grid"><div className="panel wide"><div className="panel-head"><div><p className="eyebrow">LIVE INVENTORY</p><h2>Recent articles</h2></div><button className="ghost" type="button" onClick={() => setSelectedView("articles")}>View all <ChevronRight size={15} /></button></div><ArticlesView articles={articles.slice(0, 5)} competitors={competitors} {...commonProps} /></div><DelaySplit overview={overview} /></section><CompetitorsView competitors={competitors} {...commonProps} busy={busy} onAdd={() => setIsCompetitorFormOpen(true)} onAction={action} /><MonitoringView checks={checks.slice(0, 6)} competitors={competitors} {...commonProps} /></>}{selectedView === "articles" && <ArticlesView articles={articles} competitors={competitors} {...commonProps} />}{selectedView === "competitors" && <CompetitorsView competitors={competitors} {...commonProps} busy={busy} onAdd={() => setIsCompetitorFormOpen(true)} onAction={action} />}{selectedView === "monitoring" && <MonitoringView checks={checks} competitors={competitors} {...commonProps} />}{selectedView === "analytics" && <ViewState loading={dataLoading} error={error} empty={!overview}><><Stats overview={overview} /><DelaySplit overview={overview} /></></ViewState>}{selectedView === "notifications" && <NotificationsPanel notifications={notifications} loading={notificationsLoading} error={notificationsError} />}{isCompetitorFormOpen && <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="add-competitor-title"><div className="panel-head"><div><p className="eyebrow">MONITORING FLEET</p><h2 id="add-competitor-title">Add competitor</h2></div><button className="modal-close" type="button" onClick={resetCompetitorForm} aria-label="Close add competitor form">×</button></div><form className="competitor-form" onSubmit={submitCompetitor}><label htmlFor="competitor-name">Competitor Name</label><input id="competitor-name" value={competitorName} onChange={(event) => setCompetitorName(event.target.value)} required autoFocus /><label htmlFor="website-url">Website URL</label><input id="website-url" type="url" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} placeholder="https://example.com" required /><label htmlFor="blog-url">Blog URL <span>(optional)</span></label><input id="blog-url" type="url" value={blogUrl} onChange={(event) => setBlogUrl(event.target.value)} placeholder="https://example.com/blog" /><label htmlFor="feed-url">Feed URL <span>(optional)</span></label><input id="feed-url" type="url" value={feedUrl} onChange={(event) => setFeedUrl(event.target.value)} placeholder="https://example.com/feed.xml" /><label htmlFor="sitemap-url">Sitemap URL <span>(optional)</span></label><input id="sitemap-url" type="url" value={sitemapUrl} onChange={(event) => setSitemapUrl(event.target.value)} placeholder="https://example.com/sitemap.xml" /><div className="modal-actions"><button className="ghost" type="button" onClick={resetCompetitorForm} disabled={isSubmittingCompetitor}>Cancel</button><button className="primary" type="submit" disabled={isSubmittingCompetitor}>{isSubmittingCompetitor ? "Adding..." : "Add competitor"}</button></div></form></section></div>}</main></div>;
}

export default App;
