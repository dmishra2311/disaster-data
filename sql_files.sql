CREATE OR REPLACE TABLE dwh_usgs_events AS
          SELECT  feature.id as event_id,
                  feature.properties.mag as magnitude,
                  feature.properties.place as place_description,
                  to_timestamp(feature.properties.time / 1000) AS event_time,
                  feature.geometry.coordinates[1] AS longitude,
                  feature.geometry.coordinates[2] AS latitude,
                  feature.geometry.coordinates[3] AS depth,
                  feature.properties.type AS event_type,
                  feature.properties.tsunami AS tsunami_flag,
                  source_file,
                  to_timestamp(feature.properties.updated / 1000) AS last_update_time                 
          FROM stg_usgs_events
  QUALIFY row_number() OVER (
  PARTITION BY feature.id
  ORDER BY feature.properties.updated DESC
) = 1





SELECT feature.id,
                             feature.properties.mag,
                             feature.properties.place,
                             to_timestamp(feature.properties.time / 1000) AS event_time,
                             feature.geometry.coordinates[1] AS longitude,
                             feature.geometry.coordinates[2] AS latitude,
feature.geometry.coordinates[3] AS depth,
feature.properties.tsunami AS tsunami
                      FROM stg_usgs_events
                      LIMIT 5;