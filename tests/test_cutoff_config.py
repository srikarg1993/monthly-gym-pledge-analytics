import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

from config.globals import WINNER_CUTOFF, WINNER_CUTOFF_BY_MONTH, winner_cutoff_for_month


def test_winner_cutoff_for_month_uses_default_when_not_overridden():
    assert winner_cutoff_for_month("2099-12") == WINNER_CUTOFF
    assert winner_cutoff_for_month(None) == WINNER_CUTOFF


def test_winner_cutoff_for_month_uses_override():
    assert winner_cutoff_for_month("2026-02") == 15
    assert WINNER_CUTOFF_BY_MONTH["2026-02"] == 15
