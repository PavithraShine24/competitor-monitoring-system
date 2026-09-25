"""Controlled demo publishers for RSS, sitemap, and direct-page detection."""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import html, json

articles = {"a": [], "b": [], "c": []}

def now(): return datetime.now(timezone.utc).isoformat()
def article(site, item):
    return f"http://localhost:9100/{site}/article/{item['slug']}"

class Handler(BaseHTTPRequestHandler):
    def send(self, body, content_type="text/html", status=200):
        encoded = body.encode(); self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(encoded))); self.end_headers(); self.wfile.write(encoded)
    def do_GET(self):
        path = urlparse(self.path).path.strip("/").split("/")
        if path == ["health"]: return self.send('{"status":"ok"}', "application/json")
        if len(path) >= 2 and path[0] in articles:
            site = path[0]
            if path[1] in {"feed.xml", "rss.xml"}:
                entries = ''.join(f"<item><title>{html.escape(x['title'])}</title><link>{article(site, x)}</link><pubDate>{x['published']}</pubDate><description>{html.escape(x['body'])}</description></item>" for x in articles[site])
                return self.send(f'<?xml version="1.0"?><rss version="2.0"><channel><title>Demo {site}</title>{entries}</channel></rss>', "application/rss+xml")
            if path[1] == "sitemap.xml":
                urls = ''.join(f'<url><loc>{article(site, x)}</loc><lastmod>{x["published"]}</lastmod></url>' for x in articles[site])
                return self.send(f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', "application/xml")
            if path[1] == "blog":
                links = ''.join(f'<a href="{article(site, x)}">{html.escape(x["title"])}</a>' for x in articles[site])
                return self.send(f'<html><head><title>Demo blog</title></head><body><main><h1>Demo blog</h1>{links}</main></body></html>')
            if len(path) >= 3 and path[1] == "article":
                match = next((x for x in articles[site] if x["slug"] == path[2]), None)
                if not match: return self.send("not found", status=404)
                return self.send(f'<html><head><link rel="canonical" href="{article(site, match)}"/><meta name="description" content="Demo article"/><script type="application/ld+json">{{"@type":"Article","headline":{json.dumps(match["title"])},"datePublished":{json.dumps(match["published"])}}}</script></head><body><article><h1>{html.escape(match["title"])}</h1><p>{html.escape(match["body"])}</p></article></body></html>')
        return self.send("not found", status=404)
    def do_POST(self):
        if urlparse(self.path).path != "/publish": return self.send("not found", status=404)
        length = int(self.headers.get("Content-Length", 0)); payload = json.loads(self.rfile.read(length) or b"{}")
        site = payload.get("site", "a"); title = payload.get("title", "Demo article"); item = {"slug": f"article-{len(articles[site]) + 1}", "title": title, "body": payload.get("body", "Controlled demo content."), "published": now()}; articles[site].insert(0, item)
        return self.send(json.dumps({"url": article(site, item), "published_at": item["published"]}), "application/json", 201)

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 9100), Handler).serve_forever()
