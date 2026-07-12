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

DELTA_TOPIC        = f"$aws/things/{THING_NAME}/shadow/update/delta"
UPDATE_TOPIC       = f"$aws/things/{THING_NAME}/shadow/update"
GET_TOPIC          = f"$aws/things/{THING_NAME}/shadow/get"
GET_ACCEPTED_TOPIC = f"$aws/things/{THING_NAME}/shadow/get/accepted"

LED_SCRIPT = "./led_ctrl.sh"
# --------------

def set_led(state: bool):
    cmd = "on" if state else "off"
    subprocess.run([LED_SCRIPT, cmd])
    print(f"[LED] {'ON' if state else 'OFF'}")

_get_sub_mid = None   # get/accepted 購読のメッセージID（購読完了を判定するため）

def on_connect(client, userdata, flags, rc):
    global _get_sub_mid
    if rc == 0:
        print(f"[OK] Connected to AWS IoT Core")
        client.subscribe(DELTA_TOPIC)
        # get/accepted を購読し、その購読が完了してから（on_subscribe 内で）get を投げる。
        # すぐ publish すると購読確定前に応答が返って取りこぼすため（AWS IoT のレース対策）。
        _, _get_sub_mid = client.subscribe(GET_ACCEPTED_TOPIC)
        print(f"[SUB] Subscribed: {DELTA_TOPIC}")
    else:
        print(f"[ERROR] Connection failed: rc={rc}")

def on_subscribe(client, userdata, mid, granted_qos):
    # get/accepted の購読が確定したら、現在の Shadow を取得する
    # （オフライン中/停止中に更新された desired を再接続時に同期するため）
    if mid == _get_sub_mid:
        client.publish(GET_TOPIC, "")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    if msg.topic == GET_ACCEPTED_TOPIC:
        # 再接続/再起動時：Shadow に残っている delta を取り出す
        led = payload.get("state", {}).get("delta", {}).get("led")
        if led:
            print(f"\n[GET] 未反映の delta を検出: led={led}")
    else:
        # 通常の delta 通知（desired 更新時にリアルタイムで届く）
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
client.on_subscribe = on_subscribe
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
    # 終了時に LED はそのままにする（停止＝オフライン。実機の状態を勝手に変えない）
    client.disconnect()
