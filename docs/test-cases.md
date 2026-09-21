# テストケース

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-18
- 状態: 実装済みベースライン / チームレビュー待ち

## 目的

現行機能に対する主要テストケースと、要件・受入基準とのトレーサビリティを定義する。

## 参照標準と適用方針

本プロジェクトは次の標準・ガイドラインを参考にする。ただし、PoCであり、完全準拠や第三者認証を主張しない。採用項目はプロジェクト要件へ具体化し、適用除外と理由を記録する。

- ISO/IEC/IEEE 29148:2018: 要求工学
- ISO/IEC 25010:2023: システム・ソフトウェア品質モデル
- ISO/IEC/IEEE 29119-1:2022、29119-2:2021: ソフトウェアテスト
- ISO/IEC TR 29119-11:2020: AIベースシステムのテスト
- NIST SP 800-218 SSDF 1.1: セキュア開発
- OWASP ASVS 5.0.0: Webアプリケーションセキュリティ検証
- NIST AI RMF 1.0: AIリスク管理
- WCAG 2.2: Webアクセシビリティ
- RFC 9457: HTTP APIのProblem Details

### 公式参照先

- https://www.iso.org/standard/72089.html
- https://www.iso.org/standard/81291.html
- https://www.iso.org/standard/79428.html
- https://www.iso.org/standard/79016.html
- https://www.iso.org/standard/78176.html
- https://csrc.nist.gov/pubs/sp/800/218/final
- https://owasp.org/www-project-application-security-verification-standard/
- https://www.nist.gov/itl/ai-risk-management-framework
- https://www.w3.org/TR/WCAG22/
- https://www.rfc-editor.org/rfc/rfc9457.html

## 形式

各ケースはID、関連要件、前提、入力、手順、期待結果、後処理を持つ。

## CSV

- TC-CSV-001: 正常CSVを保存できる
- TC-CSV-002: 空CSVを拒否する
- TC-CSV-003: 必須列不足を拒否する
- TC-CSV-004: 日時不正を拒否する
- TC-CSV-005: 数値不正を拒否する
- TC-CSV-006: 欠損を拒否または仕様どおり処理する
- TC-CSV-007: 不正拡張子・MIMEを拒否する
- TC-CSV-008: Size/行数境界を確認する
- TC-CSV-009: 重複checksumを仕様どおり扱う
- TC-CSV-010: DB失敗時に実ファイルを残さない

## Analysis / Report

- TC-ANA-001: 統計値が期待値と一致する
- TC-ANA-002: 閾値未満、等値、超過を区別する
- TC-ANA-003: 空DataFrameを拒否する
- TC-REP-001: ReportとChunkとstatusが整合して保存される
- TC-REP-002: 登録済みCSVの再生成を409とする
- TC-REP-003: AI失敗時に不整合を残さない

## RAG / Chat

- TC-RAG-001: 類似質問で関連Chunkを取得する
- TC-RAG-002: Equipment、期間、種別で絞り込む
- TC-RAG-003: LimitとSimilarity計算を確認する
- TC-RAG-004: 他利用者Dataを返さない。認証実装後必須
- TC-CHAT-001: 根拠付き回答とSourceを返す
- TC-CHAT-002: 根拠なしで回答不能を返す
- TC-CHAT-003: Prompt injectionを命令として扱わない

## API / Security

- TC-API-001: 400/404/409/422/500/502を仕様どおり返す
- TC-SEC-001: ErrorとLogに秘密情報・内部Pathがない
- TC-SEC-002: 未認証と権限外を拒否する。認証実装後必須
- TC-SEC-003: Path traversal Filenameを拒否する
- TC-SEC-004: CORSを許可Originへ限定する

## Frontend / Accessibility

- TC-UI-001: Loading、Empty、Error、Retry
- TC-UI-002: CSV DialogとReport DialogのFocus
- TC-UI-003: AI Drawerの開閉、送信、Source
- TC-UI-004: Chart axis、Tooltip、単位、異常点
- TC-ACC-001: Keyboard操作、Label、aria-label、Focus visible

### 実装済みFrontendテスト範囲

#### 共通基盤およびAPI

- API Path
- 共通API Client
- API Error変換
- Health API
- Measurement取得API
- Report一覧API
- Report生成API
- PDF Download API
- CSV Upload API
- RAG Chat API

#### Hooks

- `useRagChat`: 初期状態、Pending、成功、Error変換、Abort、Reset
- `useMeasurements`: 初期状態、Loading、成功、Error変換、多重実行防止、Reset
- `useCsvAnalysis`: Uploading、Generating、成功、各段階の失敗、多重実行防止、Reset、進捗メッセージ

#### Components

- `AnalysisProgress`: 表示条件とProgress表示
- `CsvFilePreview`: FilenameとKB表示
- `CsvDropzone`: File選択、Accept属性、未選択時の処理
- `ChatInput`: 入力、Trim、送信、Enter、Disabled、Progress、Accessible Name
- `ChatMessage`: User/Assistant表示、Source、Chunk label、日付Fallback、Similarity
- `ChatMessageList`: Empty、Message一覧、Pending表示
- `PdfDownloadButton`: Disabled、Download、Pending、Error表示
- `ReportListItem`: 項目表示、Fallback、Status、選択操作
- `ReportList`: 一覧、空配列、Pagination表示、選択操作
- `HealthStatus`: Loading、接続成功、Error、非Error値のFallback

### Frontend自動テスト実績

2026-09-18時点:

- Test Files: 24件成功
- Tests: 141件成功
- ESLint: 0 errors / 0 warnings
- TypeScript: 成功
- Next.js Production Build: 成功

### Frontend Coverage実績とGate

実績:

- Statements: 45.95%
- Branches: 42.21%
- Functions: 35.15%
- Lines: 47.10%

Gate:

- Statements: 40%以上
- Branches: 35%以上
- Functions: 30%以上
- Lines: 40%以上

## PDF

- TC-PDF-001: 日本語PDFと必須項目
- TC-PDF-002: 長文、異常多数、文字切れ
- TC-PDF-003: 404・権限・生成失敗
- TC-PDF-004: 失敗時に不完全Fileを残さない

## 未実施または後日対応

- 認証・認可に依存する利用者分離、権限外アクセス、ID差替えテスト
- Loginを含むE2Eテスト
- `CsvUploadModal`、`AiChatDrawer`、`ReportDetailModal`、`DashboardContent`、`VibrationChart`など大規模複合Componentの網羅的テスト
- 実Azure OpenAI接続を用いた承認済み環境での確認

## チームで決定・運用する項目

以下は標準から自動的に確定せず、チームで合意して記録する。

- [ ] 文書オーナー
- [ ] 承認者
- [ ] レビュー頻度
- [ ] 採用する標準の版
- [ ] 適用する項目
- [ ] 適用しない項目と理由
- [ ] PoC完了条件
- [ ] 本番化前の追加対応
- [ ] 未確定事項の担当者と期限
- [ ] 変更履歴の記録方法
