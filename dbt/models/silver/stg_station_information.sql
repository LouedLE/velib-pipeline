-- Dernière version connue de chaque station.
with source as (
    select * from {{ source('bronze', 'station_information') }}
)

select
    station_id::varchar        as station_id,
    station_code::varchar      as station_code,
    trim(name)                 as station_name,
    lat::double                as latitude,
    lon::double                as longitude,
    capacity::integer          as capacity,
    snapshot_at::timestamptz   as last_seen_at
from source
qualify row_number() over (partition by station_id order by snapshot_at desc) = 1
