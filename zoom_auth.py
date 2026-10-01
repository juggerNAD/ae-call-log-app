import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("ZOOM_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("ZOOM_SUPABASE_SERVICE_KEY")


def get_zoom_access_token():
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/zoom_oauth_tokens?id=eq.zoom_app&select=refresh_token",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        },
    )
    res.raise_for_status()
    refresh_token = res.json()[0]["refresh_token"]

    zoom_client_id = os.getenv("ZOOM_CLIENT_ID")
    zoom_client_secret = os.getenv("ZOOM_CLIENT_SECRET")

    import base64
    basic_auth = base64.b64encode(f"{zoom_client_id}:{zoom_client_secret}".encode()).decode()

    token_res = requests.post(
        "https://zoom.us/oauth/token",
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    print("Zoom token refresh status:", token_res.status_code)
    print("Zoom token refresh response:", token_res.text)
    token_res.raise_for_status()
    token_data = token_res.json()

    # Save the newly rotated refresh token back
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/zoom_oauth_tokens?id=eq.zoom_app",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json={"refresh_token": token_data["refresh_token"]},
    )

    return token_data["access_token"]


if __name__ == "__main__":
    token = get_zoom_access_token()
    print("Got Zoom access token, length:", len(token))