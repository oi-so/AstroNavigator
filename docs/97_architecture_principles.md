# Architecture Principles

## 1. Scene First

ソフトウェアの状態は必ずSceneに集約する。
Scene の状態変更は必ず SceneController を経由する。
Scene はデータ保持のみを担当する。

---

## 2. Data Driven

データを中心に設計する。

GUIはデータを表示するだけとする。

---

## 3. Interface First

実装ではなく抽象クラスへ依存する。

---

## 4. Event Driven

モジュール間通信はイベントを利用する。

---

## 5. Renderer Independent

描画と天文学計算を完全に分離する。

---

## 6. Platform Independent

OS依存コードはDevice層に限定する。

---

## 7. Plugin Friendly

機能追加はプラグインで行える設計を目指す。

---

## 8. Offline First

ネットワークが利用できなくても基本機能は動作する。

必要なデータのみ更新する。

---

## 9. Astronomy Accuracy First

見た目よりも天文学的な正確性を優先する。

---

## 10. Performance Where Needed

性能最適化は必要な箇所に限定し、
可読性を犠牲にしない。