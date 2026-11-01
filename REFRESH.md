# REFRESH.md: data-refresh playbook

The daily refresh (scheduled task `microreactors-daily-refresh`, 16:00 local, on this Mac) follows
this file. A human running a refresh by hand follows it too.

## Cadence and the rolling PR

- **One open refresh PR at a time**, branch `refresh/<start-date>`, title `Refresh <start-date>: ...`,
  label-free. Find it with `gh pr list --state open --search "head:refresh/" --json number,headRefName,createdAt`.
- **Each daily run commits onto that branch.** No open refresh PR -> create the branch from an
  up-to-date `main` and open one.
- **Merge when the PR is 2 days old or older** (createdAt), after the review gate below passes.
  A run that merges starts no new PR; the next day's run opens one.
- Every run validates shipped data as well as adding new data (the `checks` agents and the gates).

## One run, step by step

```bash
cd /Users/pranava/Projects/microreactors
git fetch origin && git checkout <refresh branch> && git pull --ff-only   # or: git checkout main && git pull && git checkout -b refresh/$(date +%F)
D=$(date +%F)
python3 tools/refresh_init.py --date $D                    # pass dir, CONTRACT.md, prompts/, skip/
python3 tools/news_watch.py --json data/research/$D-refresh/skip/candidates.json   # RSS + SEC leads for the news agent
```

1. **Research agents: Haiku only, at most 4 running at once.** One agent per file in
   `data/research/$D-refresh/prompts/` (news, politics, deals, vendors, applications, costs, ideas).
   Prompt each with: "Read `<repo>/data/research/$D-refresh/prompts/<name>.md` and carry out that
   task exactly." Launch 4, then the other 3 as slots free. A daily run may skip agents whose
   tab rarely moves (costs, ideas, applications) on alternate days.
2. **Repair and verify quotes** (needs the venv, see below):
   ```bash
   V=~/.venvs/microreactors/bin/python
   $V tools/repair_pass_quotes.py data/research/$D-refresh
   $V tools/verify_pass_quotes.py data/research/$D-refresh      # FABRICATED / SLOPPY must be 0
   $V tools/check_pass_numbers.py data/research/$D-refresh      # UNSUPPORTED: fix the prose or drop the record
   python3 tools/research_pass.py validate data/research/$D-refresh
   ```
3. **Integrate:** `python3 tools/refresh_integrate.py data/research/$D-refresh --apply`, then
   `python3 tools/merge_news.py data/research/news`. Re-running on the same pass is safe
   (applied corrections and shipped ids are skipped). To ship a Type S application, set its
   `group` to a `data/segments.json` `_meta.groups` id (add a group there if none fits). Read `REPORT.md`; for every "needs a human"
   line, make the edit by hand only if the fetched source plainly supports it, else leave it.
4. **Read every new news item and correction against its source before committing.** Haiku
   paraphrases: check each number and date in the prose is on the cited page (the quote gate
   checks quotes, not prose). Drop what you cannot confirm.
5. **Cache new sources:** `python3 tools/fetch_source.py <every new url>` (extends the quote gate).
6. **Build and test:**
   ```bash
   python3 tools/build_gaps.py && python3 tools/build_data.py && python3 tools/build_meta.py
   $V tools/verify_quotes.py --cache            # MISMATCH must be 0
   $V -m unittest discover -s tests             # must pass; print the exit code, never tail -1
   $V tools/uat_paths.py                        # phone interaction cost; compare with the last run
   ```
7. **Commit** to the refresh branch (`Refresh <D>: <n> news, <n> corrections`), push, and append a
   section for the day to the PR body.
8. **Merge gate** (PR >= 2 days old): run `/code-review` on the PR diff in the main session,
   fix real findings, re-run step 6, then `gh pr merge <n> --merge`. Never merge red.

## Setup this needs

- Venv at `~/.venvs/microreactors` with `PyMuPDF==1.24.14 pypdf==5.1.0 playwright==1.48.0`
  (system python is stdlib-only; e2e layout tests and the PDF quote gate need it).
- `gh` authenticated as the repo owner. Repo-local git identity `Pranava Raparla
  <2497510+pranava0x0@users.noreply.github.com>`. No AI attribution in commits or PRs.

## Learned

- **2026-10-18: web search alone misses the news.** Four Haiku agents searching blind found 1 news
  item between them; `tools/news_watch.py` found 14 candidates from RSS + SEC in one run. Always run
  the watcher first and hand the news agent `skip/candidates.json`.
- **2026-10-08: Haiku finds leads well and quotes badly.** WebFetch returns a summary, so a
  "fetched" quote is often a paraphrase. `repair_pass_quotes.py` + `verify_pass_quotes.py` decide
  what ships, never the agent's own status flag.
- **`unverifiable` checks are wasted tokens.** The contract now forbids them; a check ships only
  with a fetched page behind it.
- **2026-10-21: X (x.com) is the best discovery layer for the last 72 hours.** Searched in the
  user's logged-in Chrome (Latest tab, `since:` operator), it surfaced 15 leads in four queries,
  including a Navy selection and a NANO supplier deal posted that morning, which the RSS watcher,
  Reddit and four Haiku web-search agents all missed (search indexes lag 1-2 days). Queries and
  noise patterns: `data/research/news/x-leads-2026-10-21.md`. Hand the leads to Haiku
  agents, but expect them to fail on anything under ~2 days old; the main session sources those
  in the browser. Discovery only: cite the primary page, never a post.
- **2026-10-21: a page that blocks scripts can still be cached.** radiantnuclear.com and inl.gov
  (403 to curl) and newsfilecorp.com (HTTP 202 with an empty body) all render in headless
  Playwright from the venv; index the rendered HTML with `fetch_source.py URL --from-file
  page.html --force` and the offline quote gate checks it. neimagazine.com and energynews.pro
  403 even to Playwright: verify those in the browser pane (`document.body.innerText`). An empty
  body is now FETCH FAILED / UNREACHABLE in both tools, not a page the quote is missing from.
- **2026-10-21: two refreshes in one checkout collide.** The scheduled routine ran while a manual
  refresh was mid-pass, committed its working tree and opened the PR, dropping an item the manual
  run had verified. Before a manual run, check `gh pr list --search head:refresh/` and the
  sessions list; a routine that finds an uncommitted pass dir it did not create should stop.
  `refresh_integrate.py` re-runs now append to `refresh-<date>.json` instead of overwriting it.
- **2026-10-27: SEC EDGAR full-text search 403s the GitHub noreply address.** After the history
  rewrite that removed the personal email, `news_watch.py` sends
  `2497510+pranava0x0@users.noreply.github.com` and efts.sec.gov answers 403 (a generic
  `@example.org` contact gets 200, so it is the domain, not the tool). The SEC leg is dark until
  the contact is read from `SEC_CONTACT_EMAIL` (open PR #29) and that variable is set to a real
  mailbox. The watcher reports it as `unreachable SEC EDGAR: HTTPError`, not as zero filings.
- **2026-10-27: the agent hook caps this project at 2 concurrent agents**
  (`.claude/agent-cap`), not the 4 this playbook assumed. Seven Haiku lanes plus a prospects
  lane ran as 2-wide waves in ~20 minutes. Order the waves by what the run is for: this run
  put news and deals first, applications and politics second.
- **2026-10-27: main-session web search first, then agents.** Eight searches in the main
  session (one `extended`) found the week's leads in ~2 minutes and went to every agent as
  `skip/web-leads.md`. Agents still could not open 403 press releases (BWXT, GlobeNewswire);
  the adjudicator (Sonnet) retried alternate copies.
- **2026-10-27: measure phone navigation cost each refresh.** `tools/uat_paths.py` (venv)
  prints taps, swipes and screens for 14 key questions. Baseline after this run at 375x812:
  mean 1.65, 0 swipes (re-measured 1.69 on 2026-10-31 after a tool fix, below). A new tab, sub-tab or Home block that raises the mean is a regression
  to justify in the PR.
- **2026-10-28: `refresh_integrate.py` drops `unsupported` verdicts without a report line.** Only
  `outdated`/`wrong` are applied and only `confirmed` is counted, so an `unsupported` check vanishes from
  REPORT.md. Read every check in the pass files, not just the report. Haiku also judges "unsupported"
  after opening one of a row's sources: open them all before acting on it.
- **2026-10-28: a check that a row is "outdated" must quote the whole shipped sentence.** The costs
  agent flagged a 2023 base rate as stale; the same sentence already gave the 2026 rate. Before applying
  an `outdated` check, grep the shipped field for the corrected figure.
- **2026-10-28: the agent-cap hook allows 2 concurrent agents here.** Seven agents run as four pairs
  (~25 min wall clock). Start quote repair on finished files while the last pairs run.
- **2026-10-29: two different dates for one filing are not a contradiction.** The vendors agent marked
  "NRC notice filed 2025-02-17" wrong because Westinghouse says the letter was submitted 2025-02-28.
  Both are true: one is the letter's date, the other is the submission date. Before applying a
  date correction, check whether the two dates name different events, and write both if they do.
  The deals agent also re-checked `canada-src` for a second day running. A shipped row that passed a
  check in the last week is wasted tokens; the skip list should carry recently checked ids.
- **2026-10-30: integrate splices a correction into the claim's sentence, and has no "rejected" verdict.**
  A costs check's claim was the first clause of a longer sentence; `--apply` would have left
  "...is proposed.: its per-utility appendix..." in the shipped note. Read each correction against the
  surrounding text before `--apply`. To overrule an agent check, set `verdict: confirmed`, keep the
  agent's call in `agent_verdict`, and write why in `review`; the validator rejects any other verdict.
  Two of seven checks were overruled this run, both because the agent read one source or one clause.
- **2026-10-31: `uat_paths.py` charged free scroll to every journey after the first.** Re-navigating to
  the same `#home` URL is a same-document hash change, and the anchor jump counted as travel already
  done (phone lead story 1.27 screens instead of 1.94). Journeys now start from `about:blank`; the
  corrected phone baseline is **1.69**. Compare against that number, not 1.65.
- **2026-10-31: a refresh in a git worktree needs two fixes before agents launch.** `refresh_init.py`
  writes prompts naming the main checkout, so agents would write there: `sed` the pass dir's prompts
  and CONTRACT.md to the worktree path. `data/cache/` is gitignored and empty in a fresh worktree, so
  the quote gate checks nothing: symlink it to the main checkout's cache (and add `data/cache` to
  `.git/info/exclude`, since the gitignore's `data/cache/` does not match a symlink).
- **2026-10-31: radiantnuclear.com now times out headless Playwright too** (the 10-21 note no longer
  holds). Read it in the browser pane, write the paragraphs you cite to an HTML file, and index that
  with `fetch_source.py URL --from-file`. A quiet week: four Haiku lanes found one item between them
  (Centrus); the main session's own searches found the week's only microreactor event (Radiant's DSA).
- **2026-11-01: `verify_pass_quotes.py` labels a check's punctuation slip FABRICATED.** A check record
  has no `name`/`speaker`, so any span not found verbatim falls to FABRICATED ("subject: (none)"),
  never SLOPPY. The Valar KUNC quote was real; Haiku had swapped the page's trailing comma for a
  period. When a check is FABRICATED with no subject, grep the page for the span before dropping it.
- **2026-11-01: a weekend with an empty watcher is a confirmations-only day.** The watcher found 2
  SMR leads, web search nothing after 10-30, and four agents spent ~620K tokens on 5 confirmations.
