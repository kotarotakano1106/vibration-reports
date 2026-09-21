# PDF帳票設計書

## 文書情報

- プロジェクト: 振動AI日報生成アプリ
- リポジトリ: `vibration-reports`
- 区分: PoC
- 最終更新日: 2026-09-14
- 状態: Draft / チームレビュー待ち

## 目的

振動分析レポートのA4 PDFについて、内容、視覚、アクセシビリティ、安全な生成条件を定義する。

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


## 帳票要件

- A4縦、原則1ページ
- 日本語文字化けがない
- 白、チャコール、ネイビーを基調とし、異常のみ落ち着いた赤で強調
- Web画面のブランドレッドとは役割を分ける

## 必須項目

- Report title / ID
- 設備ID、測定日、天候
- 件数、最小、最大、平均、中央値、標準偏差、閾値
- 異常件数と代表的な異常
- AI分析概要、判定根拠、推奨対応
- 振動推移Chart
- AI結果は補助情報であり現場確認が必要である旨

## Layout

- Header: title、設備、測定日
- Summary: 主要統計と状態
- Chart: 閾値、最大、異常点
- Analysis: 概要、根拠、推奨
- Footer: 生成日時、Report ID、注意事項

## Chart

- Web Chartとは別の`ChartService`でPNG生成
- 軸、単位、閾値、異常点、最大値を読み取れること
- 色だけで異常を表現しない

## 生成・保存

- 利用者入力をPathへ直接使用しない
- 安全なFilenameを生成する
- 生成成功後のみDBのPDF情報を更新する
- 失敗した不完全PDFを残さない
- Responseは`application/pdf`、Attachment、必要に応じ`no-store`

## テスト

- 日本語、長文、0件、異常多数、特殊文字
- 文字切れ、重なり、改ページ
- 数値とDBの一致
- 404、権限、生成失敗

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

