# ✅ visionOS特化 開発準備チェックリスト（2025）

Apple Vision Pro / visionOS 向けアプリ開発のための実践チェックリスト。  
Mac（Xcode環境）を前提に、**開発準備 → 設計 → 実装 → テスト → 配布** の5ステップ構成です。

---

## 🧩 1️⃣ 開発環境の準備

| 項目 | 内容 | チェック |
|------|------|----------|
| 💻 **Mac環境** | macOS Sequoia 26.x 以降（Apple Silicon対応推奨） | ☐ |
| 🧰 **Xcode** | Xcode 16.0 以上（visionOS SDK含む） | ☐ |
| ☁️ **Xcode Cloud（任意）** | CI/CD自動ビルド設定を有効化 | ☐ |
| 🧠 **Swift & SwiftUI** | Swift 5.10+、SwiftUI for visionOS対応 | ☐ |
| 📦 **visionOS SDK** | Xcodeの追加コンポーネントに含まれる。インストール確認 | ☐ |
| 🧾 **Apple Developer登録** | Developer Program（有料）加入済み | ☐ |
| 🪪 **証明書・プロビジョニング** | visionOS用ProfileをApp Store Connectで作成 | ☐ |

---

## 🧠 2️⃣ 開発設計の基本指針（Human Interface Guidelines）

| 項目 | 内容 | チェック |
|------|------|----------|
| 👁 **空間デザイン理解** | 2D／3D／空間UIのレイヤー構造を把握 | ☐ |
| 🪟 **Volume / Window / Full Space** | 3種類のアプリ表示モードを理解 | ☐ |
| 🎯 **フォーカスと深度** | Eye Trackingを中心にUI設計 | ☐ |
| 🌈 **Material効果** | RealityKit / SceneKitを用いた透明・反射素材の活用 | ☐ |
| 📱 **UIKit移行対応** | UIKitアプリのvisionOS移行計画（UIKit → SwiftUI） | ☐ |
| 🕹 **インタラクション設計** | GestureKit、Hand Tracking対応 | ☐ |
| 🗣 **音声／空間オーディオ** | AudioEngine / AVFoundation / Spatial Audio活用 | ☐ |
| 👂 **アクセシビリティ** | VoiceOver / Captions対応 | ☐ |

---

## 🧰 3️⃣ 実装フェーズ

| 項目 | 内容 | チェック |
|------|------|----------|
| 🧱 **RealityKit統合** | ARオブジェクトや3D空間演出を構築 | ☐ |
| 🪶 **SwiftUI for visionOS** | `WindowGroup`, `ImmersiveSpace`, `RealityView`利用 | ☐ |
| 🧩 **Scene Understanding** | 空間内の深度・平面認識を利用 | ☐ |
| 🔊 **Spatial Audio** | 距離・方向による音響再現 | ☐ |
| 💬 **Multimodal AI連携（任意）** | CoreML / OpenAI / Gemini API連携可 | ☐ |
| 🔐 **Privacy / Security設定** | カメラ・マイク・空間スキャンの権限設定 | ☐ |

---

## 🧪 4️⃣ テスト・デバッグ

| 項目 | 内容 | チェック |
|------|------|----------|
| 🧭 **Simulator（visionOS）** | Xcodeに同梱のVision Proシミュレーター利用 | ☐ |
| 🪄 **Reality Composer Pro** | 空間アセットの事前プレビュー・微調整 | ☐ |
| 🧍 **Physical Test（実機）** | Vision Pro実機テスト（Apple Developer Center予約） | ☐ |
| 🐞 **Debug / Profiling** | InstrumentsでGPU負荷・フレームレートを測定 | ☐ |
| 📊 **テレメトリ** | Xcode Cloudでクラッシュ・パフォーマンス確認 | ☐ |

---

## 🚀 5️⃣ 配布・公開

| 項目 | 内容 | チェック |
|------|------|----------|
| 🏁 **ビルド署名** | visionOSターゲットのビルド署名を確認 | ☐ |
| 📦 **TestFlight配布** | 内部・外部テスター向けビルド配布 | ☐ |
| 🏪 **App Store Connect** | visionOSカテゴリ登録・スクリーンショット提出 | ☐ |
| 🌍 **多言語対応（任意）** | `Localizable.strings`設定 | ☐ |
| 💡 **マーケティング素材** | App Clip動画・空間紹介ムービー準備 | ☐ |

---

## ⚙️ 推奨ツール＆リソースまとめ

| 用途 | ツール・リソース |
|------|------------------|
| 3D/空間オーサリング | Reality Composer Pro / Blender / Unity PolySpatial |
| コード開発 | Xcode 16+ / Swift Playgrounds (iPad) |
| デザイン／UI | SF Symbols 6 / Figma visionOS Kit |
| 学習 | [Apple Developer Tutorials](https://developer.apple.com/visionos/) / [WWDC2024 Videos](https://developer.apple.com/videos/) |

---

🧭 **使用方法:**  
このファイルを `~/Projects/visionOS/` などに保存し、進行状況を ☐ → ☑ に更新して管理してください。

