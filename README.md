# ペットみまもりカメラ

人感センサーで犬の動きを検知し、ESP32カメラで撮影。Wi-Fi経由でPCに送信後、MobileNetV2で犬かどうかを判定し、Discordへリアルタイム通知するIoTシステム。

## システム構成

```
HC-SR501 → ESP32-WROVER → Wi-Fi → PC → MobileNetV2 → Discord
（人感センサー）（撮影・送信）        （画像認識）  （通知）
```

## 使用機材

- ESP32-WROVER（Freenove ESP32-WROVER Basic Starter Kit）
- OV3660（カメラモジュール）
- HC-SR501（人感センサー）
- 単色LED × 3（赤・青・緑）
- 220Ω抵抗 × 3

## 使用言語・環境

- C++（Arduino）
- Python
- Arduino IDE
- PyTorch / torchvision / Pillow
- Discord Webhook

## LEDステータス

| LED | 色 | タイミング |
|---|---|---|
| 緑 | 点灯 | WiFi接続成功 |
| 青 | 点灯 | センサー検知〜送信完了 |
| 赤 | 点滅 | カメラ失敗・PC接続失敗 |

## セットアップ

### ESP32側（main.ino）

以下の部分を自分の環境に合わせて書き換えてください。

```cpp
const char *ssid     = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";
#define REMOTE_IP "YOUR_PC_IP"
```

### PC側（server.py）

以下の部分を自分のDiscord Webhook URLに書き換えてください。

```python
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"
```

### サーバーの起動

`start_server.bat` をダブルクリックするとサーバーが起動します。
