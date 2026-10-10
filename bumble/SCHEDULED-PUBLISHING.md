# Scheduled publishing connection

The existing cloud tasks **BLAQUE BAUX Market Pulse** and **BLAQUE BAUX Weekly Brief** now carry direct publication instructions for `blaquebaux/site`, branch `main`. Their original generation schedules are preserved. Scheduled report generation and GitHub validation/publication run in the cloud; no desktop or separate machine is needed for this configured path.

Cloud task identities:

- Market Pulse: `6abe86724fb08191b2cbf909be92ec5a`; the existing custom recurring schedule is unchanged.
- Weekly Brief: `6abe81ccb00c819193316f60bac66334`; the existing Saturday schedule is unchanged.

Each task reads [CLOUD-PUBLISHING.md](CLOUD-PUBLISHING.md) and [PUBLISHING.md](PUBLISHING.md), then creates only its complete, sourced article JSON in `bumble/briefings/` through the installed GitHub plugin. Existing editions must not be duplicated or silently overwritten. GitHub Actions validates the inputs, compiles `bumble/briefings.json`, and explicitly requests a Pages build after any compiler-generated commit.

The original briefing conversation is `6a920c82-1ff0-83ea-b4be-bb7adfe637d5`. It continues to retain the generated reports and publication results. The site does not scrape that private conversation.

## Validation on October 10, 2026

Both cloud prompts were saved and re-opened to confirm persistence. The GitHub plugin is installed with write capabilities. A manual GitHub workflow run passed the publisher and importer tests, compiled the actual existing archive, and successfully requested a Pages build; Pages reported the new configuration built successfully. A manual Weekly task run reached GitHub, read both contracts, and found the existing October 10 edition, so it left that article unchanged. No test article or invented market figures were published.

A fresh scheduled article creation has not yet been observed. The next eligible edition will exercise the producer's write path. Publication failures must be reported explicitly rather than described as live articles. Unresolved source claims retain the verification-pending label.

## Retired desktop relay

The earlier desktop heartbeat **Publish BLAQUE BAUX briefings to BUMBLE** (`publish-blaque-baux-briefings-to-bumble`) is PAUSED. It must not be reactivated alongside direct cloud publication. Its `publishing-state.json` baseline and importer are retained for archival maintenance and tests, but are no longer the active scheduling connection.

Ad hoc briefings supplied by the user remain additional editions and require their explicit publication instruction. Routine scheduled publication is already authorized by the user. This connection generates no substitute reports if the original task fails.
