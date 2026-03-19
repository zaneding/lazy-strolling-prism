#!/bin/bash
# absence.io 打卡定时任务管理

CHECKIN_PLIST=~/Library/LaunchAgents/com.absence.checkin.plist
CHECKOUT_PLIST=~/Library/LaunchAgents/com.absence.checkout.plist
PYTHON=/Users/zijian/Stampen/venv/bin/python
SCRIPT=/Users/zijian/Stampen/absence_clock.py

case "$1" in
  start)
    launchctl load "$CHECKIN_PLIST" && echo "[✓] 上班打卡定时已启用 (周一至周五 08:00)"
    launchctl load "$CHECKOUT_PLIST" && echo "[✓] 下班打卡定时已启用 (周一至周五 17:00)"
    ;;
  stop)
    launchctl unload "$CHECKIN_PLIST" 2>/dev/null && echo "[✓] 上班打卡定时已暂停"
    launchctl unload "$CHECKOUT_PLIST" 2>/dev/null && echo "[✓] 下班打卡定时已暂停"
    ;;
  status)
    echo "=== 打卡定时任务状态 ==="
    launchctl list | grep absence || echo "（未激活）"
    ;;
  checkin)
    "$PYTHON" "$SCRIPT" checkin
    ;;
  checkout)
    "$PYTHON" "$SCRIPT" checkout
    ;;
  log)
    echo "=== 上班打卡日志 ==="
    tail -20 /Users/zijian/Stampen/checkin.log 2>/dev/null || echo "（暂无日志）"
    echo ""
    echo "=== 下班打卡日志 ==="
    tail -20 /Users/zijian/Stampen/checkout.log 2>/dev/null || echo "（暂无日志）"
    ;;
  *)
    echo "用法: ./manage.sh [start|stop|status|checkin|checkout|log]"
    echo ""
    echo "  start     启用自动打卡（周一至周五 08:00/17:00）"
    echo "  stop      暂停自动打卡"
    echo "  status    查看是否已激活"
    echo "  checkin   立即手动打上班卡"
    echo "  checkout  立即手动打下班卡"
    echo "  log       查看最近打卡日志"
    ;;
esac
