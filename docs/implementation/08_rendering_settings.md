# 08. Rendering Settings

## 1. 目的

描画設定を Scene に集約し、Renderer と Layer が同じ設定を参照できるようにする。

## 2. 完成した機能

- RenderingSettings
- 等級制限
- GridSettings
- 座標系グリッドごとの表示ON/OFF
- 座標系グリッドごとの色設定

## 3. 実装クラス

- RenderingSettings
- GridSettings
- ColorSettings

## 4. 処理

```text
Scene
    ↓
RenderingSettings
    ↓
Renderer
    ↓
Layer
```

## 5. 設計判断

描画設定をCameraから分離した。

GridSettings は RenderingSettings の一部として保持する。
これにより、赤道座標グリッド、方位高度座標グリッド、将来の銀河座標グリッドを同じ仕組みでON/OFFできる。

## 6. TODO

- 恒星サイズ
- 恒星色
- 星雲の描画設定
- ラベル設定
