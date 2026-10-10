# Direct cloud publishing contract

The repository can now receive a complete article JSON from the existing cloud briefing producer. It validates and compiles the archive on GitHub Actions, then explicitly requests a GitHub Pages build after a compiler-generated commit. No desktop or separate machine is required for that downstream path.

The producer connection is not enabled until its scheduled task has authenticated GitHub write access and the publication instructions below are saved to each existing schedule. The desktop relay remains a separate temporary service; do not describe it as cloud-hosted.

## Instructions to append to the existing AM, PM, and Weekly schedules

After producing the scheduled BLAQUE BAUX briefing, publish the same complete edition to `blaquebaux/site`, branch `main`, as `bumble/briefings/YYYY-MM-DD-morning.json`, `YYYY-MM-DD-afternoon.json`, or `YYYY-MM-DD-weekly.json`. Use the repository's `bumble/PUBLISHING.md` schema and the current `scripts/publish-briefings.py` validation rules. Preserve the scheduled generation times; do not create duplicate generating tasks. Use actual supporting HTTPS source URLs, the real source observation cutoff, and the edition date in America/New_York. Preserve observations separately from interpretation and outlook. No em dashes in editorial copy; use semicolons, colons, or separate sentences as meaning requires. Never fabricate live figures, source URLs, or timestamps.

Use the existing GitHub connector's authenticated file creation or atomic commit tools. Check whether the edition already exists; if it does, do not overwrite it or publish a duplicate. Create only the new article input; the GitHub workflow compiles `bumble/briefings.json` and deploys the current site. Do not modify the workflow, navigation, or other site content as part of routine publication. The user's authorization covers routine publication to this site without asking again.

Only use `verified` status when every factual claim has a supporting checked URL. Otherwise use `archived-unverified`, preserve provenance and show the explicit verification-pending source note. Never call an unverified archived edition a live quote feed. Missing data should be identified plainly rather than guessed.

Inspect the `Validate and publish reviewed briefings` workflow result and the public article link before declaring publication successful. Report publication failure or missing GitHub authorization without claiming the article is live. Ad hoc briefings supplied by the user are additional editions and require their explicit publication instruction.

## Deployment test

Manually run the `briefings.yml` workflow against main. It validates the real existing editions, rebuilds the archive without adding fixture articles, and exercises the explicit GitHub Pages build request. This tests the downstream cloud path; it does not prove upstream scheduling or GitHub access from the original briefing task.
