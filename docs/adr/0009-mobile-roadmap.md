# ADR 0009: Mobile + backend roadmap

- **Status**: Proposed
- **Date**: 2026-05-09
- **Deciders**: Srikar Gunisetty
- **Tags**: roadmap, architecture, mobile, backend

## Context

The app today is a Streamlit dashboard backed by a Google Sheet that humans
populate via a Google Form. It's a **read-only group reporting tool**. The
stated north-star goal is different: participants should install something
on their phones that **auto-imports calorie / workout data** from the
device (Apple HealthKit, Android Health Connect, watch sensors) instead of
manually filling a form.

That goal cannot be reached by extending Streamlit. HealthKit and Health
Connect are only accessible from a signed native app on each platform —
no web API exists. The current architecture also has no auth, no
per-user scoping, no write API, no background jobs, and no notification
channel — all of which the mobile experience requires.

This ADR captures the strategic plan so the conversation that produced it
isn't lost, and so future work can be sequenced against a single
reference.

Related context:
- The analytical core ([gym_pledge/data/metrics.py](../../gym_pledge/data/metrics.py))
  is pure-functional and Streamlit-free by design (see
  [ADR 0001](0001-flat-package-layout.md) and the layering rule in
  [agents.md](../../agents.md) §3). That makes it cheap to host behind a
  different frontend later.
- Source of truth today is a Google Sheet read via
  [gym_pledge/data/source.py](../../gym_pledge/data/source.py). The Sheet
  is the single biggest blocker to scaling, auth, and mobile.
- Hosting today is Streamlit Community Cloud (free tier) at
  https://pledge2fit.streamlit.app/. Cold-start ~10-30 s, single-tenant
  rerun model, no API surface.

## Decision

Adopt a **phased migration** rather than a rewrite. Streamlit stays as the
web client for the foreseeable future; the architecture underneath it
gets replaced one layer at a time, in dependency order.

### Trigger rule for moving off Streamlit

Do not migrate proactively. Migrate the web frontend off Streamlit only
when **two or more** of the following are true:

1. >20 active monthly users (today: ~6-8).
2. The mobile app has shipped or is in active development.
3. Streamlit Cloud's free tier has broken our usage (cold-start, OOM,
   rate limits).
4. We need a feature Streamlit can't do (real auth, webhooks, background
   jobs).

Until then, keep building on Streamlit and absorb the limitations.

### Phased plan

| Phase | Horizon | Scope | Effort |
|---|---|---|---|
| **0 — current** | now | Ship the queued PR. Streamlit + Google Sheet + Google Form. | 0 |
| **1 — Postgres migration** | Q3 2026 | Replace Google Sheet with Supabase Postgres. Keep Google Form as input (writes a webhook into Postgres). Rewrite `gym_pledge/data/source.py` only — UI untouched. Add nightly CSV snapshot to S3 for DR. | ~1 week |
| **2 — API layer** | Q4 2026 | Add a FastAPI backend that exposes today's analytical functions as REST/JSON endpoints. Streamlit becomes one of two clients (still reads the same shapes). Add Supabase Auth (or Clerk) so the API has a notion of "current user". | ~2 weeks |
| **3 — Mobile app** | Q1 2027 (only if committed) | React Native (Expo) or Flutter app. Auth via Supabase. HealthKit (iOS) + Health Connect (Android) integration for auto-import. Push notifications via Firebase. Phone-only — no watch app. | ~6-8 weeks |
| **4 — optional** | TBD | Apple Watch / Wear OS companion. Only if v1 mobile lands and engagement justifies it. | ~4-6 weeks per platform |

### Per-user views / privacy

- **Today**: keep the "everyone sees everyone" leaderboard. It's the
  point of a public pledge among friends.
- **Cheap interim step**: a Streamlit "personal mode" toggle that masks
  other participants' names (`Anonymous #3`) for the current viewer.
  Placebo, not auth, but ~30 LOC and addresses the "I don't want to be
  named publicly" concern.
- **Real auth + per-user scoping is required when** any of these
  becomes true:
  - We onboard anyone outside the original friend group.
  - We start auto-importing HealthKit data (heart rate, sleep, weight
    are medical-class).
  - We collect GPS / location data.
  - We take any money for hosting or features.
  - We host a second pledge group.
- **Visibility model when we add it**: participants in the same
  `group_id` see each other's *aggregates* (workout counts, calorie
  totals). Raw timestamps and watch data are owner + admin only.
- **Required by App Store policy** (not just GDPR): "download my data"
  + "delete my account" flows. Build them in Phase 2, not Phase 3.

### Mobile platform decision

- **PWA** rejected as the primary mobile path. PWAs cannot read
  HealthKit / Health Connect, so they don't move us toward the north
  star. May still be worth shipping a manifest + service worker so the
  Streamlit dashboard is "add to home screen"-able in the meantime —
  near-zero effort.
- **React Native (Expo)** is the recommended stack. Expo's
  `expo-health-connect` and HealthKit modules cover the integration we
  need. One codebase ships to both stores.
- **Flutter** is a viable alternative; pick whichever the implementer
  knows. Don't rewrite if the first prototype is in the other.
- **Native Swift + Kotlin** rejected — 12-16 weeks of duplicated UI
  work for a 6-person friend group is unjustifiable.
- **Watch apps** explicitly out of scope for v1. HealthKit on the
  phone already reads watch data; the watch UI would be a companion,
  not a primary surface. React Native does not target watchOS, so a
  watch app means writing real Swift / Kotlin separately.

### Things to do *now* that make migration cheaper later

1. **Hold the layering line.** Streamlit primitives must never leak
   into `gym_pledge/data/*` or `gym_pledge/config/*`. This is already
   in [agents.md](../../agents.md) §3; enforce it on every PR.
2. **Lock the data shapes.** Add Pydantic models or `TypedDict`s for
   the leaderboard row, scorecard payload, and year-calendar payload.
   Today these are loose pandas DataFrames. Locking the schema now
   makes a future FastAPI + React frontend trivial — same JSON shape
   on the wire as today's DataFrames.
3. **Weekly CSV snapshot of the Google Sheet** to a git-tracked or
   S3-tracked location. This is our DR plan if the Google account is
   ever locked or the API rate-limits us.

### Cost ceiling for v1 mobile

| Line item | Monthly | Annual |
|---|---|---|
| Streamlit Cloud hosting | $0 | $0 |
| Supabase Postgres (free tier, <500 MB) | $0 | $0 |
| FastAPI hosting (Fly.io / Render free tier) | $0-7 | $0-84 |
| Apple Developer Program | — | **$99** |
| Google Play Developer (one-time) | — | $25 (year 1 only) |
| Firebase push notifications (free tier) | $0 | $0 |
| **Realistic total v1 mobile** | | **~$110/year** |

The $99 Apple fee is the only non-negotiable cost. If avoided, fall
back to TestFlight (free, 90-day rolling builds) or Android-only.

## Consequences

### Positive
- Sequencing is clear; no premature rewrite.
- Each phase is independently shippable and reversible up to the
  Postgres cutover.
- The analytical core (`data/metrics.py`) carries forward unchanged
  through every phase — the work we've already done is preserved.
- Cost stays near $0 until v1 mobile, and ~$110/year after.
- Privacy posture stays appropriate to the actual user base — no
  premature account system for 6 friends.

### Negative
- We commit to *not* fixing some Streamlit pain (cold start, layout
  brittleness, single-tenant rerun) until trigger conditions are met.
- The Postgres migration in Phase 1 has migration risk: source-of-truth
  swap. Need a dual-write or one-way snapshot strategy during cutover.
- A native mobile build means a real release process (App Store review,
  versioning, crash reporting) that doesn't exist today.

### Neutral
- The Google Form stays as the entry point even after the Postgres
  migration — it just writes to Postgres via a webhook instead of
  appending to a Sheet. Friends keep their muscle memory.
- Streamlit doesn't go away when the mobile app ships; it's the
  desktop / browser view of the same backend.

## Alternatives considered

- **Pure PWA with no native app.** Rejected: doesn't reach the auto-
  import north star. HealthKit / Health Connect are not exposed to
  PWAs.
- **Stay on Google Sheets forever, build a mobile app that reads the
  Sheet directly.** Rejected: gspread from a mobile client is a
  permissions and rate-limit nightmare, and there's no per-user auth
  story without a backend in the middle.
- **No-code platform (Glide, Bubble, Retool).** Rejected: locks us
  into a vendor and discards the existing Python codebase. Worth
  reconsidering only if the human maintainer decides not to write code
  for this project.
- **Django + DRF + React Native.** Workable but heavier than needed
  for the user count. Revisit if we ever cross 100+ users.
- **Migrate everything in one big rewrite.** Rejected: 4-6 month
  project with no shippable milestones. Phased plan ships value at
  each step.
- **Build the watch app first.** Rejected: watch apps are 10x harder
  than phone apps and the phone reads watch data anyway.

## References

- [agents.md](../../agents.md) §3 (layering rules), §6 (domain model)
- [ADR 0001](0001-flat-package-layout.md) — flat package layout that
  enables this migration path
- [ADR 0002](0002-streamlit-cache-strategy.md) — caching strategy that
  will need to move to backend-side once API ships
- [ADR 0004](0004-timezone-via-app-time.md) — `app_time` already
  abstracts time, so backend can adopt without changes
- [docs/backlog.md](../backlog.md) — short-term tooling backlog (this
  ADR is the long-term roadmap)
- Apple HealthKit docs: https://developer.apple.com/documentation/healthkit
- Android Health Connect docs: https://developer.android.com/health-and-fitness/guides/health-connect
- Supabase: https://supabase.com/
- Expo Health: https://docs.expo.dev/versions/latest/sdk/health/
