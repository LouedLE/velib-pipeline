-- Profil horaire moyen par station, séparé semaine / week-end (heure de Paris).
select
    station_id,
    case when is_weekend then 'week-end' else 'semaine' end as day_type,
    hour_paris,
    count(*)                                   as n_snapshots,
    round(avg(bikes_available), 2)             as avg_bikes_available,
    round(avg(bikes_available / capacity), 4)  as avg_fill_rate,
    round(avg(is_empty::integer), 4)           as pct_empty,
    round(avg(is_full::integer), 4)            as pct_full
from {{ ref('int_valid_status') }}
group by all
