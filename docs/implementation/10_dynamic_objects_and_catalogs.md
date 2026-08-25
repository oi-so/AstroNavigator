## 1. 目的

太陽・月・惑星、ISS、Messier・NGC・ICを、現在の描画・検索・選択・架台導入へ安全に統合する。

2026年9月3日の資料提出までに、全種類を網羅することより、各系統を一つずつ操作可能な状態で完成させ、設計判断・精度・性能を記録することを優先する。

## 2. 2026年8月12日時点の実装状況

### 実装済み

- `StereographicProjection` を標準投影として使用
- HYG恒星カタログと星座線の読込み
- JPL DE440sのローカル保存とSkyfieldContextへの読込み
- ObjectIndexによる天体種別・等級・表示範囲の絞り込み
- ObjectLayer、LabelLayer、SelectionLayer、MountLayer
- 時刻変更、停止、等速、加減速
- E-ZEUS IIの接続、位置取得、導入、同期、停止、追尾

### 型・インターフェース実装済み（実データ未投入）

- `Planet`
- `Moon`
- `Satellite`
- `DeepSkyObject`
- `ObjectType.PLANET / MOON / SATELLITE / DSO`
- `SkyObject.get_position(time, observer)`
- `SkyObject.get_magnitude(time, observer)`

### 未完成

- 動的天体の位置・等級計算
- 全呼出し元から Time と Observer を渡す処理
- 惑星の描画処理
- 動的天体を固定座標用空間インデックスから除外する処理
- カタログの更新期限と失敗時フォールバック
- OpenNGCとISS軌道要素の読込み

## 3. 現在の問題

現在の ObjectIndex は `update()` 時に `obj.get_position()` と `obj.get_magnitude()` を引数なしで呼び、固定座標として赤緯ビンと等級順を構築する。この方式を太陽系天体や人工衛星へそのまま適用すると、未実装例外が発生するか、時刻変更後も古い位置で検索される。

また、Projection、LabelLayer、SelectionPanel、MainActionsなどにも引数なしの位置・等級取得が残っている。動的天体を追加する前に、この呼出し経路を修正する。

## 4. 採用する設計

### 固定天体

StarとDeepSkyObjectは、現在の等級・赤経・赤緯インデックスへ登録する。

### 動的天体

Planet、Moon、Satellite、Comet、Asteroidは固定座標用空間インデックスへ登録しない。初期実装ではObjectTypeごとのリストから列挙し、描画時点のTimeとObserverで位置・等級を得る。

太陽系天体は10個未満、ISSは当初1機なので、動的天体向けの高度な空間インデックスは作らない。

### キャッシュ

- 太陽・月・惑星: 約1秒
- ISS: 約0.05秒
- 観測地点変更: 全動的天体キャッシュを無効化
- 時刻の大幅変更・逆再生: 対応するキャッシュを無効化
- 軌道要素更新: Satelliteキャッシュを無効化

キャッシュのキーは少なくとも天体ID、丸めた時刻、観測地点、元データの版を含む。

## 5. 実装順

### Step 1: 動的天体共通処理

1. 固定天体か動的天体かを判別できる契約を追加する
2. ObjectIndexのID・名前・種別検索には両方を含め、空間・等級インデックスには固定天体だけを入れる
3. Projection、ObjectLayer、LabelLayer、SelectionPanel、MainActionsへSceneのTimeとObserverを渡す
4. 動的天体用キャッシュと無効化処理を追加する
5. 固定天体の描画時間が悪化していないことを測定する

完成条件:

- ダミー動的天体が時刻変更に合わせて移動する
- 選択、ラベル、中央移動、導入が同じ現在位置を使う
- HYG恒星表示に回帰がない

### Step 2: 太陽・月・惑星

1. DE440sとSkyfieldで観測地点から見た見かけの赤経赤緯を計算する
2. 地球を表示対象から除外し、太陽、月、水星から海王星までを登録する
3. 惑星の視等級を計算する
4. ObjectLayerへ太陽・月・惑星の最小描画を追加する
5. 選択パネルへ現在位置と等級を表示する

内部Positionは既存恒星と合わせるため、ICRF/J2000系との整合を保つ。表示用のDate座標と混同しない。

完成条件:

- 時間を進めると各天体が連続的に移動する
- 観測地点変更により月などの地心視差が反映される
- 既知のプラネタリウムまたはSkyfield計算値と位置を比較できる

### Step 3: ISS 1機

1. CelesTrakのOMM CSVを取得・保存する
2. Skyfieldの `EarthSatellite.from_omm()` で読込む
3. 観測地点から見たtopocentric位置を計算する
4. ISSを描画・選択し、RA/Dec、Alt/Az、距離、軌道要素元期を表示する
5. 数分先までの予想経路を描画する
6. 更新失敗時は最後に正常取得したデータを使用する

完成条件:

- ISSの現在方向と予想経路が時刻変更に追従する
- 軌道要素が古い場合に警告を表示する
- オフラインでも保存済みデータで起動できる

この段階では架台追尾へ接続しない。表示位置と時刻処理の正しさを確認した後に行う。

### Step 4: Messier・NGC・IC

1. OpenNGCの `NGC.csv` と `addendum.csv` を取得する
2. OpenNGCParserでDeepSkyObjectへ変換する
3. 正規IDとaliasesを保持する
4. `M31`、`M 31`、`NGC224`、`NGC 224`などを正規化して同一天体へ解決する
5. 銀河、散開星団、球状星団、星雲を簡単な記号で描き分ける

M40、M45などNGC/IC番号を持たない対象も扱うため、`addendum.csv`を必ず読む。同一天体のカタログ名を別オブジェクトとして重複登録しない。

完成条件:

- Messier、NGC、ICの代表天体を複数表記で検索できる
- 選択・中央移動・固定天体導入ができる
- 追加前後の天体数、ObjectIndex構築時間、1フレーム描画時間を記録する

### Step 5: 実機確認とISS追尾

1. E-ZEUS IIで恒星・惑星の導入方向を確認する
2. MountLayerの表示と実機方向を比較する
3. ISSの予測位置、更新周期、通信周期を測定する
4. 安全な停止処理を確認してから連続追尾へ接続する

## 6. データ更新方針

| データ | 標準形式 | 更新方針 |
|---|---|---|
| HYG・OpenNGC | CSV | 手動または版変更時 |
| DE440s | BSP | 通常は再取得しない |
| ISS | OMM CSV | 2時間未満では再取得せず、自動・手動更新 |

ファイルが存在するだけで更新不要とは判断しない。CatalogInfoまたは別のメタデータに取得日時、元データの版、更新期限を保持する。ダウンロードは一時ファイルへ行い、解析成功後にのみ前回ファイルと置き換える。

## 7. テスト

- 固定天体だけが空間インデックスへ入る
- 動的天体もID・名前・種別で検索できる
- 時刻・観測地点の変更で動的位置が変わる
- キャッシュ範囲内では再計算されず、無効化条件では再計算される
- OMM取得失敗時に正常な旧データが残る
- OpenNGCのaliasesが同一天体を返す
- M40、M45を検索できる
- 固定天体の描画性能に大きな回帰がない

## 8. 提出資料として残すもの

- 機能追加前後のクラス図またはデータフロー図
- 固定天体と動的天体を分離した理由
- 惑星位置を他ソフトと比較した表
- ISSの予想経路と実際の通過を比較したスクリーンショットまたは動画
- OpenNGC追加前後の天体数、起動時間、ObjectIndex構築時間、1フレーム時間
- オフライン時に前回データで動作する様子
- E-ZEUS II実機の方向とMountLayer表示の比較
- 失敗と修正内容を含むGitコミット・Issue・テスト結果

## 9. 今回は後回しにするもの

- 全活動衛星・Starlink全機の常時表示
- 精密なDSO輪郭・テクスチャ
- 惑星表面の写実描画
- 一般化したプラグイン機構
- ISS以外の人工衛星追尾
- Plate Solveとカメラ自動撮影の統合

## 10. 参考資料

- AstroNavigator `develop`: https://github.com/oi-so/AstroNavigator/tree/develop
- Skyfield Earth Satellites: https://rhodesmill.org/skyfield/earth-satellites.html
- CelesTrak GP Data Formats: https://celestrak.org/NORAD/documentation/gp-data-formats.php
- CelesTrak Usage Policy: https://celestrak.org/usage-policy.php
- OpenNGC: https://github.com/mattiaverga/OpenNGC

OpenNGCはCC BY-SA 4.0で公開されているため、配布時はライセンス表示と帰属を含める。
