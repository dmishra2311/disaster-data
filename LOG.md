## 2026-08-29
Did: set up repo. Fetch script pulls USGS all_day feed and lands raw JSON.
  Loaded to staging in DuckDB, built dwh_usgs_events with dedup on latest
  'updated'. First chart: event count by magnitude bucket. 189 events.
Broke: DuckDB silently renamed my duplicate column alias to event_time_1
  instead of throwing an error like Postgres would(fixed it by renaming the field). 
  Also hit a file lock —the CLI holds the db as a writer, so Python couldn't open it until I quit.
Next: split the chart by US vs non-US to test the two-populations idea.
Questions: why do the bars jump back up at magnitude 4? what does
  'magnitude of completeness' mean? why does the CLI lock the file even
  when I open it read-only?
  
  
  
  
## 2026-08-30
Did: Second fetch (26 hrs after the first). Rebuilt stage and dwh.
  Split place_description on last comma to get region.
Found: ~89% of all 367 events are US (CA alone is 167). The "global"
  magnitude chart was mostly a chart of California. Region strings are
  messy 4 ways: CA vs California, no comma at all, US territories,
  and prose like "off the coast of Oregon".
Broke: 26 hrs between pulls, so a 2h02m window fell out of the rolling
  feed — ~16 events lost. Dedup logic still untested, no overlap yet.
Next: fetch within 24 hrs to test dedup. Build ref_us_regions lookup
  table. Backfill the gap via the USGS query API (start/end params).
Questions: what happens to my dataset if I skip a weekend? what's the
  difference between "can detect" and "complete"? why did some regions
  come back as the whole string instead of a suffix?




## 2026-09-06
Did: Backfilled a year of history via the USGS query API (not the daily
  feed). Monthly chunks, resumable, splits a chunk if it exceeds the cap.
  139,504 events. Widened the staging glob to usgs_*.json and added
  union_by_name — the query API returns fields the feed doesn't.
Found: 352 events arrived twice, but 367 should have. The missing 15 were
  published live and later deleted by USGS. Confirmed independently:
  includedeleted=true returns 12,437 for August vs 11,945 without — 4%
  retracted, matching the 15/367 rate. Also: August grew by one event
  between my count check and my download. The catalogue is live, not fixed.
Broke: re-running with includedeleted=true is much slower server-side —
  504 Gateway Timeout on the first chunk. The script splits on count but
  not on failure, so adaptive chunking never triggered for this. Fix
  written, not yet run.
Next: apply the split-on-failure retry, re-run the deleted backfill.
  Then check how a deleted event is actually marked (properties.status).
  Add status and magType to the dwh table.
Questions: how does a rebuild-from-raw design detect a deletion at all?
  what's the difference between automatic and reviewed status?
  why would asking for deleted events be so much slower for their server?  
  
  
  
  
 ## 2026-09-21
Did: Checked the deleted-events backfill. 21 files, June missing.
Broke: June failed on count, not query — retry fix only covered the query
  call. Patched count path too; June still fails. Likely USGS server-side.
  Main June data is intact; only deleted-event markers are missing.
Next: check whether the retry lines printed. Test June count URL in browser
  with/without includedeleted.
  
  
## KNOWN GAPS
- 2026-06: deleted-event markers unavailable. USGS returns 504 for
  includedeleted=true on this month, in script and browser alike.
  Regular June events are present and complete.
  
  
  
  ## 2026-09-22 (cont.)
Did: Rebuilt dwh with status, magType, is_deleted, and a two-level QUALIFY
  ordering (prefer a row with a status, then newest updated) so a tombstone
  can't overwrite a live record. Recovered aka2026rdzttb.
Found: three distinct bad-row classes, not one —
  1. tombstones (~295): status null, everything stripped, coords 0,0
  2. deleted-with-data (~4,700): status 'deleted', real mag and location
  3. ten uw* rows (PNW network): status 'deleted', coords 0,0, null place,
     mag 0.0 or null, but a REAL event_time. Feb and May bursts.
  Group 3 is a published bad record, not a deletion artefact — and it would
  pass a naive "has a timestamp" check.
  305 rows unplottable in total. No out-of-range coords.
Next: decide how to represent groups 1-3 in the model. Then dbt.
Questions: why does one network emit 0,0 records in bursts?
  should the dwh hold unplottable rows at all, or a separate table?

