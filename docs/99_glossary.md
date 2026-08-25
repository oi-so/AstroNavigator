# 99. Glossary（用語集）

この文書は、本プロジェクトで使用する用語の定義をまとめたものである。

他の設計書・仕様書・ソースコードは、本用語集の定義に従うものとする。

---

# 1. Scene

## Scene

ソフトウェア全体の現在状態を保持するデータモデル。

Renderer、GUI、TrackingなどはSceneを参照して処理を行う。

### 責務

- 現在時刻
- 観測地点
- SkyCamera
- SkyObject一覧
- ObjectIndex
- Selection
- Focus
- RenderingSettings
- GuiSettings
- SkyfieldContext
- Mountと架台現在位置
- SatelliteRenderSnapshot
- CometRenderSnapshot

### 責務ではないもの

- 描画
- 座標計算
- 更新処理

---

## SceneController

Scene を変更する唯一の公開インターフェース。

Scene の更新後に EventBus を通じてイベントを通知する。

天文学計算・描画・機器制御は担当しない。

---

## Observer

観測地点を表す。

### 保持する情報

- 緯度
- 経度
- 標高
- タイムゾーン

---

## Time

現在のシミュレーション時刻。

UTCを基準とする。

時間倍率も保持する。

---

## Selection

現在ユーザーが選択しているSkyObject。

画面中心とは一致しない場合がある。

---

## Focus

画面の中心、または追尾対象。

Selectionとは独立する。

---

## ObjectIndex

Scene に存在する SkyObject へ高速にアクセスするためのインデックス。

ObjectIndex は SkyObject 自体を保持するものではなく、
Scene に登録された SkyObject を検索・列挙するための補助構造である。

### 責務

- IDによる検索
- 名前による検索
- 最近傍オブジェクトの検索
- 表示範囲内オブジェクトの取得
- ObjectTypeごとの列挙

### 責務ではないもの

- SkyObjectの生成
- SkyObjectの削除
- Catalogの管理
- GUI一覧表示
- 描画

ObjectIndex は Scene と同期し、Renderer や検索機能から利用される。

固定座標を前提とする空間・等級インデックスには固定天体だけを登録する。太陽系天体や人工衛星などの動的天体は、ID・名前・種類の検索対象には含めるが、固定座標の空間インデックスには含めない。動的天体の表示候補は種別ごとのリストから列挙し、現在時刻と観測地点で位置を求める。

---

# 2. Sky

## SkyObject

天球上へ表示されるすべてのオブジェクトの基底クラス。

### 例

- Star
- Planet
- Moon
- Satellite
- Comet
- DeepSkyObject

### 責務

- 名前
- 現在位置取得
- 等級
- 描画属性

### 責務ではないもの

- 描画
- 更新処理

`get_position(time, observer)` と `get_magnitude(time, observer)` を共通インターフェースとする。固定天体は引数を使用せず固定値を返し、動的天体は現在時刻と観測地点を使用する。

### Fixed SkyObject

時刻と観測地点によって赤経赤緯が変わらない天体。

例：Star、DeepSkyObject。

### Dynamic SkyObject

時刻または観測地点によって見かけの位置・等級が変化する天体。

例：Sun、Moon、Planet、Satellite、Comet、Asteroid。

動的天体の位置を利用する呼出し元は、Scene の Time と Observer を必ず渡す。計算結果は天体の変化速度に応じて短時間キャッシュできる。
---

## Star

恒星。

---

## Planet

惑星。

---

## Moon

地球の月。

木星・土星などの惑星衛星は、将来 `NaturalSatellite` などの別概念として追加し、人工衛星を表す `Satellite` と混同しない。

---

## DeepSkyObject

メシエ・NGC・ICなどの深宇宙天体。

---

## Satellite

人工衛星。

ISSやStarlinkなど。

標準入力は GP 軌道要素の OMM CSV とする。従来TLEは互換入力として扱う。

---

## Comet

彗星。

---

## Asteroid

小惑星。

---

## CameraFOV

カメラ画角。

---

## MountMarker

架台が向いている方向。

---

## CometRenderSnapshot

彗星描画のために、現在時刻・観測地点に対して事前計算した
位置と等級のスナップショット。

Scene に保持し、Renderer はこのスナップショットを参照して描画する。

---

# 3. Rendering

## Renderer

Sceneを描画するコンポーネント。

### 入力

Scene

### 出力

画面

Rendererは天文学や望遠鏡制御を知らない。

---

## SkyCamera

天球のどの方向を、どの画角と回転角で見るかを定義する仮想カメラ。

### 保持する情報

- 視線方向
- FOV
- 回転角
- 表示限界等級

投影法は ProjectionManager が保持する。

---

## Projection

天球を2次元画面へ投影する方式。

### 例

- ステレオ投影
- 正射投影
- 魚眼投影

現在の実装では Projection は SkyObject と CoordinateGrid の座標を画面座標へ変換する。
投影方式が扱う座標系とグリッドが生成する座標系が異なる場合も、Projection が必要な座標変換を行う。

## StereographicProjection

現在の標準投影。

天球上の方向ベクトルをステレオ投影で画面へ変換する。投影コンテキストは時刻、観測地点、SkyfieldContext、観測者位置、天球基底を保持する。

---

## ProjectionManager

現在の Projection を保持するクラス。

Renderer や SceneController は ProjectionManager から Projection と ProjectionContext を取得する。

---

## LinearProjection

赤経赤緯を直接2D画面へ投影する線形投影。

主に開発・確認用の単純な投影方式である。

---

## HorizontalLinearProjection

赤経赤緯を方位高度へ変換してから2D画面へ投影する線形投影。

観測地、時刻、SkyfieldContext を利用する。

LinearProjection と HorizontalLinearProjection は、現在は開発・比較・回帰確認用として扱う。


---

## CoordinateGrid

座標系ごとのグリッド線を生成する抽象。

### 例

- EquatorialGrid
- HorizontalGrid

CoordinateGrid はグリッド線上の座標列を生成する。
画面座標への変換は Projection が担当する。

---

## GridSettings

座標系グリッドの表示設定。

座標系ごとの表示ON/OFFと色を保持する。

---

## Layer

表示対象の分類。

### 例

- 恒星
- 惑星
- DSO
- ラベル
- グリッド
- 天の川
- 架台
- ISS

---

## LayerManager

Layerを管理するクラス。

表示順・表示ON/OFFなどを管理する。

現在は Renderer が保持する。

---

# 4. Devices

## Mount

架台制御インターフェース。

### 実装例

- ASCOM
- Alpaca
- INDI
- Simulator

---

## Camera

カメラ制御インターフェース。

### 例

- Sony
- Canon
- Nikon
- ZWO

---

## Plate Solve

撮影画像から天球座標を求める機能。

---

# 5. Tracking

## Tracker

追尾制御。

---

## Predictor

人工衛星などの将来位置を計算するコンポーネント。

---

## Guider

追尾誤差を補正するコンポーネント。

---

## TrackingMode

SkyCameraやMountの追従方式。

### 例

- None
- Object
- Mount
- Satellite

---

# 6. Astronomy

## Astronomy Engine

天文学計算を行うモジュール。

### 例

- Skyfield
- SGP4
- 座標変換
- 時刻変換

---

## ICRS

国際天文基準座標系。

---

## J2000

標準エポック。

---

## Epoch

座標系の基準時刻。

---

## RA

赤経。

---

## Dec

赤緯。

---

## Alt

高度。

---

## Az

方位角。

---

## LST

地方恒星時。

---

# 7. GUI

## Dock

移動・分離可能なGUIパネル。

---

## Widget

GUI部品。

---

## Panel

Dock内の画面。

---

## Toolbar

ツールバー。

---

## Status Bar

状態表示バー。

---

# 8. Observation

## Observation Mode

表示レイヤー構成のプリセット。

### 例

- 観望
- 撮影
- 人工衛星
- ISS追尾

---

## Observation Session

1回の観測記録。

### 含まれる情報

- 日時
- 観測天体
- 撮影履歴
- GoTo履歴
- ログ

---

# 9. Design Principles

## Scene First

すべての状態はSceneに集約する。

---

## Event Driven

モジュール間通信はイベントを基本とする。

---

## Interface First

実装ではなく抽象インターフェースへ依存する。

---

## Renderer Independent

描画と計算を分離する。

---

## Platform Independent

OS依存コードは可能な限り限定する。


# 10. Naming

本プロジェクトにおけるクラス名・変数名・関数名などの命名規則は
「98_naming_convention.md」に従うものとする。
