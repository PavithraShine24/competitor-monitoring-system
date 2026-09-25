import {
  Activity,
  Bell,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock3,
  LayoutDashboard,
  Plus,
  Radio,
  RefreshCw,
  Settings,
  ShieldAlert,
  SlidersHorizontal,
  XCircle,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { api, Article, AUTH_TOKEN_KEY, Competitor, Overview } from "./api";
import Login from "./Login";

const formatDelay = (seconds: number | null) => {
  if (seconds === null) return "Unavailable";
  const total = Math.floor(seconds);
  if (total < 60) return `${total} seconds`;
  if (total < 3600)
    return `${Math.floor(total / 60)}m ${(total % 60).toString().padStart(2, "0")}s`;
  return `${Math.floor(total / 3600)}h ${Math.floor((total % 3600) / 60)
    .toString()
    .padStart(2, "0")}m`;
};
const time = (value: string | null) =>
  value
    ? new Date(value).toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Never";

function App() {
  const [token, setToken] = useState(() =>
    sessionStorage.getItem(AUTH_TOKEN_KEY),
  );
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
  const [checks, setChecks] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const authenticate = (accessToken: string) => {
    sessionStorage.setItem(AUTH_TOKEN_KEY, accessToken);
    setToken(accessToken);
  };
  const logout = () => {
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
    setToken(null);
    setOverview(null);
    setCompetitors([]);
    setArticles([]);
    setChecks([]);
  };
  const refresh = async () => {
    try {
      setError("");
      const [o, c, a, h] = await Promise.all([
        api.overview(),
        api.competitors(),
        api.articles(),
        api.checks(),
      ]);
      setOverview(o);
      setCompetitors(c);
      setArticles(a);
      setChecks(h);
    } catch (e) {
      setError(e instanceof Error ? e.message : "API unavailable");
    }
  };
  useEffect(() => {
    if (!token) return;
    refresh();
    const id = window.setInterval(refresh, 15000);
    return () => window.clearInterval(id);
  }, [token]);
  const action = async (id: number, kind: "check" | "analyze" | "enable" | "disable") => {
    setBusy(id);
    try {
      const request = kind === "check" ? api.check(id) : kind === "analyze" ? api.analyze(id) : kind === "enable" ? api.enableCompetitor(id) : api.disableCompetitor(id);
      await request;
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(null);
    }
  };
  const resetCompetitorForm = () => {
    setCompetitorName("");
    setWebsiteUrl("");
    setBlogUrl("");
    setFeedUrl("");
    setSitemapUrl("");
    setIsCompetitorFormOpen(false);
  };
  const submitCompetitor = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!competitorName.trim() || !websiteUrl.trim()) {
      setError("Competitor name and website URL are required.");
      return;
    }
    setIsSubmittingCompetitor(true);
    setError("");
    try {
      await api.createCompetitor({
        name: competitorName.trim(),
        website_url: websiteUrl.trim(),
        ...(blogUrl.trim() && { blog_url: blogUrl.trim() }),
        ...(feedUrl.trim() && { feed_url: feedUrl.trim() }),
        ...(sitemapUrl.trim() && { sitemap_url: sitemapUrl.trim() }),
      });
      resetCompetitorForm();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to add competitor.");
    } finally {
      setIsSubmittingCompetitor(false);
    }
  };
  const stats = overview
    ? [
        {
          label: "Competitors",
          value: overview.total_competitors,
          icon: Radio,
          accent: "blue",
        },
        {
          label: "Detected today",
          value: overview.articles_detected_today,
          icon: BookOpen,
          accent: "orange",
        },
        {
          label: "Avg. delay",
          value: formatDelay(overview.average_detection_delay_seconds),
          icon: Clock3,
          accent: "green",
        },
        {
          label: "Failed checks",
          value: overview.failed_checks,
          icon: ShieldAlert,
          accent: "red",
        },
      ]
    : [];
  if (!token) return <Login onAuthenticated={authenticate} />;
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <span className="brand-mark">S</span>
          <div>
            <strong>Signalwatch</strong>
            <small>content intelligence</small>
          </div>
        </div>
        <nav>
          {[
            ["Overview", LayoutDashboard],
            ["Competitors", Radio],
            ["Articles", BookOpen],
            ["Monitoring", Activity],
            ["Analytics", SlidersHorizontal],
            ["Notifications", Bell],
          ].map(([label, Icon]) => (
            <button
              className={label === "Overview" ? "active" : ""}
              key={label as string}
            >
              <Icon size={17} />
              {label as string}
            </button>
          ))}
        </nav>
        <button className="settings">
          <Settings size={17} />
          Settings
        </button>
      </aside>
      <main>
        <header>
          <div>
            <p className="eyebrow">OPERATIONS CENTER</p>
            <h1>Competitive signal, without the noise.</h1>
            <p className="subhead">
              A live view of what your market is publishing and how quickly you
              catch it.
            </p>
          </div>
          <button className="refresh" onClick={refresh}>
            <RefreshCw size={16} />
            Refresh
          </button>
        </header>
        {error && (
          <div className="error">
            <XCircle size={18} />
            {error}
          </div>
        )}
        <section className="stats">
          {stats.map(({ label, value, icon: Icon, accent }) => (
            <div className="stat" key={label}>
              <div className={`stat-icon ${accent}`}>
                <Icon size={18} />
              </div>
              <div>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            </div>
          ))}
        </section>
        <section className="grid">
          <div className="panel wide">
            <div className="panel-head">
              <div>
                <p className="eyebrow">LIVE INVENTORY</p>
                <h2>Recent articles</h2>
              </div>
              <button className="ghost">
                View all <ChevronRight size={15} />
              </button>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Article</th>
                    <th>Published</th>
                    <th>Detected</th>
                    <th>Delay</th>
                    <th>Method</th>
                  </tr>
                </thead>
                <tbody>
                  {articles.length ? (
                    articles.map((article) => (
                      <tr key={article.id}>
                        <td>
                          <strong>{article.title}</strong>
                          <small>
                            {article.author || "Author unavailable"}
                          </small>
                        </td>
                        <td>{time(article.published_at)}</td>
                        <td>{time(article.detected_at)}</td>
                        <td>
                          <span
                            className={
                              article.detection_delay_seconds !== null &&
                              article.detection_delay_seconds > 300
                                ? "delay late"
                                : "delay"
                            }
                          >
                            {formatDelay(article.detection_delay_seconds)}
                          </span>
                        </td>
                        <td>
                          <span className="method">
                            {article.detection_method}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="empty">
                        No detections yet. Add a competitor to start watching.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">ATTENTION</p>
                <h2>Delay split</h2>
              </div>
              <Activity size={18} className="muted" />
            </div>
            <div className="split">
              <div>
                <strong>{overview?.within_five_minutes ?? 0}</strong>
                <span>≤ 5 minutes</span>
              </div>
              <div className="divider" />
              <div>
                <strong className="orange-text">
                  {overview?.over_five_minutes ?? 0}
                </strong>
                <span>&gt; 5 minutes</span>
              </div>
            </div>
            <div className="bar">
              <span
                style={{
                  width: `${overview && overview.within_five_minutes + overview.over_five_minutes ? (overview.within_five_minutes / (overview.within_five_minutes + overview.over_five_minutes)) * 100 : 0}%`,
                }}
              />
            </div>
            <p className="note">
              Every delay is stored exactly. No late detection is hidden.
            </p>
          </div>
        </section>
        <section className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">MONITORING FLEET</p>
              <h2>Competitors</h2>
            </div>
            <button className="primary" type="button" onClick={() => setIsCompetitorFormOpen(true)}>
              <Plus size={16} />
              Add competitor
            </button>
          </div>
          <div className="competitor-list">
            {competitors.length ? (
              competitors.map((competitor) => (
                <div className="competitor" key={competitor.id}>
                  <div className="favicon">
                    {competitor.name.slice(0, 1).toUpperCase()}
                  </div>
                  <div className="competitor-name">
                    <strong>{competitor.name}</strong>
                    <small>{competitor.website_url}</small>
                  </div>
                  <span className={`status ${competitor.status}`}>
                    {competitor.status}
                  </span>
                  <span className="last-check">
                    {time(competitor.last_checked_at)}
                  </span>
                  <button
                    className="ghost competitor-toggle"
                    type="button"
                    disabled={busy === competitor.id}
                    onClick={() => action(competitor.id, competitor.enabled ? "disable" : "enable")}
                  >
                    {busy === competitor.id ? "Working..." : competitor.enabled ? "Disable" : "Enable"}
                  </button>
                  <button
                    className="icon-button"
                    title="Check now"
                    disabled={busy === competitor.id}
                    onClick={() => action(competitor.id, "check")}
                  >
                    {busy === competitor.id ? (
                      <RefreshCw className="spin" size={16} />
                    ) : (
                      <CheckCircle2 size={16} />
                    )}
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-block">
                <Radio size={24} />
                <strong>Your monitoring fleet is empty</strong>
                <span>
                  Connect a competitor website to begin discovering signals.
                </span>
                <button className="primary" type="button" onClick={() => setIsCompetitorFormOpen(true)}>
                  <Plus size={16} />
                  Add your first competitor
                </button>
              </div>
            )}
          </div>
        </section>
        <section className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">CHECK HISTORY</p>
              <h2>Recent monitoring cycles</h2>
            </div>
          </div>
          <div className="history">
            {checks.length ? (
              checks.map((check) => (
                <div className="history-row" key={check.id}>
                  <span className={`dot ${check.status}`} />
                  <strong>{check.strategy}</strong>
                  <span>{time(check.started_at)}</span>
                  <span>{check.new_articles_found} new articles</span>
                  <span>
                    {check.duration_ms ? `${check.duration_ms}ms` : "Running"}
                  </span>
                </div>
              ))
            ) : (
              <div className="empty">No monitoring cycles recorded.</div>
            )}
          </div>
        </section>
        {isCompetitorFormOpen && (
          <div className="modal-backdrop" role="presentation">
            <section className="modal" role="dialog" aria-modal="true" aria-labelledby="add-competitor-title">
              <div className="panel-head">
                <div>
                  <p className="eyebrow">MONITORING FLEET</p>
                  <h2 id="add-competitor-title">Add competitor</h2>
                </div>
                <button className="modal-close" type="button" onClick={resetCompetitorForm} aria-label="Close add competitor form">×</button>
              </div>
              <form className="competitor-form" onSubmit={submitCompetitor}>
                <label htmlFor="competitor-name">Competitor Name</label>
                <input id="competitor-name" value={competitorName} onChange={(event) => setCompetitorName(event.target.value)} required autoFocus />
                <label htmlFor="website-url">Website URL</label>
                <input id="website-url" type="url" value={websiteUrl} onChange={(event) => setWebsiteUrl(event.target.value)} placeholder="https://example.com" required />
                <label htmlFor="blog-url">Blog URL <span>(optional)</span></label>
                <input id="blog-url" type="url" value={blogUrl} onChange={(event) => setBlogUrl(event.target.value)} placeholder="https://example.com/blog" />
                <label htmlFor="feed-url">Feed URL <span>(optional)</span></label>
                <input id="feed-url" type="url" value={feedUrl} onChange={(event) => setFeedUrl(event.target.value)} placeholder="https://example.com/feed.xml" />
                <label htmlFor="sitemap-url">Sitemap URL <span>(optional)</span></label>
                <input id="sitemap-url" type="url" value={sitemapUrl} onChange={(event) => setSitemapUrl(event.target.value)} placeholder="https://example.com/sitemap.xml" />
                <div className="modal-actions">
                  <button className="ghost" type="button" onClick={resetCompetitorForm} disabled={isSubmittingCompetitor}>Cancel</button>
                  <button className="primary" type="submit" disabled={isSubmittingCompetitor}>{isSubmittingCompetitor ? "Adding..." : "Add competitor"}</button>
                </div>
              </form>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
export default App;
