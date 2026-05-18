# 第1回：デバイスを AWS IoT Core に接続し、MQTTで温度データを送信してみよう

## ゴール

- Raspberry Pi（またはPythonシミュレーター）を AWS IoT Core に接続する
- MQTTで温度データをPublishする
- MQTT Test Clientでデータ受信を確認する

> 質問は Slido の Q&A へ、感想・実況は X `#jawsug_iot` `#jawsug` へ。進捗確認は Slido 投票を使います。

---

## 参加形式別の進め方

| 参加形式 | 使用するもの |
|---|---|
| 会場参加（実機あり） | Raspberry Pi + Python |
| オンライン・実機なし | PC + Python シミュレーター |

AWS側の設定手順（Thing作成・証明書発行・Policy設定）は**全員共通**です。

---

## 所要時間（目安）

| パート | 時間 |
|---|---|
| 概要説明（IoT・MQTT・AWS IoT Core） | 15分 |
| AWS側設定（Thing・証明書・Policy） | 20分 |
| デバイス/シミュレーター実装 | 20分 |
| 動作確認（MQTT Test Client） | 20分 |
| トラブル対応・質疑 | 15分 |
| **合計** | **90分** |

---

## 学習内容

### IoTの基本構造

```
[Sensor] -> [Raspberry Pi] -> (Wi-Fi/TLS) -> [AWS IoT Core] -> [Cloud Services]
[Sensor] -> [Python script] -> (TLS)       -> [AWS IoT Core] -> [Cloud Services]
```

- デバイス：データを収集・送信する端末（今回はRaspberry PiまたはPC上のPythonスクリプト）
- 通信：MQTT over TLS（セキュアな軽量プロトコル）
- クラウド：データを受け取り、処理・保存・可視化する

### MQTTの基礎

- **Broker**：メッセージの中継役（AWS IoT Core がBrokerになる）
- **Topic**：メッセージの宛先（例：`jawsug/2026-05/raspi-001/telemetry`）
- **Publish**：メッセージを送信すること
- **Subscribe**：メッセージを受信すること
- **QoS**：メッセージ配信の品質レベル（今回はQoS 1を使用）

### AWS IoT Coreの構成要素

| 要素 | 役割 |
|---|---|
| Thing | デバイスをAWS上で管理するリソース |
| Certificate | デバイス認証に使うX.509証明書 |
| Policy | 証明書に紐づくIoT操作の権限設定 |
| Endpoint | デバイスが接続するMQTT Brokerのアドレス |

---

## AWS側設定手順（全員共通）

設定方法は2つあります。**CloudFormationを強く推奨します。手動ルートはAWSコンソールの操作を学びたい方向けです。**

| 方法 | 所要時間 | 向いている人 |
|---|---|---|
| **A. CloudFormation（推奨）** | 約5分 | **全員（特に初めての方）** |
| B. マネジメントコンソール（手動） | 約20分 | AWSコンソールの操作を一つひとつ学びたい方 |

> 初めての方はAルートで進めてください。Bルートは「AWSの操作を覚えたい」という目的がある場合のみ選択してください。

---

### A. CloudFormation（推奨）

#### 1. テンプレートのダウンロード

[cfn/session-01/iot-setup.yaml](../../cfn/session-01/iot-setup.yaml) をダウンロードします。

> **リポジトリをクローン済みの場合はこの手順は不要です。** `cfn/session-01/iot-setup.yaml` をそのまま使用してください。

#### 2. スタックの作成

1. AWSマネジメントコンソール → **CloudFormation** → 「スタックの作成」→「新しいリソースを使用」
2. 「テンプレートファイルのアップロード」→ `iot-setup.yaml` を選択
3. スタック名：`jawsug-iot-handson-001`
4. パラメータを入力：
   - `EventId`：`2026-05`（講師から案内された値）
   - `DeviceId`：`raspi-001`（好きな番号でOK）
5. 「次へ」→「次へ」→「送信」
6. ステータスが `CREATE_COMPLETE` になるまで待つ（約1〜2分）

#### 3. 出力の確認

スタック → 「出力」タブを開き、以下を控えておきます：

| キー | 内容 |
|---|---|
| `ThingName` | IoT コンソール上のモノの名前（`jawsug-raspi-001` 形式） |
| `TopicTelemetry` | 送信先トピック（コードの `DEVICE_ID` = `DeviceId` パラメータ部分） |
| `NextStep` | 次の手順の案内 |

#### 4. 証明書の発行（手動・必須）

CloudFormationでは秘密鍵を取得できないため、証明書だけ手動で発行します。

1. IoT Core → 「管理」→「すべてのデバイス」→「モノ」→ `jawsug-{DeviceId}` を選択
2. 「証明書」タブ → 「証明書を作成」
3. 「証明書とキーをダウンロード」ダイアログが表示される。**以下のファイルを必ずダウンロード**（後から再取得不可）

```
[OK] デバイス証明書     (xxxxx-certificate.pem.crt)
[OK] パブリックキー     (xxxxx-public.pem.key)
[OK] プライベートキー   (xxxxx-private.pem.key)
[OK] Amazon Root CA 1  (AmazonRootCA1.pem)
```

4. **ダイアログ内**の「デバイス証明書」行にある「証明書をアクティブ化」をクリック

> 💡 ダイアログを閉じてしまった場合：「証明書」タブの証明書 ID リンクをクリック → 証明書詳細ページの「アクション」→「有効化」

5. 「完了」をクリックしてダイアログを閉じる
6. 証明書詳細ページの「ポリシー」タブ → 「ポリシーをアタッチ」→ `jawsug-handson-policy-{DeviceId}` を選択してアタッチ

> ⚠️ プライベートキーはこの画面でしかダウンロードできません。必ず保存してください。

> 🔒 証明書ファイルは画面共有しないでください。

#### 5. Endpointの取得

1. IoT Core → 「接続」→「ドメイン設定」
2. 一覧から「iot:Data-ATS」の「ドメイン名」をコピーして控えておく

```
例：xxxxxxxxxxxxxx-ats.iot.ap-northeast-1.amazonaws.com
```

---

### B. マネジメントコンソール（手動）

AWSコンソールの操作を一つひとつ学びたい方はこちらを進めてください。

#### 1. Thingの作成

1. AWSマネジメントコンソール → **AWS IoT Core** を開く（東京リージョン）
2. 左メニュー「管理」→「すべてのデバイス」→「モノ」を選択
3. 「モノを作成」→「一つのモノを作成」→「次へ」
4. Thing名を入力：`jawsug-raspi-001`（末尾の番号は好きな値でOK）
5. Device Shadowは「名前付きシャドウ」を選択し、シャドウ名に `led` を入力
6. 「次へ」をクリック

#### 2. 証明書の発行とポリシーのアタッチ

> 証明書はデバイスの「身分証」です。AWS IoT Coreはこの証明書でデバイスを識別・認証します。

1. 「新しい証明書を自動生成（推奨）」を選択 → 「次へ」
2. 「証明書にポリシーをアタッチ」画面に遷移します

#### 3. ポリシーのアタッチ

ポリシーがまだない場合は「ポリシーを作成」から作成してください：

1. ポリシー名：`jawsug-handson-policy`
2. 以下のポリシードキュメントを入力：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect",
        "iot:Publish",
        "iot:Subscribe",
        "iot:Receive"
      ],
      "Resource": "arn:aws:iot:ap-northeast-1:*:*"
    }
  ]
}
```

3. 「作成」→「証明書にポリシーをアタッチ」画面に戻ると、作成したポリシーが自動で選択されているので、そのまま「モノを作成」をクリック

#### 4. 証明書ファイルのダウンロード

「モノを作成」をクリックすると「証明書とキーをダウンロード」ダイアログが自動で開きます。**以下のファイルを必ずダウンロード**（後から再取得不可）

```
[OK] デバイス証明書     (xxxxx-certificate.pem.crt)
[OK] パブリックキー     (xxxxx-public.pem.key)
[OK] プライベートキー   (xxxxx-private.pem.key)
[OK] Amazon Root CA 1  (AmazonRootCA1.pem)
```

ダウンロード後、「完了」でダイアログを閉じます。証明書はすでにアクティブ化された状態で作成されます。

> ⚠️ プライベートキーはこの画面でしかダウンロードできません。必ず保存してください。

> 🔒 証明書ファイルは画面共有しないでください。

#### 5. Endpointの取得

CloudShell を開いて以下を実行：

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS --region ap-northeast-1
```

```
例：xxxxxxxxxxxxxx-ats.iot.ap-northeast-1.amazonaws.com
```

---

## 実装（Raspberry Pi）

会場で Raspberry Pi を使用する方はこちらを進めてください。  
**PCのみの方は次のセクションへ。**

### 必要なライブラリ

Raspberry Pi 上で以下を実行します。

```bash
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt  # または pip3
```

> 💡 最新の Raspberry Pi OS では `pip3 install` 実行時に `error: externally-managed-environment` が発生します。venv を使ってインストールしてください。

### 証明書の配置

PCからダウンロードした証明書を Raspberry Pi に転送します。

**scp を使う場合：**

```bash
# PC側で実行（raspi.local は Raspberry Pi のホスト名）
scp certificate.pem.crt private.pem.key AmazonRootCA1.pem pi@raspi.local:~/certs/
```

**USBメモリを使う場合：**

1. PC でダウンロードした証明書を USB メモリにコピー
2. Raspberry Pi に USB メモリを挿して `~/certs/` にコピー

### ディレクトリ構成

`device.py` は本リポジトリをクローンすれば `scripts/session-01/` に含まれています。証明書ファイルだけ `certs/` に配置してください。

```
~/
├── device.py        ← リポジトリの scripts/session-01/device.py をコピー
└── certs/
    ├── certificate.pem.crt   ← xxxxx-certificate.pem.crt をリネーム
    ├── private.pem.key       ← xxxxx-private.pem.key をリネーム
    └── AmazonRootCA1.pem     ← そのままでOK
```

### device.py の入手・設定

本リポジトリの [scripts/session-01/device.py](../../scripts/session-01/device.py) を Raspberry Pi にコピーし、冒頭の設定値を書き換えます。

```python
ENDPOINT  = "xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"  # 取得したEndpointに書き換える
EVENT_ID  = "2026-05"
DEVICE_ID = "raspi-001"  # 好きな番号でOK（例：raspi-001）
```

### 実行

```bash
source venv/bin/activate
python3 device.py
```

出力例：

```
Connecting to xxxxxx-ats.iot.ap-northeast-1.amazonaws.com...
[OK] Connected to AWS IoT Core
[SEND] jawsug/2026-05/raspi-001/telemetry: {"deviceId": "raspi-001", "temperature": 52.6, "timestamp": 1748700000}
   -> Published (mid=1)
[SEND] jawsug/2026-05/raspi-001/telemetry: {"deviceId": "raspi-001", "temperature": 53.1, "timestamp": 1748700005}
```

> 温度は Raspberry Pi の CPU 温度（`/sys/class/thermal/thermal_zone0/temp`）を読み取っています。

`Ctrl+C` で停止できます。

---

## 実装（Pythonシミュレーター）

Raspberry Pi をお持ちでない方向けです。PC 上で動作します。

### 必要なライブラリ

```bash
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt  # または pip3
```

> 💡 OS によっては `pip3 install` 実行時に `error: externally-managed-environment` が発生します。venv を使ってインストールしてください。

### ディレクトリ構成

本リポジトリをクローンすれば `simulator.py` と `certs/` は既に存在します。証明書ファイルを `certs/` に配置してリネームするだけで準備完了です。

```
scripts/session-01/
├── simulator.py              ← クローン済みなら不要
└── certs/
    ├── certificate.pem.crt   ← xxxxx-certificate.pem.crt をリネーム
    ├── private.pem.key       ← xxxxx-private.pem.key をリネーム
    └── AmazonRootCA1.pem     ← そのままでOK
```

### simulator.py の設定

以下の値を必要に応じて書き換えます。

```python
EVENT_ID  = "2026-05"   # 開催年月（再開催時に変更）
DEVICE_ID = "raspi-001"  # 好きな番号でOK（例：raspi-001）
```

`ENDPOINT` は環境変数で渡します（スクリプトへの直書き不要）。

### 実行

```bash
cd scripts/session-01
source venv/bin/activate
export AWS_IOT_ENDPOINT="xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"  # 自分のEndpointに書き換える
python3 simulator.py
```

出力例：

```
Connecting to xxxxxx-ats.iot.ap-northeast-1.amazonaws.com...
[OK] Connected to AWS IoT Core
[SEND] jawsug/2026-05/sim-001/telemetry: {"deviceId": "sim-001", "temperature": 24.3, "timestamp": 1748700000}
   -> Published (mid=1)
```

---

## 動作確認（全員共通）

1. AWSマネジメントコンソール → AWS IoT Core
2. 左メニュー「テスト」→「MQTT テストクライアント」
3. 「トピックをサブスクライブする」タブ
4. トピックフィルターに `jawsug/#` を入力して「サブスクライブ」
5. データが届いていることを確認

```json
{
  "deviceId": "raspi-001",
  "temperature": 52.6,
  "timestamp": 1748700000
}
```

---

## ハマりポイントと対処法

| 症状 | 原因 | 対処 |
|---|---|---|
| AWS IoT Coreに接続できない | Endpointのミス | 設定画面からコピーし直す |
| 接続できるがPublishできない | PolicyのAllow設定不足 | `iot:Publish` が許可されているか確認 |
| 証明書エラー | ファイルパスのミス | `certs/` のパスと各ファイル名を確認 |
| 証明書を作ったが接続できない | 証明書の有効化忘れ | Thing → 証明書タブ → 「有効化」を確認 |
| 接続できるがデータが届かない | Policyが証明書にアタッチされていない | Thing → 証明書タブ → 「ポリシー」タブを確認 |
| Wi-Fi接続できない（Raspberry Pi） | SSID/パスワードミス or 5GHz帯 | 2.4GHz帯のSSIDを使用 |
| ポート8883がブロックされる | 企業ネットワーク・VPN | テザリングに切り替える |
| `paho-mqtt` のインポートエラー | ライブラリ未インストール、または venv 未アクティベート | `source venv/bin/activate` を実行してから `python3` を起動 |
| SSH で Raspberry Pi に繋がらない | IP アドレス不明 | `ping raspberrypi.local` で確認、または HDMI でIPを確認 |

---

## 後片付け

ハンズオン終了後は以下の手順でAWSリソースを削除してください。

```bash
cd scripts/session-01
DEVICE_ID=raspi-001 bash teardown.sh
```

実行内容：

1. Thing にアタッチされた証明書を無効化・削除
2. CloudFormation スタック（`jawsug-iot-handson-{番号}`）を削除
3. ローカルの `certs/` ディレクトリを削除

> 💡 実行前に `aws sts get-caller-identity` でAWS認証が通っているか確認してください。

---

## 次回予告

第2回では、今回作ったデバイスとAWS IoT Coreの接続を活かして、**クラウドからデバイスを制御**します。Device Shadowを使ってLEDをON/OFFしてみましょう。
