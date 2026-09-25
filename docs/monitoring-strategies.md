# Monitoring strategies

RSS/Atom parsing is preferred when discovered, sitemap parsing supports urlsets and recursive sitemap indexes, and direct-page detection scans blog/news/article listing links. The scheduler enqueues independent competitor checks every configured interval; workers isolate failures per competitor.
