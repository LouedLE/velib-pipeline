-- État global du réseau à chaque collecte.
select
    snapshot_at,
    snapshot_at_paris,
    count(*)                         as stations_reporting,
    sum(bikes_available)             as bikes_available,
    sum(ebike_available)             as ebike_available,
    sum(is_empty::integer)           as stations_empty,
    sum(is_full::integer)            as stations_full
from {{ ref('int_valid_status') }}
group by all
