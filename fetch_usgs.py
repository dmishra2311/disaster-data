"""
Download the USGS 'all earthquakes, past day' feed and save it to disk unchanged.

Run it:  python fetch_usgs.py

Each run writes one new file into data/raw/ named with the UTC time of the fetch,
e.g. data/raw/usgs_all_day_20260829T143000Z.json

Nothing here parses or cleans the data. That is on purpose. This file is the
permanent record of what the source said at the moment we asked it.
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
RAW_DIR = Path("data/raw")
TIMEOUT_SECONDS = 30


def fetch(url):
    """Ask the URL for its contents. Returns the raw bytes."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "personal-learning-project (contact: deba)"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def main():
    fetched_at = datetime.now(timezone.utc)
    stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")

    try:
        payload = fetch(FEED_URL)
    except urllib.error.HTTPError as err:
        print(f"USGS returned an error status: {err.code} {err.reason}")
        return 1
    except urllib.error.URLError as err:
        print(f"Could not reach USGS: {err.reason}")
        return 1
    except TimeoutError:
        print(f"USGS did not respond within {TIMEOUT_SECONDS} seconds.")
        return 1

    # A cheap sanity check: is this actually JSON, and does it look like the feed?
    # We are not cleaning the data here, only refusing to save obvious garbage.
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        print("Response was not valid JSON. Nothing saved.")
        return 1

    if "features" not in parsed:
        print("JSON came back but has no 'features' key. Nothing saved.")
        return 1

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"usgs_all_day_{stamp}.json"

    # Write the original bytes, not the re-serialised parsed version.
    out_path.write_bytes(payload)

    event_count = len(parsed["features"])
    size_kb = len(payload) / 1024
    print(f"Saved {out_path}  ({event_count} events, {size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
