import json
import random
import time
import ssl
import paho.mqtt.client as mqtt

# ---- 設定 ----
ENDPOINT  = "xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"  # 取得したEndpointに書き換える
EVENT_ID  = "2026-05"   # 開催年月（再開催時に変更）
DEVICE_ID = "raspi-001"  # 割り当てられた番号に書き換える
TOPIC     = f"jawsug/{EVENT_ID}/{DEVICE_ID}/telemetry"

CERT_DIR  = "./certs"
CA_CERT   = f"{CERT_DIR}/AmazonRootCA1.pem"
CERT_FILE = f"{CERT_DIR}/certificate.pem.crt"
KEY_FILE  = f"{CERT_DIR}/private.pem.key"
# --------------

def read_temperature() -> float:
    """CPU温度を読み取る。取得できない場合はダミー値を返す。"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except OSError:
        return round(25.0 + random.uniform(-3.0, 3.0), 1)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[OK] Connected to AWS IoT Core")
    else:
        print(f"[ERROR] Connection failed: rc={rc}")

def on_publish(client, userdata, mid):
    print(f"   -> Published (mid={mid})")

client = mqtt.Client(client_id=DEVICE_ID)
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
        temperature = read_temperature()
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
