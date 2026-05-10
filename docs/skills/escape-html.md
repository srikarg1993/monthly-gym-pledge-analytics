# Escape HTML before injecting into the UI

This repo writes a lot of dynamic HTML / SVG via
`st.markdown(..., unsafe_allow_html=True)`. Anything pulled from the
Google Sheet (names, calorie totals, custom labels) MUST be escaped
before it lands in that string, or a participant could XSS the
dashboard by setting their form name to `<img src=x onerror=...>`.

## Helpers

```python
from ui.escape import safe_html, safe_attr, safe_js_string
```

| Helper          | Use when…                                                   |
|-----------------|-------------------------------------------------------------|
| `safe_html(x)`  | Interpolating into HTML / SVG **text content**              |
| `safe_attr(x)`  | Interpolating into an HTML **attribute value**              |
| `safe_js_string(x)` | Interpolating into a literal inside a `<script>` block (avoid; prefer Altair / Streamlit native widgets) |

`safe_html` returns `""` for `None` / `pd.NA` / `NaN`, and
`html.escape(str(x), quote=True)` for everything else.

## Hard rules

- Every place that writes `f"...{name}..."` into HTML must wrap
  `name` in `safe_html` (or `safe_attr` if it's inside `class="..."` /
  `title="..."` / `style="..."`).
- Never assume "names are clean" because the sheet is private. Hostile
  values can come from a typo, an emoji, an unexpected unicode lookalike,
  or a future iteration where the sheet is opened up.
- Prefer `st.dataframe` / `st.metric` over `render_styled_table` when
  no special styling is needed — Streamlit handles escaping for you.

## Tests

`tests/test_source_io.py::test_styled_table_escapes_hostile_cell_values`
locks in the contract for the one place that builds `<td>` values from
a DataFrame. When you add a new helper that injects raw HTML, add a
matching test that feeds it `<script>alert(1)</script>` and asserts the
output contains `&lt;script&gt;` and not `<script>`.
