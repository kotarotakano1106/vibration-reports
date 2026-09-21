# テスト戦略

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-18
- 状態: 実装済みベースライン / チームレビュー待ち

## 目的

国際的なテスト標準を参考に、本PoCのテストレベル、リスク優先度、AI評価、自動化、完了条件を定義する。

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

## 適用方針

ISO/IEC/IEEE 29119の概念・プロセスを参考にし、PoC規模へTailoringする。品質観点はISO/IEC 25010、AIはISO/IEC TR 29119-11とNIST AI RMF、SecurityはOWASP ASVSを参考にする。

## テストレベル

- Unit: Schema、Service、計算、Utility、Hook
- Integration: Service-Repository、DB、File、Workflow
- API: Input、status、response、side effect
- Component: UI state、Interaction、Accessibility
- E2E: Login、CSV、Report、PDF、Chat

## リスク優先度

最優先:
- CSV検証とFile/DB整合性
- 数値計算と閾値判定
- Report/Chunk transaction
- 秘密情報漏えい
- 認証・認可
- RAGの根拠外回答

## テスト設計技法

- 同値分割
- 境界値分析
- Decision table
- 状態遷移
- Error guessing
- Pairwiseを必要に応じて採用

## AI・RAG評価

- 数値保持
- 根拠性
- 参照元整合
- 根拠不足時の拒否
- Equipment / Date取り違え防止
- Prompt injection耐性
- 完全一致ではなく決定的な検査項目で判定

## 自動化

### Backend

- `pytest`: Unit、API、Integration、Workflow
- `ruff`: Lintおよび静的解析
- `mypy`: 型検査
- Azure OpenAIは通常Mockとし、実接続確認は承認済みの分離環境で実施する

### Frontend

- Vitest 5およびReact Testing Libraryを使用する
- 安定動作のため、テストは `vmThreads`、`maxWorkers=1`、`--no-isolate` で実行する
- ESLint、TypeScript、Vitest、Next.js Production Buildを品質検証に含める
- V8 ProviderでCoverageを計測する
- Coverage生成物 `frontend/coverage/` はGitおよびESLintの対象外とする

### 実行コマンド

プロジェクトルートから日常的なFrontend品質検証を実行する。

```powershell
npm --prefix ".\frontend" run check
```

Frontend CoverageとCoverage Gateを検証する。

```powershell
npm --prefix ".\frontend" run test:coverage
```

## 品質ベースライン

2026-09-18時点の検証済みベースラインを以下に示す。

### Backend

- Ruff: 成功
- mypy: 成功
- pytest: 330件成功
- Coverage: 97.43%

### Frontend

- ESLint: 0 errors / 0 warnings
- TypeScript: 成功
- Test Files: 24件成功
- Tests: 141件成功
- Next.js Production Build: 成功

### Frontend Coverage実績

- Statements: 45.95%
- Branches: 42.21%
- Functions: 35.15%
- Lines: 47.10%

### Frontend Coverage Gate

- Statements: 40%以上
- Branches: 35%以上
- Functions: 30%以上
- Lines: 40%以上

Coverage実績値は、その時点で `src/**/*.{ts,tsx}` を対象に測定したベースラインである。未テストの大規模複合Componentを含むため、実績値とGateを混同しない。Gateは品質低下の検知を目的とし、数値達成のみを目的としたテスト追加は行わない。

## Entry / Exit

Entry:
- 要件・受入基準・変更差分が特定済み
- Test dataとEnvironmentが利用可能

Exit:
- Must受入基準が成功
- Critical / High defectが0
- 未実施と残存Riskを記録
- BackendのLint、型検査、主要回帰、Coverage基準が成功
- FrontendのLint、型検査、141件の回帰テスト、Production Buildが成功
- Frontend Coverage Gateが成功

## 証跡

- 実行Command、日時、環境
- 成功・失敗・Skip
- Failure logから秘密情報を除外
- 手動確認の担当と結果
- Coverage Reportはローカル生成物とし、Gitへ登録しない

## 既知の制約と保留事項

- 認証・認可は未実装であり、開発用の固定 `dev-user` を使用している
- 認証・認可が未実装の状態でBackendをインターネットへ公開しない
- 外部公開または本番化前に、認証、利用者単位の認可、権限テストを必須とする
- Loginを含むE2Eテストは認証実装後に追加する
- 大規模複合Componentの追加テストは、変更リスクと利用頻度に基づいて優先順位を決定する

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
