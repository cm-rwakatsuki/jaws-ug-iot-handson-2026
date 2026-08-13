"""負荷生成スクリプト（R2-1〜R2-8）。

CPU 使用率やメモリ使用率を意図的に変動させ、
CloudWatch のグラフに反映されることを体感するためのツール。

使い方:
    python3 load_gen.py cpu    --target 90 --duration 180
    python3 load_gen.py memory --target 70 --duration 180
    python3 load_gen.py memory --mb 1024   --duration 180
"""

import argparse
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


def validate_memory_target(
    target_mb: float, total_mb: float, used_mb: float = 0.0
) -> float:
    """追加確保量を検証し、確保後の総使用量が安全上限内になるようクランプする。

    Returns:
        安全に追加確保できる MB 値

    Raises:
        ValueError: target_mb が負の場合
    """
    if target_mb <= 0:
        raise ValueError(f"メモリ目標は正の値で指定してください: {target_mb}")

    max_alloc_mb = max(0.0, total_mb * MEMORY_SAFETY_RATIO - used_mb)
    if target_mb > max_alloc_mb:
        print(
            f"[WARN] 要求 {target_mb:.0f} MB を追加すると、メモリ総使用量が安全上限 "
            f"{total_mb * MEMORY_SAFETY_RATIO:.0f} MB "
            f"(総容量 {total_mb:.0f} MB の {MEMORY_SAFETY_RATIO*100:.0f}%) を超えます。"
            f"追加確保量を {max_alloc_mb:.0f} MB にクランプします。"
        )
        return max_alloc_mb
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


def memory_percent_to_mb(
    target_percent: float, total_mb: float, used_mb: float = 0.0
) -> float:
    """最終的な目標使用率から追加確保すべき MB 数を計算する。

    目標は安全上限（総容量の 85%）にクランプし、現在使用中のメモリを
    差し引いた分だけを返す。すでに目標以上なら 0 MB を返す。
    """
    if not isinstance(target_percent, (int, float)):
        raise ValueError(f"メモリ目標は数値で指定してください: {target_percent!r}")
    if target_percent <= 0 or target_percent > 100:
        raise ValueError(
            f"メモリ目標は 0 より大きく 100 以下で指定してください: {target_percent}"
        )

    safe_percent = min(float(target_percent), MEMORY_SAFETY_RATIO * 100)
    if target_percent > safe_percent:
        print(
            f"[WARN] 目標 {target_percent:.0f}% は安全上限 "
            f"{safe_percent:.0f}% を超えています。上限値にクランプします。"
        )

    target_used_mb = total_mb * safe_percent / 100.0
    return max(0.0, target_used_mb - used_mb)


# ============================================================
# ワーカー関数
# ============================================================


def cpu_worker(duty: float, stop_event):
    """CPU 負荷ワーカー。duty cycle 制御で目標使用率に近づける。"""
    # 親から継承したシグナルハンドラを解除する。
    # multiprocessing の fork では子が親のハンドラを継承するため、
    # 親が terminate()（SIGTERM）を送ると親用のクリーンアップ処理が
    # 子プロセス内で動き、Process.is_alive() が
    # 「AssertionError: can only test a child process」を投げる。
    # 子は素直に終了させたいので既定動作へ戻す。
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

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
    main_pid = os.getpid()
    released = False

    def release():
        """ワーカーを停止して終了メッセージを出す。

        シグナル経路と finally の両方から呼ばれるため冪等にする。
        子プロセスから呼ばれた場合は何もしない（保険。ワーカー側でも
        ハンドラを解除しているので通常ここには来ない）。
        """
        nonlocal released
        if released or os.getpid() != main_pid:
            return
        released = True

        stop_event.set()
        for w in workers:
            if w.is_alive():
                w.terminate()
        for w in workers:
            w.join(timeout=3)

        print(f"\n[CPU LOAD] 実終了: {format_jst(time.time())}")
        print("[CPU LOAD] 完了。負荷を解放しました。")

    def on_signal(signum, frame):
        release()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    try:
        # ワーカー起動
        for _ in range(cpu_count):
            w = multiprocessing.Process(
                target=cpu_worker, args=(duty, stop_event), daemon=True
            )
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

    finally:
        release()


def run_memory_load(target_mb: float, duration: int):
    """メモリ負荷を生成する。"""
    mem = psutil.virtual_memory()
    total_mb = mem.total / (1024 * 1024)
    used_mb = (mem.total - mem.available) / (1024 * 1024)
    target_mb = validate_memory_target(target_mb, total_mb, used_mb)

    if target_mb <= 0:
        print(
            "[MEMORY LOAD] 現在のメモリ使用量が安全上限に達しているため、"
            "追加確保せず終了します。"
        )
        return

    start_time = time.time()
    end_time = start_time + duration

    print(f"[MEMORY LOAD] 確保目標: {target_mb:.0f} MB / 総容量: {total_mb:.0f} MB")
    print(f"[MEMORY LOAD] 開始: {format_jst(start_time)}")
    print(f"[MEMORY LOAD] 終了予定: {format_jst(end_time)}")
    print(f"[MEMORY LOAD] 継続時間: {duration}秒")
    print()

    buffer = None
    released = False

    def release():
        """確保したメモリを解放して終了メッセージを出す（冪等）。"""
        nonlocal buffer, released
        if released:
            return
        released = True
        buffer = None  # GC に任せる
        print(f"\n[MEMORY LOAD] 実終了: {format_jst(time.time())}")
        print("[MEMORY LOAD] 完了。メモリを解放しました。")

    def on_signal(signum, frame):
        release()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

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
    mem_group.add_argument(
        "--target", type=float, help="実行後の目標メモリ使用率（%%）"
    )
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
        mem = psutil.virtual_memory()
        total_mb = mem.total / (1024 * 1024)
        used_mb = (mem.total - mem.available) / (1024 * 1024)
        if args.mb is not None:
            target_mb = args.mb
        else:
            target_mb = memory_percent_to_mb(args.target, total_mb, used_mb)
            if target_mb <= 0:
                print(
                    f"[MEMORY LOAD] 現在の使用率 {mem.percent:.1f}% は目標 "
                    f"{min(args.target, MEMORY_SAFETY_RATIO * 100):.1f}% "
                    "以上のため、追加確保は不要です。"
                )
                return
        run_memory_load(target_mb, args.duration)


if __name__ == "__main__":
    main()
