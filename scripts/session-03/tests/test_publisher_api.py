"""paho-mqtt のコールバック API バージョンに関するテスト。

paho-mqtt 2.x で旧形式（Callback API version 1）のまま `mqtt.Client()` を作ると
起動時に DeprecationWarning が出る。参加者の画面に警告が出ると
「何か失敗したのか」と不安になるため、新形式（VERSION2）を使う。

第1回の `simulator.py` は既に VERSION2 を使っており、そちらに揃える。
"""

import inspect
import sys
from pathlib import Path

import pytest

SESSION_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SESSION_DIR))

TARGETS = ["metrics_publisher", "simulator"]

# VERSION2 のコールバックシグネチャ（paho-mqtt 2.x）
EXPECTED_PARAMS = {
    "on_connect": ["client", "userdata", "connect_flags", "reason_code", "properties"],
    "on_disconnect": ["client", "userdata", "disconnect_flags", "reason_code", "properties"],
    "on_publish": ["client", "userdata", "mid", "reason_code", "properties"],
}


@pytest.mark.parametrize("module_name", TARGETS)
def test_uses_callback_api_version2(module_name):
    """`mqtt.Client()` の生成で CallbackAPIVersion.VERSION2 を指定していること。"""
    source = (SESSION_DIR / f"{module_name}.py").read_text(encoding="utf-8")
    assert "mqtt.Client(" in source, f"{module_name}.py に mqtt.Client( がありません"
    assert "CallbackAPIVersion.VERSION2" in source, (
        f"{module_name}.py が Callback API version 1 のままです。"
        "paho-mqtt 2.x では起動時に DeprecationWarning が出ます"
    )


@pytest.mark.parametrize("module_name", TARGETS)
def test_callback_signatures_match_version2(module_name):
    """コールバックの引数が VERSION2 の形式になっていること。

    VERSION2 では引数が増える（reason_code / properties）。
    旧形式のままだと呼び出し時に TypeError になる。
    """
    module = __import__(module_name)

    for name, expected in EXPECTED_PARAMS.items():
        fn = getattr(module, name, None)
        if fn is None:
            continue  # そのコールバックを使っていないモジュールは対象外
        actual = list(inspect.signature(fn).parameters)
        assert actual == expected, (
            f"{module_name}.{name} の引数が VERSION2 の形式ではありません。\n"
            f"  期待: {expected}\n  実際: {actual}"
        )
