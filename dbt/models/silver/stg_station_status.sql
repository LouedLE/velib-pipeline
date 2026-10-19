-- Une ligne par station et par collecte, typée et enrichie d'un indicateur de fraîcheur.
with source as (
    select * from {{ source('bronze', 'station_status') }}
),

typed as (
    select
        station_id::varchar                                   as station_id,
        snapshot_at::timestamptz                              as snapshot_at,
        timezone('Europe/Paris', snapshot_at::timestamptz)    as snapshot_at_paris,
        to_timestamp(last_reported)                           as last_reported_at,
        num_bikes_available::integer                          as bikes_available,
        coalesce(num_mechanical_available, 0)::integer        as mechanical_available,
        coalesce(num_ebike_available, 0)::integer             as ebike_available,
        num_docks_available::integer                          as docks_available,
        is_installed = 1                                      as is_installed,
        is_renting = 1                                        as is_renting,
        is_returning = 1                                      as is_returning
    from source
),

deduplicated as (
    -- Une collecte relancée deux fois produirait des doublons : on garde une ligne.
    select *
    from typed
    qualify row_number() over (partition by station_id, snapshot_at order by last_reported_at desc) = 1
)

select
    {{ dbt.concat(["station_id", "'_'", "strftime(snapshot_at, '%Y%m%d%H%M%S')"]) }} as status_key,
    *,
    date_diff('minute', last_reported_at, snapshot_at)                   as staleness_minutes,
    date_diff('minute', last_reported_at, snapshot_at) > {{ var('stale_after_minutes') }} as is_stale
from deduplicated
