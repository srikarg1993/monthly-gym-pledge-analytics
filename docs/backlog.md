# Backlog — CI/CD & Tooling

Captured 2026-05-05. None of these are blocking; revisit when you want to
invest a session in repo-grade tooling.

---

## Current state

- ✅ **CI**: `.github/workflows/ci.yml` runs `ruff check` + `pytest` on push
  to `main` / `p2f` and on every PR.
- ❌ **CD**: none. App runs locally via `start-app.sh` or in the dev
  container. No hosted URL.

---

## CD — hosting options (only if you want a public URL)

| Host | Cost | Setup | Trade-off |
|---|---|---|---|
| Streamlit Community Cloud | Free | ~5 min | Public repo or paid; auto-deploy on push |
| Fly.io | Free / ~$5 mo | ~30 min | Real container; private repos OK; needs Dockerfile + fly.toml; secrets via `fly secrets set` |
| Render.com | Free (sleeps idle) | ~15 min | Auto-deploy on push |
| Hugging Face Spaces | Free | ~10 min | Public Streamlit hosting |
| Railway | $5/mo | ~10 min | Slick UX; auto-deploy on push |

**Recommendation if/when needed**: Fly.io for private repo support + free
tier + secrets management.

---

## GitHub Actions — backlog

### Tier 1 — likely worth it

- [ ] **Coverage gate**: add `--cov-fail-under=75` to the pytest step in
      `ci.yml`. One line; prevents future regressions on the floor we just
      hit.
- [ ] **Pre-commit in CI**: add a job that runs `pre-commit run --all-files`
      so PRs can't bypass local hooks.
- [ ] **Dependabot version updates**: drop a
      `.github/dependabot.yml` to auto-PR `pip` + `github-actions` updates
      weekly.
- [ ] **CodeQL scanning**: enable in repo Settings → Security; one-click
      free static analysis for Python.
- [ ] **Branch protection on `main`**: require green CI + 1 approval before
      merge. Repo settings, no code.

### Tier 2 — nice to have

- [ ] **Secret scanning + push protection**: enable in Settings → Security.
- [ ] **Coverage badge in README**: wire up Codecov or Coveralls.
- [ ] **Auto-format bot**: action that runs `ruff format` and pushes a
      fixup commit.
- [ ] **Stale issue/PR sweeper**: `actions/stale` with N-day window.
- [ ] **release-please / changesets**: auto-changelog + tag from
      conventional commits (matches `docs/skills/commit-messages.md`).

### Tier 3 — only if app grows

- [ ] **Build & push Docker image to GHCR**: reusable container artifact.
- [ ] **Python matrix**: 3.11 + 3.12 + 3.13.
- [ ] **Playwright smoke test**: boot Streamlit headless, screenshot, assert
      no error banner.
- [ ] **Scheduled health-check**: cron hits live URL, alerts on failure.
- [ ] **Performance regression**: benchmark `clean()` /
      `month_leaderboard()` on a fixture.

---

## Repo Settings (no code) — backlog

Settings → Security / Code security and analysis:

- [ ] Dependency graph + Dependabot alerts (free, passive CVE alerts)
- [ ] Dependabot version updates (auto-PRs)
- [ ] Secret scanning
- [ ] Push protection
- [ ] Private vulnerability reporting

Settings → Branches:

- [ ] Branch protection rule on `main` (require CI, require review)

---

## Adjacent tooling — backlog

| Tool | Value | Free tier |
|---|---|---|
| Sentry | Catches Python exceptions in the running app | Free dev plan |
| PostHog / Plausible | Lightweight page-view analytics | Free for low traffic |
| `pyright` / `mypy` | Static type checking on the type hints we added | free |
| `pip-audit` / `uv audit` | Scans `requirements.txt` for CVEs | free |
| Renovate Bot | Smarter Dependabot (groups updates, schedules) | free for personal |

---

## Recommended next session (if you pick this up)

Smallest set of changes that captures most of the value:

1. Add coverage gate to `ci.yml`
2. Add `.github/dependabot.yml` for `pip` + `github-actions`
3. Enable Dependabot alerts + secret scanning + push protection in repo
   settings
4. Add branch protection on `main`

Everything else is over-engineering for a private friend-group app.
