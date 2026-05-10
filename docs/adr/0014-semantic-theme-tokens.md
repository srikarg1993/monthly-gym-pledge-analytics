# 0014 — Semantic theme tokens in `ui/theme.py`

**Status**: Accepted
**Date**: 2026-05-10
**Driver**: 2026-05-10 adversarial review (P3-01, P3-04)

## Context

ADR 0005 defined the unified dark visual language. The actual hex codes
were inlined throughout `ui/common.py` (~2.7k LOC). When a chart needed
the "winners" color, the literal `"#5FE1C7"` appeared in twenty
different places, and a future palette tweak meant a 20-touch find /
replace. Worse, three pages had drifted slightly — `ui/scorecard.py`
defined its own `STATUS_COLORS` dict that almost-but-not-quite matched
common.py's.

## Decision

Extract a single `ui/theme.py` module that owns the palette as named
tokens:

```python
BG = "#0B1220"
PANEL = "#11182A"
TEXT = "#E6EAF2"
MUTED = "#9AA2B6"

WINNER_BRIGHT = "#5FE1C7"
WINNER_GLOW   = "#1F8C7A"
GROUP_BRIGHT  = "#FFB57A"
GROUP_GLOW    = "#C77744"
NEUTRAL       = "#9DCEFF"
BEHIND_BRIGHT = "#F47A8E"

# Altair-flavoured aliases for axis / grid / text styling.
ALT_PRIMARY = WINNER_BRIGHT
ALT_TEXT    = TEXT
ALT_MUTED   = MUTED
ALT_GRID    = "#1B2438"

STATUS_COLORS = {"winner": WINNER_BRIGHT, "behind": BEHIND_BRIGHT, ...}
```

`ui/common.py`, `ui/yearcalendar.py`, and (eventually) `ui/scorecard.py`
import from `ui.theme` instead of inlining hex codes.

## Consequences

### Positive
- One source of truth for the palette.
- A future palette tweak is a one-file diff.
- Tokens are semantic (`WINNER_BRIGHT`, not `MINT_3`), so a reader
  knows what they mean without consulting the design doc.

### Negative
- One more file in the import graph.

### Neutral
- Migration is incremental: `common.py` and `yearcalendar.py` already
  use the tokens; `scorecard.py` still has its local `STATUS_COLORS`
  and is on the cleanup backlog.
