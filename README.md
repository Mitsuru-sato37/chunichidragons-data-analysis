# 中日ドラゴンズ データ分析

最初の対象は [Nippon Baseball Data Repository](https://github.com/armstjc/Nippon-Baseball-Data-Repository)（NBDR）の2026年「Player Game Stats」と「PBP」です。中日（`team_id=4`）の試合別打撃成績を `game_id` でPBPに結び、日付と試合区分を検証してから月別に集計します。Python 3.10以上、追加パッケージ不要です。

作業記録とDrive/GitHubの保存方法は[リポジトリ作業手順](docs/repository_workflow.md)を参照してください。

## データの配置と実行

NBDRのZIPをローカルに保存し、そのパスをそのまま指定できます。ZIPの中に `game_stats/2026-*_game_stats.csv` と `pbp/2026-*_pbp.csv` が必要です。展開済みのCSVディレクトリも指定できます。ZIPとCSVはGitに入れません。リポジトリ内の `data/` も `.gitignore` の対象ですが、リポジトリ外のディレクトリも指定できます。

```text
<data-dir>/
  game_stats/2026-03_game_stats.csv
  game_stats/2026-04_game_stats.csv
  ...
  pbp/2026-03_pbp.csv
  pbp/2026-04_pbp.csv
  ...
```

ファイルは両方とも `2026-*_game_stats.csv` / `2026-*_pbp.csv` という名前で読み込みます。NBDRはリリースのデータが最新で、リポジトリ内のファイルはシーズン終了後などに更新されるという[説明](https://github.com/armstjc/Nippon-Baseball-Data-Repository#data)があります。取得日時とリリースを手元で記録してください。

```powershell
python analyze.py --data-dir "C:\Users\msato\Downloads\Nippon-Baseball-Data-Repository-main.zip" --out-dir output
# または展開済みのディレクトリを指定
python analyze.py --data-dir C:\path\to\nbdr --out-dir output
python -m unittest discover -s tests -v
```

`output/validation.json` は、補正前後の月別試合数、試合別成績とPBPの試合数、結合できた試合数、区分別の試合数・投球行数、日付不一致の `game_id` と両側の日付、片側だけにある試合ID、日付・試合区分・打撃値の欠損や矛盾、通過可否を記録します。検証に失敗した場合は終了コード1とし、同じ出力先にある古い月別集計・結合結果も削除します。`passed` はこの2ファイル間の内部検証が通った意味で、143試合の収録や独立ソースとの一致を保証しません。区分別試合数の `regular` と `interleague` を合計して収録範囲を確認してください。

## 2026年10月3日の欠損試合を補う

手元のNBDR ZIPにない中日対ヤクルトの10月3日（SPAIA `game_id=2021049818`）は、明示的に `fetch_game.py` を実行すると、SPAIAの試合経過・投球履歴・打撃成績APIから取得できます。取得したCSVはGit対象外の `data/supplement/` に保存します。自動ダウンロードはしません。球数0の打席記録は投球として数えず、正の球数を持つ投球の対応漏れを検査します。[NPB公式の試合記録](https://npb.jp/scores/2026/1003/s-d-25/index.html)にある中日の5安打・3得点を取得時の照合値にしています。

```powershell
python fetch_game.py --game-id 2021049818 --game-date 2026-10-03 --out-dir data/supplement --expected-hits 5 --expected-runs 3
python analyze.py --data-dir "C:\Users\msato\Downloads\Nippon-Baseball-Data-Repository-main.zip" --supplement-dir data/supplement --out-dir output
```

この補完CSVは分析に必要な列だけを持ち、NBDRのPBP全列を再現しません。`joined_pbp.csv` では補完試合だけ存在しない列が空欄になります。元データに同じ `game_id` が追加された場合、重複を検出して集計を停止します。手元のZIPとの組み合わせでは、オープン戦18試合、公式戦125試合、交流戦18試合、日付不一致69試合となりました。公式戦・交流戦は合計143試合ですが、この内部検証と1試合の得点・安打照合だけで全数値が確定したわけではありません。

通過時は `output/monthly_batting.csv` に中日の月別打撃成績を、`output/joined_pbp.csv` にPBPの各投球行と全ての元列、中日の試合別打撃合計、補正日付、試合区分を出します。元の `game_date` は残し、`corrected_game_date` と `stats_game_date_original` を追加します。結合結果は大きくなるのでローカル専用です。月別集計は `preseason`（オープン戦）、`regular`（公式戦）、`interleague`（交流戦）を別行にします。PBPの `game_type_name` が判定できない場合は検証失敗です。打率はH/AB、出塁率は(H+BB+HBP)/(AB+BB+HBP+SF)、長打率は塁打/AB、OPSは出塁率+長打率です。分母0は空欄です。

## 日付と公開利用について

先行調査では2026年の中日戦160試合のうち69試合で両データの `game_date` が不一致でした。NBDRの[試合別成績収集コード](https://github.com/armstjc/Nippon-Baseball-Data-Repository/blob/main/get_game_stats.py)では、`game_id` の配列だけをシャッフルして日付配列と同じ位置で組み合わせる処理が見られます。これが原因である可能性がありますが、ここでは原因を確定扱いしません。本ツールはPBPの試合内日付が一意なときだけ、その日付で試合別成績の日付を補正します。**PBPの日付自体は独立ソースで未照合です。動画用の確定値にする前に、NPB公式記録など別ソースで試合日と対象試合を照合してください。**

NBDRの[説明](https://github.com/armstjc/Nippon-Baseball-Data-Repository#readme)によると、データの主な収集元はSPAIAです。NBDRのコードのライセンスや帰属表記案内だけで、SPAIA由来データの公開利用許諾が確認できたとは扱いません。**公開利用の許諾は未確認です。**元データ、ZIP、大量の抜粋、結合データは公開リポジトリに追加しないでください。公開・動画利用前に権利条件を確認してください。
