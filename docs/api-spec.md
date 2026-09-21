# API仕様書

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

現行APIの契約に加え、認証、Validation、Pagination、Timeout、冪等性、競合、Error、監査要件を定義する。

## 参照標準と適用方針

本プロジェクトは以下を参考にする。PoC段階では完全準拠や認証取得を主張せず、採用項目、適用除外、理由、残存リスクをチームで記録する。

- ISO/IEC/IEEE 29148:2018: 要求工学
- ISO/IEC 25010:2023: 製品品質モデル
- ISO/IEC/IEEE 29119-1:2022、29119-2:2021: テスト概念・プロセス
- ISO/IEC TR 29119-11:2020: AIベースシステムのテスト
- NIST SP 800-218 SSDF 1.1: セキュア開発
- OWASP ASVS 5.0.0: Web・APIセキュリティ
- NIST AI RMF 1.0: AIリスク管理
- WCAG 2.2: Webアクセシビリティ
- RFC 9457: HTTP API Problem Details

公式参照先は `standards-and-tailoring.md` に集約する。

## 1. 共通契約

- Base path: `/api/v1`
- JSONはUTF-8、File uploadは`multipart/form-data`
- DateはISO 8601、UUIDは標準文字列表現
- Server時刻はtimezone付き、表示時刻はJST方針を確認する
- Response fieldの追加は原則Backward compatible、削除・型変更はVersioning対象
- Request IDを受け付けまたは生成しResponse/Logへ返す

## 2. 認証・認可

- 本番化時はBearer token等の正式方式を定義する。
- 401は未認証、403は認証済みだが権限不足。
- Resource IDによる全取得・更新・Download・検索で所有者/Roleを検証する。
- 現行`dev-user`固定処理はPoC暫定である。

## 3. 共通Validation

- Stringのtrim、空白のみ、max length
- Numberの有限性、min/max
- Date rangeの前後関係
- Limit/offsetの上限
- Enum以外の値
- 未知Fieldの扱い
- File size、filename、MIME、encoding

## 4. Error契約

現行`detail`を維持しつつ、RFC 9457への移行時は以下を定義する。

```json
{
  "type": "https://example.invalid/problems/validation-error",
  "title": "入力値を確認してください",
  "status": 400,
  "detail": "利用者向け説明",
  "instance": "/api/v1/...",
  "error_code": "CSV_INVALID_VALUE",
  "request_id": "..."
}
```

- 400: 業務・File入力不正
- 401: 未認証
- 403: 権限不足
- 404: Resourceなし。情報露出を避ける場合403/404方針を統一
- 409: 重複、処理中、状態競合
- 413: Upload size超過を採用するか決定
- 422: Pydantic schema error
- 429: Rate limit / concurrency limit
- 500: Internal failure
- 502: Azure OpenAI等Upstream failure
- 503: 一時的利用不可
- 504: Gateway/processing timeout

Error code、Retry可否、Log level、監査対象をError catalogで管理する。

## 5. Pagination・Filter・Sort

- `limit`、`offset`またはCursor方式をAPIごとに統一する。
- Max limitを定義する。
- Stable sortとして`created_at DESC, id DESC`等を使用する。
- Filter field、部分一致、Case、Timezoneを定義する。
- Total countを返す要否とCostを決定する。

## 6. POST /files

- Input: `file`, `equipment_id`, `measurement_date?`, `encoding`
- Success: 201。重複時に既存resourceを返すか409とするか最終統一する。
- Side effect: File保存、`uploaded_files`登録
- Idempotency: checksumと所有範囲、任意のIdempotency-Keyを定義する。
- Concurrency: 同一checksum競合をDBで保証する。
- Timeout: Upload/read timeoutと最大Sizeを定義する。

## 7. GET /files/{id}/measurements

- Query: `threshold_value > 0`
- Success: metadata、threshold、measurement count、時系列points
- Security: 所有者/Role確認
- Capacity: 最大返却points、Sampling/Downsampling方針を定義する。
- Cache: CSV・threshold・access scopeを含むCache key方針を決定する。

## 8. GET /reports

- Query: limit、offset、将来equipment/status/date/search
- Stable sort、Max limit、Total count方針
- Security: 利用者範囲でFilterしてからPagination
- Response: Report概要と元CSV名

## 9. POST /reports/generate

- Input: uploaded_file_id、threshold_value、weather?
- Process: 同期PoC。処理時間がHTTP timeoutを超える場合非同期Jobへ移行する。
- Concurrency: 同一uploaded_file_idの開始を一件に制限する。
- Idempotency: 既存Report、processing、failed再実行のResponseを定義する。
- Transaction: AI待機中にDB Transactionを保持しない。
- Error: 404、409、422、429、500、502、504

## 10. GET /reports/{id}/pdf

- Success: `application/pdf`、attachment、`Cache-Control: no-store`
- Security: Download前に認可
- Idempotency: 有効な生成済みPDFは再利用可能
- Concurrency: 同時生成で正式Fileを破損させない
- Error: 404/403、409処理中、500生成、504 timeout

## 11. POST /search

- Input: query 1..2000、limit 1..20、equipment/date/chunk types
- Security: 利用者範囲を必ずRepository queryへ適用
- Similarity: distance function、変換式、minimum relevanceを明記
- Capacity: Context/result size上限
- Error: 400、401/403、429、500、502、504

## 12. POST /chat

- Searchと同じAccess filterを適用する。
- Answer、source_count、sourcesを返す。
- Root evidenceがない場合は定型の回答不能を返す。
- Prompt injection、Output validation、max tokensを定義する。
- Chat historyはPoCで保存しない。

## 13. Health・Readiness

- `/health`: Process生存確認。外部Dependencyへ重いCallをしない。
- `/ready`: 本番化時にDB等の処理可能性を確認する候補。

## 14. Rate limit・Timeout

API別に、Client timeout、Server timeout、Retry可否、Retry-After、同時実行上限を一覧化する。

## 15. API変更管理

- OpenAPI diffを確認する。
- Breaking changeは新VersionまたはMigration期間を設ける。
- Consumer、Frontend、Test、Documentを同時更新する。

## チームで決定・運用する項目

- [ ] 文書オーナーと承認者
- [ ] 適用する標準、版、適用範囲
- [ ] 適用除外と理由、残存リスク
- [ ] 未確定値の決定者と期限
- [ ] PoC完了条件と本番化条件
- [ ] レビュー頻度と変更承認方法
- [ ] 証跡の保存先と保持期間
- [ ] 例外承認の担当者、有効期限、見直し日
