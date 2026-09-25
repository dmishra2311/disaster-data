SELECT  feature.id AS event_id,
        feature.properties.mag AS magnitude,
        feature.properties.magType AS magnitude_type,
        feature.properties.place AS place_description,
        to_timestamp(feature.properties.time / 1000) AS event_time,
        feature.geometry.coordinates[1] AS longitude,
        feature.geometry.coordinates[2] AS latitude,
        feature.geometry.coordinates[3] AS depth,
        feature.properties.type AS event_type,
        feature.properties.status AS status,
        feature.properties.tsunami AS tsunami_flag,
        source_file,
        to_timestamp(feature.properties.updated / 1000) AS last_revised_at,
        bool_or(feature.properties.status IS NULL
                OR feature.properties.status = 'deleted')
          OVER (PARTITION BY feature.id) AS is_deleted
FROM {{ ref('stg_usgs_events') }}
QUALIFY row_number() OVER (
  PARTITION BY feature.id
  ORDER BY (feature.properties.status IS NOT NULL) DESC,
           feature.properties.updated DESC
) = 1