# MinoPRO オールコミュニケーター 設計計画 v1.0
AIチャットボット + FAX / Mail / VoIP / SNS / LINE ｜ ローカルデータ主権 ｜ Odoo 19 + PostgreSQL 基盤

作成日: 2026-09-16 ｜ 区分: 内部資料 WM-03 ｜ 状態: 草案（本人レビュー前）
上位文書: LOCAL-ORCH-PLAN.md（データ分類 L0〜L3・VLAN 40 egress 既定拒否）
準拠ドクトリン: omni-comms-center（法的境界・確定スタック）／ SAOS ／ Eco 7層

---

## 0. 結論（先出し）

1. **odoo.sh は使わない。** odoo.sh は Odoo SA が Google Cloud Platform 上で運用するマネージドホスティングで、リージョンは自動割当（東京なし、最寄りはシンガポール）。GAFAM 排除・国内データ主権の方針と正面から矛盾する。**Odoo 19 Enterprise をオンプレ（VLAN 30）または国内事業者の VPS に自社ホスト**し、PostgreSQL も同居させる。ライセンス費は同じ Enterprise 契約で賄える（ホスティング費のみ自前）。
2. **通信の中心は Odoo ではなく Chatwoot（MIT）。** Odoo は顧客・案件・請求の「真実の源泉」、Chatwoot は全チャネル受信箱、Asterisk が音声、agent-zero + Ollama がAI応対。すべて REST で疎結合。
3. **AIは L4 ローカル推論のみが顧客対話に触れる。** 通話・チャット・FAX の内容は外部 LLM に送らない（通信の秘密＋APPI＋自社方針の三重理由）。Claude はプロンプト設計・コード生成・L0 資料作成の L1 支援に限定。
4. **自己利用の範囲に留める限り電気通信事業の届出は不要。** 顧客企業の通信を取り次ぐ外販に踏み出す時点で第三号事業の建付けが必須。本計画は自己利用（段階A）に限定する。

---

## 1. 全体アーキテクチャ

```
[顧客]  電話(03/050)   FAX      Mail      LINE     Web/SNS
           │            │        │          │         │
        ITSP(SIP)   faximo/    MX/IMAP   Messaging  Webhook
           │        秒速FAX      │        API        │
   ┌───────┴────────────┴────────┴──────────┴─────────┴──────┐  VLAN 90 (voip) / DMZ
   │  Asterisk 22 LTS ──ARI──┐                                │
   │                          ▼                                │
   │  Chatwoot (MIT, 自社ホスト)  ← 全チャネル統合受信箱        │  VLAN 30
   │        │ REST/Webhook                                     │
   │        ▼                                                  │
   │  agent-zero + Ollama (L4)  ← 分類・要約・応答案・STT/TTS  │  VLAN 40 (egress 既定拒否)
   │        │ /json/2                                          │
   │        ▼                                                  │
   │  Odoo 19 Enterprise + PostgreSQL 16 (自社ホスト)          │  VLAN 30
   │        │                                                  │
   │  L7 追記専用監査ログ / OpenBao (秘密)                      │
   └───────────────────────────────────────────────────────────┘
```

データの流れ: 顧客 → チャネル → Chatwoot（会話）→ agent-zero（AI）→ Odoo（顧客・案件・請求）。逆方向の自動送信は USER GATE。

---

## 2. コンポーネント確定表

| 機能 | 採用 | ライセンス | 配置 | 備考 |
|---|---|---|---|---|
| ERP/CRM/請求 | Odoo 19 Enterprise 自社ホスト | 商用（Enterprise） | VLAN 30 | odoo.sh 不採用（§0） |
| DB | PostgreSQL 16 | PostgreSQL License | VLAN 30 | pgBackRest で国内保管バックアップ |
| オムニチャネル | Chatwoot CE | MIT（enterprise/ 配下除外） | VLAN 30 | LINE 公式チャネル対応の唯一の自社ホストOSS |
| PBX | Asterisk 22 LTS + FreePBX | GPL系 | VLAN 90 | Odoo VoIP（WSS必須）には依存しない |
| SIPトランク | Arcstar IP Voice 等の国内ITSP | — | — | 承認機種条項の照会が必要（§6） |
| FAX | faximo（受信）/ 秒速FAX Plus（API送受信） | — | — | T.38 自前実装は禁止 |
| メール | 自社 MX（Phase 3 で主権化判断）＋当面 MS365 IMAP 読取 | — | — | 外部公開アドレスは WinWin@minopro.one のみ |
| LINE | Messaging API webhook → Chatwoot | — | — | Reply 無料・Push 課金。2026-10-01 改定注意 |
| SNS | X/Instagram は API 制約が強く、Phase 2 以降で個別判断 | — | — | Meta/X も GAFAM 側であり主権対象外データのみ |
| AIオーケストレータ | agent-zero + Ollama | MIT | VLAN 40 | 本リポジトリ |
| STT | kotoba-whisper-v2.2（後処理）/ parakeet-tdt_ctc-0.6b-ja（リアルタイム候補） | Apache-2.0 / CC-BY-4.0 | VLAN 40 | 電話帯域 CER は要実測 |
| TTS | AivisSpeech | LGPL-3.0 | VLAN 40 | Style-Bert-VITS2 は AGPL のため法務確認前不採用 |
| 秘密管理 | OpenBao | MPL-2.0 | VLAN 30 | Vault は BSL のため不採用 |
| ワークフロー | n8n（社内利用） | Sustainable Use | VLAN 30 | 外販時は Temporal へ |

---

## 3. AIチャットボットの応対設計（無事故）

| 段階 | 動作 | 実行者 | ゲート |
|---|---|---|---|
| 1 受信 | チャネルから Chatwoot へ着信 | 自動 | — |
| 2 分類 | L0〜L3 判定、意図分類（問合せ/見積/クレーム/営業） | agent-zero (Ollama) | 判定不能は L2 扱い |
| 3 一次応答 | FAQ・営業時間・受付確認の定型応答（AI応対である旨を明示） | 自動 | **テンプレート応答のみ自動。自由生成文は送らない** |
| 4 起案 | 見積依頼→Odoo に「承認待ちリード」作成、返信案を Chatwoot に下書き | agent-zero | Odoo への書込みは承認待ちステータス固定 |
| 5 送信 | 下書きを担当者が確認して送信 | 本人/担当者 | USER GATE（外部送信） |
| 6 通話 | IVR 冒頭で録音＋AI解析を明示 → 通話後 STT → 要約を Chatwoot/Odoo に添付 | Asterisk + L4 | 外部 LLM 送信禁止 |
| 7 監査 | 全応答に L7 ログ（チャネル・データ区分・モデル・担当者） | 自動 | 月次 compliance-auditor |

プロンプトインジェクション対策: 顧客入力を扱うプロファイルでは agent-zero の `code_execution` と外部 MCP を無効化。ツールは「Chatwoot 下書き作成」「Odoo 承認待ち作成」「FAQ 検索」の3種に限定。

---

## 4. Odoo + PostgreSQL データ基盤の主権設計

- **配置**: 自社サーバ（VLAN 30）が第一候補。冗長化が要る場合は国内事業者の VPS（さくら/IDCF/KDDI 等、GAFAM 系 IaaS は除外）。**未確認**: 現行 Odoo の稼働形態（運用台帳 INDEX で確認）。
- **PostgreSQL**: Odoo 専用インスタンス＋Chatwoot 専用インスタンスを分離（AGPL 伝播回避ではなく障害分離目的。Chatwoot は MIT）。pgBackRest でオンサイト＋国内オフサイト保管、暗号化鍵は OpenBao。
- **個人情報の分離**: 通話録音・STT 全文は Odoo に入れず、VLAN 40 内ストレージに保持期間付きで保管。Odoo には要約と参照 ID のみ。恒久設定「個人情報の平文ログ禁止」に整合。
- **API 経路**: Odoo `/json/2` のみ（SAOS 第一原則）。GUI 自動化はしない。
- **Odoo Enterprise の外部通信**: IAP（SMS/OCR 等の Odoo クラウドサービス）は無効化。IAP を有効にすると Odoo SA 経由で外部に出るため、egress ACL でもブロックする。

---

## 5. 法務ゲート（設計より先に確定）

| 論点 | 判定 | 対応 |
|---|---|---|
| 電気通信事業法 届出 | 自己利用 → 不要 | 外販（段階B）は第三号事業として顧客企業が回線契約、当社はソフト提供 |
| 通信の秘密（第4条） | 第三号事業者にも適用 | IVR/チャット冒頭で「録音・AI解析」を明示。解析はローカル |
| 外部送信規律（第27条の12） | 顧客向け Web ポータルで該当し得る | タグ棚卸し＋外部送信ポリシー公表 |
| APPI 28条 | データが国内に留まる限り越境なし | odoo.sh 不採用の直接理由。LINE/Meta 側に渡るメタデータは利用規約上の明示で対応 |
| EU AI Act 第50条 | チャットボットの AI 開示（2026-12-02 実効） | 全チャネルで AI 応対を開示（国内向けも統一） |
| 特殊詐欺対策 | 発信者番号偽装・大量自動発信の禁止 | アウトバウンド自動発信機能は実装しない |

---

## 6. 発注前に潰す未確認事項

1. **odoo.sh のホスティング先が GCP であること**は複数の二次情報で一致するが、Odoo SA 公式ページで本人確認（odoo.sh の Security/Infrastructure ページ）。
2. **現行 Odoo 契約形態**（odoo.sh 契約済みなら移行費・契約期間の確認、運用台帳）。
3. **Chatwoot CE で LINE チャネルが実機で動くか**（動かなければ API Channel への自前ブリッジ）。
4. **Arcstar IP Voice の承認機種に Asterisk が含まれるか**（NTTドコモビジネスへ照会）。
5. **parakeet-ja の電話帯域 CER・遅延の実測**。
6. **LINE 2026-10-01 改定後の Push 単価**。
7. **DGX Spark / GPU 機の VRAM**（STT+TTS+チャット LLM の同時常駐可否）。

---

## 7. フェーズ計画

| Phase | 期間 | 内容 | Go 条件 |
|---|---|---|---|
| 0 | 2〜4週 | Odoo 19 自社ホスト＋PostgreSQL 構築、Chatwoot 起動、LINE/メール受信のみ、AI は分類のみ | 受信取りこぼし 0、L2 外部送信 0（パケット実測） |
| 1 | 1〜2ヶ月 | agent-zero 連携、テンプレート自動応答、Odoo 承認待ちリード作成 | 誤分類 < 5%、担当者の下書き採用率 ≥ 50% |
| 2 | 2〜3ヶ月 | Asterisk + ITSP、通話後 STT 要約、FAX 受信取り込み | 通話接続成功率 ≥ 99%、STT 要約の担当者承認率 ≥ 70% |
| 3 | 3〜6ヶ月 | メール基盤主権化判断、SNS チャネル個別判断、リアルタイム STT PoC | 到達性テスト合格、CER 実測で採否 |
| B | 別案件 | 外販（第三号事業の建付け） | 法務レビュー完了が前提 |

---

## 8. 採用しないもの

| 対象 | 理由 |
|---|---|
| odoo.sh | GCP 上・リージョン自動割当。主権方針に反する |
| Odoo VoIP 直結 | WSS 必須・検証済プロバイダが日本の番号を持たない |
| UniFi Talk | 日本非対応 |
| Twilio Fax | 2021-12 EOL |
| Zammad / erxes / FreeScout | LINE 非対応 or AGPL・競合禁止条項 |
| Fish Speech / Style-Bert-VITS2（本番） | 商用不可 / AGPL 法務未確認 |
| 外部 LLM への通話・チャット内容送信 | 通信の秘密・APPI・自社方針 |

---

<!-- AI透かし: {"生成者":"Claude AI（Anthropic社）","準拠法規":["APPI_日本","電気通信事業法","GDPR_2016_679","EU_AI_Act_2024_1689"],"免責":"AI生成コンテンツ。人的検証が必要です。法的助言ではありません。","文書ID":"MNRKW-PLAN-2026-OMNICOMM-01","生成日時UTC":"2026-09-16T00:00:00Z"} -->
[AI:Claude/Anthropic][WM-03][状態:草案・未検証] 人的レビュー必須。
