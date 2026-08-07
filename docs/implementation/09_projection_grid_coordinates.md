# 09. Projection and Grid Coordinates

## 1. 目的

Projection を LinearProjection と HorizontalLinearProjection のどちらに切り替えても、座標系グリッドを描画できるようにする。

## 2. 問題

以前の GridLayer は、CoordinateGrid が返す座標型と Projection が受け取る座標型が常に一致すると仮定していた。

そのため、Application の ProjectionManager を LinearProjection に変更した状態で HorizontalGrid を描画すると、HorizontalGrid が `visible_bounds()` の戻り値を HorizontalPosition として扱い、実際には Position が返ってクラッシュしていた。

同じ構造のままでは、HorizontalLinearProjection で EquatorialGrid を描画する場合にも同種の問題が起きる。

## 3. 修正方針

GridLayer は座標変換を行わず、Projection へ委譲する。

CoordinateGrid は自分の座標系のグリッド線だけを生成する。
Projection はグリッド座標の座標系を受け取り、現在の投影方式に必要な座標へ変換してから画面座標へ投影する。

## 4. 実装

- `Projection.project_grid_position()` を追加した
- `LinearProjection` は HorizontalPosition を赤経赤緯へ変換して描画できるようにした
- `HorizontalLinearProjection` は Position を方位高度へ変換して描画できるようにした
- `CoordinateTransformer.horizontal_to_equatorial()` を追加した
- `EquatorialGrid` は SkyCamera の赤経赤緯中心と FOV から表示範囲を作るようにした
- `HorizontalGrid` は SkyCamera の中心を方位高度へ変換し、地平座標上の表示範囲を作るようにした
- `GridLayer` は EquatorialGrid と HorizontalGrid の両方を登録するようにした

## 5. 設計判断

Renderer と Layer は描画だけを担当する。

座標系の相互変換は CoordinateTransformer と Projection に閉じ込めた。
これにより、座標系グリッドは投影方式と独立して表示できる。

## 6. 確認

`tests/rendering/test_grid_layer_projection.py` を追加し、以下を確認した。

- LinearProjection で GridLayer が例外なく描画される
- HorizontalLinearProjection で GridLayer が例外なく描画される
