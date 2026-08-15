# BLAQUE BAUX Site

Production static site for **www.blaquebaux.com**.

## Structure
- `/` — main landing page
- `/labs/` — interactive LIVE / VALIDATION research
- `/corpus/` — research corpus index
- `CNAME` — GitHub Pages custom domain
- `.nojekyll` — serve static files directly

## Deployment
1. Publish the repository through GitHub Pages from the `main` branch root.
2. Set the Pages custom domain to `www.blaquebaux.com`.
3. Verify `blaquebaux.com` at the GitHub organization level before DNS cutover.
4. In Namecheap, point `www` to `blaquebaux.github.io` with a CNAME.
5. Configure the apex domain for GitHub Pages redirect support.
6. Enable HTTPS after GitHub provisions the certificate.

A Carter Warrens research initiative.
