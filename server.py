import socket        # TCP通信（サーバー側）
import os             # フォルダの作成やファイル操作
from datetime import datetime  # datetimeモジュールからdatetimeクラスを取り込み
import torch          # PyTorch - 機械学習の計算
from torchvision import models, transforms  # models - 学習済みモデル（MobileNetV2）, transforms - 画像の前処理
from PIL import Image # 画像を開いて読み込む
import json           # JSONデータの読み書き
import urllib.request # HTTP通信

# Discord WebhookのURL
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

os.makedirs("images", exist_ok=True) # imagesフォルダを作成. exist_ok=True - フォルダが存在してもエラーにしない

# ImageNetの1000クラスのラベル一覧をダウンロード（画像認識のスコアに対応する名前のリスト）
url = "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json"
with urllib.request.urlopen(url) as f:
    labels = json.load(f)

model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT) # MobileNetV2モデルの読み込み. ImageNetで学習した重みを使う
model.eval() # 推論モード

# MobileNetV2で処理するための画像の前処理
transform = transforms.Compose([ # Compose - 順番に実行
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(), # 多次元配列に変換し0~1に正規化
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]  # ImageNetの平均・標準偏差で正規化
    )
])

# ImageNetの1000クラスの中から犬種に該当するラベルをまとめたリスト
DOG_LABELS = [
    "chihuahua", "japanese spaniel", "maltese dog", "pekinese",
    "shih-tzu", "blenheim spaniel", "papillon", "toy terrier",
    "rhodesian ridgeback", "afghan hound", "basset", "beagle",
    "bloodhound", "bluetick", "black-and-tan coonhound",
    "walker hound", "english foxhound", "redbone", "borzoi",
    "irish wolfhound", "italian greyhound", "whippet",
    "ibizan hound", "norwegian elkhound", "otterhound",
    "saluki", "scottish deerhound", "weimaraner",
    "staffordshire bullterrier", "american staffordshire terrier",
    "bedlington terrier", "border terrier", "kerry blue terrier",
    "irish terrier", "norfolk terrier", "norwich terrier",
    "yorkshire terrier", "wire-haired fox terrier",
    "lakeland terrier", "sealyham terrier", "airedale",
    "cairn", "australian terrier", "dandie dinmont",
    "boston bull", "miniature schnauzer", "giant schnauzer",
    "standard schnauzer", "scotch terrier", "tibetan terrier",
    "silky terrier", "soft-coated wheaten terrier",
    "west highland white terrier", "lhasa",
    "flat-coated retriever", "curly-coated retriever",
    "golden retriever", "labrador retriever",
    "chesapeake bay retriever", "german short-haired pointer",
    "vizsla", "english setter", "irish setter", "gordon setter",
    "brittany spaniel", "clumber", "english springer",
    "welsh springer spaniel", "cocker spaniel", "sussex spaniel",
    "irish water spaniel", "kuvasz", "schipperke",
    "groenendael", "malinois", "briard", "kelpie",
    "komondor", "old english sheepdog", "shetland sheepdog",
    "collie", "border collie", "bouvier des flandres",
    "rottweiler", "german shepherd", "doberman",
    "miniature pinscher", "greater swiss mountain dog",
    "bernese mountain dog", "appenzeller", "entlebucher",
    "boxer", "bull mastiff", "tibetan mastiff", "french bulldog",
    "great dane", "saint bernard", "eskimo dog", "malamute",
    "siberian husky", "dalmatian", "affenpinscher",
    "basenji", "pug", "leonberg", "newfoundland",
    "great pyrenees", "samoyed", "pomeranian", "chow",
    "keeshond", "brabancon griffon", "pembroke",
    "cardigan", "toy poodle", "miniature poodle",
    "standard poodle", "mexican hairless", "dingo",
    "dhole", "african hunting dog"
]


# 画像パスを受け取りDiscordに通知を送る関数
def notify_discord(image_path):
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S") # 現在時刻を取得してメッセージを作る
    message   = f"犬を検知しました\n時刻：{timestamp}"

    boundary = "----FormBoundary7MA4YWxkTrZu0gW" # 区切り文字列

    with open(image_path, "rb") as f: # バイナリモードで読み取り
        image_data = f.read()

    # 送信ボディの組み立て. テキスト部分と画像部分をboundaryで区切って結合
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"\r\n\r\n'
        f"{message}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="pet.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    # HTTPリクエストの作成
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}", # Discordに形式を伝える
            "User-Agent":   "DiscordBot (custom, 1.0)"                   # DiscordBotを指定しCloudflareのブロックを回避
        },
        method="POST"
    )

    # try中にエラーが起きたらexceptに飛ぶ
    try:
        with urllib.request.urlopen(req) as res: # DiscordにHTTPリクエストを送信
            print(f"Discord通知成功 ステータス: {res.status}")
    except Exception as e:
        print(f"Discord通知失敗: {e}")                      # エラー内容
        print(f"詳細: {e.read().decode('utf-8')}")          # 詳細なエラー


# 画像パスを受け取り犬かどうか判定
def recognize(image_path):
    img        = Image.open(image_path).convert("RGB") # 画像ファイルをRGBに変換
    img_tensor = transform(img).unsqueeze(0)           # 前処理+バッチ次元の追加

    with torch.no_grad(): # 勾配計算を無効化
        output = model(img_tensor) # MobileNetV2に画像を入力して1000クラスのスコアを取得

    _, indices = torch.topk(output, 10) # スコア上位10件のインデックスを取得

    # 上位10件分のループ
    for i in indices[0]:
        label = labels[i].lower() # インデックスに対応するラベルを小文字で取得
        if any(dog in label for dog in DOG_LABELS): # DOG_LABELSの中のいずれかの文字列がlabelに含まれているか確認
            print(f"犬を検知しました")
            notify_discord(image_path) # 判定された画像パスを指定
            return "dog"

    print("犬は検知されませんでした")
    return "unknown"


HOST = "0.0.0.0" # すべてのネットワークインターフェースで接続を受け付ける
PORT = 8888

print(f"サーバー起動中... PORT:{PORT}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # ソケット作成. AF_INET - IPv4, SOCK_STREAM - TCP
server.bind((HOST, PORT))  # IPアドレスとポートの指定
server.listen(1)           # 接続の待ち受け開始

print("待機中...")

while True:
    conn, addr = server.accept() # ESP32からの接続を待つ. 接続したらconn（通信オブジェクト）とaddr（IPとポートのタプル）が返る
    print(f"接続: {addr}")

    size_data = conn.recv(4)                        # 最初に送られてくる4バイトを受け取る
    size      = int.from_bytes(size_data, 'little') # 4バイトを整数に変換. リトルエンディアン指定

    data = b"" # 空のバイト列

    # sizeバイトに達するまでデータを受信
    while len(data) < size:
        packet = conn.recv(4096) # 1度に最大4096バイト受け取る
        if not packet:
            break          # 受け取ったデータが空ならループ終了
        data += packet     # 受け取ったデータを蓄積

    filename = datetime.now().strftime("images/%Y%m%d_%H%M%S.jpg") # 現在時刻をファイル名にする
    with open(filename, "wb") as f: # wb - バイナリ書き込みモード
        f.write(data)               # 画像データをJPEGとして保存
    print(f"保存しました: {filename}")

    result = recognize(filename) # 犬かどうかを判定
    print(f"判定: {result}")

    conn.close() # 接続を閉じる
