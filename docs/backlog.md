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
- [x] **Branch protection on `main`**: configured 2026-05-09 by repo
      owner via Rulesets. Requires green `test`, `pre-commit`, and
      `Analyze (python)` checks. Force-push and deletion blocked.
      Streamlit Cloud still auto-deploys on merge to `main`.
      **Required approvals = 0** because this is a solo-maintainer
      repo and you can't approve your own PR. Add an approval
      requirement only if a real second contributor joins.

### Tier 2 — nice to have

- [x] **Secret scanning + push protection**: enabled 2026-05-09 by repo
      owner. GitHub now scans every push (and historical commits) for
      ~200 known token formats and blocks new pushes that contain them.
- [~] **Coverage badge in README**: deferred. Codecov upload step was
      removed from `ci.yml` because the repo owner opted not to authorize
      the Codecov GitHub app. Coverage is still enforced locally and in
      CI via the `--cov-fail-under=75` gate in `pyproject.toml`. Re-enable
      by reverting commit that removed the `Upload coverage to Codecov`
      step + re-adding the badge to `README.md`.
- [~] **Auto-format bot**: deferred. Repo owner opted not to install
      pre-commit.ci. The local `pre-commit` job in `ci.yml` still gates
      every push, so unformatted code can't merge — contributors just
      have to run `pre-commit run --all-files` themselves before pushing.
- [x] **Stale issue/PR sweeper**: `.github/workflows/stale.yml` runs
      daily at 09:00 UTC. Issues warn at 60 days idle / close at 74; PRs
      warn at 30 / close at 44. Exempt labels: `security`, `pinned`,
      `roadmap`, `WIP`, plus all draft PRs.
- [ ] **release-please / changesets**: deferred. This repo has no formal
      release cadence (every push to `main` deploys to Streamlit Cloud, no
      versioned artifacts). Revisit if we ever publish a Python package
      or tag releases manually.

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

- [x] Dependency graph + Dependabot alerts (free, passive CVE alerts) — enabled 2026-05-09
- [x] Dependabot version updates (auto-PRs) — `.github/dependabot.yml`
- [x] Secret scanning — enabled 2026-05-09
- [x] Push protection — enabled 2026-05-09
- [x] Private vulnerability reporting — enabled 2026-05-09

Settings → Branches:

- [x] Branch protection rule on `main` (require CI, require review).
      Configured by repo owner 2026-05-09.

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

---

## Adversarial review 2026-05-10 — deferred items

The following findings from `docs/adversarial/2026-05-10-adversarial-feedback.md`
were intentionally deferred during the 2026-05-10 implementation pass.
See `ADVERSARIAL_REPORT_FIXES.md` for the full disposition.

### Deferred (⏳)

- [ ] **P1-10** — Restrict sheet read to needed columns (`get_all_records`
      currently pulls every column). Low value today; payload <1 MB and
      cached.
- [ ] **P2-09** — Fail loud when `APP_TIMEZONE` is unset / unparseable.
      Currently logs nothing and falls back to system local time.
- [ ] **P2-10** — Streamlit `AppTest` smoke per page. Blocked because
      pages call `st.set_page_config` from `dashboard.main()`, which
      AppTest's harness doesn't replay cleanly. Consider extracting a
      `render_<page>(df, ...)` for each page.
- [ ] **P2-11 / P2-17 / P2-18** — SHA-pin GitHub Actions. Repo convention
      is major-version pinning; flip if a real CVE arrives.
- [ ] **P2-14** — Add pyright job in CI. Type coverage is patchy; first
      run would be very noisy.
- [ ] **P2-16** — Post-deploy synthetic health check. Streamlit Cloud has
      no public health endpoint to probe deterministically.
- [ ] **P2-20** — Replace `render_styled_table` with native `st.dataframe`
      where styling isn't required.
- [ ] **P2-28** — Cache `build_cumulative_calories_long`.
- [ ] **P2-29** — Move captions used as labels into `help=` tooltips.
- [ ] **P3-02** — Delete `_build_weekday_mix_df` (dead code in
      `ui/scorecard.py`).
- [ ] **P3-18** — Migrate scorecard's local `STATUS_COLORS` to
      `ui.theme.STATUS_COLORS`.
- [ ] **P4-01** — Backfill type hints on older public helpers in
      `data/metrics.py` and `ui/common.py`.
- [ ] **P4-05** — Add `CHANGELOG.md` / release notes process.

### Partially shipped (🟡)

- [ ] **P2-19** — Migrate `ui/scorecard.py` to import palette from
      `ui/theme.py` (common.py + yearcalendar.py done).
- [ ] **P3-01** — Continue decomposing `ui/common.py` (theme + escape
      already extracted; chart factories still need their own modules).
- [ ] **P3-15** — Decide hidden pages' fate (`monthovermonth.py`,
      `personalization.py`) — keep as deep-link targets or delete.
