# BLAQUE BAUX ANALYSIS v2.0 intelligence requirements

Status: approved product direction, implementation specification
Release posture: research only; production with explicit evidence-state labels
Primary surface: `/analysis/`

## Product principle

A company, ticker, instrument, or portfolio is an entry point into the analysis, not its boundary. ANALYSIS must distinguish three related but separate questions:

1. **Security Intelligence:** what changed at the focal issuer or instrument, how unusual is it relative to an appropriate baseline, and what context changes its interpretation?
2. **Economic Network / Financial Dependency and Propagation Intelligence:** which entities depend on, finance, compete with, supply, buy from, insure, distribute for, or otherwise face the focal entity; what consequences could move through those ties; and how uncertain is each assertion?
3. **Sleeve Intelligence:** which sleeves an observation is eligible for, which sleeve owns the research decision, and what portfolio-level concentrations or shared dependencies remain after name-level diversification?

An anomaly is a neutral deviation from a defined baseline. It is not inherently adverse, investable, causal, or material. A buyback, debt issuance, capex change, refinancing, or working-capital movement must be interpreted in context: funding source, maturity profile, liquidity, dilution, valuation, covenant headroom, stated use of proceeds, operating trajectory, and management explanation.

## Scope and non-goals

The v2.0 system produces evidence-linked research objects and bounded hypotheses. It does not claim causal certainty, calculate unsupported downstream revenue impacts, identify undisclosed counterparties, provide investment advice, or treat price movement alone as evidence of operating contagion.

The initial fictional fixture remains a contract-test asset but is no longer presented in the production interface. Production currently includes one reviewed Apple filing analysis and automated SEC submissions/Companyfacts snapshots for Microsoft, Nvidia, Alphabet, Amazon, Tesla, and SpaceX. Automated snapshots expose issuer-tagged structured facts with exact periods and filing provenance, but publish no relationship, propagation, or sleeve conclusions until narrative review.

## Core object model

### Security observation

Required fields:

- stable observation ID and focal entity identifier;
- event type, observed value or qualitative state, and neutral baseline definition;
- observed-at, source-published-at, valid-from, valid-to, and superseded-at when applicable;
- source URL, source class, retrieval timestamp, excerpt locator, and transformation notes;
- fact, estimate, management assertion, model output, or analyst hypothesis classification;
- confidence and the reason for that confidence;
- materiality with method and threshold, or `unknown`;
- contextual interpretation, including plausible positive and negative readings;
- explicit unknowns and review status.

### AN-211 economic relationship and consequence map

AN-211 is the canonical graph contract. Each relationship is directional and point-in-time. Required fields:

- edge ID, from-entity, to-entity, and direction;
- relationship type: customer, supplier, lender, borrower, competitor, counterparty, insurer, distributor, logistics provider, regulator, or other controlled vocabulary;
- source and source classification;
- valid-from, valid-to, observed-at, and last-verified-at;
- confidence level and rationale;
- materiality level, basis, and whether quantified or qualitative;
- substitutability for each exposed side: low, medium, high, or unknown, plus rationale;
- disclosed, inferred, modeled, or illustrative status;
- limitations and reviewer state.

Each consequence is separate from the edge that permits propagation. Required fields:

- trigger observation and affected entity;
- positive, negative, mixed, or indeterminate polarity;
- mechanism, time horizon, and first-, second-, or third-order depth;
- conditions that must hold, countervailing effects, confidence, and evidence state;
- no unsupported numerical impact. Quantification requires a sourced exposure and a documented model.

Propagation paths must preserve every traversed edge, direction, confidence, validity window, and assumption. Confidence may not increase automatically as path depth grows. Third-order paths should be hidden by default unless materiality and evidence thresholds are met.

### Shared portfolio dependency

Name-level diversification can conceal common economic exposure. ANALYSIS must identify when multiple holdings share a customer, supplier, lender, counterparty, geography, commodity, distribution channel, or other dependency. A shared-dependency result records:

- portfolio holdings linked to the dependency;
- the common node or factor;
- path depth and relationship types;
- overlap basis and confidence;
- point-in-time validity;
- whether the result is observed or only a scenario hypothesis.

### Sleeve decision

`eligible_sleeves` and `assigned_sleeve` are different fields.

- **Eligibility** means the observation meets a sleeve's stated research criteria. Multiple sleeves may be eligible.
- **Assignment** means one governed workflow owns the next research action. Assignment requires a rule version, reason, timestamp, reviewer or automation identity, and status.

The interface must never display eligibility as if it were an allocation recommendation. Portfolio fit and factor similarity remain estimates, not assignment logic.

## Data and provenance requirements

Every displayed fact or estimate must expose source, as-of or validity time, method, uncertainty, and limitations. Unknown values remain unknown; absence is not converted to zero.

### SEC sources

- SEC submissions, filing documents, and Inline XBRL facts are primary sources for issuer-reported financial facts.
- XBRL concepts require unit, period, filing accession, form, fiscal period, dimensions, restatement/amendment state, and taxonomy mapping.
- MD&A and risk-factor text may provide management context, not verified causality. Extracted claims retain filing section and text locator and are labeled management assertions.
- Company-reported customer concentration or supplier dependence may be represented only to the specificity actually disclosed. Do not infer a named counterparty from an unnamed concentration disclosure.

### Bank regulatory sources and MDRM

MDRM is used only when an applicable bank regulatory filing and schedule maps to the relevant reporting institution. Record agency, form, schedule, MDRM item, reporting period, consolidation scope, and revision status. MDRM is not a generic issuer taxonomy and must not be applied to non-bank corporate data.

### Other sources

Issuer filings, official investor materials, regulatory records, contractual disclosures, and other primary documents outrank aggregators. Licensed datasets must retain provider, entitlement, permitted use, coverage, refresh time, and redistribution constraints. News or secondary research can generate a lead but cannot silently become a verified relationship.

## User experience requirements

1. Preserve the existing ticker classification and portfolio workflow.
2. Keep illustrative fixtures out of the production interface. Public-source results must identify whether they are reviewed narrative analysis or automated structured-data snapshots.
3. Show the focal entity, directional relationship, validity, source class, confidence, materiality, substitutability, consequence polarity, propagation depth, conditions, and unknowns.
4. Show positive and negative consequences side by side where both are plausible.
5. Separate facts, management assertions, models, and analyst hypotheses visually and semantically.
6. Link outward to Corpus for research evidence, Bumble for event context, and Capstone for mandate research. Do not imply those products validate the fixture.
7. Production mode must fail closed: if provenance, validity, or entity resolution is missing, the edge is not published as verified.
8. Accessible keyboard controls, readable mobile layout, and graceful data-unavailable states are required.

## Phased plan

### Phase 0: contract and safe vertical slice

- Publish this specification and an AN-211 JSON schema-shaped fixture.
- Render one fictional three-hop network in ANALYSIS with conspicuous non-live labels.
- Demonstrate neutral capital-allocation interpretation, directional edges, consequence polarity, shared portfolio dependencies, and sleeve eligibility versus assignment.
- Add automated contract tests for provenance, validity, confidence, materiality, substitutability, propagation depth, labels, and cross-product links.

Exit criterion: no fixture entity can reasonably be mistaken for a real disclosed relationship, and all existing site tests pass.

### Phase 1: Security Intelligence from primary filings

Current progress: issuer/CIK resolution, SEC submissions ingestion, accession-level filing links, conservative Companyfacts extraction, automated refresh, and explicit reviewed-versus-structured-only UX are deployed for the mega-cap example and SPCX. Narrative MD&A/risk-factor review and Bumble/Corpus review workflow remain open.

- Add issuer/entity resolution using CIK and security identifiers.
- Ingest SEC submissions and applicable Inline XBRL facts with accession-level provenance.
- Add bounded MD&A/risk-factor extraction with section locators and assertion labels.
- Implement neutral baseline/anomaly objects and contextual capital-allocation interpretation.
- Add human review queues in Bumble for event triage and link accepted evidence to Corpus.

Exit criterion: a reviewer can reproduce each displayed issuer fact from its cited filing and distinguish observation from interpretation.

### Phase 2: Economic network intelligence

- Add verified directional edges from disclosed primary sources and/or appropriately licensed relationship datasets.
- Implement temporal graph queries, supersession, contradiction handling, and confidence calibration.
- Add conditional first- and second-order consequence paths; gate third-order display.
- Add portfolio shared-dependency detection and coverage indicators.

Exit criterion: every published edge has a valid source, applicable rights, time window, review state, and non-increasing propagation confidence.

### Phase 3: Sleeve intelligence and governed workflow

- Version sleeve eligibility rules and keep them separate from assignment.
- Route reviewed observations to one owning sleeve while retaining multi-sleeve eligibility.
- Connect accepted evidence to Corpus and scenario/mandate research to Capstone.
- Add audit trails, overrides, reviewer identity, and outcome feedback without converting research classifications into advice.

Exit criterion: eligibility and assignment are reproducible from versioned rules and an auditable decision record.

### Phase 4: production hardening

- Expand licensed coverage, monitoring, correction workflows, entitlements, data retention, and model validation.
- Add legal/compliance approval for data use, redistribution, disclosures, research/advice boundaries, and surveillance obligations.
- Add availability, staleness, lineage, calibration, and reviewer-throughput monitoring.

Exit criterion: legal, data, model-risk, operations, and product owners sign off on a documented production release gate.

## Blockers and open decisions

- Reliable named customer/supplier/counterparty coverage is incomplete in public filings and often requires licensed supply-chain datasets.
- Private-company, geographic, contractual, and lower-tier supplier coverage is uneven; absence of an edge cannot mean absence of a relationship.
- Exposure percentages, contract terms, lender syndicates, hedges, and substitutions are frequently stale, aggregated, or undisclosed.
- Entity resolution across issuers, subsidiaries, securities, funds, and counterparties needs a governed identifier service.
- News and narrative extraction require licensing, attribution, correction, and hallucination controls.
- Quantified consequence models need historical validation and cannot be bootstrapped from qualitative edges.
- Legal/compliance review is required for data licensing and redistribution, MNPI controls, research-versus-advice language, model disclosures, recordkeeping, and any client-specific use.
- Bank regulatory ingestion requires institution/form applicability rules; MDRM alone does not establish comparable economic exposure.

## Acceptance tests

- Existing ANALYSIS examples and unknown-ticker handling continue to work.
- The retained fixture is labeled illustrative and non-live in source data and is not rendered in the production UX.
- Every edge includes direction, relationship type, source, validity, confidence, materiality, and substitutability.
- Consequences include polarity, depth, conditions, confidence, and no fabricated quantitative impact.
- At least one second-order and one third-order path are represented, with third-order uncertainty visible.
- Shared dependency is explicitly marked as a scenario, not a discovered portfolio fact.
- Eligible sleeves can contain multiple values while assigned sleeve is singular or null.
- SEC XBRL/MD&A and applicable-bank-only MDRM boundaries appear in the specification.
- Corpus, Bumble, and Capstone links are present.
- All automated site tests pass.
