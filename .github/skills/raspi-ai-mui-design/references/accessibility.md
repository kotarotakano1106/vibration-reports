# RASPI AI Accessibility Guidelines

## 1. 目的

本書は、RASPI AI Design Systemにおけるアクセシビリティ要件と確認手順を定義する。

アクセシビリティは見た目の最終調整ではなく、要件、Design、実装、テストの各段階で扱う。

## 2. 基本原則

- 色だけでError、Warning、Successを伝えない
- Mouse hoverだけに情報や操作を依存させない
- Keyboardだけでも主要な操作を完了できるようにする
- Visible focusを維持する
- Semantic HTMLと適切なMUI Componentを優先する
- Label、Instruction、Errorを操作対象と関連付ける
- 動き、点滅、時間制限を必要最小限にする
- 文字拡大やViewport変更で情報を失わない

## 3. Color and contrast

- Primary text、Secondary text、Button text、Status textのContrastを確認する
- Gradient上の文字が読み取れることを確認する
- Brand redとError redを役割上も視覚上も区別する
- Error、Warning、SuccessにはTextまたはIconを併用する
- Chart seriesは色に加えて線種、Point、Label、Tooltipで区別する
- Disabled状態をContrast低下だけで表現しない

## 4. Keyboard

- Tab移動順が視覚的な順序と一致する
- Button、Link、Menu、Select、Dialog、DrawerをKeyboardで操作できる
- EnterとSpaceの動作がComponentの標準に従う
- EscapeでDialog、Menu、Temporary Drawerを閉じられる
- Focus trapが必要なModal内で機能する
- HiddenまたはDisabledな要素へFocusが移らない
- Keyboard trapを作らない

## 5. Focus management

- Focus indicatorを消さない
- Dialogを開いたとき、Titleまたは最初の操作可能要素へFocusを移す
- Dialogを閉じたとき、起動元へFocusを戻す
- AI Drawerを開いたとき、Drawer内へFocusを移す
- AI Drawerを閉じたとき、AI相談ButtonへFocusを戻す
- Validation failure時、最初のErrorまたはError summaryへ移動できるようにする
- Routeまたは主要Content更新時に、利用者が現在位置を理解できるようにする

## 6. Forms

- すべてのForm controlに表示Labelまたはaccessible nameを付ける
- PlaceholderだけをLabelとして使用しない
- 必須項目を文字または支援技術で判別できるようにする
- Help textとError messageを対象Inputへ関連付ける
- Error reasonと修正方法を示す
- 入力形式の例を必要に応じて提供する
- Submit errorを色だけで示さない
- 処理中はButton stateとProgressを通知する

## 7. Buttons, links, and icons

- Icon-only Buttonには `aria-label` を付ける
- Button名は実行内容を表す
- LinkとButtonの役割を混同しない
- 同じaccessible nameのButtonが複数ある場合は対象を区別する
- 装飾Iconは支援技術から不要なら隠す
- Status iconにはText labelを併用する
- Click targetを極端に小さくしない

## 8. Navigation

- Navigation landmarkを使用する
- 現在位置を視覚と支援技術の両方へ示す
- Sidebar group toggleには `aria-expanded` を付ける
- GroupとItemの階層が理解できる構造にする
- SettingsをVisual orderとKeyboard orderで不自然に分離しない
- NavigationをCollapseしてもaccessible nameを維持する

## 9. Dialog and Drawer

- Accessible titleを持たせる
- Close方法を明確にする
- 開いている間はBackgroundへFocusが移らないようにする
- 閉じた後にFocusを起動元へ戻す
- Contentだけを適切にScrollさせる
- Errorや処理結果をDialog・Drawer内で通知する
- AI DrawerのMessage listとInputのLandmark・Labelを明確にする

## 10. Tables

- Table headerに意味的なHeader cellを使用する
- Captionまたは近接TitleでTableの目的を示す
- 数値、状態、操作列の意味を明確にする
- Sorting状態を支援技術へ伝える
- Pagination controlにaccessible nameを付ける
- Row actionには対象Reportを含むaccessible nameを付ける
- Empty、Loading、ErrorをTableの状態として明示する
- 横Scrollが必要な場合もKeyboardで到達できるようにする

## 11. Charts

- Chartだけに重要情報を依存させず、SummaryまたはData tableを提供する
- Chart title、期間、設備、単位を明示する
- X軸の時刻が重なる場合は表示を間引き、正確な値はTooltipまたは代替表で確認できるようにする
- TooltipはMouse hoverだけでなくKeyboard focusで取得できる方法を検討する
- 異常点は色以外の形状やTextでも区別する
- DataなしとErrorを文章で表示する
- Screen reader向けの要約を提供する

## 12. Status, alerts, and live updates

- Status Chipには表示Textを含める
- 重要なErrorを色やSnackbarだけに依存させない
- 非同期処理の開始、完了、失敗を適切に通知する
- 頻繁な更新を過度に読み上げない
- Alertは重要度に応じたRoleを使用する
- Retry可能な場合は操作を提供する

## 13. Typography and zoom

- 小さい文字を増やしすぎない
- 文字拡大時に切れ、重なり、操作不能がないことを確認する
- 固定高さComponent内でTextを隠さない
- 長い日本語、英数字、Filenameを適切に折り返すか、省略とTooltipを併用する
- 行間と段落間隔を確保する

## 14. Motion

- `prefers-reduced-motion` を尊重する
- 点滅、激しいAnimation、不要なParallaxを使用しない
- 自動更新やAnimationを理解・操作の妨げにしない
- Progress表示は処理中であることをTextでも確認できるようにする

## 15. Loading and error recovery

- Loading中もPageまたはCardのPurposeが分かるようにする
- Skeletonだけで処理内容が不明な場合はTextを併用する
- Error messageに原因の概要と次の操作を示す
- 入力Errorで入力済み内容を不必要に失わない
- Retry後にFocusが予期しない場所へ移動しない

## 16. AI consultation accessibility

- AI相談ButtonとDrawer titleを明確にする
- 利用者MessageとAI Messageを区別できるText構造にする
- 新しい回答を適切に通知するが、読み上げを過度に割り込ませない
- 参照元をKeyboardで開けるようにする
- 回答生成中、完了、失敗を通知する
- 根拠不足の回答を視覚表現だけで示さない
- Input、Send、Cancelのaccessible nameを明確にする

## 17. Testing checklist

- Keyboardだけで主要フローを完了できる
- Focus indicatorが見える
- Tab orderが自然である
- Dialog・DrawerのFocusが戻る
- IconButtonにaccessible nameがある
- Form labelとErrorが関連付いている
- Statusを色なしでも理解できる
- Table headerとPaginationが読み取れる
- ChartにText summaryまたは代替手段がある
- 200%程度のZoomで主要操作が可能である
- Reduced motion設定が尊重される
- Loading、Empty、Errorが支援技術でも理解できる

## 18. Definition of done

アクセシビリティ対応は、次を満たしたとき完了とする。

- Mouse以外の操作方法がある
- 主要情報が色だけに依存していない
- Componentに適切なName、Role、Stateがある
- Focusの移動と復帰が正しい
- Form errorを理解して修正できる
- Table、Chart、Dialog、Drawerが代替手段を含め利用可能である
- Loading、Success、Errorが通知される
- 実施した確認と未確認事項を記録している
