# Backlog — CI/CD & Tooling

Captured 2026-05-05. None of these are blocking; revisit when you want to
invest a session in repo-grade tooling.

---

## Current state

- ✅ **CI**: `.github/workflows/ci.yml` runs `ruff check` + `pytest` on push
  to `main` / `p2f` and on every PR.
- ✅ **CD**: Streamlit Community Cloud hosts `main` at
  https://pledge2fit.streamlit.app/. Every push to `main` redeploys
  automatically. Secrets configured in the Streamlit Cloud app settings
  (mirrors `.streamlit/secrets.toml`).

## CD operational notes

- **Deploy trigger**: any commit landing on `main`.
- **Pre-merge gate**: GitHub Actions CI runs against PRs into `main`. Don't
  merge red.
- **Rollback**: redeploy a previous commit from the Streamlit Cloud
  dashboard, or `git revert <sha> && git push origin main`.
- **Secrets sync**: `.streamlit/secrets.toml` is gitignored. The
  `[gcp_service_account]` table must also exist in **Streamlit Cloud →
  App settings → Secrets**. If you rotate the service account key, update
  both places.
- **Cold-start**: free-tier apps sleep after inactivity; first request after
  sleep takes ~10-30 s.
- **Logs**: Streamlit Cloud dashboard → "Manage app" → "Logs".

## CD — alternative hosts (only if you outgrow Streamlit Cloud)

Reasons you might switch: private repo requirement, custom domain with TLS,
no cold-start, multi-region, OAuth gating, more memory/CPU.

| Host | Cost | Setup | Trade-off |
|---|---|---|---|
| Fly.io | Free / ~$5 mo | ~30 min | Real container, private repos, secrets via `fly secrets set`, no cold start on paid tier |
| Render.com | Free (sleeps) / $7 mo | ~15 min | Auto-deploy on push, cleaner logs |
| Hugging Face Spaces | Free | ~10 min | Public Streamlit hosting |
| Railway | $5/mo | ~10 min | Auto-deploy on push, slick UX |

---

## GitHub Actions — backlog

### Tier 1 — likely worth it

- [x] **Coverage gate**: pytest now runs with
      `--cov=data --cov=config --cov-fail-under=75` (configured in
      `pyproject.toml`). CI fails the build if `data/*` + `config/*`
      coverage drops below 75%. Current: ~78%.
- [x] **Pre-commit in CI**: `ci.yml` now has a `pre-commit` job using
      `pre-commit/action@v3.0.1` that runs all hooks on every push/PR.
- [x] **Dependabot version updates**: `.github/dependabot.yml` opens weekly
      PRs for `pip` (requirements*.txt) and `github-actions`.
- [x] **CodeQL scanning**: `.github/workflows/codeql.yml` runs on every
      push to `main`/`p2f`, every PR into `main`, and weekly via cron.
- [ ] **Branch protection on `main`**: require green CI + 1 approval before
      merge. Repo settings, no code. **Action for repo owner**: GitHub →
      Settings → Branches → Add rule for `main` → enable
      "Require status checks to pass" (select `test`, `pre-commit`,
      `Analyze (python)`) + "Require pull request reviews".

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

## Security follow-ups

- [ ] **Rotate leaked GCP service-account key** (HIGH).
      `gym_pledge/.streamlit/secrets.toml` was tracked in git for many
      commits because the `.gitignore` rule never matched the actual path.
      Untracked in commit `10d976f`, but the key is still recoverable from
      git history. Steps: GCP Console → IAM → Service Accounts → create new
      key → update Streamlit Cloud secrets + local
      `gym_pledge/.streamlit/secrets.toml` → disable & delete the old key.
      Optionally rewrite history with `git filter-repo` to scrub the blob.

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

1. Add coverage gate to `ci.yml` (1 line: `--cov-fail-under=75`)
2. Add `.github/dependabot.yml` for `pip` + `github-actions`
3. Enable Dependabot alerts + secret scanning + push protection in repo
   settings
4. Add branch protection on `main` — require green CI before merge
   (especially valuable now that `main` auto-deploys to Streamlit Cloud)
5. Wire a post-deploy health check: GitHub Action on `push: main` that hits
   https://pledge2fit.streamlit.app/ and fails if status != 200

Everything else is over-engineering for a private friend-group app.
