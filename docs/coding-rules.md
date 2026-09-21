# コーディング規約

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

現行のFastAPI、Next.js、SQLAlchemy、LangGraph構成に合わせて保守可能で安全な実装規則を定義する。

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


## 共通

- 必要最小限の変更
- 事実、仮定、未確認を区別
- 型を明示し、秘密情報を記載しない
- 例外を握り潰さず、エラーとログを分離
- 関係のない一括整形をしない

## Python

- PEP 8を基本とし、Ruffとmypyの設定を正とする
- 関数・Classの責務を小さくする
- Path操作は`pathlib`
- DBはRepository経由
- SessionとTransaction境界を明確にする
- `except Exception`は最終境界に限定し、logger.exceptionまたは安全な変換を行う

## FastAPI / Pydantic

- Request / Response Schemaを定義
- 適切なHTTP status
- 内部例外を直接返さない
- DependencyでSession・認証を提供
- Queryのlimit、長さ、範囲を検証

## TypeScript / React

- `any`を避ける
- `page.tsx`に業務処理を集中させない
- API Module、Hook、Viewを分離
- 不要な`use client`を付けない
- MUI ThemeとDesign Systemを使用
- Loading、Empty、Errorを実装

## SQLAlchemy / Alembic

- Model変更とMigrationとDB文書を同時更新
- SQL文字列連結を避ける
- unique、FK、check、indexを要件に合わせる
- 適用済みMigrationを安易に書き換えない

## AI / RAG

- Promptは原則`backend/src/prompts`
- AIへ最小限の情報のみ送信
- 結果を検証し、根拠外の断定を防ぐ
- Embedding次元とモデル互換性を確認
- Chunkに参照元metadataを付ける

## Comment / Document

- 「何をしているか」より、必要な「なぜ」を説明
- TODOには理由、担当、期限を可能な範囲で付ける
- API、DB、要件、テスト変更は対応するdocsを更新

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

