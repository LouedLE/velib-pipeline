-- Une remontée exploitable ne peut pas être à la fois vide et pleine.
-- Ce cas signale une station fermée qui a échappé au filtre de int_valid_status.
select station_id, snapshot_at, bikes_available, docks_available
from {{ ref('int_valid_status') }}
where is_empty and is_full
