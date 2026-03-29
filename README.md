# ペットみまもりカメラ

## 概要
人感センサーで犬の動きを検知し、ESP32カメラで撮影。
Wi-Fi経由でPCに送信後、MobileNetで犬かどうかを判定し、
Discordへリアルタイム通知するIoTシステム。

## 使用機材
- ESP32-WROVER
- OV3660（カメラモジュール）
- HC-SR501（人感センサー）
- LED 赤・青・緑（単色LED × 3）
- 抵抗 220Ω × 3

## 使用言語・環境
- C++（Arduino）
- Python
- Arduino IDE
- PyTorch / torchvision / Pillow
- Discord Webhook

## システム構成
HC-SR501 → ESP32-WROVER → Wi-Fi → PC → MobileNetV2 → Discord
