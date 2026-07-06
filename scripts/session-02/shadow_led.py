import json
import subprocess
import ssl
import paho.mqtt.client as mqtt

# ---- 設定 ----
ENDPOINT   = "xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"  # 取得したEndpointに書き換える
DEVICE_ID  = "raspi-001"  # AWS設定で作成したThing名に合わせる（jawsug-<DEVICE_ID>）
THING_NAME = f"jawsug-{DEVICE_ID}"

CERT_DIR  = "./certs"   # ダウンロードした証明書を配置したディレクトリ
CA_CERT   = f"{CERT_DIR}/AmazonRootCA1.pem"
CERT_FILE = f"{CERT_DIR}/certificate.pem.crt"
KEY_FILE  = f"{CERT_DIR}/private.pem.key"

DELTA_TOPIC  = f"$aws/things/{THING_NAME}/shadow/update/delta"
UPDATE_TOPIC = f"$aws/things/{THING_NAME}/shadow/update"

LED_SCRIPT = "./led_ctrl.sh"
# --------------

def set_led(state: bool):
    cmd = "on" if state else "off"
    subprocess.run([LED_SCRIPT, cmd])
    print(f"[LED] {'ON' if state else 'OFF'}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[OK] Connected to AWS IoT Core")
        client.subscribe(DELTA_TOPIC)
        print(f"[SUB] Subscribed: {DELTA_TOPIC}")
    else:
        print(f"[ERROR] Connection failed: rc={rc}")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    print(f"\n[RECV] Delta: {json.dumps(payload, indent=2)}")

    led = payload.get("state", {}).get("led")
    if led:
        set_led(led == "on")

        # reported を更新（desired と一致させることで delta が空になる）
        report = {"state": {"reported": {"led": led}}}
        client.publish(UPDATE_TOPIC, json.dumps(report))
        print(f"[SEND] Reported updated: led={led}")

client = mqtt.Client(client_id=THING_NAME)
client.on_connect = on_connect
client.on_message = on_message

client.tls_set(
    ca_certs=CA_CERT,
    certfile=CERT_FILE,
    keyfile=KEY_FILE,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

try:
    client.connect(ENDPOINT, 8883)
    print("Waiting for Shadow delta...")
    client.loop_forever()
except KeyboardInterrupt:
    print("Stopped.")
    set_led(False)   # 終了時にLEDを消灯
    client.disconnect()
