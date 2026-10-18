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
