-- Top five scoring performances
SELECT
    p.first_name || ' ' || p.last_name AS player,
    t.abbreviation AS team,
    g.game_date,
    s.points,
    s.rebounds,
    s.assists
FROM player_game_stats s
JOIN players p ON s.player_id = p.player_id
JOIN teams t ON p.team_id = t.team_id
JOIN games g ON s.game_id = g.game_id
ORDER BY s.points DESC
LIMIT 5;

-- Average player statistics for each team
SELECT
    t.abbreviation AS team,
    ROUND(AVG(s.points), 2) AS average_points,
    ROUND(AVG(s.rebounds), 2) AS average_rebounds,
    ROUND(AVG(s.assists), 2) AS average_assists,
    ROUND(SUM(s.field_goals_made) * 1.0 /
        NULLIF(SUM(s.field_goals_attempted), 0), 3) AS field_goal_pct
FROM player_game_stats s
JOIN players p ON s.player_id = p.player_id
JOIN teams t ON p.team_id = t.team_id
GROUP BY t.team_id, t.abbreviation
ORDER BY average_points DESC;

-- Players currently listed on the injury report
SELECT
    p.first_name || ' ' || p.last_name AS player,
    t.abbreviation AS team,
    i.report_date,
    i.status,
    i.description,
    COALESCE(i.expected_return_date, 'TBD') AS expected_return
FROM injuries i
JOIN players p ON i.player_id = p.player_id
JOIN teams t ON p.team_id = t.team_id
WHERE i.status != 'Available'
ORDER BY i.report_date DESC;

-- Game results
SELECT
    g.game_date,
    away.abbreviation AS away_team,
    g.away_score,
    home.abbreviation AS home_team,
    g.home_score,
    CASE
        WHEN g.home_score > g.away_score THEN home.abbreviation
        ELSE away.abbreviation
    END AS winner
FROM games g
JOIN teams home ON g.home_team_id = home.team_id
JOIN teams away ON g.away_team_id = away.team_id
ORDER BY g.game_date;

-- Advanced player metric leaders
SELECT
    p.first_name || ' ' || p.last_name AS player,
    t.abbreviation AS team,
    m.usage_rate,
    m.true_shooting_pct,
    m.player_efficiency_rating,
    m.offensive_rating,
    m.defensive_rating
FROM advanced_player_metrics m
JOIN players p ON m.player_id = p.player_id
JOIN teams t ON p.team_id = t.team_id
ORDER BY m.offensive_rating DESC;
