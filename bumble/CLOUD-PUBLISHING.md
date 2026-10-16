# Direct cloud publishing contract

The repository can now receive a complete article JSON from the existing cloud briefing producer. It validates and compiles the archive on GitHub Actions, then explicitly requests a GitHub Pages build after a compiler-generated commit. No desktop or separate machine is required for that downstream path.

The publication instructions below are saved to both existing cloud schedules. Their installed GitHub plugin reached the repository in the Weekly duplicate-check run. The first fresh scheduled write remains to be observed. The desktop relay is paused.

## Instructions to append to the existing AM, PM, and Weekly schedules

After producing the scheduled BLAQUE BAUX briefing, publish the same complete edition to `blaquebaux/site`, branch `main`, as `bumble/briefings/YYYY-MM-DD-morning.json`, `YYYY-MM-DD-afternoon.json`, or `YYYY-MM-DD-weekly.json`. Use the repository's `bumble/PUBLISHING.md` schema and the current `scripts/publish-briefings.py` validation rules. Preserve the scheduled generation times; do not create duplicate generating tasks. Use actual supporting HTTPS source URLs, the real source observation cutoff, and the edition date in America/New_York. Preserve observations separately from interpretation and outlook. No em dashes in editorial copy; use semicolons, colons, or separate sentences as meaning requires. Never fabricate live figures, source URLs, or timestamps.

Use the existing GitHub connector's authenticated Git data tools. Do not use the single `create_file` operation for scheduled articles; repeated OpenAI safety-gateway rejections have occurred before GitHub receives that request. The authorized handoff is an atomic Git commit:

1. Fetch `refs/heads/main` and its commit/tree SHA. Fetch the destination path. If it exists, stop successfully only when its bytes are identical; otherwise report an immutable-edition conflict and do not overwrite.
2. Validate the complete JSON locally against `scripts/publish-briefings.py`. Preserve every section, source, timestamp and verification field; never split, summarize or reconstruct the payload to get it through a policy check.
3. Create one UTF-8 blob containing the exact JSON, create a tree based on the fetched main tree with only the new `bumble/briefings/<id>.json` entry, then create a commit with the fetched main commit as its sole parent.
4. Move `refs/heads/main` with the fetched SHA as the expected SHA. On a lease conflict, fetch main again, confirm the destination is still absent, rebuild the tree and retry. Use at most three attempts with bounded backoff. Never force-update.
5. Inspect the `Validate and publish reviewed briefings` run for that commit and then request the public article URL. Success requires both a successful workflow and a public page containing the edition id.

If all three attempts fail, create or update one GitHub issue titled `BUMBLE publication failed: <edition-id>` containing the edition id, failure stage, attempt count, UTC failure time and workflow/commit link when available. Do not put unpublished article copy in the issue. Report the failure to the scheduled chat. A retry always reuses the same edition id and exact payload.

Create only the new article input; the GitHub workflow compiles `bumble/briefings.json` and deploys the current site. Do not modify the workflow, navigation, or other site content as part of routine publication. The user's authorization covers routine publication to this site without asking again.

Only use `verified` status when every factual claim has a supporting checked URL. Otherwise use `archived-unverified`, preserve provenance and show the explicit verification-pending source note. Never call an unverified archived edition a live quote feed. Missing data should be identified plainly rather than guessed.

Inspect the `Validate and publish reviewed briefings` workflow result and the public article link before declaring publication successful. Report publication failure or missing GitHub authorization without claiming the article is live. Ad hoc briefings supplied by the user are additional editions and require their explicit publication instruction.

## Deployment test

Manually run the `briefings.yml` workflow against main. It validates the real existing editions, rebuilds the archive without adding fixture articles, and exercises the explicit GitHub Pages build request. This tests the downstream cloud path; it does not prove upstream scheduling or GitHub access from the original briefing task.
