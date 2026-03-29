#include "esp_camera.h" // ESP32のカメラを操作する関数が入っている
#include <WiFi.h>       // WiFi接続、TCP通信の関数が入っている

// カメラピン定義 - カメラモジュールの線がESP32のどのピンに繋がっているか定義
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  21
#define SIOD_GPIO_NUM  26
#define SIOC_GPIO_NUM  27
#define Y9_GPIO_NUM    35
#define Y8_GPIO_NUM    34
#define Y7_GPIO_NUM    39
#define Y6_GPIO_NUM    36
#define Y5_GPIO_NUM    19
#define Y4_GPIO_NUM    18
#define Y3_GPIO_NUM     5
#define Y2_GPIO_NUM     4
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM  23
#define PCLK_GPIO_NUM  22

// WiFiの設定
const char *ssid     = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";

// 送信先PCのIPアドレスとポート
#define REMOTE_IP   "YOUR_PC_IP"
#define REMOTE_PORT 8888

#define SENSOR_PIN 13 // HC-SR501（人感センサー）のピン

// 各LEDのピン
#define LED_GREEN 32
#define LED_BLUE  33
#define LED_RED   14

camera_config_t config; // カメラの設定をまとめて入れる構造体
WiFiClient      client; // TCP接続を管理するオブジェクト

// エラー時に赤LEDをtimes回点滅させる関数
void blinkError(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_RED, HIGH); // LED_REDをHIGHに書き換える = 点灯
    delay(200);
    digitalWrite(LED_RED, LOW);  // LED_REDをLOWに書き換える = 消灯
    delay(200);
  }
}

// config構造体にカメラの設定値を入れる関数
void camera_init() {
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;      // クロック周波数
  config.pixel_format = PIXFORMAT_JPEG; // JPEG形式で画像を取得
  config.frame_size   = FRAMESIZE_VGA;  // 解像度 640x480
  config.jpeg_quality = 10;             // JPEG品質（0~63 低いほど高画質）
  config.fb_count     = 1;              // フレームバッファの数
}

// ESP32の起動時に1回だけ実行される関数
void setup() {
  Serial.begin(115200);          // シリアルモニタの通信速度を設定
  pinMode(SENSOR_PIN, INPUT);    // SENSOR_PINを入力に設定

  // LEDのピンを出力に設定
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE,  OUTPUT);
  pinMode(LED_RED,   OUTPUT);

  // LED消灯
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_BLUE,  LOW);
  digitalWrite(LED_RED,   LOW);

  camera_init();
  esp_err_t err = esp_camera_init(&config); // カメラの起動。成功すればerrにESP_OKが入る

  // エラー時にはif文実行
  if (err != ESP_OK) {
    Serial.printf("カメラ初期化失敗: 0x%x\n", err);
    blinkError(5);
    return;
  }
  Serial.println("カメラ初期化成功");

  WiFi.begin(ssid, password); // 指定したssidとパスワードでWiFi接続を開始
  Serial.print("WiFi接続中");

  // WiFiがつながるまでwhile文でループ = 待機
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi接続成功");
  Serial.println(WiFi.localIP()); // ESP32に割り振られたIPを表示

  digitalWrite(LED_GREEN, HIGH); // 緑LED点灯
}

// setup()の後繰り返し実行される
void loop() {
  int val = digitalRead(SENSOR_PIN); // SENSOR_PINの状態（HIGH/LOW）を読み取る

  // HIGHだった時
  if (val == HIGH) {
    Serial.println("検知 撮影します...");

    digitalWrite(LED_BLUE, HIGH); // 青LED点灯

    camera_fb_t *fb = esp_camera_fb_get(); // 撮影してフレームバッファのポインタを取得

    // fbがNULLの時
    if (!fb) {
      Serial.println("撮影失敗");
      digitalWrite(LED_BLUE, LOW);
      blinkError(3);
      return;
    }
    Serial.printf("撮影成功 サイズ: %dバイト\n", fb->len); // fbが指す構造体のlenメンバ

    if (client.connect(REMOTE_IP, REMOTE_PORT)) { // 送信先PCにTCP接続を試みる
      Serial.println("PC接続成功 送信中...");

      uint32_t size = fb->len;               // 画像のバイト数をsizeに入れる
      client.write((uint8_t *)&size, 4);     // 画像サイズ（4バイト）をuint8_t *に変換してPCに送信
      client.write(fb->buf, fb->len);        // fb->buf（画像データのポインタ）をfb->lenバイト送信

      Serial.println("送信完了");
      client.stop(); // 接続を切断
    } else {
      Serial.println("PC接続失敗");
      blinkError(3);
    }

    esp_camera_fb_return(fb);      // フレームバッファを解放（忘れるとメモリ不足になる）
    digitalWrite(LED_BLUE, LOW);
    delay(2000);                   // 連続検知を防ぐための2秒のディレイ
  }
}
