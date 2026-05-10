"""HTML / SVG escaping helpers for dynamic strings rendered through
`unsafe_allow_html=True` or `components.html`.

Centralizes the boring but critical work of preventing XSS through
sheet-sourced or form-sourced strings. Every page module that builds raw
HTML / SVG **must** route dynamic values through `safe_html` (for text
content) or `safe_attr` (for attribute values) — never f-string a raw
participant name straight into markup.

The 2026-05-10 adversarial review found the exact gap: participant names,
chart labels, podium HTML, lazy-bubble SVG titles, and styled-table cells
were all interpolated into HTML without escaping. A name like
``<img src=x onerror=alert(1)>`` would have executed in the browser. This
module is the fix.
"""

from __future__ import annotations

import html
import json
from typing import Any


def safe_html(value: Any) -> str:
    """Escape ``value`` for safe inclusion in HTML *text content*.

    Handles ``None`` / ``NaN`` / numerics by coercing to ``str`` first.
    Quote characters are escaped as well (``quote=True``) so the output
    is also safe inside a double-quoted attribute, though `safe_attr`
    is still preferred for attribute values for readability.
    """
    if value is None:
        return ""
    text = str(value)
    return html.escape(text, quote=True)


def safe_attr(value: Any) -> str:
    """Escape ``value`` for safe inclusion in an HTML *attribute value*.

    Identical to `safe_html` today; the separate name documents intent
    at the call site and gives us a hook for future tightening (e.g.
    URL validation for ``href`` / ``src``).
    """
    return safe_html(value)


def safe_js_string(value: Any) -> str:
    """Serialize ``value`` for inclusion inside a JavaScript string literal.

    Uses ``json.dumps`` because the JSON grammar is a strict subset of
    JavaScript expressions, so ``json.dumps("a\\"b")`` yields a literal
    that is safe to drop into ``<script>`` blocks without further escaping.
    """
    return json.dumps(value if value is not None else "", ensure_ascii=False)
