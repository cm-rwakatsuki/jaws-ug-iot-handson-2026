"""load_gen.py のユニットテスト。

テスト対象:
- validate_cpu_target: 範囲検証
- validate_memory_target: 安全上限クランプ
- calculate_duty_cycle: duty 値の計算
- memory_percent_to_mb: % → MB 変換
- クリーンアップ / 時刻表示（モック）
"""

import signal
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from load_gen import (
    validate_cpu_target,
    validate_memory_target,
    calculate_duty_cycle,
    memory_percent_to_mb,
    format_jst,
    cpu_worker,
    main,
    MEMORY_SAFETY_RATIO,
)


# ============================================================
# validate_cpu_target（R2-6）
# ============================================================


class TestValidateCpuTarget:
    """CPU 目標のバリデーション。"""

    def test_valid_target(self):
        """正常な目標値。"""
        assert validate_cpu_target(90) == 90.0

    def test_boundary_1(self):
        """下限 1。"""
        assert validate_cpu_target(1) == 1.0

    def test_boundary_100(self):
        """上限 100。"""
        assert validate_cpu_target(100) == 100.0

    def test_below_1_raises(self):
        """1 未満で ValueError。"""
        with pytest.raises(ValueError):
            validate_cpu_target(0)

    def test_above_100_raises(self):
        """100 超で ValueError。"""
        with pytest.raises(ValueError):
            validate_cpu_target(101)

    def test_negative_raises(self):
        """負の値で ValueError。"""
        with pytest.raises(ValueError):
            validate_cpu_target(-10)

    def test_non_numeric_raises(self):
        """非数値で ValueError。"""
        with pytest.raises(ValueError):
            validate_cpu_target("high")


# ============================================================
# validate_memory_target（R2-6、K-9）
# ============================================================


class TestValidateMemoryTarget:
    """メモリ目標のバリデーション。"""

    def test_within_limit(self):
        """安全上限内の値はそのまま返す。"""
        # total=4096MB, 85% = 3481.6MB
        result = validate_memory_target(2000, 4096)
        assert result == 2000

    def test_exceeds_limit_clamped(self, capsys):
        """確保後の総使用量が安全上限を超える場合にクランプされる。"""
        total_mb = 4096
        used_mb = 1024
        max_alloc_mb = total_mb * MEMORY_SAFETY_RATIO - used_mb
        result = validate_memory_target(3000, total_mb, used_mb)
        assert result == max_alloc_mb
        captured = capsys.readouterr()
        assert "[WARN]" in captured.out

    def test_negative_raises(self):
        """負の値で ValueError。"""
        with pytest.raises(ValueError):
            validate_memory_target(-100, 4096)

    def test_zero_raises(self):
        """0 で ValueError。"""
        with pytest.raises(ValueError):
            validate_memory_target(0, 4096)

    def test_exactly_at_limit(self):
        """ちょうど安全上限の場合はクランプしない。"""
        total_mb = 4096
        used_mb = 1024
        max_alloc_mb = total_mb * MEMORY_SAFETY_RATIO - used_mb
        result = validate_memory_target(max_alloc_mb, total_mb, used_mb)
        assert result == max_alloc_mb

    def test_no_safe_capacity_returns_zero(self, capsys):
        """現在使用量が安全上限以上なら追加確保量は 0。"""
        result = validate_memory_target(128, 4096, 3600)
        assert result == 0.0
        assert "[WARN]" in capsys.readouterr().out


# ============================================================
# calculate_duty_cycle（R2-1）
# ============================================================


class TestCalculateDutyCycle:
    """duty cycle 計算のテスト。"""

    def test_90_percent(self):
        """90% 目標 → duty = 0.9。"""
        assert calculate_duty_cycle(90, 4) == 0.9

    def test_50_percent(self):
        """50% 目標 → duty = 0.5。"""
        assert calculate_duty_cycle(50, 4) == 0.5

    def test_100_percent(self):
        """100% 目標 → duty = 1.0。"""
        assert calculate_duty_cycle(100, 4) == 1.0

    def test_1_percent(self):
        """1% 目標 → duty = 0.01。"""
        assert calculate_duty_cycle(1, 4) == 0.01

    def test_zero_cpu_count_raises(self):
        """CPU コア数 0 で ValueError。"""
        with pytest.raises(ValueError):
            calculate_duty_cycle(50, 0)


# ============================================================
# memory_percent_to_mb
# ============================================================


class TestMemoryPercentToMb:
    """最終目標使用率から追加確保量への変換テスト。"""

    def test_50_percent_of_4096(self):
        """現在25%使用中なら、50%到達に必要な追加量は25%。"""
        assert memory_percent_to_mb(50, 4096, 1024) == 1024.0

    def test_target_70_percent_subtracts_current_usage(self):
        """現在30%使用中の --target 70 は40%分だけ追加確保する。"""
        total_mb = 2048
        used_mb = total_mb * 0.30
        assert memory_percent_to_mb(70, total_mb, used_mb) == pytest.approx(
            total_mb * 0.40
        )

    def test_already_above_target_returns_zero(self):
        """現在使用率が目標以上なら追加確保しない。"""
        assert memory_percent_to_mb(50, 4096, 2457.6) == 0.0

    def test_target_above_safety_limit_is_clamped(self, capsys):
        """85%を超える最終目標は85%へクランプする。"""
        total_mb = 4096
        used_mb = 1024
        result = memory_percent_to_mb(100, total_mb, used_mb)
        assert result == pytest.approx(total_mb * MEMORY_SAFETY_RATIO - used_mb)
        assert "[WARN]" in capsys.readouterr().out

    @pytest.mark.parametrize("target", [0, -1, 101])
    def test_invalid_percent_raises(self, target):
        """0以下または100超の目標値は拒否する。"""
        with pytest.raises(ValueError):
            memory_percent_to_mb(target, 4096, 1024)


# ============================================================
# memory CLI の追加確保量計算
# ============================================================


class TestMemoryCli:
    """--target が最終使用率として run_memory_load へ渡されること。"""

    @patch("load_gen.run_memory_load")
    @patch("load_gen.psutil.virtual_memory")
    def test_target_subtracts_current_usage(self, mock_virtual_memory, mock_run):
        """2GB・使用率30%で目標70%なら、40%分だけ追加確保する。"""
        total_bytes = 2048 * 1024 * 1024
        mock_virtual_memory.return_value = MagicMock(
            total=total_bytes,
            available=total_bytes * 0.70,
            percent=30.0,
        )

        with patch.object(
            sys,
            "argv",
            ["load_gen.py", "memory", "--target", "70", "--duration", "180"],
        ):
            main()

        mock_run.assert_called_once()
        allocation_mb, duration = mock_run.call_args.args
        assert allocation_mb == pytest.approx(2048 * 0.40)
        assert duration == 180

    @patch("load_gen.run_memory_load")
    @patch("load_gen.psutil.virtual_memory")
    def test_target_at_or_below_current_usage_skips_allocation(
        self, mock_virtual_memory, mock_run, capsys
    ):
        """現在使用率が目標以上なら追加確保処理を呼ばない。"""
        total_bytes = 2048 * 1024 * 1024
        mock_virtual_memory.return_value = MagicMock(
            total=total_bytes,
            available=total_bytes * 0.40,
            percent=60.0,
        )

        with patch.object(
            sys,
            "argv",
            ["load_gen.py", "memory", "--target", "50", "--duration", "180"],
        ):
            main()

        mock_run.assert_not_called()
        assert "追加確保は不要" in capsys.readouterr().out


# ============================================================
# cpu_worker のシグナルハンドラ（R2-5 / 実機で発見した不具合の再発防止）
# ============================================================


class TestCpuWorkerSignalHandling:
    """ワーカーが親のシグナルハンドラを引き継がないこと。

    `multiprocessing` の fork では子が親のシグナルハンドラを継承する。
    継承したままだと親の `terminate()`（SIGTERM）で親用のクリーンアップが
    子プロセス内で走り、`Process.is_alive()` が
    `AssertionError: can only test a child process` を投げて
    大量のトレースバックが出る（2026-08-13 に実機で発生）。
    """

    @patch("load_gen.signal.signal")
    def test_worker_resets_inherited_signal_handlers(self, mock_signal):
        """ワーカーの先頭で SIGINT / SIGTERM を親から切り離すこと。"""
        stop_event = MagicMock()
        stop_event.is_set.return_value = True  # ループに入らず即終了させる

        cpu_worker(0.5, stop_event)

        handled = {c.args[0] for c in mock_signal.call_args_list if c.args}
        assert signal.SIGINT in handled, (
            "ワーカーが SIGINT のハンドラを解除していません。"
            "親のハンドラを継承したままだとトレースバックが出ます"
        )
        assert signal.SIGTERM in handled, (
            "ワーカーが SIGTERM のハンドラを解除していません"
        )

    @patch("load_gen.signal.signal")
    def test_worker_does_not_use_parent_cleanup(self, mock_signal):
        """解除先が親のハンドラ関数ではなく既定動作／無視であること。"""
        stop_event = MagicMock()
        stop_event.is_set.return_value = True

        cpu_worker(0.5, stop_event)

        for call in mock_signal.call_args_list:
            if not call.args:
                continue
            handler = call.args[1]
            assert handler in (signal.SIG_DFL, signal.SIG_IGN), (
                f"ワーカーのハンドラは SIG_DFL / SIG_IGN にすべきです: {handler}"
            )


# ============================================================
# format_jst（R2-8）
# ============================================================


class TestFormatJst:
    """JST 時刻表示のテスト。"""

    def test_contains_jst(self):
        """JST を含む。"""
        result = format_jst(1786280400)
        assert "JST" in result

    def test_contains_date_format(self):
        """YYYY-MM-DD HH:MM:SS 形式を含む。"""
        result = format_jst(1786280400)
        # 基本的な日付フォーマットチェック
        parts = result.split()
        assert len(parts) == 3  # date time JST
        assert "-" in parts[0]
        assert ":" in parts[1]
