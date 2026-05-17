import json
import os
import random
import time
import ssl
import paho.mqtt.client as mqtt

# ---- 設定 ----
ENDPOINT  = os.environ.get("AWS_IOT_ENDPOINT", "")  # export AWS_IOT_ENDPOINT=xxxxxx-ats.iot.ap-northeast-1.amazonaws.com
EVENT_ID  = "2026-05"   # 開催年月（再開催時に変更）
DEVICE_ID = "raspi-001"   # 割り当てられた番号に書き換える
TOPIC     = f"jawsug/{EVENT_ID}/{DEVICE_ID}/telemetry"

CERT_DIR  = "./certs"
CA_CERT   = f"{CERT_DIR}/AmazonRootCA1.pem"
CERT_FILE = f"{CERT_DIR}/certificate.pem.crt"
KEY_FILE  = f"{CERT_DIR}/private.pem.key"
# --------------

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code == 0:
        print(f"[OK] Connected to AWS IoT Core")
    else:
        print(f"[ERROR] Connection failed: rc={reason_code}")

def on_publish(client, userdata, mid, reason_code, properties):
    print(f"   -> Published (mid={mid})")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_ID)
client.on_connect = on_connect
client.on_publish = on_publish

client.tls_set(
    ca_certs=CA_CERT,
    certfile=CERT_FILE,
    keyfile=KEY_FILE,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

client.connect(ENDPOINT, 8883)
client.loop_start()

print(f"Connecting to {ENDPOINT}...")
time.sleep(2)

try:
    while True:
        temperature = round(25.0 + random.uniform(-3.0, 3.0), 1)
        payload = json.dumps({
            "deviceId": DEVICE_ID,
            "temperature": temperature,
            "timestamp": int(time.time())
        })
        client.publish(TOPIC, payload, qos=1)
        print(f"[SEND] {TOPIC}: {payload}")
        time.sleep(5)
except KeyboardInterrupt:
    print("Stopped.")
    client.loop_stop()
    client.disconnect()
