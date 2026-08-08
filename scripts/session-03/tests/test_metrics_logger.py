"""lambda/metrics_logger.py のユニットテスト。

テスト対象:
- 正常イベントで level=INFO の JSON 1 行
- cpu 欠落時に level=WARN で例外を出さない
- 不正型でも異常終了しない
- 出力が json.loads() でパースできる
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lambda"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics_logger import handler, normalize_record, has_required_fields


# ============================================================
# normalize_record
# ============================================================


class TestNormalizeRecord:
    """normalize_record のテスト。"""

    def test_extracts_all_fields(self):
        """全フィールドを抽出する。"""
        event = {
            "deviceId": "raspi-001",
            "cpu": 92.4,
            "memory": 41.8,
            "timestamp": 1786280400,
            "topic": "jawsug/session-03/raspi-001/metrics",
            "receivedAtMs": 1786280400123,
        }
        result = normalize_record(event)
        assert result["deviceId"] == "raspi-001"
        assert result["cpu"] == 92.4
        assert result["memory"] == 41.8
        assert result["timestamp"] == 1786280400
        assert result["topic"] == "jawsug/session-03/raspi-001/metrics"
        assert result["receivedAtMs"] == 1786280400123

    def test_missing_fields_are_none(self):
        """欠落フィールドは None。"""
        event = {"deviceId": "raspi-001"}
        result = normalize_record(event)
        assert result["cpu"] is None
        assert result["memory"] is None
        assert result["timestamp"] is None


# ============================================================
# has_required_fields
# ============================================================


class TestHasRequiredFields:
    """has_required_fields のテスト。"""

    def test_all_present(self):
        """全フィールドがあれば True。"""
        record = {
            "deviceId": "raspi-001",
            "cpu": 50.0,
            "memory": 40.0,
            "timestamp": 1786280400,
        }
        assert has_required_fields(record) is True

    def test_missing_cpu(self):
        """cpu が None なら False。"""
        record = {
            "deviceId": "raspi-001",
            "cpu": None,
            "memory": 40.0,
            "timestamp": 1786280400,
        }
        assert has_required_fields(record) is False

    def test_missing_deviceId(self):
        """deviceId がなければ False。"""
        record = {"cpu": 50.0, "memory": 40.0, "timestamp": 1786280400}
        assert has_required_fields(record) is False


# ============================================================
# handler（R4-2、R4-4、R4-6、R7-5）
# ============================================================


class TestHandler:
    """Lambda handler のテスト。"""

    def test_normal_event_info_log(self, capsys):
        """正常イベントで level=INFO の JSON 1 行が出力される（R4-2）。"""
        event = {
            "deviceId": "raspi-001",
            "cpu": 92.4,
            "memory": 41.8,
            "timestamp": 1786280400,
            "topic": "jawsug/session-03/raspi-001/metrics",
            "receivedAtMs": 1786280400123,
        }
        result = handler(event, None)
        assert result["statusCode"] == 200

        captured = capsys.readouterr()
        log = json.loads(captured.out.strip())
        assert log["level"] == "INFO"
        assert log["event"] == "metrics_received"
        assert log["deviceId"] == "raspi-001"
        assert log["cpu"] == 92.4
        assert log["memory"] == 41.8
        assert log["timestamp"] == 1786280400

    def test_missing_cpu_warn_no_exception(self, capsys):
        """cpu 欠落時に level=WARN で例外を出さない（R4-4）。"""
        event = {
            "deviceId": "raspi-001",
            "memory": 41.8,
            "timestamp": 1786280400,
        }
        # 例外を出さないこと
        result = handler(event, None)
        assert result["statusCode"] == 200

        captured = capsys.readouterr()
        log = json.loads(captured.out.strip())
        assert log["level"] == "WARN"
        assert log["event"] == "metrics_incomplete"
        assert "cpu" in str(log["message"])

    def test_invalid_type_no_crash(self, capsys):
        """cpu が文字列など不正型でも異常終了しない（R7-5）。"""
        event = {
            "deviceId": "raspi-001",
            "cpu": "high",
            "memory": 41.8,
            "timestamp": 1786280400,
        }
        # cpu は文字列だが None ではないので has_required_fields は True になる
        # handler は型チェックせず受け入れる（ログとして記録するだけ）
        result = handler(event, None)
        assert result["statusCode"] == 200

    def test_output_is_parseable_json(self, capsys):
        """出力が json.loads() でパース可能な JSON（R4-6）。"""
        event = {
            "deviceId": "raspi-001",
            "cpu": 50.0,
            "memory": 30.0,
            "timestamp": 1786280400,
        }
        handler(event, None)
        captured = capsys.readouterr()
        # パースできること（例外が出ないこと）
        parsed = json.loads(captured.out.strip())
        assert isinstance(parsed, dict)

    def test_empty_event_warn(self, capsys):
        """空イベントでも WARN で処理する。"""
        result = handler({}, None)
        assert result["statusCode"] == 200

        captured = capsys.readouterr()
        log = json.loads(captured.out.strip())
        assert log["level"] == "WARN"

    def test_topic_included_in_info_log(self, capsys):
        """topic がある場合は INFO ログに含まれる。"""
        event = {
            "deviceId": "raspi-001",
            "cpu": 50.0,
            "memory": 30.0,
            "timestamp": 1786280400,
            "topic": "jawsug/session-03/raspi-001/metrics",
        }
        handler(event, None)
        captured = capsys.readouterr()
        log = json.loads(captured.out.strip())
        assert log.get("topic") == "jawsug/session-03/raspi-001/metrics"
