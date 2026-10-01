import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    SLACK_BOT_TOKEN = st.secrets.get("SLACK_BOT_TOKEN", os.getenv("SLACK_BOT_TOKEN"))
except Exception:
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

NEW_DEAL_CHANNEL_ID = "C0AJR8Q52CC"
NEW_CLIENT_CHANNEL_ID = "C082MPAQTTK"

CLOSER_MAP = {
    "U0ANWLKABMY": "Devaughn Stewart",
    "U0BL0L21N92": "Junior Jean Baptiste",
    "U0B8PB3U9E3": "Sean Dodds",
    "U0AKE6YEF9N": "Jesus Mendez",
    "U0BDGMHSJ30": "Joshua Robinson",
    "U0BQXULSBS8": "Liam McCafferty",
}


def extract_field(text, label):
    pattern = rf"\*{re.escape(label)}\*\s*\n?([^\n*]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def get_new_deal_messages(limit=200):
    res = requests.get(
        "https://slack.com/api/conversations.history",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        params={"channel": NEW_DEAL_CHANNEL_ID, "limit": limit},
    )
    res.raise_for_status()
    data = res.json()

    if not data.get("ok"):
        raise Exception(f"Slack API error: {data.get('error')}")

    if data.get("messages"):
        print("=== RAW TEXT SAMPLE ===")
        print(repr(data["messages"][0].get("text", "")))
        print("=== END SAMPLE ===")

    deals = []
    for msg in data.get("messages", []):
        text = msg.get("text", "")
        if "Deal Owner (closer)" not in text:
            continue

        closer_raw = extract_field(text, "Deal Owner (closer)")
        closer_id_match = re.search(r"U[A-Z0-9]+", closer_raw)
        closer_id = closer_id_match.group(0) if closer_id_match else ""

        deals.append({
            "closer_name": CLOSER_MAP.get(closer_id, "Unknown"),
            "cash_collected": extract_field(text, "Cash collected"),
            "deal_first_name": extract_field(text, "Deal First Name"),
            "deal_last_name": extract_field(text, "Deal Last Name"),
            "closed_date": extract_field(text, "Closed Date"),
            "ts": msg.get("ts"),
        })

    return deals


def get_new_client_messages(limit=200):
    res = requests.get(
        "https://slack.com/api/conversations.history",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        params={"channel": NEW_CLIENT_CHANNEL_ID, "limit": limit},
    )
    res.raise_for_status()
    data = res.json()

    if not data.get("ok"):
        raise Exception(f"Slack API error: {data.get('error')}")

    clients = []
    for msg in data.get("messages", []):
        text = msg.get("text", "")

        name_match = re.search(r"Name:\s*([^\n]+)", text)
        amount_match = re.search(r"(?:Cash Collected|Amount):\s*\$?([\d,]+\.?\d*)", text)
        date_match = re.search(r"Date:\s*([^\n]+)", text)

        is_confirmed = "contract_signed" in text.lower() or "cash collected" in text.lower()
        is_pending = "pending" in text.lower()

        if not name_match or not amount_match:
            continue

        clients.append({
            "name": name_match.group(1).strip(),
            "amount": amount_match.group(1).replace(",", ""),
            "date": date_match.group(1).strip() if date_match else None,
            "confirmed": is_confirmed and not is_pending,
            "ts": msg.get("ts"),
        })

    return clients


if __name__ == "__main__":
    deals = get_new_deal_messages()
    print(f"Found {len(deals)} deal messages")
    for d in deals[:3]:
        print(d)

    clients = get_new_client_messages()
    print(f"\nFound {len(clients)} client messages")
    for c in clients[:5]:
        print(c)