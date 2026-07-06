#!/bin/bash
# led_ctrl.sh - ACT LED（基板上の緑色LED）をON/OFFする
# 使い方: ./led_ctrl.sh on  または  ./led_ctrl.sh off

LED_PATH="/sys/class/leds/led0"

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
