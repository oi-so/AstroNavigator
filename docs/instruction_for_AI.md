## 結合ファイル一覧
- 1. ai_development.md (1.1 KB)
- 2. 97_architecture_principles.md (1008 B)
- 3. 98_naming_convention.md (3.1 KB)
- 4. 99_glossary.md (4.5 KB)


## 1. ai_development.md

```md
# AI Development Guide

## Goal

AIは本プロジェクトの設計思想を尊重し、
既存設計を壊さずにコードを作成する。

---

## 必ず守ること

・97_architecture_principles.md を守る

・98_naming_convention.md を守る

・99_glossary.md の用語を使う

・既存の設計を優先する

・新しい概念を勝手に追加しない

・責務を増やさない

・抽象クラスを優先する

・Platform Independent を維持する

・Scene First を維持する

・Event Driven を維持する

・Rendererは天文学計算をしてはいけない

・GUIからSkyfieldを直接呼んではいけない

・GUIからASCOMを直接呼んではいけない


## AI Checklist

この変更で

□ 新しい責務が増えないか

□ Scene Firstを守るか

□ Layerへ追加するだけで実現できないか

□ SkyObjectで表現できないか

□ Event化できないか

□ Interfaceを追加すべきか

□ 名前は98に従っているか

□ 用語は99にあるか

□ 用語などがない場合にはmdに追記しているか
```

## 2. 97_architecture_principles.md

```md
# Architecture Principles

## 1. Scene First

ソフトウェアの状態は必ずSceneに集約する。

---

## 2. Data Driven

データを中心に設計する。

GUIはデータを表示するだけとする。

---

## 3. Interface First

実装ではなく抽象クラスへ依存する。

---

## 4. Event Driven

モジュール間通信はイベントを利用する。

---

## 5. Renderer Independent

描画と天文学計算を完全に分離する。

---

## 6. Platform Independent

OS依存コードはDevice層に限定する。

---

## 7. Plugin Friendly

機能追加はプラグインで行える設計を目指す。

---

## 8. Offline First

ネットワークが利用できなくても基本機能は動作する。

必要なデータのみ更新する。

---

## 9. Astronomy Accuracy First

見た目よりも天文学的な正確性を優先する。

---

## 10. Performance Where Needed

性能最適化は必要な箇所に限定し、
可読性を犠牲にしない。
```

## 3. 98_naming_convention.md

```md
# 98. Naming Convention

本ドキュメントは、本プロジェクトにおける命名規則を定義する。

---

# 1. 基本方針

名前だけで責務が分かることを目標とする。

略称は一般的なものを除き使用しない。

可読性を優先する。

---

# 2. 命名規則

## クラス

PascalCase

例

Scene

SkyObject

LayerManager

Renderer

---

## 抽象クラス

実装ではなく概念名を使う。

例

Mount

Camera

Renderer

Catalog

Projection

---

## 実装クラス

実装方法を前につける。

例

ASCOMMount

SimulatorMount

OpenGLRenderer

SkyfieldCatalog

---

## Interface

PythonではABCを利用するため

Iは付けない。

×

IMount

○

Mount

---

## データクラス

State

Info

Data

Config

Result

などを付ける。

例

MountState

CameraState

SceneState

TrackingConfig

PlateSolveResult

---

## Manager

管理クラス。

例

LayerManager

CatalogManager

PluginManager

---

## Controller

制御クラス。

例

SceneController

TrackingController

CameraController

---

## Engine

計算エンジン。

例

AstronomyEngine

RenderEngine

---

## Provider

データ取得。

例

CatalogProvider

TLEProvider

ImageProvider

---

## Factory

生成。

例

SkyObjectFactory

ProjectionFactory

---

## Event

イベント。

例

SceneChangedEvent

MountConnectedEvent

TimeChangedEvent

SelectionChangedEvent

---

# 3. 関数

snake_case

例

get_position()

update_scene()

draw_object()

calculate_altaz()

---

取得は

get_

設定は

set_

更新は

update_

計算は

calculate_

変換は

convert_

生成は

create_

削除は

remove_

追加は

add_

検索は

find_

読み込みは

load_

保存は

save_

描画は

draw_

---

# 4. 変数

snake_case

例

current_time

selected_object

mount_state

camera_fov

observer

scene

renderer

---

bool

is_

has_

can_

should_

enabled

visible

例

is_connected

has_focus

can_track

is_visible

---

list

複数形

stars

planets

layers

visible_objects

---

dict

○○_map

catalog_map

layer_map

---

set

○○_set

visible_set

selected_set

---

# 5. 定数

UPPER_SNAKE_CASE

DEFAULT_FOV

MAX_MAGNITUDE

MIN_ZOOM

ISS_UPDATE_INTERVAL

---

# 6. Enum

PascalCase

TrackingMode

ProjectionType

LayerType

ThemeType

---

値

UPPER_CASE

NONE

OBJECT

MOUNT

SATELLITE

---

# 7. Private

_

例

_update_scene()

_renderer

_scene

---

# 8. ファイル名

snake_case

scene.py

sky_object.py

layer_manager.py

tracking_controller.py

---

# 9. ディレクトリ名

小文字

単数形

astronomy

tracking

catalog

rendering

gui

camera

mount

---

# 10. 略称

使用可

RA

Dec

Alt

Az

UTC

LST

FOV

ISS

TLE

DSO

GUI

FPS

NGC

IC

API

NG

cfg

mgr

obj

tmp

val

calc

conv

など意味が分かりにくい略称

---

# 11. 型名

Coordinate

Position

Direction

Rotation

Magnitude

Observer

Projection

---

# 12. コメント

コメントは

「なぜそうしたか」

を書く。

コードの説明は書かない。

×

iを1増やす

○

ASCOMドライバの仕様上ここで同期が必要
```

## 4. 99_glossary.md

```md
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
```
