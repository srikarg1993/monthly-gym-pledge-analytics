# ADR 0005: Unified dark visual language for scorecard charts

- **Status**: Accepted
- **Date**: 2026-05-05
- **Tags**: ui, design

## Context

The scorecard page hosts ~12 distinct chart types (radar, race, ladder,
heartbeat, bubble clusters, diverging bars, etc.). Each was originally
authored with its own palette and chart chrome, producing visual noise: mixed
gray/copper/sage tones, bare bars next to glowing ones, inconsistent label
treatments, and unreadable text against dark backgrounds.

A coherent visual identity was needed so the page reads as one product
instead of a portfolio of demos.

## Decision

Adopt a single dark visual language for every chart in `gym_pledge/ui/common.py`:

- Background `#0B1220` everywhere (`.properties(background=...)` plus
  `configure_view(fill=...)`).
- Four-color accent palette with semantic roles:
  - Mint `#5FE1C7` / dark `#1F8C7A` — winners, candidate, "On It",
    first-half, front-loader.
  - Coral `#FFB57A` / dark `#C77744` — group, in-progress, "Catching Up",
    second-half, All-Nighter.
  - Cool blue `#9DCEFF` — neutral markers, Balanced style.
  - Raspberry `#F47A8E` — falling behind, Crammer.
- **Glow stack**: every bar/line gets a thicker, lower-alpha underlay in the
  darker shade, with a crisp narrower mark in the bright accent on top. Dots
  use a halo + core pair.
- **Label chip pattern**: render a dark stroke-only mark first
  (`color="#0B1220" stroke="#0B1220" strokeWidth=4 strokeOpacity=0.9`) and
  the colored fill mark on top with no stroke. Combining fill + stroke on
  one mark causes Vega-Lite to paint stroke over fill, muddying small text.
- Medal emojis 🥇🥈🥉 prepended to top-three rows on ranked charts.

`LAZY_ZONES` is a 6-tuple `(zone_id, label, headline, subtitle, color, icon)`
to keep the bubble cluster cards consistent with the rest of the palette.

## Consequences

### Positive
- All charts now read as one product.
- Color carries semantic meaning consistently across charts (mint always =
  the focused candidate or winners; coral = the supporting group; raspberry
  = trouble).
- Adding a new chart is a recipe — see `docs/skills/charts.md`.

### Negative
- ~1,500 lines of new chart styling code in `common.py`. Maintenance cost is
  real but bounded by the recipe.
- Future palette changes are a breaking visual update across the entire
  scorecard page. Mitigated by centralizing constants at the top of
  `common.py`.

## Alternatives considered

- **Altair theme via `alt.themes.register`**: rejected — themes don't cover
  the glow stack / chip text patterns we need.
- **Per-chart bespoke palettes**: rejected — that's the state we're moving
  away from.

## References

- Skill: [`docs/skills/charts.md`](../skills/charts.md)
