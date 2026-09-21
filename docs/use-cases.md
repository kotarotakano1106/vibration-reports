# ユースケース

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

利用者とシステムの主要な操作フロー、代替フロー、例外フローを定義する。

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


## アクター

- 利用者: CSV投入、レポート閲覧、PDF取得、AI相談を行う
- Azure OpenAI: 分析文章とEmbeddingを生成する外部サービス
- PostgreSQL / pgvector: 管理情報、レポート、チャンクを保存・検索する

## UC-CSV-001 CSVアップロード

- 事前条件: 利用者がトップ画面を表示している
- 基本フロー: Dialogを開く、設備・日付・CSVを選ぶ、検証、保存、完了通知
- 代替: 同一チェックサムは重複として扱う
- 例外: 不正CSV、保存失敗、DB失敗時は安全なエラーを返し後処理する

## UC-REP-001 レポート生成

- 事前条件: 有効なCSV管理情報と実ファイルがある
- 基本フロー: CSV解析、統計計算、異常抽出、AI分析、レポート保存、Embedding保存、状態更新
- 例外: AIまたはDB失敗時は処理状態とログを更新し、不整合を残さない

## UC-DASH-001 ダッシュボード閲覧

- 基本フロー: 設備・年月を選択、サマリー、グラフ、一覧を表示、更新する
- 代替: 0件時はEmpty stateを表示する
- 例外: API失敗時はErrorと再試行を表示する

## UC-PDF-001 PDFダウンロード

- 基本フロー: レポート選択、PDF要求、生成、ダウンロード
- 例外: 対象なし、生成失敗、権限不足を区別する

## UC-CHAT-001 AI相談

- 基本フロー: Drawerを開く、設備・期間を確認、質問、Embedding、類似検索、回答、参照元表示
- 代替: 関連情報なしの場合は回答不能を表示する
- 例外: AI接続・レート制限・検索失敗を区別する

## UC-AUTH-001 認証

- 現状: 最終方式は未確定、一部APIは開発用ユーザー固定
- 本番化条件: 認証、認可、失効、利用者別データ分離を実装・検証する

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

