import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from zoom_auth import get_zoom_access_token

load_dotenv()


def get_recordings(email, access_token, days_back=7):
    to_date = datetime.utcnow().date()
    from_date = to_date - timedelta(days=days_back)

    res = requests.get(
        f"https://api.zoom.us/v2/users/{email}/recordings",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"from": from_date.isoformat(), "to": to_date.isoformat()},
    )
    res.raise_for_status()
    return res.json().get("meetings", [])


if __name__ == "__main__":
    token = get_zoom_access_token()
    meetings = get_recordings("devaughn@thearbitrageempire.com", token)
    print(f"Found {len(meetings)} meetings")
    for m in meetings:
        print("-", m.get("topic"), m.get("start_time"), m.get("uuid"))