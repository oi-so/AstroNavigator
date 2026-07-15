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

# 6. Telescope Support

優先順位

1. E-ZEUS II
2. EQ6-R
3. その他 ASCOM 対応架台

将来的には ASCOM 以外の望遠鏡制御方式への対応も視野に入れる。

---

# 7. Design Philosophy

本ソフトウェアは

「プラネタリウムソフトにISS追尾機能を追加する」

という思想で設計する。

ISS追尾はソフトウェア全体の一機能として実装し、通常の天体観測でも日常的に利用できることを重視する。

---

# 8. Open Source

ソースコードは Git および GitHub で管理する。

十分な完成度に達した段階で Public Repository として公開し、オープンソースソフトウェアとして開発を継続する。