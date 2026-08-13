# JAWS-UG IoT 専門支部 IoT Core ハンズオン 2026

JAWS-UG IoT 専門支部 IoT Core ハンズオン（全3回）のハンズオン手順・スクリプト・IaC コードを管理するリポジトリです。

## 回ごとの内容

| 回 | テーマ | connpass |
|---|---|---|
| 第1回 | デバイスを AWS IoT Core に接続し、MQTT で温度データを送信してみよう | [イベントページ](https://jawsug-iot.connpass.com/event/391519/) |
| 第2回 | Device Shadow を使ってクラウドからデバイスを制御してみよう（Lチカ） | [イベントページ](https://jawsug-iot.connpass.com/event/397773/) |
| 第3回 | IoT Rules Engine で他の AWS サービスと連携し、データを自動処理・分析してみよう | [イベントページ](https://jawsug-iot.connpass.com/event/402082/) |

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
│       ├── handson.md           # 参加者向けハンズオン手順書
│       ├── architecture-v2.svg  # 構成図
│       └── architecture-v2.drawio   # 構成図の編集用ファイル
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
│       ├── metrics_publisher.py # Raspberry Pi 用スクリプト（CPU/メモリ使用率を送信）
│       ├── metrics.py           # 使用率の取得とペイロード組み立て
│       ├── load_gen.py          # 負荷生成スクリプト（CPU / メモリ）
│       ├── show_metrics.sh      # デバイス側の実測値を表示
│       ├── simulator.py         # 運営用の予備（実機なしでの動作確認）
│       ├── teardown.sh          # 後片付けスクリプト
│       ├── lambda/
│       │   └── metrics_logger.py    # Lambda ハンドラ（構造化ログ出力）
│       ├── tests/               # ユニットテスト（pytest）
│       ├── spec/                # 要件・設計・タスク・検証記録
│       └── requirements-dev.txt # 開発用の依存パッケージ
└── cfn/
    ├── session-01/
    │   └── iot-setup.yaml       # CloudFormation テンプレート（Thing + Policy）
    ├── session-02/
    │   └── iot-setup.yaml       # CloudFormation テンプレート（Thing + Policy）
    └── session-03/
        ├── iot-rules-cloudwatch.yaml  # Basic Course（Thing + Policy + IoT ルール → CloudWatch）
        ├── advanced-lambda.yaml       # Advanced Course1（IoT ルール → Lambda → Logs）
        └── advanced-alarm.yaml        # Advanced Course2（Alarm → SNS → メール）
```

## ハンズオン手順

- 第1回：[docs/session-01/handson.md](docs/session-01/handson.md)
- 第2回：[docs/session-02/handson.md](docs/session-02/handson.md)
- 第3回：[docs/session-03/handson.md](docs/session-03/handson.md)

## 第3回の開発者向け情報

第3回はスクリプトと CloudFormation テンプレートをテスト付きで管理しています。

```bash
cd scripts/session-03
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                              # ユニットテスト
cfn-lint ../../cfn/session-03/*.yaml   # テンプレートの静的検証
```

要件・設計・実装計画・検証記録は [scripts/session-03/spec/](scripts/session-03/spec/) にあります。
