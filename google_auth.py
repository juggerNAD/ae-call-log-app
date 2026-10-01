import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("GOOGLE_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("GOOGLE_SUPABASE_SERVICE_KEY")


def get_google_access_token():
    # 1. Fetch stored refresh token + client credentials from Supabase
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/google_oauth_tokens?id=eq.google_app&select=refresh_token,client_id,client_secret",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        },
    )
    res.raise_for_status()
    data = res.json()[0]

    print("client_id len:", len(data["client_id"]), "preview:", data["client_id"][:6], "...", data["client_id"][-6:])
    print("client_secret len:", len(data["client_secret"]), "preview:", data["client_secret"][:4], "...", data["client_secret"][-4:])
    print("refresh_token len:", len(data["refresh_token"]), "preview:", data["refresh_token"][:10], "...", data["refresh_token"][-10:])

    # 2. Exchange refresh token for a fresh access token
    token_res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": data["client_id"],
            "client_secret": data["client_secret"],
            "refresh_token": data["refresh_token"],
            "grant_type": "refresh_token",
        },
    )
    print("Google token refresh status:", token_res.status_code)
    print("Google token refresh response:", token_res.text)
    token_res.raise_for_status()
    return token_res.json()["access_token"]


if __name__ == "__main__":
    token = get_google_access_token()
    print("Got access token, length:", len(token))