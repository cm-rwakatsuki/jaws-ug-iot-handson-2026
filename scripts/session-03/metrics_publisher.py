"""Raspberry Pi 用メトリクス送信スクリプト。

CPU 使用率・メモリ使用率を一定間隔で AWS IoT Core に MQTT で送信する。
第1回・第2回と同様に、冒頭の設定値を参加者が書き換える方式。
"""

import json
import os
import signal
import ssl
import sys
import time

import paho.mqtt.client as mqtt

from metrics import (
    build_payload,
    format_stdout_line,
    read_cpu_percent,
    read_memory_percent,
)

# ---- 設定（参加者が書き換える） ----
ENDPOINT = "xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"  # 取得した Endpoint に書き換える
DEVICE_ID = "raspi-001"  # 割り当てられた番号に書き換える（jawsug-raspi-001 の raspi-001 部分）
# ----------------------------------

SEND_INTERVAL = int(os.environ.get("SEND_INTERVAL", "10"))  # 秒（R1-2）
TOPIC = f"jawsug/session-03/{DEVICE_ID}/metrics"

CERT_DIR = "./certs"
CA_CERT = f"{CERT_DIR}/AmazonRootCA1.pem"
CERT_FILE = f"{CERT_DIR}/certificate.pem.crt"
KEY_FILE = f"{CERT_DIR}/private.pem.key"


def check_cert_files():
    """証明書ファイルの存在チェック。無ければメッセージを出して終了する。"""
    for path, desc in [
        (CA_CERT, "CA 証明書 (AmazonRootCA1.pem)"),
        (CERT_FILE, "デバイス証明書 (certificate.pem.crt)"),
        (KEY_FILE, "秘密鍵 (private.pem.key)"),
    ]:
        if not os.path.isfile(path):
            print(f"[ERROR] {desc} が見つかりません: {path}")
            print(f"  → certs/ ディレクトリに以下のファイルを配置してください:")
            print(f"    - AmazonRootCA1.pem")
            print(f"    - certificate.pem.crt")
            print(f"    - private.pem.key")
            sys.exit(1)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[OK] Connected to AWS IoT Core")
    else:
        print(f"[ERROR] Connection failed: rc={rc}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[WARN] Unexpected disconnection (rc={rc}). Reconnecting...")


def on_publish(client, userdata, mid):
    pass  # 送信確認は標準出力で行うため、ここでは何もしない


def main():
    check_cert_files()

    client = mqtt.Client(client_id=f"jawsug-{DEVICE_ID}")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish

    # 自動再接続の設定（R1-7）
    client.reconnect_delay_set(min_delay=1, max_delay=60)

    client.tls_set(
        ca_certs=CA_CERT,
        certfile=CERT_FILE,
        keyfile=KEY_FILE,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    print(f"Connecting to {ENDPOINT}...")
    print(f"  Topic: {TOPIC}")
    print(f"  Interval: {SEND_INTERVAL}s")
    print()

    client.connect(ENDPOINT, 8883)
    client.loop_start()
    time.sleep(2)

    running = True

    def signal_handler(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while running:
            try:
                cpu = read_cpu_percent(interval=1.0)
                memory = read_memory_percent()
                ts = int(time.time())

                payload = build_payload(DEVICE_ID, cpu, memory, ts)
                payload_json = json.dumps(payload)

                client.publish(TOPIC, payload_json, qos=0)
                print(format_stdout_line(payload))

            except Exception as e:
                print(f"[WARN] メトリクス取得に失敗しました: {e}")

            # SEND_INTERVAL から取得にかかった時間を差し引かないシンプルな実装
            # （1 秒の cpu_percent 計測が含まれるため、実質 SEND_INTERVAL + 1 秒）
            time.sleep(max(0, SEND_INTERVAL - 1))

    finally:
        print("\n[EXIT] MQTT を切断して終了します。")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
