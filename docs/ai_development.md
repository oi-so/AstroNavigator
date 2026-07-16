# AI Development Guide

## Goal

AIは本プロジェクトの設計思想を尊重し、
既存設計を壊さずにコードを作成する。

---

## 必ず守ること

・97_architecture_principles.md を守る

・98_naming_convention.md を守る

・99_glossary.md の用語を使う

・既存の設計を優先する

・新しい概念を勝手に追加しない

・責務を増やさない

・抽象クラスを優先する

・Platform Independent を維持する

・Scene First を維持する

・Event Driven を維持する

・Rendererは天文学計算をしてはいけない

・GUIからSkyfieldを直接呼んではいけない

・GUIからASCOMを直接呼んではいけない


## AI Checklist

この変更で

□ 新しい責務が増えないか

□ Scene Firstを守るか

□ Layerへ追加するだけで実現できないか

□ SkyObjectで表現できないか

□ Event化できないか

□ Interfaceを追加すべきか

□ 名前は98に従っているか

□ 用語は99にあるか

□ 用語などがない場合にはmdに追記しているか