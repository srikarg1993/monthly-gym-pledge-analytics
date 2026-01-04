#libraries
from __future__ import annotations
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from typing import Sequence


def fetch_sheet_df(
    *,
    spreadsheet_id: str,
    worksheet_name: str,
    service_account_json_path: str,
    scopes: Sequence[str],
) -> pd.DataFrame:
    """
    Fetch a Google Sheet worksheet into a DataFrame.
    """
    creds = Credentials.from_service_account_file(service_account_json_path, scopes=list(scopes))
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)

    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)
    df = df.replace("", pd.NA).dropna(how="all")
    return df
