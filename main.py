import time
from datetime import datetime, timedelta, timezone

from zoom_auth import get_zoom_access_token
from fetch_recordings import get_recordings
from fetch_transcript import get_transcript_url, download_transcript
from clean_transcript import clean_vtt
from google_docs import create_doc, insert_text, move_to_folder
from google_sheets import get_existing_meeting_ids, append_row

CLOSERS = [
    {"name": "Devaughn Stewart", "email": "devaughn@thearbitrageempire.com"},
    {"name": "Junior Jean Baptiste", "email": "junior@thearbitrageempire.com"},
    {"name": "Sean Dodds", "email": "sean@thearbitrageempire.com"},
    {"name": "Jesus Mendez", "email": "jesus@thearbitrageempire.com"},
    {"name": "Joshua Robinson", "email": "joshua@thearbitrageempire.com"},
    {"name": "Liam McCafferty", "email": "liam@thearbitrageempire.com"},
]

TRANSCRIPTS_FOLDER_ID = "1nCmi3cAOAVmIKkuxkiqWTqwHuMl_7KPV"  # Closer Call Transcripts


def extract_prospect_name(transcript, closer_name):
    closer_lower = closer_name.strip().lower()
    generic_patterns = ["iphone", "android", "ipad", "samsung", "unknown", "guest"]

    for line in transcript.split("\n"):
        if ":" not in line:
            continue
        speaker = line.split(":", 1)[0].strip()
        speaker_lower = speaker.lower()

        if speaker_lower == closer_lower or closer_lower in speaker_lower or speaker_lower in closer_lower:
            continue
        if any(p in speaker_lower for p in generic_patterns):
            continue
        if speaker.replace("+", "").replace(" ", "").isdigit():
            continue

        return speaker

    return "Unknown"


def classify_outcome(transcript):
    text_lower = transcript.lower()

    closed_signals = [
        "down payment", "shyfi", "sign the agreement", "signed the agreement",
        "finance application", "credit card ending", "get you approved",
        "welcome aboard", "congratulations", "let's get you started",
        "account manager", "onboarded", "llc set up"
    ]
    no_close_signals = [
        "not interested", "not for me", "i'll pass", "not right now",
        "doesn't make sense for me", "not a good fit", "no thank you",
        "i don't think this is", "going to decline", "not going to move forward"
    ]
    follow_up_signals = [
        "call you back", "i'll follow up", "let me think about it",
        "talk to my spouse", "talk to my wife", "talk to my husband",
        "talk to my partner", "circle back", "touch base",
        "schedule another call", "send you more info", "i'll call you tomorrow",
        "get back to you"
    ]

    closed_hits = sum(1 for s in closed_signals if s in text_lower)
    no_close_hits = sum(1 for s in no_close_signals if s in text_lower)
    follow_up_hits = sum(1 for s in follow_up_signals if s in text_lower)

    if closed_hits >= 2:
        return "Closed/Deposit"
    if no_close_hits >= 1 and closed_hits == 0:
        return "No-close"
    if follow_up_hits >= 1 and closed_hits == 0:
        return "Follow-up"

    return "Unclear - Review"


def process_closer(closer, days_back, existing_ids, log):
    zoom_token = get_zoom_access_token()
    meetings = get_recordings(closer["email"], zoom_token, days_back=days_back)
    log(f"{closer['name']}: found {len(meetings)} meetings")

    new_count = 0
    skipped_existing = 0
    skipped_no_transcript = 0

    for meeting in meetings:
        uuid = meeting["uuid"]

        if uuid in existing_ids:
            skipped_existing += 1
            continue

        zoom_token = get_zoom_access_token()  # refresh in case of long loop
        transcript_url = get_transcript_url(uuid, zoom_token)

        if not transcript_url:
            skipped_no_transcript += 1
            continue

        vtt_text = download_transcript(transcript_url)
        clean_text = clean_vtt(vtt_text)

        if len(clean_text.strip()) < 200:  # very short / near-empty call
            speakers = set()
            for line in clean_text.split("\n"):
                if ":" in line:
                    speakers.add(line.split(":", 1)[0].strip().lower())

            if len(speakers) <= 1:
                # Closer talked alone, or near-total silence = No-show, still log it
                outcome = "No-show"
            else:
                skipped_no_transcript += 1
                continue
        else:
            outcome = classify_outcome(clean_text)

        prospect_name = extract_prospect_name(clean_text, closer["name"])

        start_time = meeting.get("start_time", "")
        doc_title = f"{closer['name']} - {start_time}"

        doc_id = create_doc(doc_title)
        insert_text(doc_id, clean_text)
        move_to_folder(doc_id, TRANSCRIPTS_FOLDER_ID)
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

        row = [
            closer["name"],
            uuid,
            meeting.get("topic", ""),
            start_time,
            str(meeting.get("duration", "")),
            meeting.get("share_url", ""),
            doc_url,
            datetime.now(timezone.utc).isoformat(),
            prospect_name,
            outcome,
        ]
        append_row(row)
        existing_ids.add(uuid)
        new_count += 1
        log(f"  + Logged: {meeting.get('topic')} ({start_time}) - prospect: {prospect_name} - outcome: {outcome}")

        time.sleep(1)  # be gentle on API rate limits

    log(f"{closer['name']}: {new_count} new, {skipped_existing} already logged, {skipped_no_transcript} skipped (no/short transcript)")
    return new_count


def run_pipeline(days_back=7, log=print):
    log("Starting pipeline run...")
    existing_ids = get_existing_meeting_ids()
    log(f"Loaded {len(existing_ids)} existing meeting IDs from sheet")

    total_new = 0
    for closer in CLOSERS:
        total_new += process_closer(closer, days_back, existing_ids, log)

    log(f"Done. {total_new} new calls logged total.")
    return total_new


if __name__ == "__main__":
    run_pipeline(days_back=7)