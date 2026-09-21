# RASPI AI Layout Specification

## 1. 目的

本書は、RASPI AI Design Systemに基づき、認証後Desktop画面の共通レイアウト、寸法、Grid、Responsive方針を定義する。

色、Typography、Spacing、Shape、Elevationは `design-system.md` を正とする。

## 2. Reference viewport

- Primary: 1440 × 900
- Secondary: 1280 × 720

認証後Dashboardは上記Desktop viewportで、原則としてページ全体の縦Scrollを発生させない。Card内部のTableやMessage一覧など、情報量が変動する領域には内部Scrollを許可する。

小さいviewportで情報欠落が発生する場合は、文字を極端に縮小せず、列の優先度、内部Scroll、折りたたみ、Responsive layoutを使用する。

## 3. Layout tokens

- Header height: 58px
- Navigation width: 184px
- AI Drawer width: 420px
- Main horizontal padding: 24px
- Main vertical padding: 12pxから20px
- Grid gap: 12pxを基本とする

寸法は `tokens.ts` で管理し、複数コンポーネントへ直接重複記載しない。

## 4. Header

- Viewport上部に固定する
- 高さは58px
- 左側に製品ロゴと製品名を配置する
- 右側にAI相談、利用者メニューを配置する
- 背景はMain surfaceを使用する
- elevationは使用せず、下境界線でMain contentと分離する
- NavigationおよびTemporary Drawerとのz-index関係をMUI themeで管理する

狭い幅では、低優先のラベルを省略しても、IconButtonのaccessible nameを維持する。

## 5. Navigation

- DesktopではPermanent MUI Drawerを使用する
- Header直下へ固定する
- 幅は184px
- Sidebar gradientはDesign SystemのTokenを使用する
- Navigation groupは `ListItemButton` と `Collapse` を使用する
- Active itemは明るい半透明Surface、文字、Iconで示す
- Settingsは下部へ固定する
- 折りたたみ状態は `aria-expanded` で伝える

Navigationの色を状態色として使用しない。

## 6. Main content

Main contentは次の領域へ固定する。

```text
Top    = Header height
Left   = Navigation width
Right  = 0
Bottom = 0
```

Main contentは次のGrid rowsを基本とする。

1. Page action row
2. Upper monitoring row
3. Lower report row

余白はDesign Systemの8px Gridに合わせる。

## 7. Page action row

1行に次を配置する。

- Page title
- Flexible spacer
- Equipment selection
- Month selection
- Refresh
- CSV upload

主要操作は右側へまとめ、CSV uploadをPrimary actionとする。Filterや操作が増える場合は、常時表示する項目を優先度で選び、Overflow menuまたはSecond rowを検討する。

## 8. Upper monitoring row

Desktopでは2列Gridを使用する。

- Summary card: 約36%
- Chart card: 約64%

推奨比率:

```text
0.72fr 1.28fr
```

Summary cardには次を縦方向に表示する。

- Error detections
- Warning detections
- Maximum vibration

Chart cardは軸、Legend、Tooltipが欠けない高さを確保する。

## 9. Lower report row

全幅のCardとして次を配置する。

- Titleとsubtitle
- Search
- Status filter
- Data table
- Pagination

TableContainerを可変領域とし、PaginationをCard下部へ保持する。行数の増加でページ全体を押し広げない。

## 10. Dialog

CSV uploadとReport detailは独立PageではなくDialogとして提供する。

- Title、Content、Actionsの構造を統一する
- Primary actionは右端に配置する
- CancelまたはClose操作を明確にする
- Errorは操作箇所に近い位置へ表示する
- 長いContentだけを内部Scrollさせる
- 開いたときに適切な要素へFocusを移す
- 閉じたときに起動元へFocusを戻す

## 11. AI consultation Drawer

- Temporary MUI Drawer
- Anchor: right
- Desktop width: 420px
- Header、Context、Message list、Input areaで構成する
- Message listだけを独立してScrollさせる
- Input areaをDrawer下部へ固定する
- 現在の設備、期間、参照範囲をContext部分に表示する
- Drawerを開いたときに内部へFocusを移す
- 閉じたときに起動ButtonへFocusを戻す

## 12. Responsive policy

本PoCのPrimary targetはDesktopとする。ただし、幅が不足した場合は次の順で対応する。

1. 可変幅を縮小する
2. TableやMessage listへ内部Scrollを適用する
3. 補助ラベルを省略しaccessible nameを維持する
4. Action controlsを折り返す
5. Upper rowを1列へ変更する
6. Permanent navigationをTemporary navigationへ変更する

Responsive対応で重要な操作や状態を非表示にしない。

## 13. Overflow policy

- Page全体: Desktopでは原則 `overflow: hidden`
- Table: `TableContainer` 内でScroll
- Chat messages: Message region内で縦Scroll
- Dialog content: Content region内で縦Scroll
- Long filename: ellipsisとTooltipを併用
- Long AI response: paragraphを折り返し、横Scrollを発生させない

## 14. Layout review checklist

- Header、Navigation、Main contentが重ならない
- 1440×900と1280×720で主要機能が利用できる
- Page全体に不要な縦Scrollがない
- Card内部Scrollが適切である
- Page actionが見切れない
- Chartの軸とTooltipが読み取れる
- Table paginationがCard下部にある
- DialogとDrawerのFocusが適切である
- Token外の独自寸法を不必要に追加していない
