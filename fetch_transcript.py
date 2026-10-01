import requests
import urllib.parse
from zoom_auth import get_zoom_access_token


def get_transcript_url(meeting_uuid, access_token):
    if "/" in meeting_uuid:
        encoded_uuid = urllib.parse.quote(urllib.parse.quote(meeting_uuid, safe=""), safe="")
    else:
        encoded_uuid = urllib.parse.quote(meeting_uuid, safe="")

    res = requests.get(
        f"https://api.zoom.us/v2/meetings/{encoded_uuid}/recordings",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"include_fields": "download_access_token"},
    )
    print("Status:", res.status_code)
    print("Response:", res.text)
    res.raise_for_status()
    data = res.json()

    files = data.get("recording_files", [])
    transcript_file = next((f for f in files if f.get("file_type") == "TRANSCRIPT"), None)

    if not transcript_file:
        return None

    token = data.get("download_access_token", "")
    return f"{transcript_file['download_url']}?access_token={token}"


def download_transcript(transcript_url):
    res = requests.get(transcript_url)
    res.raise_for_status()
    return res.text


if __name__ == "__main__":
    access_token = get_zoom_access_token()
    
    # Use one of the UUIDs from your last test
    test_uuid = "m5RdcanyS/GF1OJfbyVKGg=="
    
    url = get_transcript_url(test_uuid, access_token)
    print("Transcript URL found:", url is not None)
    
    if url:
        vtt_text = download_transcript(url)
        print("VTT length:", len(vtt_text))
        print("First 300 chars:\n", vtt_text[:300])