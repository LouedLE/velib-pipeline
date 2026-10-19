-- Fiabilité de chaque station : part du temps où elle est vide ou pleine.
with status as (
    select * from {{ ref('stg_station_status') }}
),

valid as (
    select * from {{ ref('int_valid_status') }}
),

freshness as (
    select station_id, avg(is_stale::integer) as pct_stale
    from status
    group by station_id
),

usage as (
    select
        station_id,
        count(*)                                                   as n_snapshots,
        avg(is_empty::integer)                                     as pct_empty,
        avg(is_full::integer)                                      as pct_full,
        avg(bikes_available / capacity)                            as avg_fill_rate,
        avg(ebike_available / nullif(bikes_available, 0))          as avg_ebike_share
    from valid
    group by station_id
)

select
    d.station_id,
    d.station_name,
    d.latitude,
    d.longitude,
    d.capacity,
    u.n_snapshots,
    round(u.pct_empty, 4)        as pct_empty,
    round(u.pct_full, 4)         as pct_full,
    round(u.pct_empty + u.pct_full, 4) as pct_unusable,
    round(u.avg_fill_rate, 4)    as avg_fill_rate,
    round(u.avg_ebike_share, 4)  as avg_ebike_share,
    round(f.pct_stale, 4)        as pct_stale
from {{ ref('dim_station') }} as d
inner join usage as u using (station_id)
left join freshness as f using (station_id)
