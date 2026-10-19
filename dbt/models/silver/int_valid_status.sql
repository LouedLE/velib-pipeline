{{ config(materialized='view') }}
-- Remontées exploitables : station en service, donnée fraîche, station connue du référentiel.
select
    s.*,
    d.capacity,
    s.bikes_available = 0  as is_empty,
    s.docks_available = 0  as is_full,
    isodow(s.snapshot_at_paris) >= 6 as is_weekend,
    hour(s.snapshot_at_paris)        as hour_paris
from {{ ref('stg_station_status') }} as s
inner join {{ ref('dim_station') }} as d using (station_id)
where s.is_installed
  and not s.is_stale
