-- Vélos + bornes libres ne devraient pas dépasser la capacité déclarée.
-- La source GBFS dépasse parfois la capacité (bornes ajoutées, référentiel en retard) :
-- le test alerte sans bloquer le pipeline.
{{ config(severity='warn') }}

select s.station_id, s.snapshot_at, s.bikes_available, s.docks_available, d.capacity
from {{ ref('stg_station_status') }} as s
inner join {{ ref('dim_station') }} as d using (station_id)
where s.bikes_available + s.docks_available > d.capacity
