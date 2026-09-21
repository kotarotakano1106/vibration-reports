# GitHub Copilot Instructions

## 1. この文書の目的

この文書は、振動AI日報生成アプリでGitHub Copilotを利用する際に、すべての作業で共通して守るルールを定義する。

詳細な作業手順は `.github/skills/`、正式な要件・設計・仕様は `docs/` を参照すること。
この文書へ機能ごとの詳細仕様を重複して記載しない。

## 2. プロジェクト概要

- プロジェクト名: 振動AI日報生成アプリ
- リポジトリ名: `vibration-reports`
- 開発区分: PoC
- 主な目的:
  - Raspberry Piで取得した振動データをCSVとして取り込む
  - Pythonで入力検証、統計計算、異常候補抽出を行う
  - Azure OpenAIで分析文章を生成する
  - 分析結果と日報をPostgreSQLへ保存する
  - 日報をPDFとして出力する
  - pgvectorとRAGを使用して過去レポートを検索する
  - 過去レポートを根拠にAIチャットで回答する

## 3. システム化範囲

本PoCの対象範囲は次のとおりとする。

- CSVファイルの手動アップロード
- CSVファイルの入力検証
- 振動値の統計計算と異常候補抽出
- Azure OpenAIによる分析文章生成
- レポート生成、保存、一覧表示、詳細表示
- 振動推移グラフ表示
- PDF生成とダウンロード
- Embedding生成とpgvectorへの保存
- 過去レポートの類似検索
- RAGチャット
- ログインと認証・認可は設計対象だが、現行PoCには開発用ユーザー固定などの暫定実装が残っている

## 4. システム化対象外

- Raspberry Piからのリアルタイム送信
- Raspberry Piとの常時接続
- センサー機器の遠隔制御
- ストリーミングデータのリアルタイム分析
- CSV内の全測定値のDB保存
- 本番向けの高可用性・冗長化構成
- マイクロサービス構成
- 複数拠点への展開
- 外部監視サービスとの連携
- チャット履歴のDB保存
- LangGraphチェックポイントの永続化

対象範囲を変更する場合は、実装前に関連する要件、受入基準、設計文書を更新すること。

## 5. 使用技術

### フロントエンド

- TypeScript
- React
- Next.js App Router
- Material UI
- Emotion
- TanStack Query
- React Hook Form
- Zod
- Recharts
- dayjs

### バックエンド

- Python
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy
- Alembic
- Psycopg 3
- pandas
- NumPy
- LangGraph
- OpenAI SDK / Azure OpenAI
- ReportLab
- Matplotlib

### データベース

- PostgreSQL
- pgvector

### テスト・開発

- pytest
- Ruff
- mypy
- Docker / Docker Compose
- npm / Next.js build

## 6. 正式な参照元

作業前に、依頼内容に関連する文書を確認すること。

- `docs/requirements.md`: 機能要件・非機能要件
- `docs/acceptance-criteria.md`: 完了判定条件
- `docs/use-cases.md`: 利用者操作と処理フロー
- `docs/architecture.md`: システム構成と責務分担
- `docs/backend-class-design.md`: バックエンドのクラス設計
- `docs/api-spec.md`: APIの入出力とエラー仕様
- `docs/database.md`: DBテーブル、制約、関連
- `docs/pdf-report-design.md`: PDF帳票仕様
- `docs/coding-rules.md`: コーディング規約
- `docs/test-cases.md`: テストケース
- `docs/testing-strategy.md`: テスト全体の方針、レベル、リスク、開始・終了条件
- `docs/security-requirements.md`: 認証、認可、入力、秘密情報、AI・RAGのセキュリティ要件
- `docs/concurrency-and-transaction.md`: 並行処理、冪等性、排他、状態遷移、トランザクション
- `docs/operations-requirements.md`: ログ、監視、SLO、バックアップ、復旧、デプロイ
- `docs/standards-and-tailoring.md`: 標準の版、適用範囲、適用除外、証跡

優先順位は次のとおりとする。

1. 利用者が今回明示した要求
2. `docs/requirements.md` と `docs/acceptance-criteria.md`
3. `docs/architecture.md`、API・DB・PDF等の詳細設計
4. 既存の動作コードと自動テスト
5. `.github/skills/` の作業手順
6. 本文書

文書と実装が矛盾する場合は、どちらかを推測で正とせず、差異、影響、推奨対応を明示すること。

## 7. Skillの使い分け

作業内容に応じて、該当する `.github/skills/*/SKILL.md` を確認すること。

- `coding`: 新規実装、機能追加、バグ修正、リファクタリング
- `requirements`: 要求整理、要件定義、受入基準、仕様変更
- `review`: コード、設計、テストのレビュー
- `testing`: テスト設計、実装、実行
- `security`: セキュリティ確認
- フロントエンドデザイン用Skill: MUIテーマ、画面レイアウト、アクセシビリティ、視覚的一貫性

Skillの名称と実ディレクトリ名が異なる場合は、実際に存在するファイルを確認し、不明なSkillを推測で使用しないこと。

## 7.1 変更内容に応じた追加文書

- 並行処理、重複要求、再送、状態遷移、Transactionを変更する場合は `docs/concurrency-and-transaction.md` を確認する。
- Log、Metric、Alert、Backup、Recovery、Deploymentを変更する場合は `docs/operations-requirements.md` を確認する。
- Test方針を変更する場合は `docs/testing-strategy.md` を確認する。
- Security要件を変更する場合は `docs/security-requirements.md` を確認する。
- 採用標準、版、適用除外を変更する場合は `docs/standards-and-tailoring.md` を確認する。

## 8. フロントエンド設計ルール

- ソースコードは `frontend/src/` 配下へ配置する
- URLとレイアウトの入口は `frontend/src/app/` で管理する
- ログイン前は `(auth)`、認証後トップ画面は現行のRoute Groupを確認して使用する
- 機能固有コードは `frontend/src/features/` 配下へ配置する
- 複数機能で共有するUIは `frontend/src/components/` 配下へ配置する
- MUIテーマとデザイントークンは `frontend/src/theme/` 配下で管理する
- `page.tsx` へ業務ロジックやAPI通信を集中させない
- Server Componentを基本とし、利用者操作やブラウザ状態が必要な範囲のみClient Componentにする
- 不要な `"use client"` を付けない
- 表示コンポーネントからFastAPIを直接呼び出さない
- API通信はFeatureごとの `api/` モジュールへ集約する
- サーバー状態はTanStack Queryで管理する
- CSVアップロードとレポート詳細はDialog、AIチャットは右側Drawerとして提供する
- Web画面用グラフとPDF用グラフ生成の責務を混在させない
- ローディング、空データ、成功、エラーの状態を実装する
- 色だけで状態を伝えず、文字やアイコンも併用する
- フォーム、ボタン、Drawer、Dialog、表はアクセシビリティを考慮する

## 9. バックエンド設計ルール

バックエンドは次の責務分担を維持する。

1. API層: HTTP入出力、Schema検証、Service呼び出し
2. Service層: 業務ロジックとユースケース制御
3. Workflow層: LangGraphの順序、分岐、状態遷移
4. Repository層: SQLAlchemy、PostgreSQL、pgvectorへのアクセス
5. Database層: Engine、Session、トランザクション管理

以下を禁止する。

- API層へのSQL、ORM操作、AI接続、PDF生成ロジックの直接記載
- Service層またはWorkflow層へのSQLの直接記載
- Repository層へのHTTP処理や業務判断の記載
- LangGraph Nodeへの大規模な業務ロジックの記載
- DBモデルをAPIレスポンスとして直接返すこと
- AI API呼び出し中にDBトランザクションを長時間保持すること

既存のディレクトリ構成と依存方向を、理由なく変更しないこと。

## 10. CSV・振動分析ルール

- 拡張子、ファイル名、MIMEタイプ、サイズ、文字コードを検証する
- 空ファイル、必須列不足、日時不正、数値不正、欠損値、行数上限を検証する
- 元ファイル名を保存ファイル名として直接使用しない
- パストラバーサルを防止する
- SHA-256チェックサムで重複を確認する
- CSV全測定値はDBへ保存せず、安全な保存先にCSV実ファイルとして保持する
- 数値集計はAIではなくPythonで実行する
- AIへCSV全件をそのまま送信しない
- 閾値、単位、最大サイズ、最大行数などが未確定の場合は勝手に確定しない

## 11. AI・RAGルール

- Azure OpenAIのAPIキー、接続情報、デプロイ名をソースへ直接記載しない
- AI入力は統計情報、異常候補、必要最小限のコンテキストに限定する
- AI出力を確定的な設備診断として扱わない
- AI出力は可能な範囲でPydantic Schemaまたは明示的な検証処理を使用する
- プロンプトは原則として `backend/src/prompts/` へ集約する
- 既存コード内に直接記載されたプロンプトを変更する場合は、外部ファイル化の影響を確認する
- Embedding次元数をDBの `vector` 定義と一致させる
- RAGチャンクには元レポートID、設備ID、測定日、チャンク種別などの追跡情報を保持する
- 検索件数を制限する
- 根拠が不足する場合は「確認できない」と回答させる
- 検索結果にない数値、原因、点検結果を推測させない
- プロンプトインジェクションを考慮する
- 認可実装後は、検索時にも利用者のアクセス範囲を適用する

## 12. セキュリティルール

- `.env`、APIキー、パスワード、アクセストークン、接続文字列をコミットしない
- `.env.example` にはダミー値または変数名だけを記載する
- パスワードを平文で保存しない
- 外部入力を必ず検証する
- SQL文字列を入力値と連結しない
- ORMまたはパラメータ化クエリを使用する
- ファイル名から保存先パスを直接生成しない
- 内部パス、SQL、スタックトレース、秘密情報をAPIレスポンスへ返さない
- 秘密情報、CSV全内容、AIへの完全な入力、個人情報をログへ出力しない
- CORS許可元を環境ごとに必要最小限へ制限する
- 認証が必要なAPIへ認証・認可を実装する
- `dev-user` 固定処理はPoCの暫定実装として扱い、本番相当環境へそのまま展開しない
- ファイル削除、Migration、DB更新、デプロイなどの破壊的操作は、対象と影響を明示してから行う

## 13. ログ・エラー処理ルール

- エラーを握りつぶさない
- 入力、認証、認可、ファイル、DB、Azure OpenAI、Embedding、RAG、PDF、想定外エラーを区別する
- 利用者向けメッセージと内部ログを分離する
- ログには処理を追跡できる識別子を含める
- 警告、エラー、リトライ、最終失敗を適切なログレベルで記録する
- APIキー、トークン、パスワード、接続文字列、CSV全文をログへ出力しない
- リトライには上限、タイムアウト、待機方針を設定する
- DB更新失敗時は必ずロールバックする

## 14. 実装前の必須手順

コードを変更する前に、次を行うこと。

1. 利用者の依頼内容を要約する
2. 関連する要件IDと受入基準IDを確認する
3. 関連する `docs/` 文書を確認する
4. 関連する既存コードとテストを確認する
5. 再利用できる関数、クラス、コンポーネントを確認する
6. 変更対象ファイルと影響範囲を整理する
7. API、DB、画面、AI、RAG、PDF、テストへの影響を確認する
8. 不明点、仮定、未確定事項を明示する
9. 必要最小限の実装計画を作成する

単純な修正では説明を簡潔にしてよいが、確認を省略してはならない。

## 15. 実装時の必須ルール

- 要件にない機能を勝手に追加しない
- 不明な仕様を推測だけで実装しない
- 既存アーキテクチャを無断で変更しない
- 既存の命名規則とコードスタイルを維持する
- 必要最小限のファイルだけを変更する
- 関係のない整形や一括置換を行わない
- 同じ責務のコードを重複して追加しない
- エラー処理とログを省略しない
- 新規または変更した処理に対応するテストを追加・更新する
- API変更時は `docs/api-spec.md` を更新する
- DB変更時は `docs/database.md` とAlembic Migrationを更新する
- 要件変更時は `docs/requirements.md` と `docs/acceptance-criteria.md` を更新する
- アーキテクチャ変更時は `docs/architecture.md` を更新する
- テスト変更時は `docs/test-cases.md` を更新する
- PDF仕様変更時は `docs/pdf-report-design.md` を更新する
- 自動生成ファイル、キャッシュ、バックアップ、一時ファイルを実装成果物へ混在させない

## 16. テスト・確認の基本方針

変更内容に応じて、正常系、異常系、境界値、回帰確認を行うこと。
外部AI APIを通常の自動テストから直接呼び出さず、原則としてモック化する。

### バックエンド

プロジェクトルートから実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest .\backend\tests
```

必要に応じて構文確認、Ruff、mypyを実行する。

```powershell
.\.venv\Scripts\python.exe -m compileall .\backend\src
.\.venv\Scripts\python.exe -m ruff check .\backend
.\.venv\Scripts\python.exe -m mypy .\backend\src
```

会社PCのPowerShell実行ポリシーによりActivate.ps1が使用できない場合は、仮想環境のPythonを直接実行する。

### フロントエンド

`frontend` ディレクトリで実行する。

```powershell
npm.cmd run build
```

利用可能な場合はLintと自動テストも実行する。

```powershell
npm.cmd run lint
npm.cmd test
```

`package.json` に存在しないスクリプトを推測で実行しないこと。

### DB変更

- Migrationのupgradeとdowngradeを確認する
- モデル定義、Migration、`docs/database.md` の一致を確認する
- 既存データへの影響を確認する
- 失敗時のロールバックを確認する

## 17. ファイル操作ルール

- 既存ファイルを上書きする前に対象パスを確認する
- 一括更新スクリプトは、対象マーカーが見つからない場合に処理を中止する
- ファイル削除前に、参照有無と削除理由を確認する
- バックアップを作成する場合は、プロジェクト本体の外へ配置する
- `.venv`、`node_modules`、`.next`、`__pycache__`、`.pytest_cache`、ログ、生成PDF、アップロードCSVなどを共有用ソースバンドルへ含めない
- `source_bundle.txt`、`project_structure.txt`、作業用ZIPなどは一時成果物として扱い、Gitへコミットしない
- 秘密情報を含む可能性のあるファイルを外部サービスへアップロードしない

## 18. 実装後の報告形式

実装後は、以下の形式で簡潔かつ具体的に報告すること。

### 実装概要

- 対象機能
- 関連要件ID・受入基準ID
- 実装した内容
- 実装した理由

### 変更ファイル

- 追加
- 更新
- 削除

### 影響範囲

- フロントエンド
- バックエンド
- API
- DB
- AI・RAG
- PDF
- ドキュメント

### テスト結果

- 実行したコマンド
- 成功したテスト
- 失敗したテスト
- 未実施のテストと理由
- 手動確認内容

### 注意事項

- 仮定
- 未対応事項
- 既知の制限
- 今後必要な作業

## 19. 禁止事項

- 秘密情報をコード、文書、ログ、テストデータへ記載すること
- 実行していないテストを成功と報告すること
- 実際に確認していないファイル内容を推測で断定すること
- 要件・設計・既存コードの矛盾を黙って修正すること
- 利用者が依頼していない大規模リファクタリングを行うこと
- 認証・認可が未実装の状態を本番対応済みとして扱うこと
- AIの分析結果だけで設備の安全性や保守判断を確定すること
- 破壊的コマンドを対象確認なしで提示または実行すること

## 20. 現行PoCで特に注意する事項

- 認証方式は最終確定しておらず、一部APIに開発用ユーザー固定処理がある
- CSV保存ディレクトリは設計書と実装の一致を確認してから変更する
- RAGチャンク構成は設計書と実装に差異がある可能性がある
- Health APIはルート側とAPI v1側の重複・未登録状態を確認する
- 分析用プロンプトにはService内へ直接記載されたものがあるため、外部ファイル化は影響確認後に行う
- Embedding次元数は現在のDB定義とAzure OpenAIの実際の出力を必ず一致させる
- Azureデプロイ前に、認証、CORS、環境変数、永続ストレージ、ログ、ヘルスチェックを再確認する

上記の注意事項は暫定状態を示す。解消後は、関連する `docs/` と本節を更新すること。
