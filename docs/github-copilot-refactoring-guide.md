# GitHub Copilot向けリファクタリング計画

## 1. 文書の目的

本書は、振動AI日報生成アプリの機能実装、品質基盤整備、セキュリティ対応、Frontend改善、文書同期などが完了した後に、GitHub Copilotを使用して安全にリファクタリングを進めるための参考資料である。

リファクタリングでは、動作仕様を変更せず、責務の明確化、保守性、型安全性、テスト容易性を改善する。大規模な一括変更を避け、一責務、一タスク、一検証単位で進める。

## 2. 適用タイミング

リファクタリングは、次の工程が完了した後に開始する。

- 必要な機能実装
- BackendおよびFrontendの主要テスト整備
- セキュリティ要件への対応
- 運用、監視、ログ方針の確定
- API、DB、画面仕様の確定
- 関連ドキュメントの同期
- 機密情報および不要ファイルの確認

仕様が変動している間は、構造を先に最適化しすぎない。

## 3. 現在のBackend品質ベースライン

リファクタリング開始前に、以下を最新値へ更新する。

- Ruff: All checks passed
- mypy: Success, 56 source files
- Backend Test: 330 passed
- Backend Coverage: 97.43%
- Coverage Gate: 80%
- Test Database: vibration_reports_test

検証コマンド:

```powershell
.\scripts	est-backend.ps1 -Mode quick
.\scripts	est-backend.ps1 -Mode all
.\scripts	est-backend.ps1 -Mode coverage
```

合格条件:

- Ruffが成功する
- mypyが成功する
- 既存テスト件数を下回らない
- 失敗が0件である
- Coverageが80%以上である
- 公開API、DB Schema、例外契約が意図せず変わっていない

## 4. 基本原則

### 4.1 一度に一責務だけ変更する

1つの作業では、次のいずれか1つだけを対象とする。

- Validatorの切り出し
- Storage処理の切り出し
- 純粋関数の抽出
- 型定義の明確化
- 重複ロジックの統合
- メソッド名や変数名の改善
- Dependency Injectionの整理

同時にAPI、DB、例外設計、非同期化などを変更しない。

### 4.2 公開契約を維持する

原則として次を変更しない。

- Public methodのSignature
- API Path、Method、Request、Response
- HTTP Status Code
- DB Schema、Index、Constraint
- 例外型と例外メッセージ
- ファイル保存場所と命名規則
- Transaction、Commit、Rollbackの境界
- Azure OpenAIの入力、出力、Deployment設定
- RAG Chunkの種類、順序、Metadata

変更が必要な場合は、リファクタリングではなく仕様変更タスクとして分離する。

### 4.3 Characterization Testを先に置く

現在の動作が十分に保護されていない場合は、実装変更前に現在の振る舞いを固定するテストを追加する。

### 4.4 最小差分を優先する

- 無関係なFormatter適用を行わない
- ファイル全体を書き換えない
- 不要な抽象化を追加しない
- 将来要件を推測して汎用化しない
- Protocol、Factory、Base Classは必要性が確認できるまで導入しない

## 5. 対象候補と優先順位

### 優先度1: `backend/src/services/file_service.py`

規模: 約450行

主な責務:

- アップロード入力の検証
- ファイル名、拡張子、MIME Type、設備ID、サイズの検証
- Checksum計算
- 重複判定
- 物理ファイル保存
- DB登録
- Commit、Rollback
- DB失敗時の物理ファイル削除
- 業務例外への変換

推奨する分割順:

1. ファイル名検証のみ切り出す
2. 残りの純粋な入力検証を集約する
3. Checksum計算を純粋関数化する
4. Local File Storage処理を切り出す
5. `save_csv()`をOrchestratorとして整理する
6. `FileSaveResult.uploaded_file`を具体型へ変更する

最初からFileService全体を分割しない。

### 優先度2: `backend/src/services/report_pdf_service.py`

規模: 約556行

長さの多くはReportLabのレイアウト定義であり、行数だけを理由に分割しない。

分離候補:

- `VibrationChart`
- PDF Style定義
- Header、Summary、Anomaly、Analysis、RecommendationのSection Builder
- 日付、Status、Paragraph変換などの表示Utility
- PDFファイル名生成

推奨順:

1. PDFファイル名生成の純粋関数化
2. 表示Utilityの切り出し
3. `VibrationChart`の独立Module化
4. Section Builderの分割

PDF生成結果、フォント、ページサイズ、表示順序を変更しない。

### 優先度3: `backend/src/workflows/nodes/report_nodes.py`

規模: 約344行

Node単位の責務は分かれているため、急いで分割しない。

分離候補:

- AI分析文のSection分割
- Report本文生成
- Summary生成
- 推奨対応抽出
- RAG Chunk構築

LangGraphのNode名、State Key、遷移順序を変更しない。

### 維持を優先する対象

次は現時点で単一領域にまとまっているため、行数だけで分割しない。

- `backend/src/services/azure_openai_service.py`
- `backend/src/services/csv_service.py`
- `backend/src/services/vibration_analysis_service.py`
- `backend/src/services/rag_search_service.py`

## 6. FileServiceの推奨責務境界

最終的な依存関係の候補:

```text
API
  -> FileService
       -> FileUploadValidator
       -> LocalFileStorage
       -> UploadedFileRepository
       -> SQLAlchemy Session
```

責務:

### FileService

- ユースケースの処理順序
- 重複Policy
- Repository呼び出し
- Transaction制御
- 補償処理の実行判断
- 業務例外への変換
- `FileSaveResult`の返却

### FileUploadValidator

- ファイル内容
- ファイル名
- 拡張子
- MIME Type
- 設備ID
- ファイルサイズ

ValidatorはDB、Repository、Session、FastAPIへ依存させない。

### LocalFileStorage

- 保存先ディレクトリ作成
- 保存名生成
- 物理ファイル書き込み
- 物理ファイル削除

StorageはDB、Repository、Sessionへ依存させない。

### UploadedFileRepository

- DB検索
- DB登録
- Status更新
- Flush、Refresh
- レコード削除

CommitはService側で管理する現在の境界を維持する。

## 7. セキュリティ上の不変条件

リファクタリング中も次を維持する。

- 空ファイル拒否
- ファイルサイズ上限
- 拡張子Allowlist
- MIME Type Allowlist
- パストラバーサル拒否
- 不正なファイル名、制御文字の拒否
- 設備ID検証
- 元ファイル名を保存パスへ直接使用しない
- SHA-256 Checksumによる重複判定
- DB Unique Constraintを最終防衛線として維持
- DB登録失敗時のRollback
- 保存済み物理ファイルの補償削除
- Cleanup失敗で元のDB例外を失わない
- `.env`、秘密鍵、資格情報を変更対象や出力へ含めない

検証順序や正規化順序を変更すると、セキュリティ検証を迂回する可能性がある。ロジック移動時は順序を保持する。

## 8. GitHub Copilotへ共通で渡す指示

```text
対象ファイルのリファクタリングを実施してください。
今回は指定した1責務だけを変更してください。

開始前に必ず確認:
- 関連する実装
- Unit Test
- Integration Test
- API Test
- docs/architecture.md
- docs/testing-strategy.md
- docs/security-requirements.md
- .github/copilot-instructions.md

制約:
- 公開APIを変更しない
- DB Schemaを変更しない
- Migrationを追加しない
- 既存の例外型と例外メッセージを変更しない
- Transaction境界を変更しない
- 無関係なファイルを変更しない
- 既存テストを削除しない
- 新しい仕様を追加しない
- 過剰な抽象化を行わない
- 全体Formatterを実行しない
- 一度に複数責務を変更しない

作業手順:
1. 現在の動作と依存関係を説明する
2. 変更対象ファイルを提示する
3. 最小差分で実装する
4. 必要なCharacterization Testを追加する
5. Ruff、mypy、関連テストを実行する
6. Backend全体テストを実行する
7. 変更内容、検証結果、残るリスクを報告する

品質基準:
- Ruff成功
- mypy成功
- Backend Testが既存基準以上
- 失敗0件
- Coverage 80%以上
```

## 9. 最初のFileServiceタスク用プロンプト

```text
backend/src/services/file_service.py のファイル名検証責務だけを切り出してください。

対象:
- backend/src/services/file_service.py
- 新規 backend/src/services/file_name_validator.py
- 新規または変更する関連Unit Test

実施内容:
- `_validate_filename()`の現在の処理を変更せず専用Moduleへ移す
- FileServiceから新しいValidatorへ委譲する
- 既存の例外型、例外メッセージ、正規化、検証順序を維持する
- Characterization Testを追加する

今回変更しないもの:
- `save_csv()`のSignature
- 拡張子検証
- MIME Type検証
- 設備ID検証
- ファイルサイズ検証
- Checksum
- 重複判定
- 物理ファイル保存と削除
- Repository
- Commit、Rollback
- API、Schema、Model、Migration

設計条件:
- 新ModuleはDB、Repository、Session、FastAPIへ依存しない
- Protocol、Factory、Base Classを追加しない
- 循環Importを作らない
- 無関係な整形を行わない

検証:
- 新ValidatorのUnit Test
- FileService Unit Test
- FileService Integration Test
- Files API Test
- `scripts/test-backend.ps1 -Mode all`
- `scripts/test-backend.ps1 -Mode coverage`
```

## 10. Copilotの提案を止める条件

次のいずれかに該当した場合は、変更を適用せず再計画する。

- 1タスクで4ファイル以上の本体コードを変更する
- API、Schema、Model、Migrationを同時変更する
- RepositoryとServiceを同時に全面変更する
- 例外階層を変更する
- 同時に非同期化する
- Storageを抽象化しながらValidatorも分割する
- 既存テストを削除する
- Coverageを除外設定で維持しようとする
- `type: ignore`や`noqa`を広範囲に追加する
- セキュリティ検証を簡略化する
- 仕様にない機能を追加する
- `.env`や資格情報を読み上げる、変更する、出力する

## 11. 変更後のレビュー手順

### 11.1 変更ファイル確認

Git操作を行わない期間は、更新日時で対象を確認する。

```powershell
Get-ChildItem ".\backend\src", ".\backend\tests" -Recurse -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 20 LastWriteTime, FullName
```

### 11.2 個別確認

```powershell
.\.venv\Scripts\python.exe -m ruff check ".\backend\src" ".\backend\tests"
.\.venv\Scripts\python.exe -m mypy ".\backend\src"
```

### 11.3 関連テスト

```powershell
.\.venv\Scripts\python.exe -m pytest `
    ".\backend\tests\unit\services\test_file_service.py" `
    ".\backend\tests\unit\services\test_file_service_save.py" `
    -q

.\.venv\Scripts\python.exe -m pytest `
    ".\backend\tests\integration\services\test_file_service_integration.py" `
    ".\backend\tests\api\test_files_api.py" `
    -q
```

### 11.4 全体確認

```powershell
.\scripts\test-backend.ps1 -Mode all
.\scripts\test-backend.ps1 -Mode coverage
```

## 12. タスク完了チェックリスト

- [ ] 変更対象は1責務だけ
- [ ] 変更前の品質基準を確認した
- [ ] 公開Signatureを維持した
- [ ] API契約を維持した
- [ ] DB Schemaを変更していない
- [ ] Migrationを追加していない
- [ ] 例外型とメッセージを維持した
- [ ] 検証順序を維持した
- [ ] Transaction境界を維持した
- [ ] Cleanup条件を維持した
- [ ] セキュリティ検証を維持した
- [ ] 既存テストを削除していない
- [ ] Ruffが成功した
- [ ] mypyが成功した
- [ ] 関連テストが成功した
- [ ] Backend全体テストが成功した
- [ ] Coverageが80%以上
- [ ] Copilotが変更内容と残るリスクを報告した

## 13. 推奨実施順

```text
1. 全機能とセキュリティ対応を完了
2. ドキュメントを現行仕様へ同期
3. `Mode=coverage`で最終ベースライン取得
4. FileServiceのファイル名検証を切り出す
5. 残りの入力Validatorを整理
6. Checksumを純粋関数化
7. LocalFileStorageを切り出す
8. FileServiceをOrchestratorへ縮小
9. ReportPdfServiceの純粋処理を段階的に切り出す
10. ReportNodesの変換ロジックを必要な場合のみ切り出す
11. 各タスク後に全品質検証
12. 最後にセキュリティ、仕様、文書の整合を再確認
13. Git操作は組織のセキュリティ方針に従い最終段階で実施
```

## 14. 最終完了条件

リファクタリング全体は、次を満たした場合に完了とする。

- 機能仕様に変更がない
- API契約に変更がない、または承認済みの仕様変更として記録されている
- DB整合性とTransaction境界が維持されている
- セキュリティ要件が維持または強化されている
- Ruff成功
- mypy成功
- 全テスト成功
- Coverage Gate達成
- 主要責務と依存方向が文書化されている
- 不要な抽象化や循環依存がない
- 関連ドキュメントが実装と一致している
- 機密情報が成果物に含まれていない
