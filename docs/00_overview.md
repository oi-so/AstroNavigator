# AstroNavigator（仮称）

> An open-source planetarium and telescope control software for visual observation, astrophotography, and satellite tracking.

---

# 1. Overview

AstroNavigator は、プラネタリウム機能、天体検索、望遠鏡制御、人工衛星表示、ISS自動導入・追尾などを一つに統合した天体観測支援ソフトウェアである。

本ソフトウェアは、日常の天体観測から彗星、人工衛星等の観測まで幅広く利用できる統合環境を目指す。

---

# 2. Objectives

本プロジェクトの目的は以下の通りである。

- プラネタリウムソフトウェアの開発
- 天体導入支援
- GoTo望遠鏡制御
- 多数の天体の検索、導入機能
- 彗星等の移動速度が異なる天体の追尾
- 人工衛星表示
- ISS自動導入
- ISS自動追尾
- 将来的な画像認識による閉ループ追尾

---

# 3. Target Users

開発は以下の順番で対象を広げる。

1. 開発者本人
2. 学校の天文気象部
3. 一般ユーザー

十分な完成度が得られた段階でオープンソースソフトウェアとして公開する。

---

# 4. Supported Platforms

最終目標

- Windows
- macOS
- Linux

開発初期は Windows を優先し、望遠鏡制御を実装する。

プラネタリウム機能などは macOS 上でも開発・動作できる構成とする。

---

# 5. Development Policy

GUI

- PySide6

主要言語

- Python

ライブラリ

- Skyfield
- Astropy
- NumPy
- OpenCV

---

# 6. Current Implementation

2026年8月12日時点では、`develop` ブランチの Scene を中心にした 2D プラネタリウムと E-ZEUS II 制御を実装している。

- Scene が時刻、観測地、SkyCamera、SkyObject、描画設定、架台状態を保持する
- SceneController が Scene 変更の公開インターフェースとなる
- Renderer は Scene を読み取り、LayerManager 経由で Grid、Constellation、Object、Label、Mount、Selection を描画する
- ProjectionManager は標準投影として `StereographicProjection` を保持する
- ステレオ投影上で赤道座標・地平座標グリッドを同時に描画できる
- HYG恒星カタログ、星座線、JPL DE440s天体暦をローカルへ保存して読み込む
- ObjectIndex は天体種別、等級、赤経、赤緯を使って表示候補を高速に絞り込む
- 時刻の停止、等速、加減速、任意日時への変更に対応する
- E-ZEUS II の接続、現在位置取得、導入、同期、停止、恒星時追尾に対応する
- MountLayer により架台の現在方向を SkyView 上へ表示する

現時点の主な未実装・未完成事項は以下である。

- 太陽、月、惑星の位置・等級計算と描画
- ISSを含む人工衛星の軌道要素読込み、位置計算、予想経路表示
- Messier、NGC、ICカタログの読込みと別名検索
- 動的天体の位置取得時に、すべての呼出し元から時刻と観測地点を渡す処理
- 固定天体用空間インデックスと動的天体用列挙・キャッシュの分離
- カタログの更新期限、取得失敗時の前回データ利用、手動更新

---

# 7. Telescope Support

優先順位

1. E-ZEUS II
2. EQ6-R
3. その他 ASCOM 対応架台

将来的には ASCOM 以外の望遠鏡制御方式への対応も視野に入れる。

---

# 8. Design Philosophy

本ソフトウェアは

「プラネタリウムソフトにISS追尾機能を追加する」

という思想で設計する。

ISS追尾はソフトウェア全体の一機能として実装し、通常の天体観測でも日常的に利用できることを重視する。

---

# 9. Open Source

ソースコードは Git および GitHub で管理する。

十分な完成度に達した段階で Public Repository として公開し、オープンソースソフトウェアとして開発を継続する。
