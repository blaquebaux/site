# BLAQUE BAUX Site

**Quantitative Intelligence for Finance**

**Build. Validate. Integrate.**

**A Carter Warrens Company**

> **PRODUCTION · PUBLIC RESEARCH INTERFACE** &nbsp;|&nbsp; HTML / CSS / JavaScript &nbsp;|&nbsp; [Live site](https://www.blaquebaux.com)

Production static site for **www.blaquebaux.com**.

## Structure
- `/` — main landing page
- `/start/` — guided BASE research tour
- `/analysis/` — interactive portfolio and sleeve classifier
- `/labs/` — interactive operational / validation research
- `/corpus/` — research corpus index
- `/block/` — derivatives reference and structural variation studies
- `/capstone/` — interactive meta-sleeve and allocation research
- `/tracker/` — simulated sleeve-performance tracker
- `/toolkit/` — validation methods and audit record
- `/bumble/` — reviewed market-event and briefing snapshots
- `/about/` — company, methodology, status definitions, and disclaimers
- `CNAME` — GitHub Pages custom domain
- `.nojekyll` — serve static files directly

## Deployment
1. Publish the repository through GitHub Pages from the `main` branch root.
2. Set the Pages custom domain to `www.blaquebaux.com`.
3. Verify `blaquebaux.com` at the GitHub organization level before DNS cutover.
4. In Namecheap, point `www` to `blaquebaux.github.io` with a CNAME.
5. Configure the apex domain for GitHub Pages redirect support.
6. Enable HTTPS after GitHub provisions the certificate.

See [`docs/v2-requirements-review.md`](docs/v2-requirements-review.md) for the source-grounded v2.0 inventory, acceptance criteria, dependencies, and roadmap.

## Validation

- Run `python3 scripts/build_research_registry.py --check` to verify the registry and Corpus anchors.
- Run `python3 -m unittest discover -s tests -v` for content, navigation, count, and provenance contracts.
- Serve the repository root and open `/tests/browser-smoke.html` for same-origin browser smoke checks at desktop or mobile widths.
