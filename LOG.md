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