# Reddit as a news discovery layer: patterns (captured 2026-10-02)

Reddit is discovery only. Every record in `reddit-2026-10-02.json` cites the linked article or primary document, fetched and quote-checked, never the thread.

## What works from a script (unauthenticated curl, browser User-Agent)

| Endpoint | Result |
|---|---|
| `www.reddit.com/r/X/new/.rss?limit=100` | 200. Atom feed, up to 100 posts, link posts carry the target URL in the entry HTML as `[link]`. Best option. |
| `www.reddit.com/r/X/.rss` | 200, 25 posts. |
| `www.reddit.com/search.rss?q=...&sort=new&t=month` | 200, ~25 entries. Also returns matching subreddit names as entries. Recall is thin; sort order is loose. |
| `www.reddit.com/r/X/new.json`, `search.json`, `api.reddit.com/...` | 403 (HTML block page, ~190 KB). Do not use. |
| `old.reddit.com/...json` or `.rss` | 302 to www, then returns an HTML shell, not data. |
| `www.reddit.com/r/NNE/...` | 404. The sub does not exist (see list below). |

Rate limit: the unauthenticated bucket is about one request per 60 seconds. Every response carries `x-ratelimit-remaining: 0.0` and `x-ratelimit-reset: ~58`. A second request inside the window returns 429 with an empty body and `reset` of the seconds left. The working pattern is: request, on 429 sleep `reset + 2`, retry once. Budget roughly 1 feed per 1.5 to 2 minutes; 9 feeds plus 14 searches took about 45 minutes and ~65 requests including 429 retries. Run the loop in the background and do primary-source fetching meanwhile.

Parser: feed `<entry>` has `<updated>`, `<title>`, and `<content>` (escaped HTML). Pull `href="..."` before `>[link]<` for the article URL. A 100-post pull spans 16 days of r/nuclear but only 5 days of r/energy, so high-volume subs need `?after=` paging or search instead.

## Subreddits ranked by microreactor yield (Sept 1 to Oct 2, 2026)

| Sub | Posts pulled | Microreactor-relevant | Notes |
|---|---|---|---|
| r/nuclear | 100 (Sep 15 to Oct 2) | ~8 | Best source. Links straight to WNN, Utility Dive, NPR, Reuters. Some reposts of the same story in r/NuclearPower. |
| r/NuclearPower | 100 (Sep 6 to Oct 2) | ~6 | Heavy overlap with r/nuclear; career-advice noise. Found the WNN Deep Fission borehole story and the West Virginia NLIC story. |
| r/NanoNuclear | via search only | 2 | Auto-posts NANO Nuclear press releases (acquisition, LOI). Worth a direct feed pull next time. |
| r/OKLOSTOCK | via search only | 2 | Posts NRC documents (ML numbers) and stock chatter. The NRC Oklo letter lead came from here. Note `r/OKLO` is dead (last post April 2026). |
| r/Utah, r/SaltLakeCity | 100 each | 1 (Valar Beehive, NPR link) | Almost all non-nuclear. Only useful on a big local story. |
| r/uraniumsqueeze | 100 | 0 | Stock hype and explorer drilling results. One Oklo "leaps" post. |
| r/Idaho, r/IdahoFalls, r/alaska, r/energy | 100 each | 0 | No microreactor posts survived a keyword filter. |
| r/smallmodularreactors | 17 posts total, last Nov 2025 | 0 | Dead. |
| r/NNE | 404 | n/a | Does not exist; use r/NanoNuclear. |
| r/valar_atomics, r/EveryoneVsDataCenters | search hits only | 1 lead | Opposition and tracker posts; the "Valar drops 10,200 acres" lead lives here but has no fetched primary. |

## Query terms

Worked: `microreactor`, `Valar Atomics`, `Antares nuclear`, `Oklo Aurora`, `Radiant Kaleidos`, `HALEU microreactor`. Each surfaced 1 to 3 real items and mostly repeats of what r/nuclear already showed.
Failed: bare company names (`Aalo`, `Radiant nuclear`) return Hindi food posts, game mods and fiction. Always pair the name with `nuclear` or `reactor`. `Reactor Pilot Program` returned airline pilot posts.

## Noise patterns

- Stock-hype subs repost the same press release with a price target; the press release URL is the useful part.
- Image posts (`i.redd.it`) are screenshots of a headline; search the headline text for the real article.
- `autonocion.com` and similar rewrite sites paraphrase DOE or trade-press stories (eVinci hot criticality, Oklo Groves) and sometimes mislabel the facts; find the DOE or WNN original.
- Reposts across r/nuclear and r/NuclearPower double-count the same story.
- Reddit titles ahead of the primary are often wrong on the date: check the article, not the post.

## What this pass found versus data/news.json

11 new records, none duplicating an existing id or source URL. Items Reddit surfaced that were already in the tracker (Army Janus, Radiant-Centrus, Navy Crane, Kairos-Samsung, eVinci criticality, FERC-Oklo, Deep Fission NSDA) confirm the Sept 26 refresh was current to about Sept 24. Net new coverage was mostly Sept 11 to Oct 1 items: Valar Beehive, NANO fuel-license purchase, General Matter filing, Natura salt, Antares space award, NRC-Oklo letter.

## Repeatable recipe

1. Pull `r/nuclear`, `r/NuclearPower`, `r/NanoNuclear`, `r/OKLOSTOCK` new.rss (4 requests, ~8 minutes with retries).
2. Run 4 to 6 `search.rss` queries pairing company names with `nuclear` or `reactor`.
3. Filter titles by keyword, drop reposts, take the article URL from the entry.
4. Dedupe against `data/news.json` ids, headlines and source URLs.
5. Fetch each primary source (NRC and some local outlets 403 a bare curl; WebFetch can retrieve the NRC PDF), confirm the date, and copy a verbatim span.
