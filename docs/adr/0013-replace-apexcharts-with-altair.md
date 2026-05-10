# 0013 — Replace ApexCharts CDN embed with native Altair

**Status**: Accepted
**Date**: 2026-05-10
**Driver**: 2026-05-10 adversarial review (P1-12)

## Context

The Fitness Yearbook page rendered its monthly Workouts / Qualifying
breakdown via an inline HTML+JS block that loaded ApexCharts from a
CDN (`unpkg.com/apexcharts@latest/dist/apexcharts.min.js`). Three
problems:

1. **Supply-chain risk**: a compromise of the CDN URL would inject
   arbitrary JS into the dashboard.
2. **Offline / restricted-network breakage**: anyone behind a corporate
   filter that blocks unpkg saw a blank chart with no error message.
3. **Visual inconsistency**: every other chart in the app uses Altair
   with the unified dark visual language. The Apex chart had its own
   theme, gradients, and tooltip styling.

## Decision

Replace the Apex embed with a native Altair grouped bar chart
(`_altair_monthly_chart`) that:

- Uses the existing `GROUP_BRIGHT` / `WINNER_BRIGHT` palette tokens.
- Configures axes / legend with `ALT_MUTED` / `ALT_TEXT` / `ALT_GRID`.
- Sits inside the new tabbed Yearbook layout (Overview / Monthly
  breakdown / Calendar) so it isn't buried under 12 mini-calendars on
  mobile.

No external network calls. No unsafe HTML. Altair tooltips are native.

## Consequences

### Positive
- Zero CDN dependency on the page.
- Visual consistency with every other Altair chart.
- Hostile-input safe — chart spec is JSON, no user-controlled HTML.

### Negative
- Altair's grouped bars are slightly less polished than Apex's animated
  combo (bar + area). Acceptable for the audience.

### Neutral
- A test
  (`tests/test_yearcalendar.py::test_altair_monthly_chart_builds_native_altair_chart`)
  asserts the chart spec contains both series and both months so a
  future "tidy this up" refactor doesn't accidentally drop a series.
