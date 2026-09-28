# disaster-data

An end-to-end data pipeline over public natural-hazard datasets, built as a
deliberate learning exercise rather than a product.

## What it does

Ingests earthquake data from the USGS FDSN API and Atlantic hurricane tracks
from NOAA's HURDAT2 database, lands both as immutable raw files, and
transforms them into a queryable warehouse with dbt.

Raw files are never modified. Every model rebuilds from them, so a transform
bug is fixed by re-running rather than re-downloading.

## Stack

DuckDB, dbt, Python (stdlib only). No cloud dependencies — it runs on a laptop.

## Data sources

- **USGS FDSN** — ~142,000 events, Sept 2025 to present. Daily feed plus a
  chunked, resumable historical backfill with adaptive splitting.
- **NOAA HURDAT2** — Atlantic tropical cyclones, 1851–2025, six-hourly track
  observations.

## Notes on data quality

Most of the interesting work has been in what the sources don't tell you:

- **Detection bias.** Event counts below roughly M4 measure sensor coverage,
  not seismic activity. ~89% of raw USGS events are US, because dense
  networks detect what sparse ones miss.
- **Deletions.** ~4% of published earthquakes are later retracted. Some
  become tombstone records with stripped fields and placeholder 0,0
  coordinates. A naive "latest version wins" dedup lets a tombstone
  overwrite a live event.
- **Retrospective revision.** Neither catalogue is fixed. USGS revises
  magnitudes; NOAA re-analysed the 1971–1975 hurricane seasons in
  September 2026.
- **Known gaps** are recorded explicitly rather than left implicit.

## Structure

    data/raw/        immutable source files (gitignored)
    models/staging/  raw parsing, one row per source record
    models/warehouse/ deduplicated, typed, flagged
    LOG.md           session log — what was done, what broke, what was found
