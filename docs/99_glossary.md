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
- LayerManager
- SkyObject一覧
- Selection
- Focus
- MountState
- CameraState

### 責務ではないもの

- 描画
- 座標計算
- 更新処理

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
- MountMarker
- CameraFOV

### 責務

- 名前
- 現在位置取得
- 等級
- 描画属性

### 責務ではないもの

- 描画
- 更新処理

---

## Star

恒星。

---

## Planet

惑星。

---

## Moon

衛星。

地球の月だけでなく木星・土星などの衛星も含む。

---

## DeepSkyObject

メシエ・NGC・ICなどの深宇宙天体。

---

## Satellite

人工衛星。

ISSやStarlinkなど。

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

天球をどのように観測・投影するかを定義する仮想カメラ。

### 保持する情報

- 視線方向
- FOV
- 回転角
- 投影法
- TrackingMode

---

## Projection

天球を2次元画面へ投影する方式。

### 例

- ステレオ投影
- 正射投影
- 魚眼投影

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