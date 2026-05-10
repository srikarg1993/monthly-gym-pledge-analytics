# Skill: Adding or modifying an Altair chart

Trigger: a new chart is needed in `ui/scorecard.py` (or any other UI page),
or an existing chart needs a visual change.

## Where charts live

All chart factories live in `gym_pledge/ui/common.py`. UI pages import them
and call them with a DataFrame plus parameters. **Do not** define new Altair
specs inline in `ui/<page>.py` beyond a 2-3 line wrapper.

## The recipe

1. **Pick a name**: `alt_<thing>_chart` for Altair, `<thing>_figure` for
   matplotlib.
2. **Signature**: takes a DataFrame plus keyword-only parameters. Returns an
   `alt.Chart` (or matplotlib `Figure`). Never calls `st.*` itself — the
   caller decides where the chart goes.
3. **Empty-data guard**: `if df is None or df.empty: return alt.Chart(pd.DataFrame())`.
4. **Copy before mutating**: `chart_df = df.copy().reset_index(drop=True)`.
5. **Apply the visual language** (see [ADR 0005](../adr/0005-unified-dark-visual-language.md)):
   - Background `#0B1220` via `.properties(background="#0B1220")` and
     `.configure_view(strokeOpacity=0, fill="#0B1220")`.
   - Mint / coral / blue / raspberry palette per role.
   - **Glow stack**: render a wider, low-opacity underlay first, then the
     crisp narrow mark on top.
   - **Label chip pattern**: render a dark stroke-only text mark first, then
     the colored fill text mark on top with no stroke. Never combine fill +
     stroke on a single text mark.
6. **Medal emojis**: prepend 🥇🥈🥉 to top three rows on ranked charts.
7. **Use `alt_chart_height(...)`** for row-based height calculations.

## Reference implementations

- Diverging bars with chip labels: `alt_group_split_chart` in `common.py`.
- Glow halo + core line + medal emoji labels: `alt_cumulative_calorie_race_chart`.
- Stacked progress bars with chip summary: `alt_goal_ladder_chart`.
- SVG bubble cluster with radial-gradient fill + Gaussian-blur glow:
  `render_lazy_bubble_clusters`.

## Tests

Pure data-shape helpers (`_build_*` functions used by chart factories)
**must** have a unit test in `tests/test_scorecard.py`. The chart spec itself
is exercised by running the app — no Vega-Lite snapshot tests.

## Don'ts

- Don't introduce a new accent color without an ADR amending 0005.
- Don't turn off `configure_view(strokeOpacity=0, fill="#0B1220")` —
  the chart will "float" against the page background.
- Don't add a `tooltip` field that exposes data the rest of the chart hides.
