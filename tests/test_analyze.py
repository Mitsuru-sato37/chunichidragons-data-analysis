import csv
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from analyze import run
from fetch_game import build_rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


class AnalysisTest(unittest.TestCase):
    def test_builds_supplement_from_one_game_api_records(self):
        text = [{"ID": 1, "GameID": "101", "GameDate": "20261003", "StartTime": "1800", "H_ID": "2", "V_ID": "4", "GameKindName": "公式戦", "Inning": "1", "TB": "1", "TextInfo_Bat_No": "1", "TextInfo_Bat_Text": "1球目:見逃しストライク"}]
        pitches = [{"gameId": "101", "fiveDigitSerialNumber": "01101", "atBatBallCount": "1", "ballSpeed": "145", "ballKind": 1, "pitId": "11", "batId": "22", "x": "75", "y": "80", "presult": "1", "bresult": "0"}]
        batting = [{"teamId": "4", "playerId": "22", "playerName": "選手", "pa": "1", "ab": "1", "h": "1", "h2b": "0", "h3b": "0", "hr": "0", "bb": "0", "hp": "0", "sf": "0", "so": "0", "rbi": "0", "r": "1"}]
        pbp_rows, stat_rows = build_rows("101", "2026-10-03", text, pitches, batting)
        self.assertEqual(len(pbp_rows), 1)
        self.assertEqual(pbp_rows[0]["pitch_number"], "1")
        self.assertEqual(pbp_rows[0]["release_speed_kmh"], "145")
        self.assertEqual(stat_rows[0]["batting_H"], "1")

    def test_reads_archive_without_extracting_it(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            root = Path(root)
            source = root / "source"
            archive_path = root / "nbdr.zip"
            out = root / "out"
            write_csv(source / "game_stats/2026-04_game_stats.csv", [
                {"game_id": "101", "game_date": "2026-04-02", "team_id": "4", "batting_PA": "1.0", "batting_AB": "1.0", "batting_H": "1.0", "batting_2B": "0.0", "batting_3B": "0.0", "batting_HR": "0.0", "batting_BB": "0.0", "batting_HBP": "0.0", "batting_SF": "0.0", "batting_SO": "0.0", "batting_RBI": "0.0", "batting_R": "0.0"},
            ])
            write_csv(source / "pbp/2026-04_pbp.csv", [
                {"game_id": "101", "game_date": "2026-04-01", "home_team_id": "4", "away_team_id": "1", "game_type_name": "公式戦", "pitch_number": "1", "release_speed_kmh": "140"},
            ])
            with ZipFile(archive_path, "w") as archive:
                for path in source.rglob("*.csv"):
                    archive.write(path, f"NBDR-main/{path.relative_to(source).as_posix()}")
            report = run(archive_path, out)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["date_mismatch_count"], 1)
            self.assertEqual(report["game_counts_by_type"], {"regular": 1})
            self.assertEqual(report["pitch_rows_by_type"], {"regular": 1})
            with (out / "joined_pbp.csv").open(encoding="utf-8") as handle:
                joined = list(csv.DictReader(handle))
            self.assertEqual(joined[0]["release_speed_kmh"], "140")

    def test_archive_accepts_explicit_local_supplement(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            root = Path(root)
            source = root / "source"
            extra = root / "extra"
            archive_path = root / "nbdr.zip"
            stat = {"game_id": "101", "game_date": "2026-10-01", "team_id": "4", **{f"batting_{c}": "0" for c in ("PA", "AB", "H", "2B", "3B", "HR", "BB", "HBP", "SF", "SO", "RBI", "R")}}
            write_csv(source / "game_stats/2026-10_game_stats.csv", [stat])
            write_csv(source / "pbp/2026-10_pbp.csv", [{"game_id": "101", "game_date": "2026-10-01", "home_team_id": "4", "away_team_id": "2", "game_type_name": "公式戦", "pitch_number": "1"}])
            with ZipFile(archive_path, "w") as archive:
                for path in source.rglob("*.csv"):
                    archive.write(path, f"NBDR-main/{path.relative_to(source).as_posix()}")
            write_csv(extra / "game_stats/2026-10-03_game_stats.csv", [{**stat, "game_id": "102", "game_date": "2026-10-03"}])
            write_csv(extra / "pbp/2026-10-03_pbp.csv", [{"game_id": "102", "game_date": "2026-10-03", "home_team_id": "2", "away_team_id": "4", "game_type_name": "公式戦", "pitch_number": "1", "release_speed_kmh": "150"}])
            report = run(archive_path, root / "out", extra)
            self.assertEqual(report["stats_games"], 2)
            self.assertEqual(report["pbp_games"], 2)
            self.assertEqual(report["status"], "passed")
            write_csv(extra / "game_stats/2026-10-04_game_stats.csv", [{**stat, "game_id": "101", "game_date": "2026-10-01"}])
            duplicate = run(archive_path, root / "out", extra)
            self.assertEqual(duplicate["status"], "failed")
            self.assertIn("game_id=101: stats appears in multiple source files", duplicate["invalid_batting_values"])

    def test_corrects_dates_and_aggregates_by_pbp_month_and_type(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            data = Path(root) / "data"
            out = Path(root) / "out"
            write_csv(data / "game_stats/2026-04_game_stats.csv", [
                {"game_id": "101", "game_date": "2026-04-02", "team_id": "4", "player_id": "1", "batting_PA": "4", "batting_AB": "3", "batting_H": "2", "batting_2B": "1", "batting_3B": "0", "batting_HR": "0", "batting_BB": "1", "batting_HBP": "0", "batting_SF": "0", "batting_SO": "0", "batting_RBI": "1", "batting_R": "1"},
                {"game_id": "102", "game_date": "2026-04-01", "team_id": "4", "player_id": "2", "batting_PA": "4", "batting_AB": "4", "batting_H": "1", "batting_2B": "0", "batting_3B": "0", "batting_HR": "1", "batting_BB": "0", "batting_HBP": "0", "batting_SF": "0", "batting_SO": "1", "batting_RBI": "1", "batting_R": "1"},
            ])
            write_csv(data / "pbp/2026-04_pbp.csv", [
                {"game_id": "101", "game_date": "2026-03-31 18:00:00+09:00", "home_team_id": "4", "away_team_id": "1", "game_type_name": "オープン戦", "play_id": "11", "pitch_number": "1"},
                {"game_id": "102", "game_date": "2026-04-01 18:00:00+09:00", "home_team_id": "1", "away_team_id": "4", "game_type_name": "交流戦", "play_id": "12", "pitch_number": "1"},
            ])
            report = run(data, out)
            self.assertEqual(report["status"], "passed")
            self.assertEqual([item["game_id"] for item in report["date_mismatches"]], ["101"])
            self.assertEqual(report["game_counts_before"], {"2026-04": 2})
            self.assertEqual(report["game_counts_after"], {"2026-03": 1, "2026-04": 1})
            with (out / "joined_pbp.csv").open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2)
            with (out / "monthly_batting.csv").open(encoding="utf-8") as handle:
                monthly = list(csv.DictReader(handle))
            self.assertEqual([(r["month"], r["game_type"], r["H"]) for r in monthly], [("2026-03", "preseason", "2"), ("2026-04", "interleague", "1")])
            self.assertEqual(monthly[0]["AVG"], "0.667")

    def test_missing_pbp_blocks_aggregate_but_writes_report(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            data = Path(root) / "data"
            out = Path(root) / "out"
            write_csv(data / "game_stats/2026-04_game_stats.csv", [
                {"game_id": "101", "game_date": "2026-04-02", "team_id": "4", "batting_PA": "1", "batting_AB": "1", "batting_H": "0", "batting_2B": "0", "batting_3B": "0", "batting_HR": "0", "batting_BB": "0", "batting_HBP": "0", "batting_SF": "0", "batting_SO": "1", "batting_RBI": "0", "batting_R": "0"},
            ])
            write_csv(data / "pbp/2026-04_pbp.csv", [
                {"game_id": "102", "game_date": "2026-04-01", "home_team_id": "4", "away_team_id": "1", "game_type_name": "公式戦", "play_id": "12", "pitch_number": "1"},
            ])
            report = run(data, out)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["missing_pbp_game_ids"], ["101"])
            self.assertEqual(report["missing_stats_game_ids"], ["102"])
            self.assertTrue((out / "validation.json").exists())
            self.assertFalse((out / "monthly_batting.csv").exists())

    def test_conflicting_pbp_date_removes_previous_aggregate(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            data = Path(root) / "data"
            out = Path(root) / "out"
            out.mkdir()
            (out / "monthly_batting.csv").write_text("stale", encoding="utf-8")
            write_csv(data / "game_stats/2026-04_game_stats.csv", [
                {"game_id": "101", "game_date": "2026-04-01", "team_id": "4", "batting_PA": "1", "batting_AB": "1", "batting_H": "0", "batting_2B": "0", "batting_3B": "0", "batting_HR": "0", "batting_BB": "0", "batting_HBP": "0", "batting_SF": "0", "batting_SO": "1", "batting_RBI": "0", "batting_R": "0"},
            ])
            write_csv(data / "pbp/2026-04_pbp.csv", [
                {"game_id": "101", "game_date": "2026-04-01", "home_team_id": "4", "away_team_id": "1", "game_type_name": "公式戦", "pitch_number": "1"},
                {"game_id": "101", "game_date": "2026-04-02", "home_team_id": "4", "away_team_id": "1", "game_type_name": "公式戦", "pitch_number": "2"},
            ])
            report = run(data, out)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["invalid_game_metadata"][0]["game_id"], "101")
            self.assertFalse((out / "monthly_batting.csv").exists())


if __name__ == "__main__":
    unittest.main()
