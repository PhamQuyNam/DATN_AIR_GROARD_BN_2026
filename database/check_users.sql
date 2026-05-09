SELECT u.id, u.email, u.role, COUNT(f.id) as fav_count
FROM "user" u
LEFT JOIN userfavoritestation f ON f.user_id = u.id
GROUP BY u.id, u.email, u.role
ORDER BY u.id;
