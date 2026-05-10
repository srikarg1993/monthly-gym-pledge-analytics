"""Semantic UI tokens.

Single source of truth for the dark visual language defined in
[ADR 0005](../../docs/adr/0005-unified-dark-visual-language.md). Per-page
modules MUST import from here rather than redefining colors or HTML
fragments locally — that is what produced the "three different palettes
in three files" drift the 2026-05-10 adversarial review flagged.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Surface colors
# ---------------------------------------------------------------------------
BG = "#0B1220"
PANEL = "rgba(20,28,45,0.88)"
PANEL_SOLID = "rgba(28,36,60,0.96)"
BORDER = "rgba(255,255,255,0.12)"
GRID = "rgba(255,255,255,0.08)"
TRACK = "rgba(255,255,255,0.12)"

# ---------------------------------------------------------------------------
# Typography colors
# ---------------------------------------------------------------------------
TEXT = "#E4E6EB"
MUTED = "#9AA0AB"
TEXT_DIM = "#A0A4B3"

# ---------------------------------------------------------------------------
# Semantic accent palette (ADR 0005).
#
# Each role has a "bright" mark color used for the crisp foreground stroke
# and a "glow" color used for the wider semi-transparent underlay. Use the
# constants — never hard-code one of the hex values in a chart factory or
# page module.
# ---------------------------------------------------------------------------
WINNER_BRIGHT = "#5FE1C7"
WINNER_GLOW = "#1F8C7A"

GROUP_BRIGHT = "#FFB57A"
GROUP_GLOW = "#C77744"

NEUTRAL = "#9DCEFF"

BEHIND_BRIGHT = "#F47A8E"

# ---------------------------------------------------------------------------
# Legacy-aliased "Altair" tokens used in older chart factories. Kept here
# (not in `ui/common.py`) so the split lives in one file. Prefer the
# semantic names above for new code.
# ---------------------------------------------------------------------------
ALT_TEXT = TEXT
ALT_MUTED = MUTED
ALT_GRID = GRID
ALT_PRIMARY = "#60A5FA"
ALT_FOCUS = "#F59E0B"
ALT_WORKOUT = "#64748B"
ALT_CUTOFF = "#34D399"
ALT_TRACK = TRACK
ALT_SAGE = "#5FA68D"
ALT_COPPER = "#B7835A"
ALT_STEEL = "#6E88A6"
ALT_SLATE = "#5D6B7C"
ALT_MOSS = "#7B8C5A"

# ---------------------------------------------------------------------------
# Status palette used by the Scorecard "Pledge Pulse" mix and similar
# bucketed views. Keep keys in sync with `ui.scorecard.STATUS_ORDER`.
# ---------------------------------------------------------------------------
STATUS_COLORS = {
    "Winner": ALT_SAGE,
    "1-2 away": ALT_COPPER,
    "Workout-rich": ALT_STEEL,
    "Other": ALT_SLATE,
}
