from datetime import datetime
from slack_deals import get_new_deal_messages, get_new_client_messages
from google_sheets import get_all_rows_with_numbers, update_row_outcome_and_amount

COL_CLOSER = 0
COL_START_TIME = 3
COL_PROSPECT_NAME = 8


def parse_sheet_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def match_new_client_deals(rows, already_matched_row_numbers, log=print):
    clients = get_new_client_messages()
    log(f"Fetched {len(clients)} client messages from #new-client")

    matched_count = 0

    for client in clients:
        if not client["confirmed"]:
            continue

        name_lower = client["name"].lower()
        name_parts = name_lower.split()
        if not name_parts:
            continue

        candidates = []
        for row in rows:
            if row["row_number"] in already_matched_row_numbers:
                continue
            vals = row["values"]
            if len(vals) <= COL_PROSPECT_NAME:
                continue
            prospect = vals[COL_PROSPECT_NAME].lower().strip()
            if not prospect or prospect == "unknown":
                continue
            if all(part in prospect for part in name_parts) or prospect in name_lower:
                candidates.append(row)

        if len(candidates) == 1:
            match = candidates[0]
            update_row_outcome_and_amount(match["row_number"], "Closed/Deposit", client["amount"])
            already_matched_row_numbers.add(match["row_number"])
            matched_count += 1
            log(f"  [new-client] Matched: {client['name']} -> row {match['row_number']}")

    log(f"#new-client pass: {matched_count} additional matches")
    return matched_count


def match_and_update_deals(log=print):
    deals = get_new_deal_messages()
    log(f"Fetched {len(deals)} deals from #new-deal")

    rows = get_all_rows_with_numbers()
    log(f"Loaded {len(rows)} sheet rows")

    matched_count = 0
    unmatched_count = 0
    unknown_closer_count = 0
    zero_candidates_count = 0
    ambiguous_count = 0
    bad_date_count = 0
    matched_row_numbers = set()

    for deal in deals:
        closer_name = deal["closer_name"]
        if closer_name == "Unknown":
            unknown_closer_count += 1
            continue

        try:
            closed_date = datetime.fromisoformat(deal["closed_date"])
        except Exception:
            bad_date_count += 1
            continue

        candidates = []
        for row in rows:
            vals = row["values"]
            if len(vals) <= COL_START_TIME:
                continue
            if vals[COL_CLOSER] != closer_name:
                continue
            call_date = parse_sheet_date(vals[COL_START_TIME])
            if not call_date:
                continue
            diff_days = (closed_date - call_date.replace(tzinfo=None)).days
            if 0 <= diff_days <= 14:
                candidates.append(row)

        match = None
        if len(candidates) == 1:
            match = candidates[0]
        elif len(candidates) > 1:
            first_name = deal["deal_first_name"].lower()
            name_matches = [
                r for r in candidates
                if len(r["values"]) > COL_PROSPECT_NAME and first_name in r["values"][COL_PROSPECT_NAME].lower()
            ]
            if len(name_matches) == 1:
                match = name_matches[0]
            else:
                ambiguous_count += 1
        else:
            zero_candidates_count += 1

        if match:
            cash = deal["cash_collected"].replace("$", "").replace(",", "").strip()
            update_row_outcome_and_amount(match["row_number"], "Closed/Deposit", cash)
            matched_row_numbers.add(match["row_number"])
            matched_count += 1
            log(f"  Matched: {closer_name} - {deal['deal_first_name']} {deal['deal_last_name']} -> row {match['row_number']}")
        else:
            unmatched_count += 1

    log(f"Done. {matched_count} matched, {unmatched_count} unmatched/ambiguous.")
    log(f"Breakdown: unknown_closer={unknown_closer_count}, bad_date={bad_date_count}, zero_candidates={zero_candidates_count}, ambiguous={ambiguous_count}")

    client_matches = match_new_client_deals(rows, matched_row_numbers, log=log)
    matched_count += client_matches

    return matched_count, unmatched_count


if __name__ == "__main__":
    match_and_update_deals()