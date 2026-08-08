#!/bin/bash
# デバイス側の CPU / メモリ使用率確認ヘルパー（R2-9・R2-10）
# metrics_publisher.py と同一の定義（D-7）で値を表示する。
#
# CPU:    全コア平均使用率（/proc/stat から計算）
# Memory: (total - available) / total * 100
#         ※ free コマンドの used 列とは異なる（K-2）

NOW=$(date +"%Y-%m-%d %H:%M:%S JST")

# --- CPU 使用率（1 秒間の差分で計算） ---
read_cpu_stat() {
    awk '/^cpu / {print $2+$3+$4+$5+$6+$7+$8, $5}' /proc/stat
}

CPU_BEFORE=$(read_cpu_stat)
sleep 1
CPU_AFTER=$(read_cpu_stat)

TOTAL_BEFORE=$(echo "$CPU_BEFORE" | awk '{print $1}')
IDLE_BEFORE=$(echo "$CPU_BEFORE" | awk '{print $2}')
TOTAL_AFTER=$(echo "$CPU_AFTER" | awk '{print $1}')
IDLE_AFTER=$(echo "$CPU_AFTER" | awk '{print $2}')

TOTAL_DIFF=$((TOTAL_AFTER - TOTAL_BEFORE))
IDLE_DIFF=$((IDLE_AFTER - IDLE_BEFORE))

if [ "$TOTAL_DIFF" -gt 0 ]; then
    CPU_PERCENT=$(awk "BEGIN {printf \"%.1f\", (1 - $IDLE_DIFF / $TOTAL_DIFF) * 100}")
else
    CPU_PERCENT="0.0"
fi

# --- メモリ使用率（D-7: (total - available) / total * 100） ---
MEM_TOTAL=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
MEM_AVAILABLE=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)

# free コマンド的な used (total - free - buffers - cached)
MEM_FREE=$(awk '/^MemFree:/ {print $2}' /proc/meminfo)
MEM_BUFFERS=$(awk '/^Buffers:/ {print $2}' /proc/meminfo)
MEM_CACHED=$(awk '/^Cached:/ {print $2}' /proc/meminfo)
MEM_USED_FREE_DEF=$((MEM_TOTAL - MEM_FREE - MEM_BUFFERS - MEM_CACHED))

MEM_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($MEM_TOTAL - $MEM_AVAILABLE) / $MEM_TOTAL * 100}")

# KB → MB 変換
MEM_TOTAL_MB=$((MEM_TOTAL / 1024))
MEM_AVAILABLE_MB=$((MEM_AVAILABLE / 1024))
MEM_USED_FREE_DEF_MB=$((MEM_USED_FREE_DEF / 1024))

echo "=== $NOW ==="
echo "CPU    : ${CPU_PERCENT} %   (全コア平均、/proc/stat から計算)"
echo "Memory : ${MEM_PERCENT} %   ((total - available) / total)"
echo "  total=${MEM_TOTAL_MB} MB  available=${MEM_AVAILABLE_MB} MB  used(free コマンド表記)=${MEM_USED_FREE_DEF_MB} MB"
echo ""
echo "※ free コマンドの used 列は buffers/cached を除外するため、上記の Memory と値が異なります"
echo "※ metrics_publisher.py が送信する値は上記 Memory と同じ定義です（D-7）"
