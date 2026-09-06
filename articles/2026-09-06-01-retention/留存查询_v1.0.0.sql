WITH daily AS (
  SELECT DISTINCT user_id, date(login_time) AS login_day
  FROM logins WHERE date(login_time) <= :asof
), targets(day_n) AS (VALUES (1),(3),(7))
SELECT u.signup_date, t.day_n,
       COUNT(DISTINCT u.user_id) AS new_users,
       CASE WHEN date(u.signup_date, '+'||t.day_n||' days') <= :asof
            THEN COUNT(DISTINCT d.user_id) END AS retained,
       CASE WHEN date(u.signup_date, '+'||t.day_n||' days') <= :asof
            THEN 1.0*COUNT(DISTINCT d.user_id)
                 /COUNT(DISTINCT u.user_id) END AS rate
FROM users u CROSS JOIN targets t
LEFT JOIN daily d ON d.user_id=u.user_id
 AND d.login_day=date(u.signup_date, '+'||t.day_n||' days')
WHERE u.signup_date <= :asof
GROUP BY u.signup_date,t.day_n
ORDER BY u.signup_date,t.day_n;