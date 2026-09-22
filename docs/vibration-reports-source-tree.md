# vibration-reports ソースツリー完全版

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 作成日: 2026-09-22
- 表記: `ファイル名 / 簡単要約説明コメント`
- 基準: `project-file-manifest.csv`および照合済みソース構成

## ソースツリー

```text
vibration-reports/                                      / プロジェクトルート
├─ .env.example                                         / Backend環境変数の共有用テンプレート。秘密値は含めない
├─ .gitignore                                           / Git管理から秘密情報・依存関係・Cache・生成物を除外
├─ alembic.ini                                          / Alembicの接続先・Migration配置・Logging設定
├─ docker-compose.yml                                   / PostgreSQL・pgvector等のローカル実行環境を定義
├─ ruff.toml                                            / BackendのRuff Lint・Formatルール
│
├─ .github/                                             / GitHub向け補助設定
│  ├─ copilot-instructions.md                           / GitHub Copilot向けプロジェクト指示
│  └─ skills/                                           / 開発支援用Skill定義。アプリ実行コードではない
│     ├─ coding/SKILL.md                                / Coding支援ルール
│     ├─ deployment/SKILL.md                            / Deployment支援ルール
│     ├─ documentation/SKILL.md                         / Documentation支援ルール
│     ├─ requirements/SKILL.md                          / Requirements支援ルール
│     ├─ review/SKILL.md                                / Review支援ルール
│     ├─ security/SKILL.md                              / Security支援ルール
│     ├─ testing/SKILL.md                               / Testing支援ルール
│     └─ raspi-ai-mui-design/                           / MUI画面設計の補助Skillと参照資料
│        ├─ SKILL.md                                    / MUI画面設計のSkill定義
│        └─ references/                                 / Accessibility・Component・Layout等の補助資料
│           ├─ accessibility.md                         / Accessibility設計ルール
│           ├─ component-rules.md                       / Component設計ルール
│           ├─ design-system.md                         / Design System定義
│           └─ layout-spec.md                           / Layout仕様
│
├─ backend/                                             / FastAPI・DB・AI・RAG・PDFを担当するBackend
│  ├─ __init__.py                                       / backend Package識別
│  ├─ requirements.txt                                 / Backend実行依存関係
│  ├─ requirements-dev.txt                             / pytest・Ruff・mypy等の開発・テスト依存関係
│  │
│  ├─ migrations/                                      / Alembic Database Migration
│  │  ├─ README                                        / Migrationディレクトリの説明
│  │  ├─ env.py                                        / Alembic実行時のDB接続・Model Metadata読込
│  │  ├─ script.py.mako                                / Migration File生成Template
│  │  └─ versions/                                     / Migration Revision
│  │     └─ 15a61de1c13e_create_initial_four_tables.py / User・UploadedFile・Report・ReportChunkの初期Schema
│  │
│  ├─ scripts/                                         / Backend機能の手動疎通・個別確認Script
│  │  ├─ __init__.py                                   / scripts Package識別
│  │  ├─ check_azure_openai.py                         / Azure OpenAI接続と設定値の疎通確認
│  │  ├─ check_azure_openai_service.py                 / AzureOpenAIServiceの文章生成確認
│  │  ├─ check_embedding_only.py                       / Embedding生成のみを確認
│  │  ├─ check_csv_service.py                          / CsvServiceの読込・Validation確認
│  │  ├─ check_file_service.py                         / FileServiceの保存・Metadata登録確認
│  │  ├─ check_report_repository.py                    / ReportRepositoryのCRUD確認
│  │  ├─ check_report_service.py                       / ReportServiceとAnalysis Graphの疎通確認
│  │  ├─ check_uploaded_file_repository.py             / UploadedFileRepositoryのCRUD・Checksum検索確認
│  │  ├─ check_user_repository.py                      / UserRepositoryのCRUD確認
│  │  ├─ check_vector_repository.py                    / pgvectorによる類似Chunk検索確認
│  │  └─ check_vibration_analysis_service.py           / 統計分析・異常判定の手動確認
│  │
│  ├─ src/                                             / Backend Application本体
│  │  ├─ __init__.py                                   / src Package識別
│  │  ├─ main.py                                       / FastAPI生成・CORS・Router登録・Health Endpoint
│  │  │
│  │  ├─ api/                                          / HTTP Request・Responseを扱うAPI層
│  │  │  ├─ __init__.py                                / api Package識別
│  │  │  └─ v1/                                        / Version 1 API
│  │  │     ├─ __init__.py                             / v1 Package識別
│  │  │     ├─ router.py                               / v1 Endpointを集約してFastAPIへ登録
│  │  │     ├─ files.py                                / CSV Upload APIとUploadedFile登録
│  │  │     ├─ measurements.py                         / 保存CSVを読み込み時系列測定値を返すAPI
│  │  │     ├─ reports.py                              / Report一覧・AI生成・PDF Download API
│  │  │     ├─ search.py                               / Embedding・pgvectorによるRAG検索API
│  │  │     └─ chat.py                                 / 過去Reportを根拠に回答するRAG Chat API
│  │  │
│  │  ├─ core/                                         / Application共通設定・Security補助
│  │  │  ├─ __init__.py                                / core Package識別
│  │  │  ├─ config.py                                  / 環境変数を読込みApplication設定を提供
│  │  │  └─ security.py                                / Password Hash等のSecurity補助処理
│  │  │
│  │  ├─ db/                                           / SQLAlchemy接続とSession管理
│  │  │  ├─ __init__.py                                / db Package識別
│  │  │  ├─ base.py                                    / Declarative BaseとModel Metadataの集約
│  │  │  ├─ session.py                                 / Engine・Session Factoryの生成
│  │  │  └─ dependencies.py                            / FastAPIへDB Sessionを注入するDependency
│  │  │
│  │  ├─ exceptions/                                   / 業務例外
│  │  │  ├─ __init__.py                                / exceptions Package識別
│  │  │  └─ report_exceptions.py                       / Report重複・生成失敗等の例外定義
│  │  │
│  │  ├─ models/                                       / SQLAlchemy Database Model
│  │  │  ├─ __init__.py                                / Modelを集約してMigrationから参照可能にする
│  │  │  ├─ user.py                                    / User情報と固定開発Userの永続化Model
│  │  │  ├─ uploaded_file.py                           / Upload CSVのMetadata・Path・Status Model
│  │  │  ├─ report.py                                  / AI Report・分析結果・PDF情報のModel
│  │  │  └─ report_chunk.py                            / RAG検索用Chunk・Metadata・Embedding Model
│  │  │
│  │  ├─ schemas/                                      / Pydantic API入出力・Workflowデータ型
│  │  │  ├─ __init__.py                                / schemas Package識別
│  │  │  ├─ file_schema.py                             / CSV Upload ResponseとUploadedFile Schema
│  │  │  ├─ measurement_schema.py                      / 時系列測定値・異常判定Response Schema
│  │  │  ├─ report_schema.py                           / Report生成・一覧・分析結果Schema
│  │  │  ├─ search_schema.py                           / RAG検索Request・Result Schema
│  │  │  └─ chat_schema.py                             / Chat Request・Answer・Source Schema
│  │  │
│  │  ├─ repositories/                                 / DBアクセスを集約するRepository層
│  │  │  ├─ __init__.py                                / repositories Package識別
│  │  │  ├─ user_repository.py                         / Userの作成・取得・検索
│  │  │  ├─ uploaded_file_repository.py                / Upload Metadata登録・Checksum検索・Status更新
│  │  │  ├─ report_repository.py                       / Report CRUD・一覧・PDF情報更新
│  │  │  └─ vector_repository.py                       / ReportChunk保存とpgvector類似検索
│  │  │
│  │  ├─ services/                                     / 業務ロジックと外部Service連携
│  │  │  ├─ __init__.py                                / services Package識別
│  │  │  ├─ csv_service.py                             / 保存CSVの読込・必須列・日時・数値Validation
│  │  │  ├─ file_service.py                            / CSV保存・Checksum・Metadata登録・失敗時Cleanup
│  │  │  ├─ vibration_analysis_service.py              / 統計計算・閾値判定・異常候補抽出
│  │  │  ├─ azure_openai_service.py                    / Azure OpenAI文章生成・Embedding生成
│  │  │  ├─ report_service.py                          / Analysis Graphを起動しReport生成を制御
│  │  │  ├─ rag_search_service.py                      / 質問Embedding・類似Chunk検索・Score変換
│  │  │  └─ report_pdf_service.py                      / 日本語PDF・表・振動Chartを生成
│  │  │
│  │  ├─ prompts/                                      / LLM Prompt定義
│  │  │  ├─ __init__.py                                / prompts Package識別
│  │  │  └─ rag_chat_prompt.py                         / 根拠付きChat回答用Prompt
│  │  │
│  │  └─ workflows/                                    / LangGraphの処理順・Node・State管理
│  │     ├─ __init__.py                                / workflows Package識別
│  │     ├─ graphs/                                     / Node接続・分岐・終了条件
│  │     │  ├─ __init__.py                             / graphs Package識別
│  │     │  ├─ analysis_graph.py                       / CSV確認からReport・Chunk保存までのGraph
│  │     │  └─ rag_chat_graph.py                       / RAG検索からAnswer・Source作成までのGraph
│  │     ├─ nodes/                                      / Graphで実行する処理Node
│  │     │  ├─ __init__.py                             / nodes Package識別
│  │     │  ├─ analysis_nodes.py                       / Upload確認・CSV読込・統計分析・AI分析
│  │     │  ├─ report_nodes.py                         / Report・Chunk・Embedding保存とStatus更新
│  │     │  └─ rag_nodes.py                            / Chunk検索・Context生成・Answer・Source作成
│  │     └─ states/                                     / Graph内で受け渡す状態型
│  │        ├─ __init__.py                             / states Package識別
│  │        ├─ analysis_state.py                       / Analysis Input・途中結果・Output State
│  │        └─ chat_state.py                           / Chat Input・検索結果・Answer State
│  │
│  └─ tests/                                           / Backend自動テスト
│     ├─ conftest.py                                   / Test DB・Session・Client・Fixture共通設定
│     ├─ api/                                          / FastAPI Endpoint Test
│     │  ├─ test_health_api.py                         / Health EndpointのStatus・Response確認
│     │  ├─ test_files_api.py                          / CSV Uploadの正常・Validation・重複確認
│     │  ├─ test_measurements_api.py                   / 保存CSVからの測定値取得・異常判定確認
│     │  ├─ test_reports_api.py                        / Report一覧取得の正常・空・DB Error確認
│     │  ├─ test_report_generation_api.py              / Report生成・重複・AI失敗確認
│     │  ├─ test_report_pdf_api.py                     / PDF Download・404・生成失敗確認
│     │  ├─ test_search_api.py                         / RAG検索・Filter・Limit・Error確認
│     │  └─ test_chat_api.py                           / RAG Chat回答・Source・Error確認
│     ├─ integration/                                  / DB・Repository・Service結合Test
│     │  ├─ test_database_connection.py                / Test DB接続と基本Query確認
│     │  ├─ repositories/
│     │  │  ├─ test_user_repository.py                 / User Repositoryの実DB CRUD確認
│     │  │  ├─ test_uploaded_file_repository.py        / UploadedFile登録・検索・Status確認
│     │  │  ├─ test_report_repository.py               / Report CRUD・一覧・PDF更新確認
│     │  │  └─ test_vector_repository.py               / ReportChunk保存・pgvector類似検索確認
│     │  └─ services/
│     │     ├─ test_file_service_integration.py         / File保存・DB登録・失敗時Cleanup確認
│     │     └─ test_report_service_integration.py       / Analysis GraphとReport保存の結合確認
│     └─ unit/                                          / 外部依存をMockした単体Test
│        ├─ core/
│        │  └─ test_security.py                         / Password Hash・照合等のSecurity補助確認
│        ├─ services/
│        │  ├─ test_azure_openai_service.py             / AI・Embeddingの正常・Timeout・Error確認
│        │  ├─ test_csv_service.py                      / CSV読込・列・日時・数値Validation確認
│        │  ├─ test_file_service.py                     / FileServiceの検証・Checksum等を確認
│        │  ├─ test_file_service_save.py                / File保存・Rollback・Cleanup確認
│        │  ├─ test_vibration_analysis_service.py       / 統計値・閾値境界・異常候補確認
│        │  ├─ test_rag_search_service.py               / Similarity変換・検索結果整形確認
│        │  └─ test_report_pdf_service.py               / 日本語PDF・長文・Chart・Error確認
│        └─ workflows/
│           ├─ test_analysis_nodes.py                   / Analysis Nodeの状態遷移・失敗確認
│           ├─ test_report_nodes.py                     / Report・Chunk・Embedding Node確認
│           └─ test_rag_chat_workflow.py                / RAG Chat Graph・Source・根拠なし回答確認
│
├─ frontend/                                            / Next.js・React・MUI Frontend
│  ├─ .env.example                                      / Frontend環境変数の共有用テンプレート
│  ├─ .gitignore                                        / .next・coverage等のFrontend生成物を除外
│  ├─ AGENTS.md                                         / 補助開発環境向け指示。アプリ実装外
│  ├─ CLAUDE.md                                         / 別支援環境向け補助設定。アプリ実装外
│  ├─ dashboard_filter_additional_check.txt             / Dashboard Filterの追加確認メモ
│  ├─ package.json                                      / npm Script・実行依存・開発依存定義
│  ├─ package-lock.json                                 / npm依存Versionの固定
│  ├─ next.config.ts                                    / Next.js Build設定
│  ├─ next-env.d.ts                                     / Next.js TypeScript型宣言。自動生成
│  ├─ tsconfig.json                                     / TypeScript CompilerとPath Alias設定
│  ├─ eslint.config.mjs                                 / Next.js・TypeScript ESLintとCoverage除外
│  ├─ postcss.config.mjs                                / PostCSS Plugin設定
│  ├─ vitest.config.mts                                 / Vitest・jsdom・V8 Coverage・Gate設定
│  │
│  ├─ src/                                              / Frontend Application本体
│  │  ├─ app/                                           / Next.js App Router
│  │  │  ├─ layout.tsx                                  / Root Layout・ThemeRegistry・全体Metadata
│  │  │  └─ (dashboard)/                                / Dashboard Route Group
│  │  │     └─ page.tsx                                 / DashboardContentを表示するPage
│  │  │
│  │  ├─ components/                                    / 複数Featureで共有するLayout Component
│  │  │  └─ layout/
│  │  │     ├─ AppHeader.tsx                            / Application上部Header
│  │  │     └─ AppSidebar.tsx                           / Side Navigation
│  │  │
│  │  ├─ features/                                      / 機能別Vertical Slice
│  │  │  ├─ analysis/                                   / CSV Upload・分析開始機能
│  │  │  │  ├─ api/
│  │  │  │  │  └─ upload-csv.ts                        / CSVとMetadataをFormDataでBackendへ送信
│  │  │  │  ├─ hooks/
│  │  │  │  │  └─ useCsvAnalysis.ts                    / UploadからReport生成までの状態遷移を管理
│  │  │  │  ├─ types/
│  │  │  │  │  └─ analysis.ts                          / CSV Upload Input・Response・Status型
│  │  │  │  └─ components/
│  │  │  │     ├─ CsvUploadModal.tsx                   / CSV・条件入力と分析実行Dialog
│  │  │  │     ├─ CsvDropzone.tsx                      / CSV File選択UI
│  │  │  │     ├─ CsvFilePreview.tsx                   / 選択File名とSize表示
│  │  │  │     └─ AnalysisProgress.tsx                 / 分析中の進捗表示
│  │  │  │
│  │  │  ├─ chat/                                       / RAG Chat機能
│  │  │  │  ├─ api/
│  │  │  │  │  └─ chat.ts                              / Chat RequestをBackendへ送信
│  │  │  │  ├─ hooks/
│  │  │  │  │  └─ useRagChat.ts                       / Pending・Error・Abort・Reset管理
│  │  │  │  ├─ types/
│  │  │  │  │  └─ chat.ts                             / Chat Request・Response・Message・Source型
│  │  │  │  └─ components/
│  │  │  │     ├─ AiChatDrawer.tsx                     / Chat全体・Message更新・Drawer制御
│  │  │  │     ├─ ChatInput.tsx                        / 質問入力・Trim・Enter送信・Loading表示
│  │  │  │     ├─ ChatMessage.tsx                      / User・AI MessageとSource Chip表示
│  │  │  │     └─ ChatMessageList.tsx                  / Message一覧・空状態・回答待ち表示
│  │  │  │
│  │  │  ├─ dashboard/                                  / Dashboard・Measurement表示機能
│  │  │  │  ├─ api/
│  │  │  │  │  └─ get-measurements.ts                 / File IDと閾値で時系列測定値を取得
│  │  │  │  ├─ hooks/
│  │  │  │  │  └─ useMeasurements.ts                  / Measurement取得状態・Error・多重実行防止
│  │  │  │  ├─ types/
│  │  │  │  │  └─ measurement.ts                      / Measurement Point・Response・Input型
│  │  │  │  └─ components/
│  │  │  │     ├─ DashboardContent.tsx                 / Report・Measurement・Modal・Chatを統合
│  │  │  │     ├─ DashboardHeader.tsx                  / Dashboard見出し・CSV分析開始操作
│  │  │  │     ├─ MonitoringSummary.tsx                / 統計値・状態・異常件数のSummary
│  │  │  │     └─ VibrationChart.tsx                   / 時系列振動値・閾値・異常点Chart
│  │  │  │
│  │  │  ├─ health/                                     / Backend接続状態表示機能
│  │  │  │  ├─ services/
│  │  │  │  │  └─ get-health.ts                       / Backend Health Endpointを取得
│  │  │  │  ├─ types/
│  │  │  │  │  └─ health.ts                           / Health Response型
│  │  │  │  └─ components/
│  │  │  │     └─ health-status.tsx                    / Loading・接続成功・接続失敗を表示
│  │  │  │
│  │  │  └─ reports/                                    / Report一覧・詳細・PDF機能
│  │  │     ├─ api/
│  │  │     │  ├─ get-reports.ts                       / Report一覧をBackendから取得
│  │  │     │  ├─ generate-report.ts                   / File ID・閾値・天候でAI Report生成
│  │  │     │  └─ download-report-pdf.ts               / PDF Blob取得・Browser Download開始
│  │  │     ├─ types/
│  │  │     │  └─ report.ts                            / Report・Analysis・Generation型
│  │  │     └─ components/
│  │  │        ├─ ReportList.tsx                       / Report Table・検索欄・Pagination
│  │  │        ├─ ReportListItem.tsx                   / Report 1行・Status・選択操作
│  │  │        ├─ ReportDetailModal.tsx                / Report詳細・分析結果・推奨対応Dialog
│  │  │        └─ PdfDownloadButton.tsx                / PDF Download状態・Error表示
│  │  │
│  │  ├─ lib/                                           / 複数Feature共通の基盤処理
│  │  │  ├─ api/
│  │  │  │  ├─ client.ts                               / URL生成・HTTP送信・Response・Error処理
│  │  │  │  └─ paths.ts                                / API Endpoint Pathを一元定義
│  │  │  └─ errors/
│  │  │     └─ api-error.ts                            / HTTP・Network Errorの利用者向け変換
│  │  │
│  │  └─ theme/                                         / MUI Theme・Token・型拡張
│  │     ├─ ThemeRegistry.tsx                           / MUI ThemeProviderをApplicationへ適用
│  │     ├─ theme.ts                                    / Palette・Typography・Component Theme
│  │     ├─ tokens.ts                                   / Gradient等のDesign Token
│  │     └─ mui.d.ts                                    / MUI Theme型の拡張
│  │
│  └─ tests/                                            / Frontend Vitest・Testing Library Test
│     ├─ setup.ts                                       / jest-dom等の共通Test初期化
│     ├─ smoke.test.ts                                  / Vitest環境の最小Smoke Test
│     └─ unit/
│        ├─ lib/
│        │  ├─ api/
│        │  │  ├─ client.test.ts                        / apiRequestの正常・HTTP・Network Error確認
│        │  │  └─ paths.test.ts                         / API Path生成確認
│        │  └─ errors/
│        │     └─ api-error.test.ts                     / ApiError Factory・Message変換確認
│        └─ features/
│           ├─ analysis/
│           │  ├─ upload-csv.test.ts                    / Validation・FormData・Error伝播確認
│           │  ├─ use-csv-analysis.test.ts              / Upload・生成状態遷移・多重実行防止
│           │  ├─ analysis-progress.test.tsx            / 進捗表示・非表示確認
│           │  ├─ csv-dropzone.test.tsx                 / File選択・accept・未選択確認
│           │  └─ csv-file-preview.test.tsx             / File名・KB切上げ表示確認
│           ├─ chat/
│           │  ├─ chat.test.ts                          / Chat API Request・Signal・Error確認
│           │  ├─ use-rag-chat.test.ts                  / Pending・Abort・Error・Reset確認
│           │  ├─ chat-input.test.tsx                   / 入力・Trim・Enter・Disabled・a11y確認
│           │  ├─ chat-message.test.tsx                 / Message・Source・Label・Similarity確認
│           │  └─ chat-message-list.test.tsx            / Empty・Message一覧・Pending確認
│           ├─ dashboard/
│           │  ├─ get-measurements.test.ts              / ID・閾値・Signal・Validation確認
│           │  └─ use-measurements.test.ts              / Loading・Success・Error・Reset確認
│           ├─ health/
│           │  ├─ get-health.test.ts                    / Health通信・Response・Error確認
│           │  └─ health-status.test.tsx                / Loading・成功・Error・Fallback確認
│           └─ reports/
│              ├─ get-reports.test.ts                   / Report一覧Response・Error確認
│              ├─ generate-report.test.ts               / POST Body・天候変換・Validation確認
│              ├─ download-report-pdf.test.ts            / PDF Blob・Filename・HTTP Error確認
│              ├─ pdf-download-button.test.tsx          / Pending・Download・Error表示確認
│              ├─ report-list-item.test.tsx             / Report行・Fallback・選択Callback確認
│              └─ report-list.test.tsx                  / Table・空配列・Pagination・行選択確認
│
├─ data/                                                / Application実行・学習用データ
│  └─ uploads/                                          / Upload済みCSVの保存先
│     └─ *.csv                                          / CSV分析・Report生成に使用するダミー振動測定データ
│
├─ docs/                                                / 要件・設計・テスト・運用・学習資料
│  ├─ requirements.md                                   / 機能・非機能要件
│  ├─ acceptance-criteria.md                            / PoC受入条件
│  ├─ use-cases.md                                      / 利用者操作と主要業務フロー
│  ├─ architecture.md                                   / 全体Architectureと責務分担
│  ├─ backend-class-design.md                           / Backend Class・Service設計
│  ├─ api-spec.md                                       / API Endpoint・Request・Response仕様
│  ├─ database.md                                       / Table・Relation・保存方針
│  ├─ concurrency-and-transaction.md                    / 同時実行・Transaction・Rollback方針
│  ├─ pdf-report-design.md                              / PDF構成・日本語表示・出力仕様
│  ├─ coding-rules.md                                   / Coding・命名・例外・型ルール
│  ├─ security-requirements.md                          / Security要件・認証認可の未対応事項
│  ├─ standards-and-tailoring.md                        / 参照標準とPoC向けTailoring
│  ├─ testing-strategy.md                               / Test Level・品質基準・Coverage Gate
│  ├─ test-cases.md                                     / 主要Test Caseと実装済み範囲
│  ├─ operations-requirements.md                        / Log・監視・Backup等の運用要件
│  └─ github-copilot-refactoring-guide.md               / 将来の段階的Refactoring手順
│
└─ scripts/                                             / プロジェクト共通の補助Script
   ├─ init-db.sql                                       / PostgreSQL初期化補助SQL
   └─ test-backend.ps1                                  / Backend Lint・型・Test・Coverage一括実行
```

## 学習資料の推奨配置

次の学習資料は、正式資料として`docs/learning/`へ配置することを推奨する。

```text
docs/
└─ learning/                                            / 構築・処理・テストを学ぶための補助資料
   ├─ project-foundation-backend-detailed.csv           / 基盤・Backend工程の詳細学習表
   ├─ project-frontend-detailed.csv                     / Frontend・品質・運用工程の詳細学習表
   ├─ project-api-vertical-flow.csv                     / API機能ごとのFrontendからDBまでの縦割り表
   └─ source-tree.md                                    / 本ソースツリー完全版
```

## ツリーから除外する生成物

以下はローカル実行やToolが生成するため、ソースツリー本体およびGit管理対象から除外する。

```text
.coverage                                             / Backend Coverage Data
.mypy_cache/                                          / mypy解析Cache
.ruff_cache/                                          / Ruff解析Cache
.pytest_cache/                                        / pytest実行Cache
__pycache__/                                          / Python Bytecode Cache
*.pyc                                                 / Python Compile済みFile
.venv/                                                / Python Virtual Environment
venv/                                                 / Python Virtual Environment
node_modules/                                         / npm依存Package
frontend/node_modules/                                / Frontend npm依存Package
frontend/.next/                                       / Next.js Build生成物
frontend/coverage/                                    / Frontend Coverage Report
htmlcov/                                              / Backend HTML Coverage Report
frontend/tsconfig.tsbuildinfo                         / TypeScript増分Build情報
dist/                                                 / Distribution生成物
build/                                                / Build生成物
*.bak                                                 / 作業用Backup
```

## 今後追加予定で現在未作成の成果物

```text
README.md                                             / Project概要と最短の開始手順
QUICKSTART.md                                         / Windows・Mac向けの詳細Setup手順
scripts/setup.sh                                      / Mac・Linux向け環境構築Script
frontend/tests/e2e/                                   / Playwright等のE2E Test
.github/workflows/ci.yml                              / Backend・Frontend品質GateのCI定義
runbook/                                              / 障害対応・Backup・Restore手順
```
