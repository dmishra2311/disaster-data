"""Count earthquakes by magnitude bucket and save a chart."""

import duckdb
import matplotlib
matplotlib.use("Agg")          # write to a file, don't open a window
import matplotlib.pyplot as plt

con = duckdb.connect("disaster.duckdb", read_only=True)

rows = con.sql("""
    SELECT floor(magnitude * 2) / 2 AS mag_bucket,
           count(*)                 AS event_count
    FROM dwh_usgs_events
    WHERE magnitude IS NOT NULL
    GROUP BY 1
    ORDER BY 1
""").fetchall()

buckets = [str(r[0]) for r in rows]
counts = [r[1] for r in rows]

plt.figure(figsize=(9, 5))
plt.bar(buckets, counts)
plt.xlabel("Magnitude")
plt.ylabel("Number of events")
plt.title("USGS earthquakes by magnitude")
plt.tight_layout()
plt.savefig("magnitude_distribution.png", dpi=120)

print(f"Saved magnitude_distribution.png ({sum(counts)} events, {len(buckets)} buckets)")