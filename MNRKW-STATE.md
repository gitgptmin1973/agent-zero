<!-- MNRKW-STATE — 唯一の中核MD。派生MDを作らないこと。 -->
<!-- 機械が書く区画: LEDGER / SWEEP / LOG。人が書くのは「決定」節のみ。 -->
# MNRKW-STATE

**このファイルだけを参照する。** 司令塔（`webui/orchestrator.html`）が台帳区画を、PowerShell 巡回が環境区画と履歴を上書きする。手書きは「決定」節だけ。

| 参照順 | 内容 | 書き手 |
|---|---|---|
| 1 | 台帳（LEDGER） | 司令塔が再生成 |
| 2 | 環境実測（SWEEP） | PowerShell 巡回が上書き |
| 3 | 履歴（LOG） | 巡回が追記のみ |
| 4 | 決定 | 人が書く |

<!-- LEDGER:BEGIN -->

## 1. 現況

| 項目 | 値 |
|---|---|
| 台帳生成 | 2026-09-16T10:47:59.152Z |
| 登録タスク | 20 本（有効 20） |
| 時刻 実測 / 未確認 | 20 / 0 本 |
| 出典 | claude.ai Routines API（list_triggers）の cron_expression を JST 換算 |
| 実行時間 実測 / 仮定 | 17 / 3 本 |
| Desktop 依存（単一障害点） | 3 本 |
| ローカル実行 | 12 / 20 本 |
| 同時実行ピーク / 上限 | 3 / 2 本 |
| 時刻衝突 | 2 件 |

## 2. タスク台帳

| # | タスク | 頻度 | cron | 時刻確度 | Tier | 実行先 | ウェーブ | 想定分 | ゲート | 依存 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 広交会140 視察情報 毎日巡回（01:00 JST）／登録開放とビザ工程を監視 | 毎日 01:00 | `0 1 * * *` | 実測 | L4 | claude.ai 残置 | W1 | 4 | 外部取得・人手必須 | — |
| 2 | 規制対応レーダー 毎日AM2時巡回 | 毎日 02:00 | `0 2 * * *` | 実測 | L4 | claude.ai 残置 | W1 | 1 | 外部取得 | — |
| 3 | 統合司令塔ダッシュボード週次自動更新 | 月曜 04:00 | `0 4 * * 1` | 実測 | L1 | agent-zero | W2 | 7 | — | saos, dgs3, board, memory, infra |
| 4 | Prohands daily command center | 毎日 05:00 | `0 5 * * *` | 実測 | L4 | claude.ai 残置 | W2 | 3 | 外部取得 | gz140, kisei, newsify |
| 5 | ビジネスタウン・ダッシュボード毎朝自動更新（Deep Research＋ファクトチェック） | 毎日 05:00 | `0 5 * * *` | 実測 | L3 | agent-zero＋API | W2 | 13 | 外部取得 | kisei, oss-cn, yakushin |
| 6 | SAOS 100点到達ダッシュボード 週次巡回（月曜05:30 JST） | 月曜 05:30 | `30 5 * * 1` | 実測 | L2 | agent-zero | W1 | 8(仮) | 外部取得 | — |
| 7 | Newsify daily scan | 毎日 05:30 | `30 5 * * *` | 実測 | L2 | agent-zero | W1 | 2 | 外部取得 | — |
| 8 | モーニングブリーフ | 平日 06:30 | `30 6 * * 1-5` | 実測 | L3 | agent-zero＋API | W3 | 6 | 外部取得・個人情報 | newsify, kisei, pdcc, biztown |
| 9 | 観光PJ 毎日自動巡回（Deep Research＋EVOLVE-100自己診断） | 毎日 06:40 | `40 6 * * *` | 実測 | L3 | agent-zero＋API | W1 | 19 | 外部取得 | — |
| 10 | 統合インフラ 週次自律巡回 | 月曜 07:30 | `30 7 * * 1` | 実測 | L1 | agent-zero | W0 | 8(仮) | システム変更 | — |
| 11 | Claude統合ダッシュボード 週次自律更新 | 月曜 07:30 | `30 7 * * 1` | 実測 | L2 | agent-zero | W2 | 12 | 外部取得 | — |
| 12 | 躍進 第14回 告示・見積 ウォッチ（みのりかわPROHANDS） | 毎日 07:30 | `30 7 * * *` | 実測 | L3 | agent-zero＋API | W1 | 3 | 外部取得・人手必須 | — |
| 13 | Self heal weekly maintenance | 月曜 08:00 | `0 8 * * 1` | 実測 | L1 | agent-zero | W0 | 1 | システム変更・削除系 | — |
| 14 | MinoPRO統合メモリ 週次自動棚卸 | 月曜 08:00 | `0 8 * * 1` | 実測 | L1 | agent-zero | W2 | 1 | 削除系・個人情報 | — |
| 15 | 3DGSカオスマップ 週次Deep Research自動更新 | 月曜 08:00 | `0 8 * * 1` | 実測 | L3 | agent-zero＋API | W1 | 27 | 外部取得 | — |
| 16 | 基板巡回 Odoo19/n8n/PG EOL・CVE監視 | 火曜 03:00 | `0 3 * * 2` | 実測 | L2 | agent-zero | W1 | 7 | 外部取得・システム変更 | — |
| 17 | 週次 学習チェックイン（Claude活用） | 金曜 17:00 | `0 17 * * 5` | 実測 | L2 | agent-zero | W3 | 19 | — | claude-dash |
| 18 | Weekly report | 金曜 17:00 | `0 17 * * 5` | 実測 | L2 | agent-zero | W3 | 3(仮) | — | — |
| 19 | 観光PJ 週次自己監査（KANKO-STATE） | 土曜 19:00 | `0 19 * * 6` | 実測 | L2 | agent-zero | W2 | 12 | 外部取得 | kanko-daily |
| 20 | 中国系OSS AI + 輸出規制 月次ウォッチ | 毎月2日 06:40 | `40 6 2 * *` | 実測 | L2 | agent-zero | W1 | 4 | 外部取得 | — |

## 3. 未確認（埋めるまで自動実行しない）

- [ ] ウェーブ割付と依存エッジは名称・プロンプトからの推定。実運用で確認する
- [ ] **SAOS 100点到達ダッシュボード 週次巡回（月曜05:30 JST）** — 実行時間の実測が無い（未実行、または常駐セッションへの配信待ちを含む異常値のため不採用）
- [ ] **統合インフラ 週次自律巡回** — 実行時間の実測が無い（未実行、または常駐セッションへの配信待ちを含む異常値のため不採用）
- [ ] **Weekly report** — 実行時間の実測が無い（未実行、または常駐セッションへの配信待ちを含む異常値のため不採用）
- [ ] Ollama のモデル名（巡回結果から選び、n8n 出力の PUT-YOUR-OLLAMA-MODEL-HERE を置換）

## 4. USER GATE（自動実行を許さない操作）

| タスク | 停止対象 |
|---|---|
| 広交会140 視察情報 毎日巡回（01:00 JST）／登録開放とビザ工程を監視 | 人手必須 |
| モーニングブリーフ | 個人情報 |
| 統合インフラ 週次自律巡回 | システム変更 |
| 躍進 第14回 告示・見積 ウォッチ（みのりかわPROHANDS） | 人手必須 |
| Self heal weekly maintenance | システム変更・削除系 |
| MinoPRO統合メモリ 週次自動棚卸 | 削除系・個人情報 |
| 基板巡回 Odoo19/n8n/PG EOL・CVE監視 | システム変更 |

## 5. 出典（コード実測）

- 静的配信 `run_ui.py:28` / タスク永続化 `python/helpers/task_scheduler.py:444-462`
- スケジュール形 `task_scheduler.py:48-57, 930-940` / ポート解決 `python/helpers/runtime.py:132`
- 文字コード `python/helpers/files.py:85-95`（utf-8 固定・BOM を剥がさない）
- tick のループバック限定 `run_ui.py:95-106`, `python/api/scheduler_tick.py`
- n8n Schedule Trigger 形: n8n 本体 `packages/nodes-base/nodes/Schedule/ScheduleTrigger.node.ts`（type `n8n-nodes-base.scheduleTrigger` / `rule.interval[].field="cronExpression"`）

<!-- LEDGER:END -->

## 6. 環境実測

<!-- SWEEP:BEGIN -->
未巡回。07タブの巡回ブロックを1回実行すること。
<!-- SWEEP:END -->

## 7. 履歴（追記のみ）

<!-- LOG:BEGIN -->
<!-- LOG:END -->

## 8. 決定（人が書く）

- 2026-09-16 Docker 不使用。基盤は Odoo + n8n + PostgreSQL + Python + Ollama + Qwen。
- 2026-09-16 参照MDは本ファイル1枚のみ。派生MDを作らない。
- 2026-09-16 claude.ai 側の停止・時刻変更は Routines API 経由で Claude が実行できる（USER GATE：本人の明示指示が要る。削除は行わない）。
