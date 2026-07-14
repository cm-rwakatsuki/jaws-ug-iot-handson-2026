# JAWS-UG IoT 専門支部 IoT Core ハンズオン 2026

JAWS-UG IoT 専門支部 IoT Core ハンズオン（全3回）のハンズオン手順・スクリプト・IaC コードを管理するリポジトリです。

## 回ごとの内容

| 回 | テーマ | connpass |
|---|---|---|
| 第1回 | デバイスを AWS IoT Core に接続し、MQTT で温度データを送信してみよう | [イベントページ](https://jawsug-iot.connpass.com/event/391519/) |
| 第2回 | Device Shadow を使ってクラウドからデバイスを制御してみよう（Lチカ） | [イベントページ](https://jawsug-iot.connpass.com/event/397773/) |
| 第3回 | IoT Rules Engine で他の AWS サービスと連携し、データを自動処理・分析してみよう | T.B.D. |

## ディレクトリ構成

```
.
├── docs/
│   ├── session-01/
│   │   └── handson.md           # 参加者向けハンズオン手順書
│   ├── session-02/
│   │   ├── handson.md           # 参加者向けハンズオン手順書
│   │   └── architecture.drawio.svg  # 構成図
│   └── session-03/
├── scripts/
│   ├── session-01/
│   │   ├── device.py            # Raspberry Pi 用スクリプト（CPU温度を送信）
│   │   ├── simulator.py         # PC 用シミュレーター（ランダム温度を送信）
│   │   └── teardown.sh          # 後片付けスクリプト
│   ├── session-02/
│   │   ├── shadow_led.py        # Raspberry Pi 用スクリプト（Shadow delta で ACT LED 制御・再接続時に同期）
│   │   ├── led_ctrl.sh          # ACT LED を ON/OFF するシェルスクリプト
│   │   └── teardown.sh          # 後片付けスクリプト
│   └── session-03/
└── cfn/
    ├── session-01/
    │   └── iot-setup.yaml       # CloudFormation テンプレート（Thing + Policy）
    ├── session-02/
    │   └── iot-setup.yaml       # CloudFormation テンプレート（Thing + Policy）
    └── session-03/
```

## ハンズオン手順

- 第1回：[docs/session-01/handson.md](docs/session-01/handson.md)
- 第2回：[docs/session-02/handson.md](docs/session-02/handson.md)
- 第3回：T.B.D.
