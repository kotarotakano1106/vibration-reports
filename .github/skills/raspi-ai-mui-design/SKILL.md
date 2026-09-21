---
name: raspi-ai-mui-design
description: RASPI AIのReact・TypeScript・MUI画面を共通デザインシステム、レイアウト、コンポーネント、アクセシビリティ基準に沿って実装・レビューする。
---

# RASPI AI MUI Design Skill

## 使用条件

Dashboard、MUI Theme、Navigation、Chart、Report、Dialog、AI Drawer、Responsive、Accessibilityを作成・変更・レビューするときに使用する。

## 必須参照

1. `references/design-system.md`
2. `references/layout-spec.md`
3. `references/component-rules.md`
4. `references/accessibility.md`
5. `assets/design-comp.jpg`。存在する場合

## 実装原則

- Brand redとError redを区別する。
- Primitiveはtokens、Semantic roleはtheme、型拡張はmui.d.tsへ置く。
- Component内へBrand color、共通Shadow、共通Radiusを重複記載しない。
- MUIを使用し、別UI frameworkを混在させない。
- Loading、Empty、Error、Retryを実装する。
- 色だけで状態を伝えない。Keyboard、Focus、Label、Status messageを確認する。
- Web ChartとPDF Chartを分離する。
- 1440x900と1280x720で確認する。
- Voice and toneはDesign Systemの方針に従い、簡潔で落ち着いた業務表現を使用する。

## 作業手順

1. 対象画面と利用者操作を確認する。
2. Design Systemと既存Themeを確認する。
3. 再利用ComponentとTokenを確認する。
4. 変更対象と状態一覧を整理する。
5. MUI Componentを優先して実装する。
6. Responsive、Keyboard、Focus、Contrast、Error状態を確認する。
7. Build、Lint、Component testを実行可能な範囲で行う。
8. 新しいTokenと例外の理由を報告する。

## 禁止事項

- Pageごとの独自ThemeProvider
- 色だけのStatus表現
- Hoverのみで使える操作
- 表示Componentからの直接API呼出し
- Brand colorの無秩序なHardcode
- Desktop Dashboardの不要なPage全体Scroll
- AI相談を独立Routeへ変更すること
