# Refresh 2026-10-27 handoff (branch refresh/2026-10-27, from origin/main)

Done + committed: 1555a44 (phone nav 2 rows, hero Latest line, #home anchor fix, copy cleanup,
tools/uat_paths.py: 375px mean cost 2.83 -> 1.65, swipes 13 -> 0; 768px 1.56 -> 1.32),
af786d7 (Type P prospects in research_pass/refresh_integrate, REFRESH.md learned entries).
Full suite was 155 OK before af786d7.

Pass files: news(3 items) deals(2 checks + 3 opportunities -> to become prospects)
applications(5) politics(1 check, 1 docket, 1 item: NRC final rule DOE/DoD authorization)
vendors(1 item Antares Mark-1 NSDA, 1 check) ideas(1 check, ERCOT durations unsupported)
prospects(0; Sonnet adjudicator building up to 8 with load "Not published" allowed).

Running: Sonnet adjudicator (prompts/adjudicate.md) -> writes ADJUDICATION.md, edits pass files.

Remaining (REFRESH.md steps 2-8): repair/verify quotes, check_pass_numbers, validate,
refresh_integrate --apply, merge_news, read each new item vs source, set `group` on
applications, fetch_source.py new urls, build_gaps/build_data/build_meta, verify_quotes --cache,
unittest, uat_paths, commit, push, open PR (plain-text model disclosure, no AI co-author).
Open human items: SEC_CONTACT_EMAIL (PR #29), Eielson binding flag (adjudicator answer a).
