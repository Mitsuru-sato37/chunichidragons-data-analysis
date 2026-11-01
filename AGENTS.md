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

- When suggesting Chunichi Dragons video ideas, check [video idea index](docs/video_idea_index.md) first. New public-safe candidate details belong in this repository; use [video candidate workflow](docs/drive_github_workflow.md). Do not put private planning details or private Drive titles/links in this public repository.


## Idea storage and shared standards

- Store ideas specific to this project in its repository's existing idea index or under docs/ideas/, one Markdown file per idea. Keep a single canonical copy; do not duplicate the same memo in Drive.
- Store ideas for standards or templates shared across repositories in Google Drive AI-Workspace/00_Inbox. Put ideas with no known project there temporarily, then move them to the owning repository when identified.
- Check repository visibility before adding idea details. In a public repository, record only content intended for public release. Keep private planning details in a private project-specific location and do not expose its title or link in public files.
- When a shared standard changes, update this repository's applicable instructions and procedures, preserve project-specific rules, and record the change in the canonical handoff. Follow the current process at https://github.com/Mitsuru-sato37/ai-workspace-foundation/blob/main/docs/14_shared_standard_rollout.md and the idea-storage source at https://github.com/Mitsuru-sato37/ai-workspace-foundation/blob/main/docs/11_idea_intake.md.
