# JAWS-UG IoT 専門支部 IoT Core ハンズオン 2026

JAWS-UG IoT 専門支部 IoT Core ハンズオン（全3回）のハンズオン手順・スクリプト・IaC コードを管理するリポジトリです。

## 回ごとの内容

| 回 | テーマ |
|---|---|
| [第1回](https://jawsug-iot.connpass.com/event/391519/) | デバイスを AWS IoT Core に接続し、MQTT で温度データを送信してみよう |
| 第2回 | Device Shadow を使って LED を制御してみよう |
| 第3回 | IoT Rules Engine で他の AWS サービスと連携し、データを自動処理・分析してみよう |

## ディレクトリ構成

```
.
├── docs/
│   ├── session-01/
│   │   └── handson.md           # 参加者向けハンズオン手順書
│   ├── session-02/
│   └── session-03/
├── scripts/
│   ├── session-01/
│   │   ├── device.py            # Raspberry Pi 用スクリプト（CPU温度を送信）
│   │   ├── simulator.py         # PC 用シミュレーター（ランダム温度を送信）
│   │   └── teardown.sh          # 後片付けスクリプト
│   ├── session-02/
│   └── session-03/
└── cfn/
    ├── session-01/
    │   └── iot-setup.yaml       # CloudFormation テンプレート（Thing + Policy）
    ├── session-02/
    └── session-03/
```

## ハンズオン手順

- 第1回：[docs/session-01/handson.md](docs/session-01/handson.md)
- 第2回：T.B.D.
- 第3回：T.B.D.
