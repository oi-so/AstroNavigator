# 02. Software Architecture

## 1. 設計方針

本ソフトウェアはモジュール構成を採用する。

各モジュールは責務を明確に分離し、可能な限り独立して開発・テストできるものとする。

---

## 2. 設計原則

- GUIと計算処理を分離する
- GUIと望遠鏡ドライバを直接接続しない
- モジュール間の依存を最小限にする
- プラットフォーム依存コードを限定する
- 将来的な機能追加を容易にする

---

## 3. モジュール

aplication
astronomy
scene
sky
Mount
Tracking
Camera
Plate Solve
Rendering
GUI

---

## 4. 依存関係

GUI

↓

Senceモジュール

↓

各機能モジュール

↓

外部ライブラリ
(Skyfield、ASCOM、OpenCV等)

## Senceモジュール

Senceモジュール はアプリケーション全体の状態を管理する中核モジュールである。

Senceモジュール は以下のコンポーネントで構成される。

- Scene
- SceneController
- EventBus

### Scene

Scene はアプリケーション全体の状態を保持する。

Scene 自身は状態を保持するのみであり、状態変更のロジックは持たない。

### SceneController

SceneController は Scene を変更する唯一の公開インターフェースとする。

GUI や各モジュールは Scene を直接変更せず、必ず SceneController を経由する。

SceneController は

- Scene の更新
- Event の発行

のみを担当する。

天文学計算、描画、機器制御などの責務を持ってはならない。

### EventBus

Scene の変更通知は EventBus を利用して各モジュールへ通知する。

EventBus はイベント配送のみを担当し、
状態は保持しない。

---

## 5. ドライバ設計

望遠鏡・カメラなどの機器は抽象インターフェースを介して制御する。

対応ドライバ例

- ASCOM
- Alpaca
- INDI
- Simulator

---

## 6. プラットフォーム

Windowsでは全機能を利用可能とする。

macOSおよびLinuxでは利用可能な機能のみを有効化し、未対応機能は無効化または代替手段を提供する。

---

## 7. 拡張性

以下を追加できる構造とする。

- 新しい星表
- 新しい人工衛星ソース
- 新しい架台
- 新しいカメラ
- 新しい描画レイヤー
- 新しい観測支援機能