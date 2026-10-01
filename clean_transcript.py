def clean_vtt(vtt_text):
    lines = vtt_text.split('\n')
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == '' or stripped == 'WEBVTT':
            continue
        if stripped.isdigit():
            continue
        if '-->' in stripped:
            continue
        clean_lines.append(stripped)
    return '\n'.join(clean_lines)


if __name__ == "__main__":
    from fetch_transcript import get_transcript_url, download_transcript
    from zoom_auth import get_zoom_access_token

    access_token = get_zoom_access_token()
    test_uuid = "m5RdcanyS/GF1OJfbyVKGg=="
    url = get_transcript_url(test_uuid, access_token)
    vtt_text = download_transcript(url)

    clean_text = clean_vtt(vtt_text)
    print("Clean length:", len(clean_text))
    print("First 300 chars:\n", clean_text[:300])