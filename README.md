# AstroNavigator

望遠鏡架台を操作でき、ISSや人工衛星の追尾が可能なソフトウェアです。

現在は、E-ZEUS IIの制御に対応しています。

## 主な機能
- 星や星座、太陽系天体や人工衛星、メシエ、NGC天体などの表示
- 望遠鏡架台の操作
- 指定しいた天体への自動導入
- ISSなどの人工衛星の追尾


## 使用技術
- GUI: PySide6
- 望遠鏡通信: PySerial(E-ZEUS II)
- 天体計算: Skyfield


## 動作確認済み環境
- MacOS 26.6.2 / Windows 11
- uv 0.11.29

## インストール方法

### 前提条件
- git
- uv

1. このリポジトリをクローン
```
git clone https://github.com/oi-so/AstroNavigator
cd AstroNavigator
```

2. 実行環境を構築
```
uv sync
```


3. AstroNavigatorを起動
```
uv run astronavigator
```

