# Individual Framework Performance

The intermediate project feedback suggested evaluating the performance of the individual parts of the framework instead of trying to evaluate the entire framework at once. I addressed this by adding `benchmark_framework.py`.

The benchmark uses the local CSV sample data and an in-memory SQLite database. This keeps the test repeatable and avoids mixing API network time with database time.

## Benchmark Command

```bash
python benchmark_framework.py --iterations 1000 --output benchmark_results.csv
```

## Results From Local Test

| Framework Part | Result |
|---|---:|
| Schema creation and index creation | 0.9183 ms |
| Load `teams` CSV | 6.6278 ms |
| Load `players` CSV | 6.4617 ms |
| Load `games` CSV | 6.3043 ms |
| Load `player_game_stats` CSV | 6.8532 ms |
| Load `injuries` CSV | 6.3872 ms |
| Load `advanced_player_metrics` CSV | 6.2215 ms |
| Top scoring query, 1,000 runs | 11.8010 ms |
| Team summary query, 1,000 runs | 25.5828 ms |
| Injury report query, 1,000 runs | 7.3376 ms |
| Advanced leaders query, 1,000 runs | 15.0208 ms |
| pandas statistics module, 1,000 runs | 6417.7009 ms |
| Query plan check | 0.0572 ms |
| Foreign-key validation | 0.0345 ms |

## Interpretation

The query timing shows that the SQL reports are fast on the current sample data. The pandas statistics module is the slowest measured part because it repeatedly loads SQL results into a dataframe and calculates descriptive statistics and correlations.

The query plan check showed:

```text
SCAN player_game_stats USING INDEX idx_stats_points
```

This means SQLite is using the `idx_stats_points` index for the top-scoring query. The current data set is small, so these timings are mainly a framework baseline. The same benchmark can be repeated after loading more API data.
