"""シミュレーター — 運営用の予備ツール（参加者向けではない）。

2026-08-13 の前提変更により、参加者は全員が会場で実機（Raspberry Pi）を操作する。
本スクリプトは参加者向けの提供物ではなく、次の 2 つの用途に限定する。

1. 当日、貸出 Raspberry Pi が故障・接続不能になったときの運営側のバックアップ
2. 実機を用意できない開発・検証環境から AWS 側の経路
   （Rules → CloudWatch / Lambda / Alarm）を確認する用途

同一トピック・同一ペイロード形式で CPU/メモリを疑似生成する。
--spike-after / --spike-duration / --spike-level で高負荷区間を再現し、
実機なしでもアラーム発火まで到達できる。

手順書（docs/session-03/handson.md）には記載しない。
"""

import argparse
import json
import os
import random
import signal
import ssl
import sys
import time

import paho.mqtt.client as mqtt

from metrics import build_payload, format_stdout_line

# ---- 設定（参加者が書き換える） ----
ENDPOINT = os.environ.get(
    "AWS_IOT_ENDPOINT", "xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"
)
DEVICE_ID = "raspi-001"  # 割り当てられた番号に書き換える
# ----------------------------------

SEND_INTERVAL = int(os.environ.get("SEND_INTERVAL", "10"))
TOPIC = f"jawsug/session-03/{DEVICE_ID}/metrics"

CERT_DIR = "./certs"
CA_CERT = f"{CERT_DIR}/AmazonRootCA1.pem"
CERT_FILE = f"{CERT_DIR}/certificate.pem.crt"
KEY_FILE = f"{CERT_DIR}/private.pem.key"


def parse_args():
    parser = argparse.ArgumentParser(
        description="IoT メトリクスシミュレーター（運営用の予備ツール）"
    )
    parser.add_argument(
        "--spike-after",
        type=int,
        default=60,
        help="開始から何秒後にスパイクを開始するか（既定: 60）",
    )
    parser.add_argument(
        "--spike-duration",
        type=int,
        default=180,
        help="スパイクの継続時間（秒）（既定: 180）",
    )
    parser.add_argument(
        "--spike-level",
        type=float,
        default=90.0,
        help="スパイク時の CPU 使用率目標（%%）（既定: 90）",
    )
    return parser.parse_args()


def generate_value(base: float, jitter: float = 3.0) -> float:
    """基準値にジッタを加えた疑似メトリクスを生成する。"""
    return round(base + random.uniform(-jitter, jitter), 1)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[OK] Connected to AWS IoT Core")
    else:
        print(f"[ERROR] Connection failed: rc={rc}")


def main():
    args = parse_args()

    # 証明書チェック
    for path in [CA_CERT, CERT_FILE, KEY_FILE]:
        if not os.path.isfile(path):
            print(f"[ERROR] 証明書が見つかりません: {path}")
            sys.exit(1)

    client = mqtt.Client(client_id=f"jawsug-{DEVICE_ID}")
    client.on_connect = on_connect
    client.reconnect_delay_set(min_delay=1, max_delay=60)

    client.tls_set(
        ca_certs=CA_CERT,
        certfile=CERT_FILE,
        keyfile=KEY_FILE,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    print(f"[SIMULATOR] Connecting to {ENDPOINT}...")
    print(f"  Topic: {TOPIC}")
    print(f"  Interval: {SEND_INTERVAL}s")
    print(f"  Spike: after {args.spike_after}s, duration {args.spike_duration}s, level {args.spike_level}%")
    print()

    client.connect(ENDPOINT, 8883)
    client.loop_start()
    time.sleep(2)

    running = True
    start_time = time.time()

    def signal_handler(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while running:
            elapsed = time.time() - start_time
            spike_start = args.spike_after
            spike_end = args.spike_after + args.spike_duration

            # スパイク区間かどうかで基準値を決定
            if spike_start <= elapsed < spike_end:
                cpu_base = args.spike_level
                mem_base = 45.0  # メモリは一定
            else:
                cpu_base = 15.0
                mem_base = 35.0

            cpu = max(0.0, min(100.0, generate_value(cpu_base)))
            memory = max(0.0, min(100.0, generate_value(mem_base)))
            ts = int(time.time())

            payload = build_payload(DEVICE_ID, cpu, memory, ts)
            payload_json = json.dumps(payload)

            client.publish(TOPIC, payload_json, qos=0)
            print(format_stdout_line(payload))

            time.sleep(SEND_INTERVAL)

    finally:
        print("\n[EXIT] MQTT を切断して終了します。")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
