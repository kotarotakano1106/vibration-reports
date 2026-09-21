# 受入基準

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

各要件の完了を客観的に判定する条件を定義する。

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


## 記述規則

Given / When / Thenで、観測可能な結果を記載する。AI文章は完全一致ではなく、必須事実、禁止事項、根拠、構造で判定する。

## 受入基準

### AC-CSV-001 正常アップロード
- Given: UTF-8、必須列`measured_at`と`vibration_value`を含むCSV
- When: 利用者がアップロードする
- Then: `uploaded_files`が登録され、安全な保存名で実ファイルが保存される

### AC-CSV-002 不正CSV
- Given: 空、必須列不足、日時不正、数値不正のいずれか
- When: アップロードする
- Then: 4xxで拒否され、レポートと不完全ファイルが残らない

### AC-REP-001 レポート生成
- Given: 有効な保存済みCSVと利用可能なAI設定
- When: レポート生成APIを実行する
- Then: 統計、異常候補、AI分析、レポート、検索チャンクが整合した状態で保存される

### AC-REP-002 重複生成
- Given: 同じ`uploaded_file_id`のレポートが存在する
- When: 再生成する
- Then: 409を返し、重複レポートを作らない

### AC-RAG-001 類似検索
- Given: 対象設備のレポートチャンクが登録済み
- When: 関連する質問を送る
- Then: 上限件数内で類似度順に参照元付き結果を返す

### AC-CHAT-001 根拠付き回答
- Given: 関連チャンクが存在する
- When: チャットAPIへ質問する
- Then: 検索結果内の事実だけを用い、参照元を返す

### AC-CHAT-002 根拠不足
- Given: 条件に一致するチャンクがない
- When: 質問する
- Then: 推測せず、確認できないことを回答する

### AC-PDF-001 PDF
- Given: レポートが存在する
- When: PDFを要求する
- Then: 日本語が読め、必須項目を含むPDFを`application/pdf`で返す

### AC-SEC-001 秘密情報
- Given: エラーまたはログ出力が発生する
- When: 応答とログを確認する
- Then: APIキー、パスワード、接続文字列、CSV全文が含まれない

### AC-UI-001 状態表示
- Given: 読込、0件、API失敗の各状態
- When: トップ画面を表示する
- Then: Loading、Empty、Errorと次の操作を判別できる

## 完了判定

- 必須のMust要件に対応する受入基準が全て成功すること。
- 未実施項目、既知制限、手動確認を記録すること。

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

