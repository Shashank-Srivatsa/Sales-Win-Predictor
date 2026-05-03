WITH activities AS (
    SELECT
        opportunity_id,
        activity_date,
        activity_type,
        is_positive_outcome,
        is_negative_outcome
    FROM {{ ref('stg_crm_activities') }}
),

agg AS (
    SELECT
        opportunity_id,
        COUNT(*)                                            AS total_activities,
        SUM(is_positive_outcome)                            AS total_positive_activities,
        SUM(is_negative_outcome)                            AS total_negative_activities,
        MAX(activity_date)                                  AS last_activity_date,
        SUM(CASE WHEN activity_date >= DATEADD('day', -14, CURRENT_DATE) THEN 1 ELSE 0 END)
                                                            AS activities_last_14_days,
        SUM(CASE WHEN activity_type = 'In-Person Meeting' THEN 1 ELSE 0 END) AS total_meetings,
        SUM(CASE WHEN activity_type = 'Phone Call'        THEN 1 ELSE 0 END) AS total_calls,
        SUM(CASE WHEN activity_type = 'Email'             THEN 1 ELSE 0 END) AS total_emails
    FROM activities
    GROUP BY opportunity_id
)

SELECT
    opportunity_id,
    COALESCE(total_activities, {{ var('default_total_activities') }})
                                                                    AS total_activities,
    COALESCE(total_positive_activities, {{ var('default_total_activities') }})
                                                                    AS total_positive_activities,
    COALESCE(total_negative_activities, {{ var('default_total_activities') }})
                                                                    AS total_negative_activities,
    {{ safe_divide('total_positive_activities', 'total_activities') }} AS positive_activity_ratio,
    COALESCE(last_activity_date, CAST('1900-01-01' AS DATE))       AS last_activity_date,
    COALESCE(DATEDIFF('day', last_activity_date, CURRENT_DATE), {{ var('default_days_since_activity') }})
                                                                    AS days_since_last_activity,
    COALESCE(activities_last_14_days, {{ var('default_total_activities') }})
                                                                    AS activities_last_14_days,
    {{ safe_divide('activities_last_14_days', 'total_activities') }} AS engagement_score,
    COALESCE(total_meetings, {{ var('default_total_activities') }})  AS total_meetings,
    COALESCE(total_calls, {{ var('default_total_activities') }})     AS total_calls,
    COALESCE(total_emails, {{ var('default_total_activities') }})    AS total_emails
FROM agg
