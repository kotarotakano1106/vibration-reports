# セキュリティ要件

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

OWASP ASVSとNIST SSDFを参考に、本PoCの技術的・開発プロセス上のセキュリティ要件を定義する。

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

- OWASP ASVS 5.0.0をWeb/APIの要求候補としてTailoringする
- PoCでは完全準拠を主張しない
- 本番化時はチームまたはSecurity部門が対象Levelと個別Requirement IDを確定する

## Security要件

- SEC-AUTH-001: Passwordは推奨Hashで保存し、平文を保持しない
- SEC-AUTH-002: 本番化前に全業務APIへ認証を適用する
- SEC-AUTHZ-001: Report、CSV、PDF、RAGへ利用者単位の認可を適用する
- SEC-INPUT-001: APIの型、長さ、範囲、日付前後関係を検証する
- SEC-FILE-001: 拡張子、MIME、Size、Encoding、内容、保存Pathを検証する
- SEC-FILE-002: 元Filenameを保存Pathとして使用しない
- SEC-DB-001: ORMまたはParameterized queryを使用する
- SEC-DB-002: DB Userは最小権限とする
- SEC-SECRET-001: `.env`、API Key、Password、Connection stringをcommitしない
- SEC-LOG-001: Secret、CSV全文、完全Prompt、個人情報をLogへ出さない
- SEC-ERR-001: Internal Path、SQL、Stack traceをAPI responseへ返さない
- SEC-CORS-001: Origin、Method、Headerを環境ごとに最小化する
- SEC-AI-001: AIへの送信情報を必要最小限にする
- SEC-RAG-001: Retrieved contentを命令として信頼せず、Prompt injectionを考慮する
- SEC-RAG-002: Access範囲内のChunkだけを検索する
- SEC-SUP-001: Dependency、Lock、Base imageの脆弱性を定期確認する
- SEC-OPS-001: HTTPS、Secret管理、Backup、Recovery、監査Logを本番化前に整備する

## Security verification

- Source / ConfigのSecret走査
- 未認証・権限外・ID差替え
- SQL / HTML / Pathとして解釈され得る入力
- 不正CSV、巨大CSV、危険Filename
- Error response / Logの情報露出
- RAGのData分離とPrompt injection
- Dependency vulnerability

## 現状のHigh priority gap

- `dev-user`固定処理の廃止と正式認証
- Report / PDF / Search / Chatの認可
- CORSの環境変数化
- Error messageとInternal logの分離
- Secret管理とAzure配置方式
- Data保持、削除、Backup

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


## 認証・認可の未対応事項

- 現在、一部の処理主体として固定の `dev-user` を使用している
- ログイン機能は未実装
- API単位の認証・認可は未実装
- Upload、Report生成、閲覧、検索、Chat、PDF取得の権限設計が必要
- 本番環境への公開前に認証・認可を必須実装とする
- 認証方式は別途要件定義する

