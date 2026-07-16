# AI Instructions

このプロジェクトは天文観測ソフトです。

設計書は docs/ を参照してください。

必ず
- ai_development.md
- docs/97_architecture_principles.md
- docs/98_naming_convention.md
- docs/99_glossary.md

を読んでからコードを生成してください。

状態はSceneに集約されています。

GUIからCoreへ依存します。

Rendererは描画のみを担当します。

SkyObjectは表示対象の基底クラスです。

LayerManagerで表示を管理します。

新しい概念を追加する場合は、
まず99_glossary.mdを更新してください。