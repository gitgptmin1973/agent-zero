# MinoPRO ローカルAIエコ・オーケストレーション 自律実行計画 v1.0

作成日: 2026-09-16 ｜ 区分: 内部資料 WM-03 ｜ 状態: 草案（本人レビュー前）
前提ドクトリン: SAOS（主権エージェントOS）S0〜S7 ／ Eco Super Agent 7層 ／ MinoPRO恒久設定 v4.0

---

## 0. 結論（先出し）

1. **主権の定義を「データ分類」で切る。** 「米国クラウドを一切使わない」は claude.ai も Anthropic API も米国ホスティングである以上、成立しない。成立するのは「L2（個人情報）・L3（機密/資格情報）は端末・自社VLANから一歩も出さない」という設計。L0/L1（公開・社内一般）のみ外部モデル可。
2. **メールのAI処理は Claude for Outlook アドインを使わず、ローカルパイプラインに置き換える。** 前回監査の結論（Max のままでは APPI 28条/GDPR 28条を満たさない）を、Team 化ではなく「外に出さない」で解く。
3. **オーケストレータは手元の agent-zero（本リポジトリ）を L4 に置き、Ollama を既定モデルにする。** 設定ファイル上、Ollama/LM Studio がネイティブ対応済み（`example.env`, `models.py`）で追加実装は不要。Anthropic は差し替え可能な L1 補助として API 経由のみ、L2/L3 は渡さない。
4. **無事故の担保は「モデルの賢さ」ではなく「egress 既定拒否・USER GATE・決定論スクリプト」で行う。** SAOS 第三原則（侵害される前提）を継承。

---

## 1. データ分類と経路（これが全ての判断基準）

| 区分 | 例 | 許可される処理場所 | 外部モデル |
|---|---|---|---|
| L0 公開 | 製品カタログ、公開価格、YouTube台本 | どこでも | 可 |
| L1 社内一般 | 社内手順、匿名化済み集計 | 自社VLAN + 商用規約の外部API | 可（商用規約・学習不使用のもののみ） |
| L2 個人情報 | 顧客メール本文、氏名・住所・電話、見積先 | **VLAN 40 ローカル推論のみ** | **不可** |
| L3 機密・資格情報 | パスワード、APIキー、原価表、取引ルート | **VLAN 40 + OpenBao、モデル文脈に入れない** | **不可** |

分類器はローカルで動かす。判定不能は L2 扱い（安全側）。

---

## 2. アーキテクチャ（Eco 7層への配置）

```
L1 司令塔   : 本人 + Claude（L0/L1 のみ、API 経由、差し替え可能）
L2 調査     : Crawl4AI / SearXNG（自社ホスト） → L0 情報のみ
L3 業務     : Odoo 19 (/json/2) / n8n / PostgreSQL        ← VLAN 30
L4 ローカルAI: agent-zero + Ollama（DGX Spark or GPU機）   ← VLAN 40
              ├ 分類器（L0〜L3 判定）
              ├ メールトリアージ・下書き（L2 を含む）
              ├ embedding / RAG（社内ナレッジ）
              └ 例外時のみ L1 へエスカレーション（L2/L3 をマスクして）
L5 防御     : UniFi ACL（VLAN 40 → Internet 既定拒否、許可先ホワイトリスト）
              Cloudflare ZT は管理面のみ、推論トラフィックは通さない
L6 配信     : 公開物のみ（WM-05）
L7 監査     : 追記専用ログ（rrweb + 構造化 JSON）、compliance-auditor
```

**VLAN 40 の egress 既定拒否**が本計画の背骨。Ollama・agent-zero のコンテナからはインターネットに出られない状態を初期値にし、必要な宛先（Ollama モデル取得時のレジストリ、Anthropic API）だけを時間限定で開ける。

---

## 3. メール処理の置き換え設計（Outlook アドインの代替）

現状: MS365 Exchange Online 上にメールが存在（米国/日本リージョンは未確認）。短期に MS365 を捨てるのは配送信頼性・既存顧客連絡先の観点で事故リスクが高い。よって段階分離。

### Phase A（即時〜1ヶ月）: 読み取りをローカルへ
- Claude for Outlook アドインは**無効化**（管理者向け統合アプリで組織ブロック）。
- MS Graph **Mail.Read（読取専用）**の自前アプリ登録、または IMAP OAuth で n8n がメールを取得 → VLAN 40 の agent-zero へ。
- agent-zero + Ollama で「分類 → 要約 → 返信下書き」。下書きは Outlook の下書きフォルダに書き戻さず、**社内 Web UI（agent-zero webui, VLAN 30 からのみ到達）**に置く。送信は必ず本人が Outlook で手動。
- 迷惑メール一括処理・削除は対象外（USER GATE: 削除系）。

### Phase B（3〜6ヶ月）: メール基盤の主権化を判断
- 候補: Stalwart（Apache-2.0/AGPL 二重・要ライセンス確認）/ Mailcow（GPL）を自社 or 国内 VPS に。**未検証**: 到達性（SPF/DKIM/DMARC 運用、IP レピュテーション）、既存 MS365 からの移行コスト。Phase 0 実測なしに着手しない。
- MS365 は Teams/Office 文書用に残すか、LibreOffice + Nextcloud へ。これは別案件として切り出す。

### Phase C: 送信自動化は永続的に対象外
- SAOS の USER GATE（外部送信）は解除しない。AI 起案メールの送信はすべて本人クリック。EU AI Act 第50条対応として、AI 起案文には内部ログに起案元を記録（外部への表示は案件別 WM 指定に従う）。

---

## 4. agent-zero の主権設定（本リポジトリでの具体値）

| 項目 | 設定 | 根拠 |
|---|---|---|
| chat model | `ollama` プロバイダ（`OLLAMA_BASE_URL` は VLAN 40 内ホスト） | `models.py` の `get_ollama_chat` |
| embedding | `ollama` embedding（社内RAG を外に出さない） | `get_ollama_embedding` |
| utility/browser model | 同上ローカル | 分類・要約は小型モデルで十分 |
| Anthropic | `API_KEY_ANTHROPIC` は **OpenBao から注入**、`.env` 平文禁止。L0/L1 タスクのプロファイルのみに紐付け | 恒久設定「認証情報ハードコード禁止」 |
| OpenAI/Azure/Google/OpenRouter/SambaNova | キー空欄のまま、設定UIで選択不可にする | GAFAM 排除方針 |
| `USE_CLOUDFLARE` | `false` 固定（tunnel 不使用） | 推論面を外に晒さない |
| MCP servers | ローカル（Odoo /json/2、ファイル、PostgreSQL）のみ。外部SaaS MCP は登録しない | SAOS 第一原則（APIがあるならGUIを使わない） |
| コンテナ | Docker 単体ではなく gVisor/Firecracker 上で実行、`--network` は内部ブリッジのみ | SAOS S0 |
| ログ | `logs/` を追記専用ボリュームへ、個人情報はマスク後に記録 | 恒久設定「個人情報の平文ログ禁止」 |

具体的なモデル名・量子化・VRAM 要件は**都度実測**（恒久設定により本書に固定値を書かない）。

---

## 5. 無事故運用ドクトリン（自律実行の境界）

1. **自律実行してよいもの**: 読み取り、分類、要約、下書き生成、社内DBへの「提案」書き込み（承認待ちステータス）。
2. **必ず停止して本人承認（USER GATE）**: 送信、公開、削除、決済、資格情報操作、セキュリティ設定変更、取引先ポータルへの書き込み。
3. **決定論優先**: 定型作業は n8n / Playwright スクリプトで再生し、LLM は例外とレビューのみ。セレクタ不一致は安全停止。
4. **プロンプトインジェクション前提**: 受信メール・添付・Web は全て「敵対的入力」。agent-zero のツール実行権限は最小化し、メール処理プロファイルでは `code_execution` を無効化する。
5. **キルスイッチ**: UniFi 側で VLAN 40 の全 egress を1操作で遮断できる ACL を常設。
6. **監査**: 全推論に L7 構造化ログ（誰が・何を・どのモデルで・データ区分）。月次で compliance-auditor に通す。

---

## 6. フェーズ計画と KPI（Phase 0 実測なしに次へ進まない）

| Phase | 期間 | 内容 | Go 条件（実測） |
|---|---|---|---|
| 0 | 2週 | VLAN 40 egress 既定拒否、agent-zero + Ollama 起動、分類器の代表10タスク×3回 | 分類正解率 ≥ 90%、L2 の外部送信 0 件（パケットキャプチャで証明） |
| 1 | 1ヶ月 | メール読取（Mail.Read）→ ローカル要約・下書き、社内UI表示 | 要約の本人採用率 ≥ 50%、事故 0 |
| 2 | 2ヶ月 | Odoo /json/2 連携（顧客・案件の紐付け、承認待ち書込み） | 誤紐付け率 < 2% |
| 3 | 3〜6ヶ月 | メール基盤主権化の可否判断（Phase B） | 到達性テストで主要取引先ドメイン 100% 受信確認 |
| 4 | 継続 | L1 Claude 依存の縮小（ローカルモデル性能に応じて） | L1 呼出比率を四半期ごとに計測 |

---

## 7. 未確認事項（本人 read-only 確認を要する）

- Exchange Online のメールボックス所在リージョン（Microsoft 365 管理センター → 組織プロファイル → データの場所）。
- DGX Spark の実機有無・VRAM・現行 Ollama バージョン（運用台帳 INDEX 経由で参照）。
- UniFi の現行 VLAN 40 ACL に egress 既定拒否が入っているか。
- Stalwart の現行ライセンス条件（AGPL 部分の有無）。AGPL なら SAOS 禁止事項に抵触。
- agent-zero 自体のライセンス（MIT 表記を `LICENSE` で確認済みだが、依存パッケージの AGPL 混入は未確認 → `pip-licenses` で実測）。

---

## 8. 本計画で採用しないもの（理由付き）

| 対象 | 理由 |
|---|---|
| Claude for Outlook アドイン | L2 が米国へ出る。Max では DPA 不在（前回監査 C 判定） |
| Microsoft Copilot / Azure OpenAI | GAFAM 排除方針。Graph 全域へのアクセス権が広すぎる |
| Cloudflare Tunnel で agent-zero を公開 | 推論面の外部露出。管理面のみ ZT |
| bot 検知回避ツール | SAOS 絶対禁止 |
| Manus / OpenClaw | 恒久設定の禁止リスト |

---

<!-- AI透かし: {"生成者":"Claude AI（Anthropic社）","準拠法規":["APPI_日本","GDPR_2016_679","EU_AI_Act_2024_1689"],"免責":"AI生成コンテンツ。人的検証が必要です。","文書ID":"MNRKW-PLAN-2026-LOCALORCH-01","生成日時UTC":"2026-09-16T00:00:00Z"} -->
[AI:Claude/Anthropic][WM-03][状態:草案・未検証] 人的レビュー必須。
