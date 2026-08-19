"""Lambda ハンドラ — IoT Rules から受信したメトリクスを構造化ログとして出力する。

このファイルが単一の正（D-10）。CFN テンプレートにはインラインで埋め込み、
test_lambda_inline_sync.py で両者の一致を検証する。
"""

import json


REQUIRED_FIELDS = ["deviceId", "cpu", "memory", "timestamp"]


def normalize_record(event: dict) -> dict:
    """イベントから必要なフィールドを抽出し、欠落は None を入れる。"""
    return {
        "deviceId": event.get("deviceId"),
        "cpu": event.get("cpu"),
        "memory": event.get("memory"),
        "timestamp": event.get("timestamp"),
        "topic": event.get("topic"),
        "receivedAtMs": event.get("receivedAtMs"),
    }


def has_required_fields(record: dict) -> bool:
    """必須フィールドが揃っているか判定する。"""
    for field in REQUIRED_FIELDS:
        if record.get(field) is None:
            return False
    return True


def handler(event, context):
    """構造化ログ（JSON 1 行）を出力する。欠落時は level=WARN で継続（R4-4）。"""
    try:
        record = normalize_record(event)

        if has_required_fields(record):
            log_entry = {
                "level": "INFO",
                "event": "metrics_received",
                "deviceId": record["deviceId"],
                "cpu": record["cpu"],
                "memory": record["memory"],
                "timestamp": record["timestamp"],
            }
            if record.get("topic"):
                log_entry["topic"] = record["topic"]
        else:
            missing = [f for f in REQUIRED_FIELDS if record.get(f) is None]
            log_entry = {
                "level": "WARN",
                "event": "metrics_incomplete",
                "message": f"Missing required fields: {missing}",
                "receivedEvent": event,
            }

        print(json.dumps(log_entry, ensure_ascii=False))
        return {"statusCode": 200, "body": log_entry}

    except Exception as e:
        error_entry = {
            "level": "ERROR",
            "event": "handler_exception",
            "error": str(e),
            "errorType": type(e).__name__,
        }
        print(json.dumps(error_entry, ensure_ascii=False))
        raise
