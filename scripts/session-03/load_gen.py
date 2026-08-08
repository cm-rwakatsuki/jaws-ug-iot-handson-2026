"""負荷生成スクリプト（R2-1〜R2-8）。

CPU 使用率やメモリ使用率を意図的に変動させ、
CloudWatch のグラフに反映されることを体感するためのツール。

使い方:
    python3 load_gen.py cpu    --target 90 --duration 180
    python3 load_gen.py memory --target 70 --duration 180
    python3 load_gen.py memory --mb 1024   --duration 180
"""

import argparse
import ctypes
import multiprocessing
import os
import signal
import sys
import time
from datetime import datetime, timezone, timedelta

import psutil

JST = timezone(timedelta(hours=9))

# メモリ確保の安全上限: 総容量の 85%（K-9）
MEMORY_SAFETY_RATIO = 0.85


# ============================================================
# 純粋関数（TDD 対象）
# ============================================================


def validate_cpu_target(target: float) -> float:
    """CPU 目標使用率を検証する。1〜100 の範囲外なら ValueError。"""
    if not isinstance(target, (int, float)):
        raise ValueError(f"CPU 目標は数値で指定してください: {target!r}")
    if target < 1 or target > 100:
        raise ValueError(f"CPU 目標は 1〜100 の範囲で指定してください: {target}")
    return float(target)


def validate_memory_target(target_mb: float, total_mb: float) -> float:
    """メモリ目標を検証し、安全上限にクランプする。

    Returns:
        安全上限以内に丸められた MB 値

    Raises:
        ValueError: target_mb が負の場合
    """
    if target_mb <= 0:
        raise ValueError(f"メモリ目標は正の値で指定してください: {target_mb}")

    max_mb = total_mb * MEMORY_SAFETY_RATIO
    if target_mb > max_mb:
        print(
            f"[WARN] 要求 {target_mb:.0f} MB は安全上限 {max_mb:.0f} MB "
            f"(総容量 {total_mb:.0f} MB の {MEMORY_SAFETY_RATIO*100:.0f}%) を超えています。"
            f"上限値にクランプします。"
        )
        return max_mb
    return target_mb


def calculate_duty_cycle(target_percent: float, cpu_count: int) -> float:
    """目標 CPU 使用率から 1 ワーカーあたりの duty cycle を計算する。

    全コアにワーカーを配置する場合、各ワーカーの duty = target / 100。
    """
    if cpu_count <= 0:
        raise ValueError("CPU コア数は 1 以上が必要です")
    # 全コアにワーカーを配置するので、duty は target% そのまま
    duty = target_percent / 100.0
    return min(1.0, max(0.0, duty))


def memory_percent_to_mb(target_percent: float, total_mb: float) -> float:
    """目標パーセントから確保すべき MB 数を計算する。"""
    return total_mb * target_percent / 100.0


# ============================================================
# ワーカー関数
# ============================================================


def cpu_worker(duty: float, stop_event):
    """CPU 負荷ワーカー。duty cycle 制御で目標使用率に近づける。"""
    cycle_time = 0.1  # 100ms サイクル
    busy_time = cycle_time * duty
    sleep_time = cycle_time * (1 - duty)

    while not stop_event.is_set():
        # ビジーループ
        end = time.time() + busy_time
        while time.time() < end:
            pass
        # スリープ
        if sleep_time > 0:
            time.sleep(sleep_time)


# ============================================================
# メイン処理
# ============================================================


def format_jst(ts: float) -> str:
    """Unix タイムスタンプを JST の文字列にフォーマットする。"""
    dt = datetime.fromtimestamp(ts, tz=JST)
    return dt.strftime("%Y-%m-%d %H:%M:%S JST")


def run_cpu_load(target: float, duration: int):
    """CPU 負荷を生成する。"""
    target = validate_cpu_target(target)
    cpu_count = os.cpu_count() or 1
    duty = calculate_duty_cycle(target, cpu_count)

    start_time = time.time()
    end_time = start_time + duration

    print(f"[CPU LOAD] 目標: {target}%  コア数: {cpu_count}  duty: {duty:.2f}")
    print(f"[CPU LOAD] 開始: {format_jst(start_time)}")
    print(f"[CPU LOAD] 終了予定: {format_jst(end_time)}")
    print(f"[CPU LOAD] 継続時間: {duration}秒")
    print()

    stop_event = multiprocessing.Event()
    workers = []

    def cleanup(signum=None, frame=None):
        stop_event.set()
        for w in workers:
            if w.is_alive():
                w.terminate()
        for w in workers:
            w.join(timeout=3)
        actual_end = time.time()
        print(f"\n[CPU LOAD] 実終了: {format_jst(actual_end)}")
        if signum is not None:
            sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # ワーカー起動
        for _ in range(cpu_count):
            w = multiprocessing.Process(target=cpu_worker, args=(duty, stop_event))
            w.daemon = True
            w.start()
            workers.append(w)

        # 進捗表示
        while time.time() < end_time:
            elapsed = int(time.time() - start_time)
            current_cpu = psutil.cpu_percent(interval=1)
            print(
                f"  [{elapsed:>4d}s / {duration}s] CPU: {current_cpu:.1f}%",
                end="\r",
            )
            if time.time() >= end_time:
                break

    finally:
        stop_event.set()
        for w in workers:
            if w.is_alive():
                w.terminate()
        for w in workers:
            w.join(timeout=3)

    actual_end = time.time()
    print(f"\n[CPU LOAD] 実終了: {format_jst(actual_end)}")
    print("[CPU LOAD] 完了。負荷を解放しました。")


def run_memory_load(target_mb: float, duration: int):
    """メモリ負荷を生成する。"""
    total_mb = psutil.virtual_memory().total / (1024 * 1024)
    target_mb = validate_memory_target(target_mb, total_mb)

    start_time = time.time()
    end_time = start_time + duration

    print(f"[MEMORY LOAD] 確保目標: {target_mb:.0f} MB / 総容量: {total_mb:.0f} MB")
    print(f"[MEMORY LOAD] 開始: {format_jst(start_time)}")
    print(f"[MEMORY LOAD] 終了予定: {format_jst(end_time)}")
    print(f"[MEMORY LOAD] 継続時間: {duration}秒")
    print()

    buffer = None

    def cleanup(signum=None, frame=None):
        nonlocal buffer
        buffer = None  # GC に任せる
        actual_end = time.time()
        print(f"\n[MEMORY LOAD] 実終了: {format_jst(actual_end)}")
        if signum is not None:
            sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # メモリ確保（ページを実際に触って遅延割り当てを回避）
        alloc_bytes = int(target_mb * 1024 * 1024)
        print(f"  メモリを確保中... ({target_mb:.0f} MB)")
        buffer = bytearray(alloc_bytes)
        # 全ページに書き込み（遅延割り当て回避）
        # 4KB ごとに 1 バイト書き込む
        for i in range(0, alloc_bytes, 4096):
            buffer[i] = 0xFF
        print(f"  確保完了。保持中...")
        print()

        # 保持（進捗表示）
        while time.time() < end_time:
            elapsed = int(time.time() - start_time)
            mem = psutil.virtual_memory()
            print(
                f"  [{elapsed:>4d}s / {duration}s] Memory: {mem.percent:.1f}%",
                end="\r",
            )
            time.sleep(1)

    finally:
        buffer = None
        actual_end = time.time()
        print(f"\n[MEMORY LOAD] 実終了: {format_jst(actual_end)}")
        print("[MEMORY LOAD] 完了。メモリを解放しました。")


def main():
    parser = argparse.ArgumentParser(
        description="負荷生成スクリプト（CPU / メモリ）"
    )
    subparsers = parser.add_subparsers(dest="mode", help="負荷モード")

    # CPU サブコマンド
    cpu_parser = subparsers.add_parser("cpu", help="CPU 負荷を生成")
    cpu_parser.add_argument(
        "--target", type=float, required=True, help="目標 CPU 使用率（%%）"
    )
    cpu_parser.add_argument(
        "--duration", type=int, default=180, help="継続時間（秒）（既定: 180）"
    )

    # Memory サブコマンド
    mem_parser = subparsers.add_parser("memory", help="メモリ負荷を生成")
    mem_group = mem_parser.add_mutually_exclusive_group(required=True)
    mem_group.add_argument("--target", type=float, help="目標メモリ使用率（%%）")
    mem_group.add_argument("--mb", type=float, help="確保容量（MB）")
    mem_parser.add_argument(
        "--duration", type=int, default=180, help="継続時間（秒）（既定: 180）"
    )

    args = parser.parse_args()

    if args.mode is None:
        parser.print_help()
        sys.exit(1)

    if args.mode == "cpu":
        run_cpu_load(args.target, args.duration)
    elif args.mode == "memory":
        total_mb = psutil.virtual_memory().total / (1024 * 1024)
        if args.mb:
            target_mb = args.mb
        else:
            target_mb = memory_percent_to_mb(args.target, total_mb)
        run_memory_load(target_mb, args.duration)


if __name__ == "__main__":
    main()
