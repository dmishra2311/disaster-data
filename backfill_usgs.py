"""
Backfill historical USGS earthquakes, one month at a time.

Run it:  python backfill_usgs.py

Writes one file per chunk into data/raw/, e.g.
    data/raw/usgs_query_2025-09-01_2025-10-01.json

Safe to re-run. Chunks already on disk are skipped, so if it dies at month 9
you just run it again and it picks up where it stopped.

Nothing here parses or cleans. Same rule as fetch_usgs.py: land it as it came.
"""

import sys
import json
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

COUNT_URL = "https://earthquake.usgs.gov/fdsnws/event/1/count"
QUERY_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
RAW_DIR = Path("data/raw")
TIMEOUT_SECONDS = 120
PAUSE_SECONDS = 2          # be polite to a free public API
SAFETY_MARGIN = 0.8        # split a chunk if it exceeds 80% of the cap

# How far back to go. Change these two lines to backfill a different span.
START = date(2026, 6, 1)
END = date(2026, 7, 1)


def month_edges(start, end):
    """Yield (chunk_start, chunk_end) pairs, one per calendar month."""
    edges = []
    cursor = start
    while cursor < end:
        if cursor.month == 12:
            nxt = date(cursor.year + 1, 1, 1)
        else:
            nxt = date(cursor.year, cursor.month + 1, 1)
        edges.append((cursor, min(nxt, end)))
        cursor = nxt
    return edges


def midpoint(start, end):
    """The date halfway between two dates, used when a chunk is too big."""
    return start + (end - start) / 2


def call_api(base_url, start, end):
    """Ask USGS for a date range. Returns raw bytes."""
    #params = urllib.parse.urlencode({
     #   "format": "geojson",
      #  "starttime": start.isoformat(),
      #  "endtime": end.isoformat(),
    #})
    params = urllib.parse.urlencode({
        "format": "geojson",
        "starttime": start.isoformat(),
        "endtime": end.isoformat(),
        "includedeleted": "true",
    })
    request = urllib.request.Request(
        f"{base_url}?{params}",
        headers={"User-Agent": "personal-learning-project (contact: deba)"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def get_count(start, end):
    """How many events are in this range, and what's the per-request cap?"""
    payload = json.loads(call_api(COUNT_URL, start, end))
    return payload["count"], payload["maxAllowed"]


def fetch_chunk(start, end):
    """
    Download one date range and save it. Recurses into halves if the range
    holds more events than one request is allowed to return.
    """
    #out_path = RAW_DIR / f"usgs_query_{start.isoformat()}_{end.isoformat()}.json"
    out_path = RAW_DIR / f"usgs_deleted_{start.isoformat()}_{end.isoformat()}.json"

    if out_path.exists():
        print(f"  skip   {start} -> {end}  (already on disk)")
        return True

    try:
        count, max_allowed = get_count(start, end)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as err:
        print(f"  FAIL   {start} -> {end}  count request failed: {err}")
        return False

    # Too big for one request? Split the range in half and do each side.
    if count > max_allowed * SAFETY_MARGIN:
        mid = midpoint(start, end)
        if mid <= start or mid >= end:
            print(f"  FAIL   {start} -> {end}  cannot split further ({count} events)")
            return False
        print(f"  split  {start} -> {end}  ({count} events, cap {max_allowed})")
        left = fetch_chunk(start, mid)
        right = fetch_chunk(mid, end)
        return left and right

    try:
        count, max_allowed = get_count(start, end)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as err:
        mid = midpoint(start, end)
        if mid > start and mid < end and (end - start).days > 1:
            print(f"  retry  {start} -> {end}  count failed ({err}), splitting")
            time.sleep(PAUSE_SECONDS)
            return fetch_chunk(start, mid) and fetch_chunk(mid, end)
        print(f"  FAIL   {start} -> {end}  count request failed: {err}")
        return False

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        print(f"  FAIL   {start} -> {end}  response was not valid JSON")
        return False

    if "features" not in parsed:
        print(f"  FAIL   {start} -> {end}  no 'features' key in response")
        return False

    got = len(parsed["features"])
    if got != count:
        # Not fatal, but you want to know. Events get added and revised.
        print(f"  WARN   {start} -> {end}  expected {count}, got {got}")

    out_path.write_bytes(payload)
    print(f"  ok     {start} -> {end}  {got} events, {len(payload)/1024/1024:.1f} MB")
    time.sleep(PAUSE_SECONDS)
    return True


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    chunks = month_edges(START, END)
    print(f"Backfilling {START} to {END} in {len(chunks)} monthly chunks.\n")

    failures = []
    for start, end in chunks:
        if not fetch_chunk(start, end):
            failures.append((start, end))

    print()
    if failures:
        print(f"{len(failures)} chunk(s) failed. Re-run to retry just those:")
        for start, end in failures:
            print(f"  {start} -> {end}")
        return 1

    total_files = len(list(RAW_DIR.glob("usgs_query_*.json")))
    print(f"Done. {total_files} query files on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
    
