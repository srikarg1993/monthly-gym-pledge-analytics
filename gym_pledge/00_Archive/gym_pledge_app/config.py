from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class SheetConfig:
    spreadsheet_id: str
    worksheet_name: str
    service_account_json_path: str
    scopes: Sequence[str]


@dataclass(frozen=True)
class AppConfig:
    page_title: str = "Monthly Gym Pledge"
    page_icon: str = "💪"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    cache_ttl_seconds: int = 45
    default_winner_cutoff: int = 16


SHEET = SheetConfig(
    spreadsheet_id="17RADj_LH-Lj_lB8QFZyxjv8iKFerNZfNT-7wmtPNuzk",
    worksheet_name="Form Responses",
    service_account_json_path="secrets/service_account.json",
    scopes=(
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ),
)

APP = AppConfig()
