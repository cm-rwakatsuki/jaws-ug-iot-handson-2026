# 第2回：Device Shadow を使ってクラウドからデバイスを制御してみよう（Lチカ）

## ゴール

- Device Shadow の概念を理解する
- クラウド（マネジメントコンソール）から LED を ON/OFF する
- デバイスが状態変化を `reported` に反映する流れを体験する

MQTT では主にデバイス → クラウドへデータを「送る」ことができます。今回は Device Shadow（状態管理）を使って、クラウド → デバイスの「制御する」を学びます。通信の一歩先、状態の同期です。

---

## 進め方

今回は **Raspberry Pi（実機）** を使い、基板上の ACT LED（緑）を点灯・消灯します。

AWS 側の設定（Thing・証明書・Policy）から Raspberry Pi の実装まで、**この手順書だけで完結**します。第1回の受講は前提としません。

---

## 所要時間（目安）

| パート | 時間 |
|---|---|
| Wi-Fi 接続と SSH 接続（会場参加のみ） | 15分 |
| Device Shadow の概念 | 20分 |
| AWS 側設定（Thing・証明書・Policy） | 20分 |
| デバイス側実装（Shadow Subscribe + LED 制御） | 30分 |
| 動作確認（マネコンから LED 操作） | 20分 |
| 応用・質疑 | 10分 |
| **合計** | **115分** |

---

## 学習内容

### 双方向通信とは

MQTT では主にデバイス → クラウドの一方向でデータを送ります。今回はクラウド → デバイスの制御を加えた**双方向通信**を体験します。

![第2回 構成図：Device Shadow によるクラウドからのデバイス制御フロー](./architecture.drawio.svg)

### Device Shadow とは

Device Shadow は、デバイスの「あるべき状態（`desired`）」と「現在の状態（`reported`）」をクラウド上で管理する仕組みです。

```json
{
  "state": {
    "desired":  { "led": "on" },
    "reported": { "led": "on" },
    "delta":    {}
  }
}
```

| フィールド | 意味 |
|---|---|
| `desired` | クラウド側が「こうしてほしい」と指示する状態 |
| `reported` | デバイスが「現在こうなっている」と報告する状態 |
| `delta` | `desired` と `reported` の差分（デバイスへの指示として使う） |

### Device Shadow のメリット

- デバイスがオフラインでも `desired` を更新しておける
- デバイスが再接続したとき、`delta` を見て最新の指示を受け取れる
- 状態の同期が自動的に管理される

> Device Shadow は「単なる MQTT 通信」ではなく、デバイスの状態を管理する API です。クラウド側からは「状態を書く」、デバイス側からは「状態を読んで反映する」という設計思想で動いています。

### Device Shadow の Topic 構造

```
$aws/things/{thingName}/shadow/update           # Shadow更新（Publish）
$aws/things/{thingName}/shadow/update/accepted  # 更新成功（Subscribe）
$aws/things/{thingName}/shadow/update/rejected  # 更新失敗（Subscribe）
$aws/things/{thingName}/shadow/update/delta     # 差分通知（Subscribe）← 今回メインで使う
$aws/things/{thingName}/shadow/get              # Shadow取得（Publish）
$aws/things/{thingName}/shadow/get/accepted     # 取得成功（Subscribe）
```

> 今回は **Classic Shadow**（名前なしシャドウ）を使用します。上記の Topic はすべて Classic Shadow のものです。

---

## AWS 側設定

デバイスを AWS IoT Core に接続するため、**Thing（モノ）・証明書・Policy** を用意します。設定方法は2つあります。**CloudFormation を強く推奨します。手動ルートは AWS コンソールの操作を学びたい方向けです。**

| 方法 | 所要時間 | 向いている人 |
|---|---|---|
| **A. CloudFormation（推奨）** | 約5分 | **全員（特に初めての方）** |
| B. マネジメントコンソール（手動） | 約20分 | AWS コンソールの操作を一つひとつ学びたい方 |

---

### A. CloudFormation（推奨）

#### 1. テンプレートのダウンロード

[cfn/session-02/iot-setup.yaml](../../cfn/session-02/iot-setup.yaml) をダウンロードします。

> **リポジトリをクローン済みの場合はこの手順は不要です。** `cfn/session-02/iot-setup.yaml` をそのまま使用してください。

#### 2. スタックの作成

1. AWS マネジメントコンソール →（東京リージョン）→ **CloudFormation** →「スタックの作成」→「新しいリソースを使用」
2. 「テンプレートファイルのアップロード」→ `iot-setup.yaml` を選択
3. スタック名：`jawsug-iot-handson-s2-001`
4. パラメータを入力：
   - `DeviceId`：`raspi-001`（好きな番号で OK）
5. 「次へ」→「次へ」→「送信」
6. ステータスが `CREATE_COMPLETE` になるまで待つ（約1〜2分）

#### 3. 出力の確認

スタック →「出力」タブを開き、以下を控えておきます：

| キー | 内容 |
|---|---|
| `ThingName` | IoT コンソール上のモノの名前（`jawsug-raspi-001` 形式） |
| `ShadowDeltaTopic` | デバイスがサブスクライブする delta トピック |
| `NextStep` | 次の手順（証明書発行・Endpoint 取得）の案内 |

#### 4. 証明書の発行（手動・必須）

CloudFormation では秘密鍵を取得できないため、証明書だけ手動で発行します。

1. IoT Core →「管理」→「すべてのデバイス」→「モノ」→ `jawsug-{DeviceId}` を選択
2. 「証明書」タブ →「証明書を作成」
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
6. 証明書詳細ページの「ポリシー」タブ →「ポリシーをアタッチ」→ `jawsug-handson-policy-{DeviceId}` を選択してアタッチ

> ⚠️ プライベートキーはこの画面でしかダウンロードできません。必ず保存してください。

> 🔒 証明書ファイルは画面共有しないでください。

#### 5. Endpoint の取得

1. IoT Core →「接続」→「ドメイン設定」
2. 一覧から「iot:Data-ATS」の「ドメイン名」をコピーして控えておく

```
例：xxxxxxxxxxxxxx-ats.iot.ap-northeast-1.amazonaws.com
```

---

### B. マネジメントコンソール（手動）

AWS コンソールの操作を一つひとつ学びたい方はこちらを進めてください。

#### 1. Thing の作成

1. AWS マネジメントコンソール → **AWS IoT Core** を開く（東京リージョン）
2. 左メニュー「管理」→「すべてのデバイス」→「モノ」を選択
3. 「モノを作成」→「一つのモノを作成」→「次へ」
4. Thing 名を入力：`jawsug-raspi-001`（末尾の番号は好きな値で OK）
5. Device Shadow は「無名のシャドウ (classic)」を選択
6. 「次へ」をクリック

#### 2. 証明書の発行

> 証明書はデバイスの「身分証」です。AWS IoT Core はこの証明書でデバイスを識別・認証します。

1. 「新しい証明書を自動生成（推奨）」を選択 →「次へ」
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

#### 5. Endpoint の取得

CloudShell を開いて以下を実行：

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS --region ap-northeast-1
```

```
例：xxxxxxxxxxxxxx-ats.iot.ap-northeast-1.amazonaws.com
```

---

## Wi-Fi 接続と SSH 接続

> 会場参加（実機あり）の方のみ実施してください。

1. PC を専用 Wi-Fi（`JAWSUG-IoT-PC`）に接続します。
2. ラズパイの電源を入れます。
3. ラズパイに SSH で接続します。

```bash
# ホスト名で接続する場合（ラズパイ本体に記載の名前を使用）
ssh jawsug-user@ラズパイに記載の名前.local

# または IP アドレスで接続する場合（ラズパイ本体に記載の IP を使用）
ssh jawsug-user@ラズパイに記載のIP
```

ラズパイの Wi-Fi 接続は設定済みです（`JAWSUG-IoT-Pi`）。

---

## 実装（Raspberry Pi）

### 必要なライブラリ

Raspberry Pi 上で以下を実行します。

```bash
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt  # または pip3
```

> 💡 最新の Raspberry Pi OS では `pip3 install` 実行時に `error: externally-managed-environment` が発生します。venv を使ってインストールしてください。

### Raspberry Pi の LED 表現について

今回は基板上の **ACT LED（緑色の LED）** を制御します。GPIO へのハンダ付けや外付け部品は不要です。

ACT LED は通常 SD カードアクセスに連動していますが、`sysfs` 経由でトリガーを解除することで自由に点灯・消灯できます。

```
LED ON  -> /sys/class/leds/led0/brightness に 1 を書き込む
LED OFF -> /sys/class/leds/led0/brightness に 0 を書き込む
```

> `led0` が ACT LED です。操作には `sudo` が必要です。

### 証明書の配置

PC からダウンロードした証明書を Raspberry Pi の `scripts/session-02/certs/` に転送します。

**scp を使う場合：**

```bash
# PC側で実行（raspi.local は Raspberry Pi のホスト名）
scp certificate.pem.crt private.pem.key AmazonRootCA1.pem \
  jawsug-user@raspi.local:~/jaws-ug-iot-handson-2026/scripts/session-02/certs/
```

**USB メモリを使う場合：**

1. PC でダウンロードした証明書を USB メモリにコピー
2. Raspberry Pi に USB メモリを挿して `scripts/session-02/certs/` にコピー

### ディレクトリ構成

`shadow_led.py` と `led_ctrl.sh` は本リポジトリをクローンすれば `scripts/session-02/` に含まれています。証明書ファイルだけ `certs/` に配置・リネームしてください。

```
scripts/session-02/
├── shadow_led.py    # MQTTでShadow deltaを受信するメインスクリプト
├── led_ctrl.sh      # ACT LEDを制御するシェルスクリプト
└── certs/
    ├── certificate.pem.crt   ← xxxxx-certificate.pem.crt をリネーム
    ├── private.pem.key       ← xxxxx-private.pem.key をリネーム
    └── AmazonRootCA1.pem     ← そのままでOK
```

### led_ctrl.sh

まず LED 制御スクリプトに実行権限を付与します（本リポジトリの [scripts/session-02/led_ctrl.sh](../../scripts/session-02/led_ctrl.sh)）。

```bash
cd scripts/session-02
chmod +x led_ctrl.sh
```

スクリプト単体で動作を確認します。

```bash
./led_ctrl.sh on    # ACT LEDが点灯
./led_ctrl.sh off   # ACT LEDが消灯
```

スクリプト全体は [scripts/session-02/led_ctrl.sh](../../scripts/session-02/led_ctrl.sh) を参照してください。

### shadow_led.py の設定

本リポジトリの [scripts/session-02/shadow_led.py](../../scripts/session-02/shadow_led.py) の冒頭の設定値を、AWS 設定で取得・作成した値に書き換えます。

```python
ENDPOINT  = "xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"  # 取得したEndpointに書き換える
DEVICE_ID = "raspi-001"  # 作成したThing名に合わせる（jawsug-<DEVICE_ID>）
```

スクリプト全体は [scripts/session-02/shadow_led.py](../../scripts/session-02/shadow_led.py) を参照してください。

### 実行

```bash
cd scripts/session-02
source venv/bin/activate
python3 shadow_led.py
```

出力例：

```
Waiting for Shadow delta...
[OK] Connected to AWS IoT Core
[SUB] Subscribed: $aws/things/jawsug-raspi-001/shadow/update/delta
```

この状態でマネジメントコンソールから `desired` を更新すると、`delta` を受信して LED が点灯・消灯します（次の「動作確認」参照）。

`Ctrl+C` で停止できます。

---

## 動作確認

### マネジメントコンソールから LED を操作する

1. AWS IoT Core →「管理」→「すべてのデバイス」→「モノ」→ 対象の Thing を選択
2. 「Device Shadow」タブ →「Classic Shadow」を選択
3. 「Shadow ドキュメント」の編集ボタンをクリック
4. 以下の JSON を入力して保存

**LED ON：**

```json
{
  "state": {
    "desired": { "led": "on" }
  }
}
```

**LED OFF：**

```json
{
  "state": {
    "desired": { "led": "off" }
  }
}
```

5. Raspberry Pi の ACT LED が点灯・消灯することを確認

### 確認ポイント

- `desired` を更新 → デバイスが `delta` を受信 → LED 制御 → `reported` が更新される
- `desired` と `reported` が一致したら `delta` は空になる

---

## ハマりポイントと対処法

| 症状 | 原因 | 対処 |
|---|---|---|
| AWS IoT Core に接続できない | Endpoint のミス | 設定画面からコピーし直す |
| delta が届かない | Subscribe 未実装 or Topic ミス | `$aws/things/` のプレフィックスを確認 |
| JSON parse エラー | Shadow JSON の構造ミス | `state.led` のパスを確認 |
| reported が更新されない | update Topic への Publish 失敗 | Policy の `iot:Publish` 権限を確認 |
| LED が変わらない | `led_ctrl.sh` の実行権限なし | `chmod +x led_ctrl.sh` を実行 |
| LED が変わらない | `sudo` のパスワード要求 | `sudo visudo` で NOPASSWD を設定するか、講師に確認 |
| LED が変わらない | trigger が解除されていない | `./led_ctrl.sh on` を単体で実行して動作確認 |
| Thing 名のミス | コードと AWS の Thing 名が不一致 | `DEVICE_ID` 変数を確認 |
| 証明書エラー | ファイルパス・ファイル名のミス | `certs/` のパスと各ファイル名を確認 |
| 接続できるが操作が拒否される | 証明書の有効化・ポリシー未アタッチ | 証明書タブでステータスとポリシーを確認 |
| `paho-mqtt` のインポートエラー | ライブラリ未インストール、または venv 未アクティベート | `source venv/bin/activate` を実行してから `python3` を起動 |

---

## 発展課題（時間が余ったら）

- Shadow の `get` を使って起動時に最新状態を取得する
- ボタン入力で `reported` を更新してみる
- 温度データの Publish（デバイス → クラウドの送信）と組み合わせる

---

## 参考：このセッションで学んだこと

```
クラウド → desired更新 → delta通知 → デバイスが反映 → reported更新
```

Device Shadow を使うと、デバイスがオフラインの間に指示を出しておき、再接続時に自動で同期させることができます。これが IoT の「状態管理」の基本パターンです。

---

## 後片付け

ハンズオン終了後は以下の手順で AWS リソースを削除してください。

```bash
cd scripts/session-02
DEVICE_ID=raspi-001 bash teardown.sh
```

実行内容：

1. Thing にアタッチされた証明書を無効化・削除
2. CloudFormation スタック（`jawsug-iot-handson-s2-{番号}`）を削除
3. ローカルの `certs/` ディレクトリを削除

> 💡 実行前に `aws sts get-caller-identity` で AWS 認証が通っているか確認してください。

> 手動（B ルート）で作成した方は、マネジメントコンソールから Thing・証明書・Policy を削除してください。
