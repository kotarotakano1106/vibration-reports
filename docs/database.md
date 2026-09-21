# データベース設計書

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

4テーブルのSchemaに加え、制約、Index、並行更新、保持、Backup、Migration、性能要件を定義する。

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

## 1. 基本方針

- PostgreSQL + pgvector、UUID PK、timezone付き日時
- SQLAlchemy Model、Alembic Migration、本文書を同期する
- CSV全測定値はDBへ保存しない
- Application DB userは最小権限

## 2. テーブル

### users

`id`, `login_id` unique, `password_hash`, `display_name`, `role`, `is_active`, timestamps。

### uploaded_files

所有者、設備、元名、安全な保存名・Path、Size、MIME、Encoding、checksum、測定日、status、Error、timestamps。

### reports

1 uploaded_fileにつき最大1 Report。所有者、設備、測定日、統計、閾値、異常、AI文章、Model/Prompt version、Chart/PDF、timestamps。

### report_chunks

Report 1対多。index/type/content、VECTOR(1536)、Embedding model/version、設備、測定日、metadata、timestamps。

## 3. 制約

- FK delete behaviorを業務要件と一致させる。
- `reports.uploaded_file_id` unique
- `report_chunks(report_id, chunk_index)` unique
- file_size > 0、record_count > 0、anomaly_count >= 0
- minimum <= maximum
- role/status/chunk_typeの許容値管理方法を決定する。
- 同一checksumのUnique範囲を決定する。

## 4. Index

- 所有者、設備、日付、status、created_at、checksum
- 一覧Queryの複合Indexを実測に基づき設計
- pgvector indexはData量、Recall、Build costを評価してHNSW/IVFFlat等を選択
- 未使用・重複Indexを監視する

## 5. Transaction境界

- Repositoryは原則flush、Service/Use caseがcommit/rollback
- AI待機中にTransactionを保持しない
- Report + Chunk + completedのAtomicity範囲を定義
- File systemはDB transaction対象外のため補償処理を設計

## 6. 並行更新

- status条件付きUPDATEまたは必要なRow lock
- Scale-out時にProcess lockだけを使わない
- Lock順序を統一
- Deadlock/serialization failureを識別し有限回Retry
- Optimistic lock用version列の導入条件を定義

## 7. 状態遷移

```text
uploaded -> validating -> processing -> completed
                     \-> failed
failed -> processing  # 承認された再実行
```

DB constraint、Service validation、監査Logのどこで保証するかを決定する。

## 8. Connection pool

- Pool size、max overflow、recycle、pre-ping、connect timeout
- Web instance数との総Connections上限
- Long taskによるConnection占有を避ける
- Pool exhaustion metricとAlert

## 9. Data lifecycle

- CSV、Report、Chunk、PDF、Logの保持期間
- Soft delete / hard delete
- Legal holdの要否
- 利用者削除時の関連Data
- Backupからの削除反映
- Test dataの定期Cleanup

## 10. Backup・Restore

- Full/Incremental、頻度、暗号化、保管先、Access
- RPO、RTO
- Restore test頻度
- DBとFile storageの整合点
- pgvector extensionとMigrationを含む復旧

## 11. Migration

- 適用前Backupと容量確認
- Backward compatibleなExpand/Migrate/Contractを優先
- Long lockを避ける
- upgrade/downgradeまたはForward fix方針
- 複数instance起動時にMigrationを一度だけ実行する
- Model/Migration/Document diffをCIで確認する候補

## 12. Security・監査

- TLS、Secret管理、最小権限
- Productionへの直接手動更新制限
- Audit対象: Login、権限拒否、Export、削除、Migration
- Sensitive dataをSQL Logへ出さない

## 13. 容量・性能

- 予想User、CSV、Report、Chunk件数
- 年間増加量
- Query SLO
- Explain planとSlow query監視
- Vacuum/Analyze、Statistics、Maintenance window

## チームで決定・運用する項目

- [ ] 文書オーナーと承認者
- [ ] 適用する標準、版、適用範囲
- [ ] 適用除外と理由、残存リスク
- [ ] 未確定値の決定者と期限
- [ ] PoC完了条件と本番化条件
- [ ] レビュー頻度と変更承認方法
- [ ] 証跡の保存先と保持期間
- [ ] 例外承認の担当者、有効期限、見直し日
