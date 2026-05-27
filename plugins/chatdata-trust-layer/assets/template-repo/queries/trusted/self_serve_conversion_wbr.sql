select
  week_start,
  qualified_signups,
  qualified_sessions,
  round(100.0 * qualified_signups / nullif(qualified_sessions, 0), 1) as self_serve_conversion_pct
from analytics.self_serve_conversion_wbr
where week_start >= current_date - interval '28 day'
order by week_start desc;
