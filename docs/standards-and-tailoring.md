# 標準・ガイドライン適用表

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

参照標準の版、採用目的、適用範囲、除外、証跡、見直しを一元管理する。

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

## 1. 適用ルール

- 標準本文を複製せず、Project要件へ落とし込む。
- 標準名、版、Requirement IDを記録する。
- 「参考」「部分適用」「準拠」「認証済み」を区別する。
- 改訂時は自動追随せず影響分析する。

## 2. 適用候補

### ISO/IEC/IEEE 29148:2018

- 目的: 要求の明確性、検証可能性、追跡性
- 適用: requirements、acceptance criteria、traceability
- 状態: 参考・Tailoring
- 見直し: 次版発行時

### ISO/IEC 25010:2023

- 目的: 品質特性の漏れ防止
- 適用: 性能、互換性、使用性、信頼性、Security、保守性等
- 状態: 参考・Tailoring

### ISO/IEC/IEEE 29119 series

- 目的: Test process、documentation、design techniques
- AI: TR 29119-11を参考
- 状態: 参考・PoC向け簡略化

### OWASP ASVS 5.0.0

- 目的: Web/API/File/Auth/Authorization/Log/Security controls
- Target level: チーム・Security部門が決定
- Requirement mapping: `security-requirements.md`へ記録

### NIST SP 800-218 SSDF 1.1

- 目的: Secure SDLC、artifact保護、脆弱性対応
- 適用: coding、review、dependency、release、incident

### NIST AI RMF 1.0

- 目的: Govern、Map、Measure、Manage
- 適用: AI/RAG品質、risk、human oversight、monitoring
- 注意: Framework改訂を定期確認

### WCAG 2.2

- 目標候補: Level AA
- 適用: Keyboard、Focus、Label、Contrast、status messages
- 最終Target: チーム決定

### RFC 9457

- 目的: Machine-readable API error
- 状態: 将来移行候補。現行FastAPI detailとのCompatibilityを評価

## 3. Mapping記録欄

各採用項目について以下を記録する。

- Standard / version / requirement ID
- Project requirement ID
- Design / implementation location
- Test case ID
- Status
- Evidence
- Exception / expiry

## チームで決定・運用する項目

- [ ] 文書オーナーと承認者
- [ ] 適用する標準、版、適用範囲
- [ ] 適用除外と理由、残存リスク
- [ ] 未確定値の決定者と期限
- [ ] PoC完了条件と本番化条件
- [ ] レビュー頻度と変更承認方法
- [ ] 証跡の保存先と保持期間
- [ ] 例外承認の担当者、有効期限、見直し日
