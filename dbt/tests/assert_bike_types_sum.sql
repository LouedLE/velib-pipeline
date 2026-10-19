-- Mécaniques + électriques doivent égaler le total de vélos disponibles.
select station_id, snapshot_at, bikes_available, mechanical_available, ebike_available
from {{ ref('stg_station_status') }}
where mechanical_available + ebike_available <> bikes_available
