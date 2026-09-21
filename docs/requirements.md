# 要件定義書

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

本システムに必要な機能要件、非機能要件、制約、品質目標、運用条件を網羅的に定義する。

## 参照標準と適用方針

本プロジェクトは以下を参考にする。PoC段階では完全準拠や認証取得を主張せず、採用項目、適用除外、理由、残存リスクをチームで記録する。

- ISO/IEC/IEEE 29148:2018: 要求工学
- ISO/IEC 25010:2023: 製品品質モデル
- ISO/IEC/IEEE 29119-1:2022、29119-2:2021: テスト概念・プロセス
- ISO/IEC TR 29119-11:2020: AIベースシステムのテスト
- NIST SP 800-218 SSDF 1.1: セキュア開発
- OWASP ASVS 5.0.0: Web・APIセキュリティ
- NIST AI RMF 1.0: AIリスク管理
- WCAG 2.2: Webアクセシビリティ
- RFC 9457: HTTP API Problem Details

公式参照先は `standards-and-tailoring.md` に集約する。

## 1. システム目的

- 振動CSVを安全に受け付け、統計処理と異常候補抽出を行う。
- Azure OpenAIを利用し、根拠を限定した分析文章とRAG回答を生成する。
- 分析結果、レポート、PDF、検索用Embeddingを管理する。
- PoCとして技術的実現性、品質、運用上の課題を評価する。

## 2. ステークホルダー

- 設備保全担当者
- PoC評価者・業務責任者
- 開発者・テスト担当者
- システム運用担当者
- 情報セキュリティ・クラウド管理担当者

## 3. スコープ

### 対象

- CSVアップロード、検証、保存、重複確認
- 振動統計、閾値判定、異常候補
- AI分析、レポート、PDF
- レポート一覧・詳細、振動グラフ
- Embedding、pgvector検索、RAGチャット、参照元
- 認証・認可の本番化設計
- ログ、監視、バックアップ、障害復旧

### 対象外

- Raspberry Piからのリアルタイム送信・遠隔制御
- ストリーミング分析
- CSV全測定値のDB保存
- PoCにおけるチャット履歴・LangGraph Checkpoint永続化
- マルチリージョン、高可用性、複数拠点、マイクロサービス

## 4. 機能要件

### 認証・利用者

- REQ-AUTH-001: 利用者を認証できること。
- REQ-AUTH-002: 無効利用者、期限切れ・不正な認証情報を拒否すること。
- REQ-AUTH-003: LogoutまたはToken失効を提供すること。
- REQ-AUTHZ-001: CSV、Report、PDF、RAGを利用者・Roleに応じて認可すること。
- REQ-AUTHZ-002: IDを変更しても他利用者のDataを取得できないこと。

### CSV・ファイル

- REQ-CSV-001: multipart/form-dataでCSVを手動Uploadできること。
- REQ-CSV-002: Filename、拡張子、MIME、Size、Encoding、必須列、行数を検証すること。
- REQ-CSV-003: 日時、数値、欠損、非有限値、並び順を検証すること。
- REQ-CSV-004: UUID等の安全な保存名を使用し、許可Directory外へ保存しないこと。
- REQ-CSV-005: SHA-256により重複を判定し、同時Uploadでも重複登録を防ぐこと。
- REQ-CSV-006: File保存またはDB登録失敗時に片方だけを残さないこと。

### 分析

- REQ-ANA-001: 件数、最小、最大、平均、中央値、標準偏差をPythonで算出すること。
- REQ-ANA-002: 設定された閾値に基づき異常候補、件数、率、発生時刻を算出すること。
- REQ-ANA-003: 閾値の単位、適用範囲、Versionを追跡できること。
- REQ-ANA-004: 同一CSVに対する同時分析を制御すること。

### AI・レポート

- REQ-AI-001: CSV全件ではなく統計と必要最小限のContextを送信すること。
- REQ-AI-002: Timeout、Rate limit、認証、接続、空応答、形式不正を区別すること。
- REQ-AI-003: AI出力を検証し、確定診断として扱わないこと。
- REQ-REP-001: 統計、異常、AI分析を整合したReportとして保存すること。
- REQ-REP-002: 同一uploaded_file_idのReportを重複作成しないこと。
- REQ-REP-003: 一覧、Filter、Pagination、詳細を提供すること。

### Graph・PDF

- REQ-GRAPH-001: 保存CSVから時系列Dataと異常Flagを取得できること。
- REQ-GRAPH-002: 軸、単位、閾値、Tooltip、Dataなし・Errorを表示すること。
- REQ-PDF-001: A4縦、日本語、必須項目、Chartを含むPDFを生成すること。
- REQ-PDF-002: 同時生成でFileを破損させず、完成後のみDB情報を更新すること。
- REQ-PDF-003: 有効な生成済みPDFを再利用する条件を定義すること。

### RAG・Chat

- REQ-RAG-001: Reportを定義済みChunkへ分割し、元Reportを追跡できるMetadataを保存すること。
- REQ-RAG-002: Embedding model、Version、Dimensionsを保存しDB定義と一致させること。
- REQ-RAG-003: Equipment、Period、Chunk type、利用者範囲で検索できること。
- REQ-RAG-004: Limit、Distance function、Minimum relevanceを構成可能にすること。
- REQ-RAG-005: 再Embeddingを原子的に切り替え、失敗時に既存検索Dataを失わないこと。
- REQ-CHAT-001: 検索結果だけを根拠に回答し、参照元を返すこと。
- REQ-CHAT-002: 根拠不足時は推測せず回答不能を返すこと。
- REQ-CHAT-003: Retrieved content内の命令を信頼しないこと。

### UI

- REQ-UI-001: `/login`と認証後Topを基本とすること。
- REQ-UI-002: CSVとReport詳細はDialog、AI相談は右Drawerで提供すること。
- REQ-UI-003: Loading、Empty、Success、Warning、Error、Retryを表示すること。
- REQ-UI-004: Filter、Pagination、選択状態を再取得時も整合させること。

## 5. 非機能要件

### 性能・容量

- NFR-PERF-001: API別の目標応答時間を定義し測定すること。
- NFR-PERF-002: CSV最大Bytes、最大Rows、同時Upload数を定義すること。
- NFR-PERF-003: Report生成、Embedding、PDFのTimeoutと同時実行上限を定義すること。
- NFR-PERF-004: 一覧APIはPaginationを必須とし無制限取得しないこと。
- NFR-PERF-005: DB Query、Vector検索、Memory使用量を計測可能にすること。

### 信頼性・可用性

- NFR-REL-001: 失敗時にDBをrollbackし不完全Fileを残さないこと。
- NFR-REL-002: Retryは一時障害だけを対象に上限とBackoffを持つこと。
- NFR-REL-003: processingのStale状態を検出・復旧できること。
- NFR-REL-004: Healthと将来のReadinessを区別できること。
- NFR-AVL-001: PoC稼働時間、許容停止時間、復旧目標をチームで定義すること。

### 並行処理・冪等性

- NFR-CON-001: 同一CSVの同時処理は一件のみ開始すること。
- NFR-CON-002: DB一意制約に加え、AI呼出前に競合を検出すること。
- NFR-CON-003: 同一Request再送時の結果、Idempotency key、409条件をAPI別に定義すること。
- NFR-CON-004: Lock、Isolation、Deadlock retry方針を定義すること。
- NFR-CON-005: Scale-outしてもProcess内Lockだけへ依存しないこと。

### Security・Privacy

- NFR-SEC-001: OWASP ASVSをTailoringしたSecurity要件を満たすこと。
- NFR-SEC-002: Secret、Password、Token、接続文字列をCode・Log・Responseへ出さないこと。
- NFR-SEC-003: HTTPS、最小権限、CORS、入力検証、認証・認可を実装すること。
- NFR-SEC-004: Security eventを追跡できること。
- NFR-PRV-001: 収集・保存・AI送信Dataを最小化し保持・削除方法を定義すること。

### 保守性・互換性

- NFR-MNT-001: API、Service、Workflow、Repositoryを分離すること。
- NFR-MNT-002: 型、Test、Log、Documentを変更と同時に更新すること。
- NFR-CMP-001: 対応Browser、Python、Node、PostgreSQL、pgvector Versionを固定すること。
- NFR-CMP-002: API・DB変更のBackward compatibilityとMigrationを評価すること。

### Accessibility・Usability

- NFR-ACC-001: WCAG 2.2 AAを参考目標とし、適用範囲をチームが定義すること。
- NFR-ACC-002: Keyboard、Focus、Label、Status message、Color非依存を確認すること。
- NFR-USA-001: Errorは問題と次の操作を利用者へ示すこと。

### Observability・運用

- NFR-OBS-001: Request ID、User ID、File ID、Report ID、処理時間、結果を構造化Logへ記録すること。
- NFR-OBS-002: Metric、Alert、Log保持、Clock/Timezoneを定義すること。
- NFR-OPS-001: Backup、Restore、Retention、Deletion、Incident、Rollback手順を定義すること。
- NFR-OPS-002: EnvironmentごとのConfigとSecretを分離すること。

### AI品質・コスト

- NFR-AI-001: Validity、Reliability、Safety、Transparency、Human oversightを評価すること。
- NFR-AI-002: Prompt、Model、EmbeddingのVersionを追跡すること。
- NFR-AI-003: Token、Call count、Latency、Error rateを計測すること。
- NFR-AI-004: AI結果の事実性、根拠性、拒否性能をTestすること。

## 6. 制約と前提

- Azure OpenAI、PostgreSQL、pgvectorを使用する。
- PoCでは同期APIを維持できるが、Timeout超過時は非同期Job化を検討する。
- 会社規程、Azure利用規程、秘密情報管理を最優先する。

## 7. 未確定値

- CSV最大Size・Rows、同時処理数
- 正式閾値・単位・Version管理
- API Timeout・Rate limit・Idempotency key
- Isolation level・Lock方式・Stale復旧時間
- SLO、RTO、RPO、Log/Backup/Data保持期間
- Browser・Runtime・DB Version
- Vector index、Distance、Minimum relevance

## チームで決定・運用する項目

- [ ] 文書オーナーと承認者
- [ ] 適用する標準、版、適用範囲
- [ ] 適用除外と理由、残存リスク
- [ ] 未確定値の決定者と期限
- [ ] PoC完了条件と本番化条件
- [ ] レビュー頻度と変更承認方法
- [ ] 証跡の保存先と保持期間
- [ ] 例外承認の担当者、有効期限、見直し日
