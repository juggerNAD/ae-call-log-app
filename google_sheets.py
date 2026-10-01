import requests
from google_auth import get_google_access_token

SPREADSHEET_ID = "1Dsep6RGtPdgn7_xh2RCxVfj4OrFlUtV3y_IMu5AyprQ"  # Josh - Closer Call Log


def get_existing_meeting_ids():
    access_token = get_google_access_token()
    res = requests.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Sheet1!B2:B",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    print("Sheets API status:", res.status_code)
    print("Sheets API response:", res.text)
    res.raise_for_status()
    values = res.json().get("values", [])
    return set(row[0] for row in values if row)


def append_row(row_values):
    access_token = get_google_access_token()
    res = requests.post(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Sheet1!A:J:append",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"valueInputOption": "RAW"},
        json={"values": [row_values]},
    )
    res.raise_for_status()
    return res.json()


if __name__ == "__main__":
    ids = get_existing_meeting_ids()
    print(f"Found {len(ids)} existing meeting IDs")

    test_row = [
        "TEST Closer Name",
        "TEST-meeting-id-12345",
        "TEST Topic",
        "2026-10-01T00:00:00Z",
        "5",
        "https://example.com/recording",
        "https://example.com/doc",
        "2026-10-01T00:00:00Z",
        "TEST Prospect Name",
    ]
    result = append_row(test_row)
    print("Append result:", result)