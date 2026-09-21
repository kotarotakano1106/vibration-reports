# バックエンドクラス設計書

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

現行バックエンドの主要クラス、責務、依存方向、トランザクション境界を定義する。

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


## パッケージ責務

- `api/v1`: Route、Input、HTTP response、例外変換
- `schemas`: Pydantic request / response
- `services`: 業務処理
- `workflows`: Graph、Node、State
- `repositories`: DBアクセス
- `models`: SQLAlchemy Model
- `db`: Engine、Session、Dependency
- `core`: Config、Security、Logging、共通例外
- `prompts`: AI指示と入力組立て

## 主要クラス

### FileService
- CSVファイル検証、安全な保存名、checksum、DB管理情報、失敗時後処理

### CsvService
- CSV読込、文字コード、必須列、日時、数値、欠損、時系列整列

### VibrationAnalysisService
- 統計量、閾値超過、異常率、判定

### AzureOpenAIService
- Chat、Embedding、Timeout、Retry、例外分類、次元確認

### ReportService
- CSV解析からレポート・チャンク保存までのユースケース

### RagSearchService
- 質問検証、Embedding、検索Filter、距離・類似度変換

### ReportPdfService
- レポート取得、Chart、PDF、DBのPDF情報更新

### Repository
- `UserRepository`
- `UploadedFileRepository`
- `ReportRepository`
- `VectorRepository`

## 依存規則

```text
API -> Service / Workflow -> Service -> Repository -> Model / DB
```

逆方向依存、APIからRepository直呼出し、Node内SQLを原則禁止する。

## Transaction

- CSV受付: ファイル保存と`uploaded_files`登録の整合性を管理
- レポート登録: `reports`、`report_chunks`、status更新を整合させる
- PDF: 生成成功後のみ`pdf_path`を更新
- 失敗時: rollbackし、不完全な生成物を削除または再利用不能にする

## 例外設計

- 入力・ファイル
- 対象なし・重複
- DB
- AI認証・接続・rate limit・response
- Embedding次元
- RAG
- PDF

APIは内部例外を安全なHTTP responseへ変換し、内部Pathや資格情報を返さない。

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

