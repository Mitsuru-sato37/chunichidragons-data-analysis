"""Explicitly fetch one missing NBDR-style game from SPAIA into local CSVs."""

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen


BASE = "https://spaia.jp/baseball/npb/api/"
BAT_MAP = {"PA": "pa", "AB": "ab", "H": "h", "2B": "h2b", "3B": "h3b", "HR": "hr", "BB": "bb", "HBP": "hp", "SF": "sf", "SO": "so", "RBI": "rbi", "R": "r"}
PBP_FIELDS = ("game_id", "game_date", "game_type_name", "home_team_id", "away_team_id", "play_id", "page", "inning", "description_jap", "pitch_number", "release_speed_kmh", "pitch_id", "plate_x", "plate_y", "presult", "bresult", "pitcher", "batter")
STAT_FIELDS = ("game_id", "game_date", "team_id", "player_id", "player_name_jap", *(f"batting_{name}" for name in BAT_MAP))


def get_json(path):
    request = Request(BASE + path, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not isinstance(result, list):
        raise ValueError(f"Unexpected response from {path}")
    return result


def page_for_event(item):
    if not all(item.get(key) not in (None, "") for key in ("Inning", "TB", "TextInfo_Bat_No")):
        return ""
    description = item.get("TextInfo_Bat_Text") or ""
    match = re.match(r"^(\d+)球目:", description)
    number = int(match.group(1)) if match else 0
    return f"{int(item['Inning']):02d}{item['TB']}{int(item['TextInfo_Bat_No']):02d}{number:02d}"


def build_rows(game_id, game_date, events, pitches, batting):
    day = date.fromisoformat(game_date)
    game_events = [item for item in events if str(item.get("GameID")) == game_id]
    if not game_events:
        raise ValueError(f"No PBP for game_id={game_id}")
    first = game_events[0]
    if {str(item.get("GameDate")) for item in game_events} != {day.strftime("%Y%m%d")}:
        raise ValueError("SPAIA game dates differ within game or from requested date")
    if len({str(item.get("GameKindName") or "") for item in game_events}) != 1:
        raise ValueError("SPAIA game types differ within game")
    if "4" not in (str(first.get("H_ID")), str(first.get("V_ID"))):
        raise ValueError("Requested game does not involve Chunichi team_id=4")
    by_page = {}
    for item in pitches:
        if str(item.get("gameId")) != game_id:
            continue
        page = f"{item['fiveDigitSerialNumber']}{int(item['atBatBallCount']):02d}"
        if page in by_page:
            raise ValueError(f"Duplicate pitch page {page}")
        by_page[page] = item

    pbp_rows = []
    matched_positive_pages = set()
    for item in game_events:
        page = page_for_event(item)
        pitch = by_page.get(page, {})
        # SPAIA also has count-zero at-bat records, which are not thrown pitches.
        pitch_number = int(pitch.get("atBatBallCount") or 0)
        if pitch_number > 0:
            if page in matched_positive_pages:
                raise ValueError(f"Duplicate PBP match for pitch page {page}")
            matched_positive_pages.add(page)
        row = {
            "game_id": game_id,
            "game_date": f"{game_date} {str(item.get('StartTime') or first.get('StartTime')).zfill(4)[:2]}:{str(item.get('StartTime') or first.get('StartTime')).zfill(4)[2:]}:00+09:00",
            "game_type_name": item.get("GameKindName") or first.get("GameKindName") or "",
            "home_team_id": str(item.get("H_ID") or first.get("H_ID")),
            "away_team_id": str(item.get("V_ID") or first.get("V_ID")),
            "play_id": item.get("ID", ""),
            "page": page,
            "inning": item.get("Inning") or "",
            "description_jap": item.get("TextInfo_Bat_Text") or "",
            "pitch_number": str(pitch_number) if pitch_number > 0 else "",
            "release_speed_kmh": pitch.get("ballSpeed", ""),
            "pitch_id": pitch.get("ballKind", ""),
            "plate_x": pitch.get("x", ""),
            "plate_y": pitch.get("y", ""),
            "presult": pitch.get("presult", ""),
            "bresult": pitch.get("bresult", ""),
            "pitcher": pitch.get("pitId", ""),
            "batter": pitch.get("batId", ""),
        }
        pbp_rows.append(row)
    positive_pages = {page for page, item in by_page.items() if int(item.get("atBatBallCount") or 0) > 0}
    if matched_positive_pages != positive_pages:
        raise ValueError(f"Unmatched pitches: {len(positive_pages - matched_positive_pages)}")
    if not any(str(row["pitch_number"]).strip() for row in pbp_rows):
        raise ValueError("No pitch rows matched PBP events")

    stat_rows = []
    for item in batting:
        if str(item.get("teamId")) != "4":
            continue
        row = {"game_id": game_id, "game_date": game_date, "team_id": "4", "player_id": item.get("playerId", ""), "player_name_jap": item.get("playerName", "")}
        row.update({f"batting_{name}": item.get(source, "") for name, source in BAT_MAP.items()})
        stat_rows.append(row)
    if not stat_rows:
        raise ValueError("No Chunichi batting records")
    return pbp_rows, stat_rows


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-id", required=True)
    parser.add_argument("--game-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--out-dir", type=Path, default=Path("data/supplement"))
    parser.add_argument("--expected-hits", type=int)
    parser.add_argument("--expected-runs", type=int)
    args = parser.parse_args()
    day = date.fromisoformat(args.game_date)
    gid = args.game_id
    events = get_json(f"game_text_pbp?GameID={gid}")
    pitches = get_json(f"flash_atbat_history?gameId={gid}")
    batting = get_json(f"both_batter_game_stats?matchday={day:%Y%m%d}&gameId={gid}")
    pbp_rows, stat_rows = build_rows(gid, args.game_date, events, pitches, batting)
    hits = sum(int(row["batting_H"]) for row in stat_rows)
    runs = sum(int(row["batting_R"]) for row in stat_rows)
    if args.expected_hits is not None and hits != args.expected_hits:
        raise ValueError(f"Chunichi hits: expected {args.expected_hits}, got {hits}")
    if args.expected_runs is not None and runs != args.expected_runs:
        raise ValueError(f"Chunichi runs: expected {args.expected_runs}, got {runs}")
    suffix = day.strftime("%Y-%m-%d")
    write_csv(args.out_dir / "pbp" / f"{suffix}_pbp.csv", PBP_FIELDS, pbp_rows)
    write_csv(args.out_dir / "game_stats" / f"{suffix}_game_stats.csv", STAT_FIELDS, stat_rows)
    print(json.dumps({"game_id": gid, "date": args.game_date, "pbp_events": len(pbp_rows), "matched_pitch_rows": sum(str(row["pitch_number"]).strip() != "" for row in pbp_rows), "batting_rows": len(stat_rows), "hits": hits, "runs": runs, "out_dir": str(args.out_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
