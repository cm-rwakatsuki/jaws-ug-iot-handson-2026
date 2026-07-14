#!/bin/bash
# led_ctrl.sh - ACT LED（基板上の緑色LED）をON/OFFする
# 使い方: ./led_ctrl.sh on  または  ./led_ctrl.sh off

# ACT LED の sysfs パスは OS のバージョンで異なる
#   新しい Raspberry Pi OS（Bookworm 以降）: /sys/class/leds/ACT
#   古い Raspberry Pi OS                    : /sys/class/leds/led0
if [ -d /sys/class/leds/ACT ]; then
  LED_PATH="/sys/class/leds/ACT"
else
  LED_PATH="/sys/class/leds/led0"
fi

# SDアクセス連動を解除（初回のみ必要だが毎回実行しても問題なし）
echo none | sudo tee "$LED_PATH/trigger" > /dev/null

case "$1" in
  on)
    echo 1 | sudo tee "$LED_PATH/brightness" > /dev/null
    ;;
  off)
    echo 0 | sudo tee "$LED_PATH/brightness" > /dev/null
    ;;
  *)
    echo "Usage: $0 {on|off}"
    exit 1
    ;;
esac
