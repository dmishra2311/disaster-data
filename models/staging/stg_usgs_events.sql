select
    filename as source_file,
    unnest(features) as feature
from read_json_auto("{{ var('raw_path') }}/usgs_*.json",
                    filename = true, union_by_name = true)