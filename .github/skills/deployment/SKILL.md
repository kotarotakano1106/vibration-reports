---
name: deployment
description: 振動AI日報生成アプリをAzure等へ安全に配置するため、Build、Test、Secret、Migration、Health、Monitoring、Backup、Rollbackを確認する。
---

# Deployment Skill

## 使用条件

環境構築、Staging、本番相当配置、Migration、Release、Rollback準備で使用する。

## 事前確認

- `docs/operations-requirements.md`
- `docs/security-requirements.md`
- `docs/concurrency-and-transaction.md`
- `docs/api-spec.md`
- `docs/database.md`
- `docs/testing-strategy.md`

## Gate

1. Build、Test、Security reviewが成功している。
2. `dev-user`固定等の暫定実装が対象環境で許可されているか確認する。
3. SecretをSource、Image、Logへ含めない。
4. CORS、HTTPS、Authentication、Authorizationを環境に合わせる。
5. Migrationの互換性、Backup、適用順序、単一起動を確認する。
6. Health、Readiness、Smoke testを確認する。
7. Log、Metric、Alert、Retention、Incident連絡先を確認する。
8. Rollback criteria、手順、Data互換性を確認する。
9. Azure OpenAI quota、Timeout、Rate limit、Cost alertを確認する。
10. CSV、PDF、DBの永続化とRestoreを確認する。

## 報告

- Release version / commit
- 対象環境
- 実行したBuild・Test
- Migration
- Config・Secretの確認結果。値は記載しない
- Smoke test
- Monitoring
- Rollback plan
- 未実施・残存Risk
