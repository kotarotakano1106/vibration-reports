---
name: documentation
description: 振動AI日報生成アプリの要件、設計、API、DB、テスト、運用文書を現行コードと整合させ、標準・ID・変更履歴を管理する。
---

# Documentation Skill

## 目的

Docsの新規作成、更新、レビュー、実装との差分確認に使用する。

## 必須確認

- requirements、acceptance-criteria、use-cases
- architecture、backend-class-design
- api-spec、database、pdf-report-design
- testing-strategy、test-cases
- security-requirements
- concurrency-and-transaction
- operations-requirements
- standards-and-tailoring

## 手順

1. 変更要求、関連要件ID、受入基準IDを特定する。
2. 現行Code、Router、Schema、Model、Migration、Testを確認する。
3. 確認済み事実、仮定、未確定を分ける。
4. URL、Path、Table、Field、Status、Version、IDを文書間で統一する。
5. API変更はapi-spec、DB変更はdatabase、並行処理はconcurrency文書を更新する。
6. 標準の版、適用範囲、除外、Evidenceをstandards-and-tailoringへ記録する。
7. Team checklistのOwner、期限、承認状態を更新する。
8. Git diffで無関係な変更がないことを確認する。

## 禁止事項

- 未実装機能を実装済みと記載しない。
- 標準を確認せず準拠済みと記載しない。
- 実装と矛盾する内容を黙って上書きしない。
- 秘密情報を文書へ記載しない。

## 出力

- 更新文書
- 変更理由
- Codeとの整合性
- 未確定事項
- Team決定事項
- 残存不整合
