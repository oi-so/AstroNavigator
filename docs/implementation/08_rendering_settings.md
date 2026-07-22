08 Rendering Settings

1. 目的

2. 完成した機能

- RenderingSettings
- 等級制限

3. 実装クラス

RenderingSettings

4. 処理

Scene
    ↓
RenderingSettings
    ↓
Renderer

5. 設計判断

描画設定をCameraから分離した。

6. TODO

- 恒星サイズ
- 恒星色
- 星雲の描画設定
- ラベル設定