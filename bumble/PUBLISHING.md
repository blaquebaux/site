# BUMBLE editorial publishing

The handset layout is preserved. Signal collection and editorial publication use separate feeds. An hourly signal refresh never removes the briefing archive.

Put one reviewed JSON article in `bumble/briefings/<id>.json`. Run `python3 scripts/publish-briefings.py` before submitting changes. The workflow validates submissions and rebuilds `bumble/briefings.json` when reviewed inputs reach main. Main is the production GitHub Pages source; merging is deployment and requires the site owner's authorization.

Required format:

```json
{
  "id": "2026-10-09-afternoon",
  "kind": "afternoon",
  "status": "mock",
  "title": "Market Pulse: example structure",
  "summary": "Illustrative editorial format; contains no live market data.",
  "published_at": "2026-10-09T15:47:00-04:00",
  "observed_at": "2026-10-09T15:45:00-04:00",
  "reviewed_by": "Named editor",
  "dash_replacement": ";",
  "sections": [
    {"heading": "What changed: observed", "paragraphs": ["Reviewed observations with attributable sources."]},
    {"heading": "What mattered: interpretation", "paragraphs": ["Editorial interpretation."]},
    {"heading": "What we are watching", "list": ["Upcoming event."]},
    {"heading": "Where we see things going", "paragraphs": ["Conditional outlook."]}
  ],
  "signal": "BLAQUE BAUX Signal: conditional synthesis.",
  "sources": [{"label": "Actual supporting source title", "url": "https://example.com/"}]
}
```

This is a schema example, not a publishable report. Replace example sources and copy. Kinds are `morning`, `afternoon` (Monday through Friday in America/New_York), and `weekly` (Saturday). Timestamps require an explicit UTC offset; the reader always displays ET, including daylight saving. `observed_at` describes the market snapshot, not the time a feed was fetched. Weekly titles and sections should state the reviewed date range.

`verified` means an editor checked all factual claims against the actual linked sources. It does not mean streaming quotes. `mock` means illustrative, unverified copy. `archived-unverified` is reserved for recovered historical editions whose full factual and citation review remains pending; it is distinct from a mock. Original edition dates and archival upload timestamps are displayed separately. All statuses are displayed on cards and articles. Do not promote cached ChatGPT summaries with unresolved citation markers to verified articles. Source retrieval and factual review are human editorial obligations, not inferred from a JSON flag.

Em dashes in editorial text are replaced with the chosen semicolon or colon during compilation; URLs are preserved. Prefer editing punctuation manually for sentence meaning. No raw HTML is accepted. Article links use `/bumble/#brief/<id>` and survive reload; the detail view includes the archive navigation and source links.

No automatic connection to the ChatGPT scheduled briefings exists in this repository. The producing task must export complete, sourced JSON to this editorial input directory through an authorized repository update. The publisher does not generate or invent market data. The initial archive is intentionally empty because recovered reports are incomplete and their citations are unresolved.

Legacy EDGAR/TAPE items remain visible and are labeled as source events with unverified analysis. The publisher does not retroactively verify those items. Failure of either feed is visibly reported while the other remains usable.
