select
    station_id,
    station_code,
    station_name,
    latitude,
    longitude,
    capacity,
    last_seen_at
from {{ ref('stg_station_information') }}
where capacity > 0
