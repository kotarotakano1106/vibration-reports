# RASPI AI MUI Component Rules

## 1. 目的

本書は、RASPI AI Design SystemをMUIコンポーネントへ適用するための実装規則を定義する。

色、Typography、Spacing、Shape、Elevationは `design-system.md`、配置は `layout-spec.md`、支援技術対応は `accessibility.md` を参照する。

## 2. 共通規則

- 独自HTMLよりMUIコンポーネントを優先する
- BrandやSemantic colorはThemeから取得する
- 同じ役割には同じVariant、Size、Icon、Labelを使用する
- Loading、Empty、Error、Disabled状態を定義する
- ComponentへAPI通信と複雑な業務ロジックを集中させない
- Interactionを持つComponentにはKeyboardとFocus状態を用意する

## 3. Buttons

- CSV upload: `contained`、Primary gradient
- AI consultation: 操作優先度に応じて`contained`またはtonal treatment
- Refresh: `outlined`
- Cancel / Close: `text`または`outlined`
- Destructive action: Semantic error color、確認Dialogを必要に応じて使用
- Row actions: `IconButton`とOverflow menu

規則:

- Primary actionを同一領域に複数並べすぎない
- 処理中は二重送信を防止する
- Iconだけの場合は `aria-label` を付ける
- Disabledだけで理由が分からない場合は補足を示す

## 4. Cards

- Monitoring、Chart、ReportにはMUI `Card` を使用する
- 任意のborder付き `div` をCard代わりに増やさない
- Header areaは約48から55px
- Bodyは `theme.spacing(2)` を基本とする
- Border、Shadow、RadiusはThemeから取得する
- Error状態でもCard全体を強い赤で塗らず、AlertやStatus表示を使用する

## 5. Forms

- Compactな `Select`、`TextField`、`FormControl` を使用する
- すべてのInputに表示Labelまたは `aria-label` を付ける
- 必須、形式、範囲、文字数のエラーを入力付近に表示する
- PlaceholderだけをLabelとして使用しない
- SearchにはSearch iconをstart adornmentとして使用可能
- Submit中は入力と送信状態を一貫して管理する

## 6. Dialog

- CSV uploadとReport detailにはMUI `Dialog` を使用する
- `DialogTitle`、`DialogContent`、`DialogActions` を基本構造とする
- Close手段を明確にする
- Primary actionは右端に配置する
- Validation errorはDialog内に残して表示する
- 長い内容はContentだけをScrollさせる
- 開閉時のFocus動作を確認する

## 7. Navigation

- Desktop navigationはPermanent `Drawer`
- Group controlは `ListItemButton` と `Collapse`
- Active itemは背景、文字、Iconで示す
- Settingsは下部へ固定する
- Group toggleには `aria-expanded` を付ける
- Navigation labelをIconだけへ省略する場合もaccessible nameを維持する

## 8. Tables

- MUI `Table` と `TablePagination` を使用する
- Text列は左揃え、数値列は可能な範囲で右揃え
- Headerは意味的なTable header cellを使用する
- Statusは文字付き `Chip` を使用する
- Row actionはOverflow menuを使用する
- PaginationはTable card下部に置く
- Loading、0件、ErrorをTable内またはCard内で明示する
- 長いFilenameはellipsisとTooltipを併用する
- Hoverだけに操作や情報を依存させない

## 9. Chips and status

- Normal: `success`
- Warning: `warning`
- Error / requires attention: `error`
- Processing: information系または中立色

`Chip` には必ず状態Textを表示し、色だけで判定させない。ブランドレッドを状態色として流用しない。

## 10. Alerts and Snackbar

- Field固有エラーはField付近に表示する
- Card・Page単位のErrorは `Alert` を使用する
- 一時的な成功通知は `Snackbar` を使用できる
- 重要な失敗をSnackbarだけで消える表示にしない
- Error messageは利用者が次に取る行動を理解できる表現にする
- 内部Path、SQL、Stack traceを表示しない

## 11. Loading and empty states

- Page初期読込: SkeletonまたはProgress
- Button処理中: Button内Progressまたは明確な処理中Text
- Table読込: Headerを維持し、BodyにLoading state
- Empty: データがない理由と次の操作を表示
- Retry可能なError: 再試行Buttonを表示

Layout shiftを抑え、読み込み前後で主要領域の高さを大きく変えない。

## 12. Chart

- Measured seriesはblue-teal
- Warning thresholdはamber
- Error thresholdはdark red
- Data lineをブランドレッドにしない
- X軸Labelが重なる場合は間引き、回転、Formatterを使用する
- 正確な発生時刻はTooltipで確認できるようにする
- Tooltipは時刻、値、単位、状態を表示する
- 異常点は色だけでなくPoint shapeやLabelでも区別する
- Dataなし、読込中、Error状態を定義する
- Web表示は承認済みChart libraryを使用し、PDF用画像生成と分離する

## 13. AI side Drawer

- Temporary `Drawer anchor="right"`
- HeaderにAI icon、Title、Close buttonを置く
- 現在の設備と期間をContextとして表示する
- Message listを独立してScrollさせる
- Input areaを下部へ固定する
- Send中の二重送信を防止する
- 参照元を回答と関連付けて表示する
- 未回答、根拠不足、接続エラーを区別する
- 開閉時のFocusを管理する

## 14. Menus and tooltips

- Row actionや低頻度操作は `Menu` へ配置する
- Menu itemは動詞で始め、実行内容を明確にする
- Tooltipは補足に使用し、必須情報の唯一の提示方法にしない
- Keyboard focusでもTooltip相当情報を取得できるようにする
- TouchまたはKeyboardで利用できないHover限定操作を作らない

## 15. Component state API

再利用Componentでは、可能な範囲で次をPropsとして明示する。

```text
loading
error
empty
value / data
onRetry
onAction
aria-label
```

Component内部で外部状態を隠しすぎず、親が状態遷移を制御できる設計を優先する。

## 16. Theme integration

- `tokens.ts`: Primitive values
- `theme.ts`: Semantic roles、Typography、Component defaults
- `mui.d.ts`: Theme type augmentation
- `ThemeRegistry.tsx`: ThemeProviderとCssBaseline

Feature componentへHex color、共通shadow、共通radiusを直接記載しない。新しいTokenを追加する場合は既存Tokenで表現できない理由を確認する。

## 17. Component review checklist

- 適切なMUI Componentを使用している
- VariantとSizeが同じ役割で統一されている
- Theme Tokenを使用している
- Loading、Empty、Error、Disabledを扱う
- KeyboardとFocusで操作できる
- 色だけで状態を伝えていない
- IconButtonとInputにaccessible nameがある
- API通信や業務ロジックを表示Componentへ集中させていない
- Chartの時刻、単位、Tooltipが読み取れる
