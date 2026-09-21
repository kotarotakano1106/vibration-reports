# RASPI AI Design System

## 1. 目的

本書は、振動AI日報生成アプリの画面に共通する視覚表現、情報設計、操作性の基準を定義する。

対象は、ログイン画面、振動モニタリング、CSVアップロード、レポート一覧・詳細、AI相談Drawer、および将来追加する同一製品内の画面とする。

個別画面の都合で独自の色、余白、文字サイズ、影、角丸を増やさず、原則としてMUIテーマと本書のデザイントークンを使用する。

## 2. デザイン原則

1. **Operational clarity**
   - 設備状態、異常、注意、正常、次に行う操作を短時間で把握できること。
2. **Calm density**
   - 業務情報をコンパクトに表示しつつ、余白と整列によって窮屈さを抑えること。
3. **Semantic color**
   - ブランド色と状態色を混同しないこと。
4. **Progressive disclosure**
   - 高度な操作や補助情報はMenu、Dialog、Drawer、Collapseへ段階的に配置すること。
5. **Theme first**
   - 視覚的な判断はMUIテーマとデザイントークンを経由すること。
6. **Accessible by default**
   - 色、マウス操作、視覚情報だけに依存せず、キーボードと支援技術でも利用できること。
7. **Consistent feedback**
   - 読み込み、成功、警告、エラー、データなしを全機能で同じ考え方により表示すること。

## 3. デザイントークン

### 3.1 ブランドカラー

- Primary: `#E52F4C`
- Primary dark: `#9B1530`
- Primary light: `#FF6476`
- Primary gradient: `linear-gradient(135deg, #C51635 0%, #ED3653 58%, #FA6072 100%)`
- Sidebar gradient: `linear-gradient(180deg, #94152A 0%, #D32140 48%, #7B1022 100%)`

ブランドレッドは、製品識別、主要操作、選択状態に使用する。異常状態を示す色として無差別に使用しない。

### 3.2 Surface

- App background: `#F5F7F9`
- Main surface: `#FFFFFF`
- Subtle surface: `#FBFCFD`
- Border: `#DCE5EB`

### 3.3 Text

- Primary text: `#25323B`
- Secondary text: `#74838D`
- Subtle text: `#98A4AC`
- Text on strong brand surface: `#FFFFFF`

### 3.4 Semantic status

- Error: `#B33A45`
- Warning: `#C58627`
- Success: `#2E7D6B`
- Information / chart series: `#357493`

状態は色だけで伝えず、「異常」「注意」「正常」などの文字、アイコン、補足を併用する。

### 3.5 Chart

- Measured vibration: `#357493`
- Warning threshold: `#C58627`
- Error threshold: `#B33A45`
- Grid and axis: MUI themeのdividerおよびsecondary textを使用する
- Anomaly point: error colorと形状・Tooltipを併用する

## 4. Typography

推奨フォントスタック:

```text
Roboto, Noto Sans JP, Segoe UI, sans-serif
```

Desktop基準:

- Page title: 15px / 700
- Card title: 12px / 700
- Body: 10px / 400
- Secondary: 9px
- Caption: 8px
- Summary value: 18px / 700
- Button: 10px / 600

文字を過度に小さくしない。1280×720で読みにくい場合は情報量を減らし、文字サイズの縮小だけで解決しない。

## 5. Spacing

MUIの `theme.spacing()` を使用し、8pxグリッドを基本とする。

- 0.5 = 4px
- 1 = 8px
- 1.5 = 12px
- 2 = 16px
- 2.5 = 20px
- 3 = 24px

同じ階層のCard、Header、Formでは余白を統一する。

## 6. Shape

- Small controls: 8px
- Navigation items: 8px
- Cards: 12pxから14px
- Dialog / Drawer internal cards: 12px
- Status Chips: pill shape

角丸を装飾目的で増やしすぎず、同じ役割の部品では値を統一する。

## 7. Elevation and border

- Card: `0 6px 20px rgba(53, 63, 72, 0.06)`
- Header: elevationなし、下境界線1px
- Permanent navigation:境界線なし
- Temporary Drawer: MUI標準のelevationを使用可能
- Dialog: MUI標準を基準にし、背景との分離が不足する場合のみ調整する

強い影を多用せず、境界線、Surface、余白で階層を表現する。

## 8. Iconography

- MUI Iconsを基本とする
- 同じ操作には同じアイコンを使用する
- 装飾目的だけのアイコンを増やさない
- IconButtonには必ず `aria-label` を設定する
- 状態アイコンには文字ラベルを併用する

## 9. Motion

- Motionは状態変化と空間関係を理解しやすくする目的に限定する
- 過度な反復、点滅、長時間Animationを避ける
- `prefers-reduced-motion` を尊重する
- Dialog、Drawer、CollapseはMUI標準Motionを基本とする

## 10. Feedback states

すべてのデータ取得・更新機能は、必要に応じて次を定義する。

- Loading
- Empty
- Success
- Warning
- Error
- Retry
- Disabled / processing

Snackbarだけに重要なエラーを依存させず、操作箇所の近くにも状態を表示する。

## 11. Theme implementation

- Primitive tokenは `tokens.ts` に置く
- Semantic roleは `theme.ts` へ割り当てる
- TypeScriptのTheme拡張は `mui.d.ts` に置く
- アプリ全体のThemeProviderは1つにする
- 共通MUI上書きはThemeの `components` で管理する
- 局所レイアウトは `sx`、再利用スタイルは `styled()` または共通コンポーネントを使用する
- PageやFeature内でブランド色を直接ハードコードしない

## 12. Design review checklist

- ブランド色と状態色を区別している
- Typography、Spacing、ShapeがTokenに従っている
- Loading、Empty、Errorが定義されている
- 色だけで状態を伝えていない
- 1440×900と1280×720で情報が欠落しない
- キーボード操作とFocusが確認できる
- 新しいTokenの追加理由が説明できる
- 同じ意味のTokenやStyleを重複して追加していない
