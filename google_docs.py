import requests
from google_auth import get_google_access_token


def create_doc(title):
    access_token = get_google_access_token()
    res = requests.post(
        "https://docs.googleapis.com/v1/documents",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"title": title},
    )
    res.raise_for_status()
    return res.json()["documentId"]


def insert_text(document_id, text):
    access_token = get_google_access_token()
    res = requests.post(
        f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": text,
                    }
                }
            ]
        },
    )
    res.raise_for_status()
    return res.json()


def move_to_folder(document_id, folder_id):
    access_token = get_google_access_token()
    res = requests.patch(
        f"https://www.googleapis.com/drive/v3/files/{document_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"addParents": folder_id, "fields": "id, parents"},
    )
    res.raise_for_status()
    return res.json()


if __name__ == "__main__":
    from clean_transcript import clean_vtt
    from fetch_transcript import get_transcript_url, download_transcript
    from zoom_auth import get_zoom_access_token

    zoom_token = get_zoom_access_token()
    test_uuid = "m5RdcanyS/GF1OJfbyVKGg=="
    url = get_transcript_url(test_uuid, zoom_token)
    vtt_text = download_transcript(url)
    clean_text = clean_vtt(vtt_text)

    doc_id = create_doc("TEST - Python Doc Creation")
    print("Created doc:", doc_id)

    insert_text(doc_id, clean_text)
    print("Inserted text, length:", len(clean_text))

    FOLDER_ID = "1nCmi3cAOAVmIKkuxkiqWTqwHuMl_7KPV"  # Closer Call Transcripts folder
    move_to_folder(doc_id, FOLDER_ID)
    print("Moved to folder")

    print(f"Doc URL: https://docs.google.com/document/d/{doc_id}/edit")