# 0010 — Privacy posture: private group, URL-only, no auth gate

**Status**: Accepted
**Date**: 2026-05-10
**Driver**: 2026-05-10 adversarial review (P3-09)

## Context

The dashboard is the public face of a closed friend-group fitness pledge.
Participants log workouts via Google Form; the dashboard reads the
backing Sheet and renders names, calorie totals, workout dates, and
Venmo handles. Anyone who knows the URL https://pledge2fit.streamlit.app/
can read every participant's logs.

Two things forced an explicit posture decision:

1. The README and About page never said any of the above out loud.
2. The 2026-05-10 adversarial review flagged "no auth, no rate limit,
   no privacy notice — at minimum, document this so contributors and
   forks make an informed choice."

## Decision

We **accept URL-obscurity as the privacy mechanism** for this
deployment, with the following guard rails:

- The URL is shared only with active participants (a single private
  WhatsApp / iMessage group).
- The Sheet is **not** publicly shared. Read access is granted to the
  Streamlit Cloud service account only, via the secret in
  `.streamlit/secrets.toml`.
- The About page declares the privacy model in plain language so a new
  participant or a forker is not surprised.
- `gym_pledge/config/globals.py` exposes `PRIVACY_MODEL = "url-obscurity"`
  so callers can branch (e.g. a future deployment could set it to
  `"sso"` and gate accordingly).
- Forks targeting a non-trivial audience (large group, public web) MUST
  add an authentication gate (`streamlit-authenticator`, OAuth proxy,
  Cloud Run IAP, etc.) and update this ADR with their decision.

## Consequences

### Positive
- Honest about what we have. Contributors / users know the threat model.
- Configurable: a future deployment can flip the constant + add a gate
  without changing every page.

### Negative
- Anyone who guesses or is told the URL can scrape names + calorie
  totals.
- Search engines could in principle index the page if Streamlit Cloud's
  default `robots.txt` ever changed. Mitigation: keep the deployment
  marked as not-indexed in the Streamlit Cloud app settings.

### Neutral
- We accept the same posture older contributors already had — we just
  wrote it down.
