# 作業状態

更新日: 2026-11-04

## 打撃・ケースバッティング指標と野球IQ

- 状態: `docs/batting_metric_candidates.md` に、ケースバッティングの結果を表すRE24・WPA、期待得点ベースのスイング判断、認知能力指標AIQを記録。`docs/baseball_research_notes.md` から参照。
- 方針: 結果への貢献と判断力を分ける。RE24/WPAは実際の結果を記述するもの、期待得点ベースの指標は選択の質を評価する候補、AIQは野球IQそのものを直接測らない認知テストとして扱う。
- 検証: 追加Markdownの `git diff --check` を確認。カタログと参照リンクの2ファイルをコミット `27b26b45d829a9df601c20846edd579e251e81c4` としてpushし、ローカルと `origin/handoff/2026-dragons-analysis` のSHA一致を確認。コード変更はないためテストは未実施。
- 未確定事項: 現行NBDRデータで塁・アウト遷移、投球選択、打席結果をどこまで復元できるかは未検証。指標を実算する前に元列の定義・欠損・遷移を確認する。
- 次の作業: 必要になった場合、元CSVの列と試合記録を照合し、RE24から算出可能性を確認する。判断指標は投球時点の情報とケース課題の定義を用意してから設計する。

## 野球研究メモ（投球戦略）

- 状態: 盗塁・走者制御に加えて、投球選択・配球パターンの研究を記録。Jo & Jin (2026) は要旨等のみ、Park et al. (2026) と Miura & Fujii (2026)、Tahara et al. (2025) は公開本文を確認した範囲で整理。読了状況と未確認事項は `docs/baseball_research_notes.md` に記載。
- 今回の主な学び: Tahara et al. (2025) は、2ストライクに達した打席で球速・コースの変化を測る項目を作り、投手成績との関連を調べた研究。特定の場面の最適配球や因果効果を示したものではない。中日データへの応用は、必要な球単位データの列と定義を確認してから判断する。
- 検証: 研究メモの差分・Markdown形式を確認。文書記録のみのためコードテストは未実施。
- 次の作業: 今回はいったん研究読み込みを区切る。再開時は興味のある研究を選び、研究質問・対象・結果・限界・NPBへの応用可能性を平易に整理する。

## Drive と GitHub の運用整理

- 状態: Drive/GitHub運用と動画候補の記録を整備済み。コミット・pushの実績はGit履歴とブランチ追跡状態を正とする。
- 決定: リポジトリ全体の役割分担と引き継ぎ・終了手順は `docs/repository_workflow.md`、中日動画候補の具体的な保存先は `docs/drive_github_workflow.md` に記録する。新しいプロジェクト固有の公開可能なアイデアはGitHubの一覧・詳細文書を正本とし、調査資料・取得資料・完成成果物はDriveへ置く。Publicリポジトリには非公開の企画詳細、タイトル、Driveリンクを掲載しない。両サービスは自動同期されない。
- 対応: `AGENTS.md` から動画案の問い合わせ時にリポジトリ内一覧を確認するよう案内。`docs/video_idea_index.md` を新規候補の正本とする。既存の非公開詳細メモはDrive原本を保持し、公開範囲確認まではPublicリポジトリからリンクしない。
- 既存の詳細メモは旧正本としてDriveに保持し、公開範囲を確認するまで本文やリンクをPublicリポジトリへ複製しない。Drive原本はこの作業では変更しない。
- 検証: 対象5ファイルのMarkdown内部リンク4件を確認し、欠落0件・末尾空白0件。`git diff --check` 通過。Pythonの補助確認はWindowsAppsの起動権限エラーで実行できず、同等のリンク・空白確認をPowerShellで完了。コード・解析処理は変更していないため、テストは実行しない。
- 作業中に `README.md` と `docs/repository_workflow.md` の別更新が現れたため、内容を読み、重複しないよう本作業では一般手順に触れず動画候補固有の保存先に範囲を絞った。両ファイルは上書きしていない。
- 次の作業: 新しい中日動画候補は `docs/video_idea_index.md` と公開可能な `docs/ideas/` に記録する。非公開詳細が必要な場合はPrivateな保存先に残す。作業終了時は「お疲れ」のGit引き継ぎ後にアーカイブ可否を確認する。

## 2026-10-30 closeout

- この作業の文書変更はコミット `c178384a14bcc0a84d0f2caafd3b13d7ba887f4a` としてpush済み。push後にローカルブランチと `origin/handoff/2026-dragons-analysis` が同じSHAを指すことを確認した。
- 文書のみの変更のためコードテストは実施していない。Markdown内部リンク4件と空白検査は通過。
- `.gitignore`、`docs/video_production_plan.md`、画像・生成スクリプトなど他作業の未コミット変更は今回のコミットに含めていない。


## Shared standard alignment — 2026-11-02

- Updated this repository's instructions for scope-based idea storage and public-repository privacy.
- Canonical source: https://github.com/Mitsuru-sato37/ai-workspace-foundation/blob/main/docs/11_idea_intake.md
- Rollout record: https://github.com/Mitsuru-sato37/ai-workspace-foundation/blob/main/docs/14_shared_standard_rollout.md
- This branch contains the alignment change; it is complete after the PR is merged.
