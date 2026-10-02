"""tools/news_watch.py Reddit layer, offline: a link post must resolve to the
article it points at (the thread is never a citation), a self post must keep its
thread, and every entry must parse. A
link regex that goes quiet would hand every candidate back as a Reddit thread,
which looks like a working scan."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import news_watch as nw  # noqa: E402

FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
  <title>Valar files BLM application for Utah campus</title>
  <link href="https://www.reddit.com/r/nuclear/comments/abc123/valar/"/>
  <updated>2026-09-30T14:02:11+00:00</updated>
  <content type="html">&lt;span&gt;&lt;a href=&quot;https://www.wlrn.org/npr-breaking-news/2026-09-30/valar&quot;&gt;[link]&lt;/a&gt;&lt;/span&gt; &lt;a href=&quot;https://www.reddit.com/r/nuclear/comments/abc123/valar/&quot;&gt;[comments]&lt;/a&gt;</content>
</entry>
<entry>
  <title>Career question about microreactor operators</title>
  <link href="https://www.reddit.com/r/nuclear/comments/def456/career/"/>
  <updated>2026-09-29T10:00:00+00:00</updated>
  <content type="html">&lt;p&gt;self text&lt;/p&gt; &lt;a href=&quot;https://www.reddit.com/r/nuclear/comments/def456/career/&quot;&gt;[link]&lt;/a&gt;</content>
</entry>
<entry>
  <title>r/microreactor</title>
  <link href="https://www.reddit.com/r/microreactor/"/>
  <updated>2026-09-28T10:00:00+00:00</updated>
  <content type="html">&lt;p&gt;a subreddit&lt;/p&gt;</content>
</entry>
</feed>"""


class RedditEntries(unittest.TestCase):
    def setUp(self):
        self.rows = nw.reddit_entries(FEED, "Reddit r/nuclear")

    def test_link_post_resolves_to_article(self):
        self.assertEqual(self.rows[0]["url"], "https://www.wlrn.org/npr-breaking-news/2026-09-30/valar")
        self.assertEqual(nw.norm_date(self.rows[0]["date_raw"]), "2026-09-30")

    def test_self_post_keeps_thread(self):
        self.assertEqual(self.rows[1]["url"], "https://www.reddit.com/r/nuclear/comments/def456/career/")

    def test_every_entry_parsed(self):
        self.assertEqual(len(self.rows), 3)


if __name__ == "__main__":
    unittest.main()
