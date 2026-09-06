WITH daily AS (
  SELECT DISTINCT user_id, date(login_day) AS day
  FROM logins WHERE login_day <= :asof
), numbered AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY user_id ORDER BY day
  ) AS rn FROM daily
), islands AS (
  SELECT user_id, date(day, '-'||rn||' days') AS grp,
         MIN(day) AS start_day, MAX(day) AS end_day,
         COUNT(*) AS days
  FROM numbered GROUP BY user_id,grp
)
SELECT user_id, MAX(days) AS longest_streak,
       MAX(CASE WHEN end_day=:asof THEN days ELSE 0 END) AS current_streak
FROM islands GROUP BY user_id ORDER BY user_id;