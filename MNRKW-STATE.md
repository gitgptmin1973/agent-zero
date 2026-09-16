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
| 台帳生成 | 2026-09-16T06:32:24.684Z |
| 登録タスク | 19 本（有効 19） |
| 時刻 実測 / 未確認 | 10 / 9 本 |
| Desktop 依存（単一障害点） | 3 本 |
| ローカル実行 | 11 / 19 本 |
| 同時実行ピーク / 上限 | 3 / 2 本 |
| 時刻衝突 | 1 件 |

## 2. タスク台帳

| # | タスク | 頻度 | cron | 時刻確度 | Tier | 実行先 | ウェーブ | 想定分 | ゲート | 依存 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 広交会140 視察情報 毎日巡回 | 毎日 01:00 | `0 1 * * *` | 実測 | L4 | claude.ai 残置 | W1 | 25 | 外部取得・人手必須 | — |
| 2 | 規制対応レーダー 毎日AM2時巡回 | 毎日 02:00 | `0 2 * * *` | 実測 | L4 | claude.ai 残置 | W1 | 8 | 外部取得 | — |
| 3 | Prohands daily command center | 毎日 05:00 | `0 5 * * *` | 実測 | L4 | claude.ai 残置 | W2 | 25 | 外部取得 | gz140, kisei, newsify |
| 4 | ビジネスタウン・ダッシュボード毎朝自動更新 | 毎日 05:00 | `0 5 * * *` | 実測 | L3 | agent-zero＋API | W2 | 25 | 外部取得 | kisei, oss-cn, yakushin |
| 5 | Newsify daily scan | 毎日 05:30 | `30 5 * * *` | 実測 | L2 | agent-zero | W1 | 8 | 外部取得 | — |
| 6 | モーニングブリーフ | 平日 06:30 | `30 6 * * 1-5` | 実測 | L3 | agent-zero＋API | W3 | 8 | 外部取得・個人情報 | newsify, kisei, pdcc, biztown |
| 7 | 観光PJ 毎日自動巡回 | 毎日 06:40 | `40 6 * * *` | 実測 | L3 | agent-zero＋API | W1 | 25 | 外部取得 | — |
| 8 | 中国系OSS AI＋輸出規制 月次ウォッチ | 毎日 06:40 | `40 6 * * *` | 実測 | L2 | agent-zero | W1 | 8 | 外部取得 | — |
| 9 | 躍進 第14回 告示・見積 ウォッチ | 毎日 07:30 | `30 7 * * *` | 実測 | L3 | agent-zero＋API | W1 | 8 | 外部取得・人手必須 | — |
| 10 | Self heal weekly maintenance | 日曜 03:00 | `0 3 * * 0` | **未確認/提案** | L1 | agent-zero | W0 | 3 | システム変更・削除系 | — |
| 11 | 基板巡回 Odoo19/n8n/PG EOL | 月曜 03:20 | `20 3 * * 1` | **未確認/提案** | L2 | agent-zero | W1 | 8 | 外部取得・システム変更 | — |
| 12 | 統合インフラ 週次自律巡回 | 火曜 03:40 | `40 3 * * 2` | **未確認/提案** | L1 | agent-zero | W0 | 8 | システム変更 | — |
| 13 | SAOS 100点到達ダッシュボード | 水曜 04:00 | `0 4 * * 3` | **未確認/提案** | L2 | agent-zero | W1 | 8 | 外部取得 | — |
| 14 | 3DGSカオスマップ 週次Deep Research | 木曜 04:20 | `20 4 * * 4` | **未確認/提案** | L3 | agent-zero＋API | W1 | 25 | 外部取得 | — |
| 15 | MinoPRO統合メモリ 週次自動棚卸 | 金曜 04:40 | `40 4 * * 5` | **未確認/提案** | L1 | agent-zero | W2 | 3 | 削除系・個人情報 | — |
| 16 | Claude統合ダッシュボード 週次自動更新 | 土曜 05:00 | `0 5 * * 6` | **未確認/提案** | L2 | agent-zero | W2 | 3 | 外部取得 | — |
| 17 | 統合司令塔ダッシュボード 週次自動更新 | 土曜 05:30 | `30 5 * * 6` | **未確認/提案** | L1 | agent-zero | W2 | 3 | — | saos, dgs3, board, memory, infra |
| 18 | 観光PJ 週次自己監査 | 日曜 06:00 | `0 6 * * 0` | **未確認/提案** | L2 | agent-zero | W2 | 8 | 外部取得 | kanko-daily |
| 19 | 週次 学習チェックイン（Claude活用） | 金曜 17:00 | `0 17 * * 5` | 実測 | L2 | agent-zero | W3 | 3 | — | claude-dash |

## 3. 未確認（埋めるまで自動実行しない）

- [ ] **Self heal weekly maintenance** — claude.ai 上の実際の起動時刻（現在の提案値: 日曜 03:00）
- [ ] **基板巡回 Odoo19/n8n/PG EOL** — claude.ai 上の実際の起動時刻（現在の提案値: 月曜 03:20）
- [ ] **統合インフラ 週次自律巡回** — claude.ai 上の実際の起動時刻（現在の提案値: 火曜 03:40）
- [ ] **SAOS 100点到達ダッシュボード** — claude.ai 上の実際の起動時刻（現在の提案値: 水曜 04:00）
- [ ] **3DGSカオスマップ 週次Deep Research** — claude.ai 上の実際の起動時刻（現在の提案値: 木曜 04:20）
- [ ] **MinoPRO統合メモリ 週次自動棚卸** — claude.ai 上の実際の起動時刻（現在の提案値: 金曜 04:40）
- [ ] **Claude統合ダッシュボード 週次自動更新** — claude.ai 上の実際の起動時刻（現在の提案値: 土曜 05:00）
- [ ] **統合司令塔ダッシュボード 週次自動更新** — claude.ai 上の実際の起動時刻（現在の提案値: 土曜 05:30）
- [ ] **観光PJ 週次自己監査** — claude.ai 上の実際の起動時刻（現在の提案値: 日曜 06:00）
- [ ] ウェーブ割付と依存エッジは名称からの推定。実定義と突き合わせる
- [ ] 想定実行時間（軽量3分/標準8分/重量25分）は仮定値。実ログで置き換える
- [ ] Ollama のモデル名（巡回結果から選び、n8n 出力の PUT-YOUR-OLLAMA-MODEL-HERE を置換）

## 4. USER GATE（自動実行を許さない操作）

| タスク | 停止対象 |
|---|---|
| 広交会140 視察情報 毎日巡回 | 人手必須 |
| モーニングブリーフ | 個人情報 |
| 躍進 第14回 告示・見積 ウォッチ | 人手必須 |
| Self heal weekly maintenance | システム変更・削除系 |
| 基板巡回 Odoo19/n8n/PG EOL | システム変更 |
| 統合インフラ 週次自律巡回 | システム変更 |
| MinoPRO統合メモリ 週次自動棚卸 | 削除系・個人情報 |

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
