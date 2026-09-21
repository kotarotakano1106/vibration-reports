# 運用・監視・可用性要件

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

本番化を見据え、Environment、Observability、Incident、Backup、Recovery、Change、Costの運用要件を定義する。

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

## 1. Environment

- local、development、test、staging、productionの分離
- Environment間でSecretとDataを共有しない
- Config一覧、Default、Owner、変更方法を管理する
- Timezone、Locale、Clock同期を定義する

## 2. SLO・SLI

- Availability
- API latency p50/p95/p99
- Error rate
- Report/PDF/RAG処理成功率
- AI upstream error rate
- Data freshness

PoC目標値と本番SLOを分ける。

## 3. Logging

- Structured log
- Request/Operation/User/File/Report ID
- Start、completion、duration、result、error code
- Secret/CSV全文/完全Promptを除外
- Log level、保存先、Retention、Access、Masking

## 4. Metrics

- Request count、status、latency
- DB pool、slow query、transaction failure
- Upload size、analysis duration、PDF duration
- AI calls、tokens、latency、429/5xx、retry
- RAG result count、no-context rate、similarity distribution
- Disk/Storage、Memory、CPU
- processing status age

## 5. Alert

- Error rate / latency threshold
- DB unavailable / pool exhaustion
- AI rate limit / authentication failure
- Stale processing
- Storage capacity
- Backup failure
- Repeated authorization denial

Alert owner、severity、notification、suppression、runbookを定義する。

## 6. Incident management

- Detection、triage、containment、recovery、postmortem
- Severityと連絡経路
- Security incident escalation
- Evidence保全
- Status communication
- 再発防止項目のOwnerと期限

## 7. Backup・Recovery

- DB、CSV、PDF、Configの対象範囲
- RPO/RTO
- 暗号化とAccess
- Restore rehearsal
- DBとFile storageの整合性確認

## 8. Deployment・Rollback

- Build artifactを固定し再現可能にする
- Migration順序とCompatibility
- Health/readiness確認
- Smoke test
- Rollback criteriaと手順
- Feature flagの導入条件
- Production secretをBuildへ埋め込まない

## 9. Capacity・Cost

- Users、CSV/day、Report/day、Chat/day
- Storage growth
- Azure OpenAI token/quota/budget
- Scale-out条件
- Cost alert

## 10. Maintenance

- Dependency・Base image update
- Certificate/Secret rotation
- DB maintenance
- Log/Backup cleanup
- StandardとDocumentの定期Review

## 11. Runbook一覧

- DB unavailable
- Azure OpenAI unavailable / 429
- Stale processing
- File storage full
- Migration failure
- PDF generation failure
- Secret leakage suspicion
- Backup/restore failure

## チームで決定・運用する項目

- [ ] 文書オーナーと承認者
- [ ] 適用する標準、版、適用範囲
- [ ] 適用除外と理由、残存リスク
- [ ] 未確定値の決定者と期限
- [ ] PoC完了条件と本番化条件
- [ ] レビュー頻度と変更承認方法
- [ ] 証跡の保存先と保持期間
- [ ] 例外承認の担当者、有効期限、見直し日
