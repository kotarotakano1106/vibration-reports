# 並行処理・冪等性・トランザクション設計書

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

同時要求、排他、冪等性、状態遷移、外部API待機、FileとDBの整合性を定義する。

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

## 1. 対象処理

- CSV upload・checksum重複判定
- Report生成
- Embedding登録・再生成
- PDF生成
- status更新
- RAG検索

## 2. 基本方針

- 同一resource操作は競合を検出し、異なるresourceは上限付きで並行可能とする。
- Process内Lockだけに依存せず、DB制約・条件付き更新・Lockで保証する。
- Azure OpenAI待機中にDB TransactionとRow lockを保持しない。
- Retry可能な一時障害だけを、上限・Backoff・Jitter付きで再試行する。
- File生成は一時Pathへ書き、完了後に原子的Renameを行う。

## 3. 状態遷移

```text
uploaded -> validating -> processing -> completed
                     \-> failed
failed -> processing  # 明示的再実行時のみ
```

- 許可されない遷移をServiceまたは条件付きUPDATEで拒否する。
- statusだけでなく`updated_at`を用いてStale processingを検出する。
- 将来必要なら`version`列によるOptimistic lockingを追加する。

## 4. 同一CSVのReport生成

1. 短いTransactionで現在statusと既存Reportを確認する。
2. `uploaded/failed`から`processing`への条件付きUPDATEを実行する。
3. 更新件数0なら409または既存処理情報を返す。
4. commit後にCSV解析・AI・Embeddingを行う。
5. 新しい短いTransactionでReport、Chunk、completedを保存する。
6. 失敗時はrollbackし、別Transactionでfailedと安全なError codeを保存する。

`reports.uploaded_file_id UNIQUE`は最終防御であり、AI呼出後の重複検出だけに使用しない。

## 5. CSV重複

- checksumにDB一意性が必要かをチームで決定する。
- Equipment・Userを跨ぐ同一Fileを同一とみなす範囲を定義する。
- 同時UploadはDB制約違反を既存resourceまたは409へ安全に変換する。

## 6. PDF

- 完成済みPDFの再利用条件にReport update時刻、Template version、Chart versionを含める。
- 同時生成は一時Filenameを分離する。
- 完成後のAtomic rename前にFile sizeとPDF headerを確認する。
- DBの`pdf_path`は正式File完成後のみ更新する。

## 7. Embedding再生成

- EmbeddingはTransaction外で事前生成する。
- 入替Transaction内で既存Chunkを置換またはUpsertする。
- 失敗時は既存Chunkを維持する。
- Model/Dimensions変更は世代管理または一括Migration計画を作成する。

## 8. Isolation・Lock

- Default isolation levelを記録する。
- 条件付きUPDATEを第一候補とし、必要時のみ`SELECT FOR UPDATE`を使用する。
- Lock取得順序を統一する。
- Deadlockは識別して有限回Retryする。
- Long-running taskでRow lockを保持しない。

## 9. Idempotency

APIごとに以下を定義する。

- 安全な再送可否
- Resource key
- Idempotency keyの要否と有効期間
- 同一key・同一payloadのResponse
- 同一key・異なるpayloadのError
- 処理中、完了、失敗時のResponse

GETは副作用を持たせない。Report生成・Upload・PDF生成は再送動作を明記する。

## 10. Timeout・Retry・Backpressure

- HTTP timeout、AI timeout、DB connect timeout、Job timeoutを分離する。
- Rate limitと一時接続障害だけをRetry候補とする。
- Queue未導入時もSemaphore等で同時処理数を制限する。ただしScale-out時は分散制御を追加する。
- 上限超過は429または503とRetry-Afterの採用を検討する。

## 11. 障害復旧

- Stale processingの検出条件
- 自動failed化または手動Recovery
- 再実行前のFile、Report、Chunk整合性確認
- Operation IDによるLog追跡
- Partial failureの補償処理

## 12. テスト

- 同一CSVへ同時Report生成
- 同一checksum同時Upload
- AI成功後DB失敗
- PDF同時生成
- Embedding入替失敗
- Deadlock / Serialization failure
- Timeout / Cancel
- Stale processing復旧
- 複数Process相当の競合

## チームで決定・運用する項目

- [ ] 文書オーナーと承認者
- [ ] 適用する標準、版、適用範囲
- [ ] 適用除外と理由、残存リスク
- [ ] 未確定値の決定者と期限
- [ ] PoC完了条件と本番化条件
- [ ] レビュー頻度と変更承認方法
- [ ] 証跡の保存先と保持期間
- [ ] 例外承認の担当者、有効期限、見直し日
