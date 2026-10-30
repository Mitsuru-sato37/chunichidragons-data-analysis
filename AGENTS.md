# Repository instructions

- This repository analyzes Chunichi Dragons data. The initial scope is 2026 Nippon Baseball Data Repository CSVs.
- Keep original ZIPs, CSVs, Parquet files, joined pitch data, and derived reports out of Git. Do not add substantial excerpts as fixtures or documentation.
- Use local paths supplied at run time. Do not download or redistribute source data automatically.
- Join by `game_id`. Never pair game IDs and dates by list position after sorting or shuffling.
- Treat PBP `game_date` as the correction source for game stats dates, while clearly labeling it as unconfirmed by an independent source.
- Check one PBP date and one game type per game, both sides of the join, missing values, and batting numerics before emitting aggregates.
- Separate preseason, regular season, and interleague in output. Unknown game types should stop the aggregate and appear in validation.
- Do not present these numbers as final video publication figures until checked against an independent source and usage rights are confirmed.
- Run `python -m unittest discover -s tests -v` after changing the analyzer.

## Chunichi video candidates

- When suggesting Chunichi Dragons video ideas, check [video idea index](docs/video_idea_index.md) and the linked Drive `#00動画` folder first. For this repository's exact folder and candidate-save procedure, use [video candidate workflow](docs/drive_github_workflow.md).
