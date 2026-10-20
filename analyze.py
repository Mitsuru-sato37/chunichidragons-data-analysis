"""Validate and analyze local 2026 NBDR ZIP or extracted CSV files."""

import argparse
import csv
import fnmatch
import io
import json
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


TEAM_ID = "4"
BAT_COLUMNS = ("PA", "AB", "H", "2B", "3B", "HR", "BB", "HBP", "SF", "SO", "RBI", "R")


class ArchivedCsv:
    def __init__(self, archive, name):
        self.archive = archive
        self.name = name

    def open(self, encoding="utf-8-sig", newline=""):
        return io.TextIOWrapper(self.archive.open(self.name), encoding=encoding, newline=newline)

    def __str__(self):
        return self.name


def csv_rows(paths, required):
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = set(required) - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
            yield from reader


def date_only(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.strip()).date().isoformat()
    except ValueError:
        return ""


def game_type(name):
    value = name.strip().lower()
    if "オープン" in value or "exhibition" in value or "preseason" in value:
        return "preseason"
    if "交流" in value or "interleague" in value:
        return "interleague"
    if any(token in value for token in ("公式", "セ・リーグ", "パ・リーグ", "regular", "central league", "pacific league")):
        return "regular"
    return ""


def ratio(numerator, denominator):
    return f"{numerator / denominator:.3f}" if denominator else ""


def run(data_dir, out_dir, supplement_dir=None):
    return run_with_supplement(data_dir, out_dir, supplement_dir)


def run_with_supplement(data_dir, out_dir, supplement_dir=None):
    source = Path(data_dir)
    def add_supplement(stat_paths, pbp_paths):
        if supplement_dir is not None:
            extra = Path(supplement_dir)
            stat_paths.extend(sorted((extra / "game_stats").glob("2026-*_game_stats.csv")))
            pbp_paths.extend(sorted((extra / "pbp").glob("2026-*_pbp.csv")))
        return stat_paths, pbp_paths
    if source.is_file():
        with ZipFile(source) as archive:
            names = sorted(info.filename for info in archive.infolist() if not info.is_dir())
            stat_paths = [ArchivedCsv(archive, name) for name in names if PurePosixPath(name).parent.name == "game_stats" and fnmatch.fnmatch(PurePosixPath(name).name, "2026-*_game_stats.csv")]
            pbp_paths = [ArchivedCsv(archive, name) for name in names if PurePosixPath(name).parent.name == "pbp" and fnmatch.fnmatch(PurePosixPath(name).name, "2026-*_pbp.csv")]
            stat_paths, pbp_paths = add_supplement(stat_paths, pbp_paths)
            return analyze_files(stat_paths, pbp_paths, out_dir)
    stat_paths = sorted((source / "game_stats").glob("2026-*_game_stats.csv"))
    pbp_paths = sorted((source / "pbp").glob("2026-*_pbp.csv"))
    stat_paths, pbp_paths = add_supplement(stat_paths, pbp_paths)
    return analyze_files(stat_paths, pbp_paths, out_dir)


def analyze_files(stat_paths, pbp_paths, out_dir):
    out_dir = Path(out_dir)
    if not stat_paths or not pbp_paths:
        raise FileNotFoundError("2026 CSV files required under game_stats/ and pbp/ in the directory or ZIP")

    stats = defaultdict(list)
    stats_dates = defaultdict(set)
    pbp_dates = defaultdict(set)
    pbp_types = defaultdict(set)
    pbp_names = defaultdict(set)
    pitch_counts = Counter()
    issues = []
    stat_sources = {}
    pbp_sources = {}
    duplicate_sources = set()
    for path in stat_paths:
        for row in csv_rows([path], ("game_id", "game_date", "team_id", *(f"batting_{c}" for c in BAT_COLUMNS))):
            if row["team_id"].strip() != TEAM_ID:
                continue
            gid = row["game_id"].strip()
            if not gid:
                issues.append("stats row has empty game_id")
                continue
            if gid in stat_sources and stat_sources[gid] != str(path):
                duplicate_sources.add(("stats", gid))
            stat_sources.setdefault(gid, str(path))
            stats[gid].append(row)
            stats_dates[gid].add(date_only(row["game_date"]))
    pbp_required = ("game_id", "game_date", "home_team_id", "away_team_id", "game_type_name", "pitch_number")
    for path in pbp_paths:
        for row in csv_rows([path], pbp_required):
            if TEAM_ID not in (row["home_team_id"].strip(), row["away_team_id"].strip()):
                continue
            gid = row["game_id"].strip()
            if not gid:
                issues.append("PBP row has empty game_id")
                continue
            if gid in pbp_sources and pbp_sources[gid] != str(path):
                duplicate_sources.add(("PBP", gid))
            pbp_sources.setdefault(gid, str(path))
            pbp_dates[gid].add(date_only(row["game_date"]))
            pbp_types[gid].add(game_type(row["game_type_name"]))
            pbp_names[gid].add(row["game_type_name"].strip())
            if row["pitch_number"].strip():
                pitch_counts[gid] += 1
    for kind, gid in sorted(duplicate_sources):
        issues.append(f"game_id={gid}: {kind} appears in multiple source files")

    all_ids = sorted(set(stats) | set(pbp_dates))
    before = Counter()
    after = Counter()
    mismatches = []
    invalid_games = []
    games_by_type = Counter()
    pitches_by_type = Counter()
    for gid in all_ids:
        sd, pd, pt = stats_dates.get(gid, set()), pbp_dates.get(gid, set()), pbp_types.get(gid, set())
        if len(sd) != 1 or "" in sd or len(pd) != 1 or "" in pd or len(pt) != 1 or "" in pt:
            invalid_games.append({"game_id": gid, "stats_dates": sorted(sd), "pbp_dates": sorted(pd), "pbp_types": sorted(pt), "source_type_names": sorted(pbp_names[gid])})
        if len(sd) == 1 and "" not in sd:
            before[next(iter(sd))[:7]] += 1
        if len(pd) == 1 and "" not in pd:
            after[next(iter(pd))[:7]] += 1
        if len(sd) == len(pd) == 1 and sd != pd:
            mismatches.append({"game_id": gid, "stats_date": next(iter(sd)), "pbp_date": next(iter(pd))})
        if len(pt) == 1 and "" not in pt:
            category = next(iter(pt))
            games_by_type[category] += 1
            pitches_by_type[category] += pitch_counts[gid]

    totals = {}
    for gid, rows in stats.items():
        total = Counter()
        for row in rows:
            # Pitcher-only rows have no batting line. A populated line must be numeric.
            if not row["batting_PA"].strip():
                continue
            for column in BAT_COLUMNS:
                value = row[f"batting_{column}"].strip()
                try:
                    number = Decimal(value)
                    if not number.is_finite() or number < 0 or number != number.to_integral_value():
                        raise ValueError
                    total[column] += int(number)
                except (InvalidOperation, ValueError):
                    issues.append(f"game_id={gid}: invalid batting_{column}: {value!r}")
        totals[gid] = total

    report = {
        "status": "passed",
        "stats_rows": sum(map(len, stats.values())),
        "stats_games": len(stats),
        "pbp_games": len(pbp_dates),
        "matched_games": len(set(stats) & set(pbp_dates)),
        "game_counts_by_type": dict(sorted(games_by_type.items())),
        "pitch_rows_by_type": dict(sorted(pitches_by_type.items())),
        "game_counts_before": dict(sorted(before.items())),
        "game_counts_after": dict(sorted(after.items())),
        "date_mismatch_count": len(mismatches),
        "date_mismatches": mismatches,
        "missing_pbp_game_ids": sorted(set(stats) - set(pbp_dates)),
        "missing_stats_game_ids": sorted(set(pbp_dates) - set(stats)),
        "invalid_game_metadata": invalid_games,
        "invalid_batting_values": issues,
        "date_source": "PBP game_date; independent source not yet checked",
    }
    if any((report["missing_pbp_game_ids"], report["missing_stats_game_ids"], invalid_games, issues)) or not all_ids:
        report["status"] = "failed"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if report["status"] == "failed":
        for name in ("monthly_batting.csv", "joined_pbp.csv"):
            (out_dir / name).unlink(missing_ok=True)
        return report

    monthly = defaultdict(Counter)
    monthly_games = Counter()
    for gid in all_ids:
        day = next(iter(pbp_dates[gid]))
        category = next(iter(pbp_types[gid]))
        key = (day[:7], category)
        monthly[key].update(totals[gid])
        monthly_games[key] += 1
    fields = ("month", "game_type", "games", *BAT_COLUMNS, "AVG", "OBP", "SLG", "OPS")
    with (out_dir / "monthly_batting.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for (month, category), total in sorted(monthly.items()):
            ab, h = total["AB"], total["H"]
            bases = h + total["2B"] + 2 * total["3B"] + 3 * total["HR"]
            obp_den = ab + total["BB"] + total["HBP"] + total["SF"]
            record = {"month": month, "game_type": category, "games": monthly_games[(month, category)]}
            record.update({c: total[c] for c in BAT_COLUMNS})
            record.update(AVG=ratio(h, ab), OBP=ratio(h + total["BB"] + total["HBP"], obp_den), SLG=ratio(bases, ab))
            record["OPS"] = ratio((h + total["BB"] + total["HBP"]) * ab + bases * obp_den, obp_den * ab)
            writer.writerow(record)

    # Stream the pitch-level join; never multiply each pitch by all player rows.
    pbp_fields = []
    for path in pbp_paths:
        with path.open(encoding="utf-8-sig", newline="") as source:
            for field in csv.DictReader(source).fieldnames or []:
                if field not in pbp_fields:
                    pbp_fields.append(field)
    joined_fields = (*pbp_fields, "corrected_game_date", "game_type", "stats_game_date_original", *(f"team_batting_{c}" for c in BAT_COLUMNS))
    with (out_dir / "joined_pbp.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=joined_fields)
        writer.writeheader()
        for row in csv_rows(pbp_paths, pbp_required):
            gid = row["game_id"].strip()
            if gid not in stats or TEAM_ID not in (row["home_team_id"].strip(), row["away_team_id"].strip()):
                continue
            if not row["pitch_number"].strip():
                continue
            joined = dict(row)
            joined.update(corrected_game_date=next(iter(pbp_dates[gid])), game_type=next(iter(pbp_types[gid])), stats_game_date_original=next(iter(stats_dates[gid])))
            joined.update({f"team_batting_{c}": totals[gid][c] for c in BAT_COLUMNS})
            writer.writerow(joined)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True, help="Local NBDR ZIP or extracted root containing game_stats/ and pbp/")
    parser.add_argument("--supplement-dir", type=Path, help="Optional local CSVs for missing games, in game_stats/ and pbp/")
    parser.add_argument("--out-dir", type=Path, default=Path("output"), help="Local output directory (default: output)")
    args = parser.parse_args()
    report = run_with_supplement(args.data_dir, args.out_dir, args.supplement_dir)
    print(json.dumps({"status": report["status"], "stats_games": report["stats_games"], "pbp_games": report["pbp_games"], "date_mismatches": len(report["date_mismatches"]), "validation": str(args.out_dir / "validation.json")}, ensure_ascii=False))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
