# アーキテクチャ設計書

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

現行コードに合わせて、システム構成、責務、データフロー、技術的決定を定義する。

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


## 全体構成

```text
Browser / Next.js
  -> FastAPI REST API
      -> Service
          -> LangGraph Workflow / 専門Service
              -> Repository
                  -> PostgreSQL + pgvector
      -> Azure OpenAI
      -> data/uploads, data/reports, 一時Chart
```

## 技術構成

- Frontend: Next.js App Router、React、TypeScript、MUI、TanStack Query、React Hook Form、Zod、Recharts
- Backend: Python、FastAPI、Pydantic、SQLAlchemy、Alembic、pandas、NumPy、LangGraph、ReportLab、Matplotlib
- Data: PostgreSQL、pgvector、ファイルストレージ
- AI: Azure OpenAI ChatとEmbedding

## フロントエンド

- URLは`/login`と認証後トップ画面を基本とする。
- CSVアップロードとレポート詳細はDialog、AI相談は右Drawerとする。
- `app`は入口、`features`は機能、`components`は共有UI、`theme`はデザインシステムを担当する。
- 表示ComponentはAPIを直接呼ばず、Feature APIとTanStack Queryを経由する。

## バックエンド

- API: HTTP、Schema、status、例外変換
- Service: ユースケースと業務処理
- Workflow: LangGraphの順序、分岐、State
- Repository: SQLAlchemyとpgvector
- DB: Engine、Session、Transaction

## 現行API

- `POST /api/v1/files`
- `GET /api/v1/files/{uploaded_file_id}/measurements`
- `GET /api/v1/reports`
- `POST /api/v1/reports/generate`
- `GET /api/v1/reports/{report_id}/pdf`
- `POST /api/v1/search`
- `POST /api/v1/chat`
- `GET /health`

## データモデル

- `users`
- `uploaded_files`
- `reports`
- `report_chunks`

CSV全測定値はDBへ保存せず、保存されたCSVからグラフ用データを読み出す。

## 分析フロー

```text
CSV受付 -> 管理情報commit -> CSV検証・統計・異常抽出
-> Azure OpenAI分析 -> reports保存 -> report_chunks保存
-> uploaded_filesをcompletedへ更新
```

外部AI待機中にDB Transactionを長時間保持しないよう、実装とテストで確認する。

## RAGフロー

```text
質問検証 -> 質問Embedding -> pgvector検索
-> 関連なし: 回答不能
-> 関連あり: Context構築 -> AI回答 -> 参照元返却
```

## 現状との差分・要整理

- `api/v1/health.py`はRouter未登録で、`main.py`の`/health`と整理が必要。
- Promptは`prompts`配下への集約方針だが、一部Service内に存在する。
- `dev-user`固定はPoC暫定で、本番化前に廃止する。
- `data/csv`ではなく現行実装の`data/uploads`を標準保存先とする。
- RAGチャンク種別は実装・DB・検索Schemaで統一する。

## ADR

- ADR-001: Monolith構成をPoCで採用
- ADR-002: PostgreSQLとpgvectorを同一DBで使用
- ADR-003: CSV全測定値をDBへ保存しない
- ADR-004: 数値計算はPython、文章生成はAzure OpenAI
- ADR-005: LangGraph Nodeは薄くしServiceへ委譲
- ADR-006: WebグラフとPDFグラフを分離
- ADR-007: レポートチャンクに参照元メタデータを保持

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

