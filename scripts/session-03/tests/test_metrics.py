"""metrics.py のユニットテスト。

テスト対象:
- validate_percent: クランプ、丸め、異常値
- build_payload: 4 フィールドの型と構成
- read_cpu_percent / read_memory_percent: psutil モック
- format_stdout_line: JST 表記の表示行
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# テスト対象のモジュールをインポートできるようパスを追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics import (
    validate_percent,
    build_payload,
    read_cpu_percent,
    read_memory_percent,
    format_stdout_line,
)


# ============================================================
# validate_percent
# ============================================================


class TestValidatePercent:
    """validate_percent のテスト（R1-4）。"""

    def test_normal_value(self):
        """正常値をそのまま返す。"""
        assert validate_percent(50.0) == 50.0

    def test_clamp_below_zero(self):
        """0 未満は 0 にクランプ。"""
        assert validate_percent(-5.0) == 0.0

    def test_clamp_above_100(self):
        """100 超は 100 にクランプ。"""
        assert validate_percent(105.3) == 100.0

    def test_round_to_one_decimal(self):
        """小数第 1 位に丸める。"""
        assert validate_percent(33.456) == 33.5

    def test_boundary_zero(self):
        """境界値 0。"""
        assert validate_percent(0.0) == 0.0

    def test_boundary_100(self):
        """境界値 100。"""
        assert validate_percent(100.0) == 100.0

    def test_integer_input(self):
        """整数入力を受け入れる。"""
        assert validate_percent(75) == 75.0

    def test_non_numeric_raises(self):
        """非数値で ValueError。"""
        with pytest.raises(ValueError):
            validate_percent("abc")

    def test_none_raises(self):
        """None で ValueError。"""
        with pytest.raises(ValueError):
            validate_percent(None)

    def test_nan_raises(self):
        """NaN で ValueError。"""
        with pytest.raises(ValueError):
            validate_percent(float("nan"))

    def test_inf_raises(self):
        """Inf で ValueError。"""
        with pytest.raises(ValueError):
            validate_percent(float("inf"))


# ============================================================
# build_payload
# ============================================================


class TestBuildPayload:
    """build_payload のテスト（R1-4、4.1 節）。"""

    def test_returns_four_fields(self):
        """4 フィールドのみを含む dict を返す。"""
        result = build_payload("raspi-001", 50.0, 40.0, 1786280400)
        assert set(result.keys()) == {"deviceId", "cpu", "memory", "timestamp"}

    def test_device_id_is_string(self):
        """deviceId が文字列型。"""
        result = build_payload("raspi-001", 50.0, 40.0, 1786280400)
        assert isinstance(result["deviceId"], str)
        assert result["deviceId"] == "raspi-001"

    def test_cpu_is_float(self):
        """cpu が数値型で小数第 1 位に丸められている。"""
        result = build_payload("raspi-001", 92.456, 40.0, 1786280400)
        assert isinstance(result["cpu"], float)
        assert result["cpu"] == 92.5

    def test_memory_is_float(self):
        """memory が数値型で小数第 1 位に丸められている。"""
        result = build_payload("raspi-001", 50.0, 41.789, 1786280400)
        assert isinstance(result["memory"], float)
        assert result["memory"] == 41.8

    def test_timestamp_is_int(self):
        """timestamp が整数型。"""
        result = build_payload("raspi-001", 50.0, 40.0, 1786280400)
        assert isinstance(result["timestamp"], int)
        assert result["timestamp"] == 1786280400

    def test_no_extra_fields(self):
        """余計なフィールドを含まない。"""
        result = build_payload("raspi-001", 50.0, 40.0, 1786280400)
        assert len(result) == 4

    def test_cpu_clamped(self):
        """cpu が 100 超の場合にクランプされる。"""
        result = build_payload("raspi-001", 110.0, 40.0, 1786280400)
        assert result["cpu"] == 100.0


# ============================================================
# read_cpu_percent（psutil モック）
# ============================================================


class TestReadCpuPercent:
    """read_cpu_percent のテスト（R1-2）。"""

    @patch("metrics.psutil.cpu_percent")
    def test_returns_mocked_value(self, mock_cpu):
        """psutil の返却値を小数第 1 位に丸めて返す。"""
        mock_cpu.return_value = 45.678
        result = read_cpu_percent(interval=0.1)
        assert result == 45.7
        mock_cpu.assert_called_once_with(interval=0.1)

    @patch("metrics.psutil.cpu_percent")
    def test_returns_zero(self, mock_cpu):
        """0 % を正しく返す。"""
        mock_cpu.return_value = 0.0
        result = read_cpu_percent(interval=0.1)
        assert result == 0.0


# ============================================================
# read_memory_percent（psutil モック、D-7）
# ============================================================


class TestReadMemoryPercent:
    """read_memory_percent のテスト（D-7: (total - available) / total * 100）。"""

    @patch("metrics.psutil.virtual_memory")
    def test_correct_definition(self, mock_vmem):
        """D-7 の定義で計算されること。"""
        # total=4GB, available=2.5GB → (4-2.5)/4*100 = 37.5%
        mock_vmem.return_value = MagicMock(
            total=4 * 1024 * 1024 * 1024,
            available=int(2.5 * 1024 * 1024 * 1024),
            percent=37.5,  # psutil が内部で計算する値
        )
        result = read_memory_percent()
        assert result == 37.5

    @patch("metrics.psutil.virtual_memory")
    def test_rounds_to_one_decimal(self, mock_vmem):
        """小数第 1 位に丸める。"""
        mock_vmem.return_value = MagicMock(percent=41.789)
        result = read_memory_percent()
        assert result == 41.8


# ============================================================
# format_stdout_line（R1-5）
# ============================================================


class TestFormatStdoutLine:
    """format_stdout_line のテスト。"""

    def test_contains_send_prefix(self):
        """[SEND] プレフィックスを含む。"""
        payload = {"cpu": 92.4, "memory": 41.8, "timestamp": 1786280400}
        result = format_stdout_line(payload)
        assert result.startswith("[SEND]")

    def test_contains_jst(self):
        """JST 表記を含む。"""
        payload = {"cpu": 92.4, "memory": 41.8, "timestamp": 1786280400}
        result = format_stdout_line(payload)
        assert "JST" in result

    def test_contains_cpu_value(self):
        """cpu= の値を含む。"""
        payload = {"cpu": 92.4, "memory": 41.8, "timestamp": 1786280400}
        result = format_stdout_line(payload)
        assert "cpu=92.4%" in result

    def test_contains_memory_value(self):
        """memory= の値を含む。"""
        payload = {"cpu": 92.4, "memory": 41.8, "timestamp": 1786280400}
        result = format_stdout_line(payload)
        assert "memory=41.8%" in result

    def test_single_line(self):
        """1 行であること。"""
        payload = {"cpu": 50.0, "memory": 30.0, "timestamp": 1786280400}
        result = format_stdout_line(payload)
        assert "\n" not in result
