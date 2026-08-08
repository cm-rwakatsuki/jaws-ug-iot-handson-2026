"""純粋関数層 — CPU / メモリ使用率の取得・整形ロジック。

I/O（psutil）に依存する関数と、外部依存を持たない純粋関数に分離する（D-9）。
純粋関数は直接ユニットテスト対象になる。
"""

from datetime import datetime, timezone, timedelta

import psutil

JST = timezone(timedelta(hours=9))


def validate_percent(value: float) -> float:
    """0〜100 にクランプし小数第 1 位に丸める。

    Args:
        value: パーセント値

    Returns:
        0.0〜100.0 にクランプされ小数第 1 位に丸められた値

    Raises:
        ValueError: value が数値でない場合
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"数値を指定してください: {value!r}")
    # NaN / Inf のチェック
    if value != value or value == float("inf") or value == float("-inf"):
        raise ValueError(f"有効な数値を指定してください: {value!r}")
    clamped = max(0.0, min(100.0, float(value)))
    return round(clamped, 1)


def read_cpu_percent(interval: float = 1.0) -> float:
    """CPU 使用率（全コア平均, %）を取得し小数第 1 位に丸める。"""
    value = psutil.cpu_percent(interval=interval)
    return round(float(value), 1)


def read_memory_percent() -> float:
    """メモリ使用率を返す。

    定義: (total - available) / total * 100（D-7）
    ※ psutil.virtual_memory().percent と同一の定義。
    ※ free コマンドの used 列とは異なる（K-2）。
    """
    mem = psutil.virtual_memory()
    # psutil.virtual_memory().percent は (total - available) / total * 100
    return round(float(mem.percent), 1)


def build_payload(device_id: str, cpu: float, memory: float, ts: int) -> dict:
    """MQTT ペイロード（4.1 節）を組み立てる。純粋関数。

    Args:
        device_id: デバイス識別子（例: "raspi-001"）
        cpu: CPU 使用率（%）
        memory: メモリ使用率（%）
        ts: Unix epoch 秒

    Returns:
        deviceId / cpu / memory / timestamp の 4 フィールドのみを含む dict
    """
    return {
        "deviceId": device_id,
        "cpu": validate_percent(cpu),
        "memory": validate_percent(memory),
        "timestamp": int(ts),
    }


def format_stdout_line(payload: dict, tz_name: str = "Asia/Tokyo") -> str:
    """[SEND] 2026-08-08 21:34:10 JST cpu=92.4% memory=41.8% 形式の表示行を返す（R1-5）。"""
    ts = payload.get("timestamp", 0)
    dt = datetime.fromtimestamp(ts, tz=JST)
    time_str = dt.strftime("%Y-%m-%d %H:%M:%S JST")
    cpu = payload.get("cpu", 0.0)
    memory = payload.get("memory", 0.0)
    return f"[SEND] {time_str} cpu={cpu}% memory={memory}%"
