# BLAQUE BAUX v2.0 requirements review

Audit date: 2026-10-13  
Scope: public site, `blaquebaux/site` main branch, and the public `blaquebaux` GitHub organization  
Positioning: **Quantitative Intelligence for Finance**  
Operating line: **Build. Validate. Integrate.**  
Parent identity: **A Carter Warrens Company**

## Executive finding

BLAQUE BAUX already has a broad public research product, not a placeholder marketing site. The main branch contains 133 Corpus entries, interactive Analysis, Labs, Capstone, BLOCK, Tracker, Toolkit, and Bumble experiences, plus automated briefing and market-data pipelines. The highest-priority gap is coherence: product status, data freshness, performance type, provenance, and catalog counts have been expressed differently across pages.

The v2.0 principle is simple: every claim should tell the reader whether it is a research finding, a simulation, an operational software status, an indicative public-data observation, or verified actual performance. The public site currently supports the first four. It does not establish the fifth.

## Sources and audit method

- Live site: <https://www.blaquebaux.com/>
- GitHub organization: <https://github.com/blaquebaux>
- Site repository: <https://github.com/blaquebaux/site>
- Source inspected from the repository main branch at the audit date.
- Corpus inventory derived from the 133 rendered cards in `corpus/index.html`: 1 LIVE, 5 LIVE PATH, 3 LIVE DRIVER, 19 VALIDATION, 7 GOVERNED capstones, 33 RESEARCH, 14 CONCEPT, and 51 NULL.
- The first Corpus section contains 25 entries: 9 operational labels and 16 validation sleeves. Three additional VALIDATION labels are capstones, which explains why the site-level validation count is 16 while the total label count is 19.
- Public crawl results were treated as deployment observations, not as the source of record. During this audit, the crawler returned a stale 61-entry Corpus page while the repository contained 133 entries. Production must be verified after merge and deployment.

## Product inventory

| Capability | State | Evidence | v2.0 requirement |
|---|---|---|---|
| Brand and company positioning | Partial | Homepage and metadata used systematic-research language; footers used “research initiative” | Use the approved three-part lockup consistently while preserving page-specific product copy |
| Global navigation | Existing, inconsistent at edges | Shared navigation exists on all main index pages; Corpus link order differed; Start was absent from the sitemap; the derivatives article uses a separate local nav | Enforce one destination set, visible current-page state, keyboard dismissal, and sitemap coverage |
| Corpus | Existing | 133 rendered entries with status, finding, and repository link | Keep counts testable; define statuses; add per-entry evidence metadata in a later phase |
| Analysis | Existing, partial | Client-side ticker classification, factor estimates, portfolio scoring, mandate fit, and repository links | Label estimates and public spot values accurately; add methodology/version provenance and graceful data-state tests |
| Bumble | Existing | Reviewed event feed and briefing archive with source links, reviewer, observation time, and archive state | Preserve compact editorial voice and no-em-dash rule; expose feed freshness and empty/error states clearly |
| Tracker | Existing, partial | Simulated capstone series, benchmark comparisons, public crypto context, FRED snapshot, and indicative options | Keep simulation disclosure adjacent to every performance view; add source timestamps and automated stale-data states |
| Labs | Existing, partial | Interactive explanatory studies with a prototype disclaimer | Distinguish repository findings from user-controlled scenarios; do not present browser calculations as newly validated results |
| Capstone | Existing, partial | Interactive allocation research and remote factoid JSON with bundled fallback | Rename data freshness labels; retain simulated/gross-of-cost disclosure; version the source artifact |
| BLOCK | Existing | 120-strategy derivatives reference, factoids, and a derivatives-honesty article | Rename data freshness labels; add direct methods and source links for aggregate claims |
| Toolkit | Existing | Validation methods, audit claims, repository links, and batch descriptions | Tie audit counts to a dated artifact and avoid presenting an incomplete audit as corpus-wide coverage |
| About and provenance | Partial | Founder, Carter Warrens relationship, FAQs, disclaimers, and partnership copy | Remove unsupported deployment/performance claims; define the company and terminology in one authoritative location |
| Structured data and discovery | Partial | Canonicals, Open Graph data, JSON-LD, robots, sitemap | Align names/descriptions, include every public entry page, and add automated checks |
| Accessibility and resilience | Partial | Semantic controls and focus handling exist on key pages | Add automated keyboard, reduced-motion, contrast, load-failure, and mobile checks |
| Verified live performance | Missing | No audited account record, administrator, custodian statement, or verification artifact is published | Do not claim it; define evidence and legal review required before introducing it |
| Central research registry | Missing | Counts and status copy are duplicated in HTML and JSON snapshots | Create one versioned registry that generates Corpus, homepage counts, status definitions, and cross-links |
| Release evidence | Missing | No site-wide contract test or preview checklist existed | Run automated content contracts and browser smoke tests on every review branch |

## Requirements and acceptance criteria

### P0: approved positioning and claim safety

1. The homepage title and hero use “Quantitative Intelligence for Finance.”
2. “Build. Validate. Integrate.” remains visible as the operating line.
3. “A Carter Warrens Company” replaces “research initiative” in primary identity locations.
4. “Live” is never used as shorthand for actual performance unless a verified actual-performance artifact exists.
5. Operational labels such as LIVE PATH are explicitly defined as software/research maturity.
6. Simulated and hypothetical performance remains labeled near the result, including data window, benchmark, rebasing method, and cost treatment.
7. Indicative public quotes are labeled indicative or delayed, never execution-grade.
8. No copy states or implies proprietary-capital deployment or an attributable live track record without evidence and legal approval.

### P0: navigation and discovery

1. Every primary page exposes Home, Start here, System, Corpus, Analysis, Labs, Capstone, BLOCK, Tracker, Toolkit, Bumble, About, Carter Warrens, and GitHub.
2. Each page marks its current destination where applicable.
3. The menu works without JavaScript and supports outside-click and Escape dismissal with JavaScript.
4. All public primary pages are present in `sitemap.xml`.
5. Internal root-relative links resolve in a local static-server crawl and in the deployed GitHub Pages path model.

### P1: inventory, counts, and taxonomy

1. Corpus rendered-card count equals 133 until the registry changes.
2. Section headers equal their rendered contents: active 25, capstone 14, research 29, concept 14, null 51.
3. Homepage summary counts reconcile to the same taxonomy: operational 9, capstone 14, validation 16, research plus concept 43, null 51.
4. “Catalog entry,” “repository,” and “sleeve” are not treated as interchangeable unless the underlying object really is each of those things.
5. Future count changes occur through a central registry or fail an automated contract test.

### P1: interactive product verification

1. Analysis loads `data.json`, reports its as-of date, handles unknown tickers, runs all example portfolios, and labels Coinbase spot as indicative.
2. Bumble loads both event and briefing data, opens and closes detail views, retains source links, displays reviewer and timestamps, and contains no em dashes in editorial content.
3. Tracker loads `performance.json`, renders every sleeve, switches tabs by mouse and keyboard, and distinguishes simulated sleeves from delayed or indicative market context.
4. Tracker handles unavailable CoinGecko, FRED, Nasdaq, and Yahoo data without substituting invented values.
5. Labs identifies fixed repository findings separately from interactive scenarios.
6. Capstone and BLOCK identify whether data came from the current remote source or the bundled snapshot.

### P1: cross-page research links and provenance

1. Every named sleeve shown in Analysis, Labs, Capstone, Tracker, or Toolkit links to its Corpus entry or canonical GitHub repository.
2. Every aggregate claim includes an as-of date, method note, and source artifact where feasible.
3. Corpus remains the human-readable index; GitHub remains the code and history source of record.
4. Each data-backed product exposes: source, as-of time, transformation/method, simulation status, and limitations.

## Dependencies

| Dependency | Needed for | Current status |
|---|---|---|
| Versioned central research registry | Count consistency and generated cross-links | Not present |
| Browser test runtime | Full interaction, keyboard, mobile, and failure-state verification | Not present in repository |
| Stable public-data APIs and CORS | Analysis spot, Tracker crypto/macro/options | External and failure-prone; fallbacks exist only for some views |
| Dated methods artifacts | Provenance for aggregate and performance claims | Partial across repositories |
| Legal/compliance review | Any capital, advisory, offer, or actual-performance language | Required before reintroduction |
| Independent performance evidence | Verified live-performance claims | Not available in audited sources |
| GitHub Pages deployment access | Production verification | Repository access exists; deployment is intentionally outside this review change |

## Implementation roadmap

### Phase 0: review branch, completed in this change

- Apply the approved positioning to title, hero, shared navigation, About, README, and primary footers.
- Clarify operational, simulated, indicative, and verified-performance terminology.
- Remove unsupported capital-deployment and track-record statements.
- Add Start to the sitemap.
- Add source-grounded requirements and content-contract tests.

### Phase 1: completed in this review branch

- Created `research-registry.json` with canonical id, repository, category, status, finding, evidence date, methods link, related products, and direct Corpus URL.
- Added a reproducible registry builder and contract checks that reconcile homepage counts and Corpus sections.
- Added stable Corpus anchors and direct entry links from Analysis, Labs, Tracker, Capstone, and Toolkit while retaining canonical repository links where both are useful.
- Added a same-origin browser smoke harness for navigation, Analysis, Bumble, Tracker, and mobile-width rendering.
- Added visible stale, unavailable, and last-success states for Analysis, Bumble, Tracker crypto, FRED, options, and simulated performance data.

### Phase 2: two to four iterations

- Add per-study provenance drawers with data window, benchmark, costs, validation stage, code commit, and limitations.
- Add a release manifest containing site commit, registry version, and data artifact timestamps.
- Add accessibility checks and a preview deployment gate.
- Consolidate duplicated navigation markup through a safe static build step while preserving no-JavaScript navigation.

### Phase 3: evidence-gated only

- Introduce actual-performance surfaces only after independent evidence, operational controls, legal review, and a clear separation between simulated, paper, proprietary, and client results.
- Add real-time or Bloomberg-level features only with licensed data, entitlements, redistribution rights, timestamp and latency disclosure, and operational monitoring.

## Test plan

- Run `python3 -m unittest discover -s tests`.
- Serve the repository root with a local static server and open every sitemap URL.
- Exercise Analysis examples, unknown inputs, and unavailable Coinbase data.
- Exercise Bumble feed, brief detail, Back behavior, source links, empty feed, and malformed-item handling.
- Exercise all Tracker tabs, selectors, tooltips, mobile widths, keyboard navigation, and unavailable external feeds.
- Compare production homepage and Corpus counts after GitHub Pages deploy.

## Remaining gaps and blockers

- The repository has no browser-test dependency, so this change adds source-level contract coverage but cannot certify full visual and interaction behavior.
- The public crawler returned stale Corpus content during the audit. Production freshness must be checked after deployment and cache invalidation.
- The 133-entry catalog is encoded directly in HTML. Count drift will remain a maintenance risk until Phase 1 introduces a central registry.
- Claims inside external research repositories were not independently reproduced in this site-focused pass. Links indicate provenance, not third-party validation.
- Verified actual performance, licensed real-time data, institutional entitlements, and legal approval are outside the evidence currently available.

