{{ config(materialized='view') }}
-- Remontées exploitables : station installée et ouverte (location et dépôt possibles),
-- donnée fraîche, station connue du référentiel.
-- Une station fermée affiche 0 vélo et 0 borne : sans ce filtre, elle serait comptée vide ET pleine.
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
  and s.is_renting
  and s.is_returning
  and not s.is_stale
