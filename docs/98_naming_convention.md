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