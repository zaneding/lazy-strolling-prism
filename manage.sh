#!/bin/bash
# absence.io 打卡定时任务管理 / Clock management / Stempel-Verwaltung

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECKIN_PLIST_SRC="$SCRIPT_DIR/launchagents/com.absence.checkin.plist"
CHECKOUT_PLIST_SRC="$SCRIPT_DIR/launchagents/com.absence.checkout.plist"
CHECKIN_PLIST=~/Library/LaunchAgents/com.absence.checkin.plist
CHECKOUT_PLIST=~/Library/LaunchAgents/com.absence.checkout.plist
PYTHON="$SCRIPT_DIR/venv/bin/python"
SCRIPT="$SCRIPT_DIR/absence_clock.py"
ENV_FILE="$SCRIPT_DIR/.env"
SKIP_FILE="$SCRIPT_DIR/skip_dates.txt"

# Read CHECKIN_TIME and CHECKOUT_TIME from .env
_load_times() {
    CI_TIME=$(grep -E '^CHECKIN_TIME=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d ' ')
    CO_TIME=$(grep -E '^CHECKOUT_TIME=' "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d ' ')
    CI_TIME=${CI_TIME:-08:00}
    CO_TIME=${CO_TIME:-17:00}
    CI_HOUR=$(echo "$CI_TIME" | cut -d: -f1 | sed 's/^0*//')
    CI_MIN=$(echo  "$CI_TIME" | cut -d: -f2 | sed 's/^0*//')
    CO_HOUR=$(echo "$CO_TIME" | cut -d: -f1 | sed 's/^0*//')
    CO_MIN=$(echo  "$CO_TIME" | cut -d: -f2 | sed 's/^0*//')
    CI_HOUR=${CI_HOUR:-0}; CI_MIN=${CI_MIN:-0}
    CO_HOUR=${CO_HOUR:-0}; CO_MIN=${CO_MIN:-0}
}

# Write a launchd plist for weekdays Mon–Fri
_write_plist() {
    local label="$1" action="$2" hour="$3" min="$4" dest="$5"
    {
        printf '<?xml version="1.0" encoding="UTF-8"?>\n'
        printf '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"\n'
        printf '  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        printf '<plist version="1.0">\n<dict>\n'
        printf '    <key>Label</key>\n    <string>%s</string>\n' "$label"
        printf '    <key>ProgramArguments</key>\n    <array>\n'
        printf '        <string>%s</string>\n' "$PYTHON"
        printf '        <string>%s</string>\n' "$SCRIPT"
        printf '        <string>%s</string>\n' "$action"
        printf '    </array>\n'
        printf '    <key>StartCalendarInterval</key>\n    <array>\n'
        for d in 1 2 3 4 5; do
            printf '        <dict>\n'
            printf '            <key>Weekday</key><integer>%d</integer>\n' "$d"
            printf '            <key>Hour</key><integer>%d</integer>\n' "$hour"
            printf '            <key>Minute</key><integer>%d</integer>\n' "$min"
            printf '        </dict>\n'
        done
        printf '    </array>\n'
        printf '    <key>StandardOutPath</key>\n'
        printf '    <string>%s/%s.log</string>\n' "$SCRIPT_DIR" "$action"
        printf '    <key>StandardErrorPath</key>\n'
        printf '    <string>%s/%s_error.log</string>\n' "$SCRIPT_DIR" "$action"
        printf '    <key>EnvironmentVariables</key>\n    <dict>\n'
        printf '        <key>TZ</key>\n        <string>Europe/Berlin</string>\n'
        printf '    </dict>\n</dict>\n</plist>\n'
    } > "$dest"
}

case "$1" in
  start)
    _load_times
    _write_plist "com.absence.checkin"  "checkin"  "$CI_HOUR" "$CI_MIN" "$CHECKIN_PLIST_SRC"
    _write_plist "com.absence.checkout" "checkout" "$CO_HOUR" "$CO_MIN" "$CHECKOUT_PLIST_SRC"
    cp "$CHECKIN_PLIST_SRC"  "$CHECKIN_PLIST"
    cp "$CHECKOUT_PLIST_SRC" "$CHECKOUT_PLIST"
    launchctl load "$CHECKIN_PLIST"  && echo "[✓] 上班打卡已启用 / Check-in enabled: $CI_TIME"
    launchctl load "$CHECKOUT_PLIST" && echo "[✓] 下班打卡已启用 / Check-out enabled: $CO_TIME"
    ;;

  stop)
    launchctl unload "$CHECKIN_PLIST"  2>/dev/null && echo "[✓] 上班打卡已暂停 / Check-in disabled"
    launchctl unload "$CHECKOUT_PLIST" 2>/dev/null && echo "[✓] 下班打卡已暂停 / Check-out disabled"
    ;;

  status)
    echo "=== 打卡定时任务状态 / Status / Stempel-Status ==="
    launchctl list | grep absence || echo "（未激活 / Inactive / Inaktiv）"
    ;;

  checkin)
    "$PYTHON" "$SCRIPT" checkin
    ;;

  checkout)
    "$PYTHON" "$SCRIPT" checkout
    ;;

  set-time)
    _load_times
    _write_plist "com.absence.checkin"  "checkin"  "$CI_HOUR" "$CI_MIN" "$CHECKIN_PLIST_SRC"
    _write_plist "com.absence.checkout" "checkout" "$CO_HOUR" "$CO_MIN" "$CHECKOUT_PLIST_SRC"
    echo "[✓] 配置已更新 / Updated / Aktualisiert: checkin=$CI_TIME, checkout=$CO_TIME"
    echo "    运行以下命令使更改生效 / Run to apply / Zum Anwenden ausführen:"
    echo "    ./manage.sh stop && ./manage.sh start"
    ;;

  skip)
    if [ -z "$2" ]; then
        echo "用法 / Usage: ./manage.sh skip YYYY-MM-DD"
        exit 1
    fi
    echo "$2" >> "$SKIP_FILE"
    echo "[✓] 已添加跳过日期 / Skip date added / Ausnahmedatum hinzugefügt: $2"
    ;;

  log)
    echo "=== 上班打卡日志 / Check-in Log / Einstempel-Log ==="
    tail -20 "$SCRIPT_DIR/checkin.log" 2>/dev/null || echo "（暂无日志 / No logs yet / Noch keine Logs）"
    echo ""
    echo "=== 下班打卡日志 / Check-out Log / Ausstempel-Log ==="
    tail -20 "$SCRIPT_DIR/checkout.log" 2>/dev/null || echo "（暂无日志 / No logs yet / Noch keine Logs）"
    ;;

  *)
    echo "用法 / Usage: ./manage.sh [command]"
    echo ""
    echo "  start                启用自动打卡 / Enable auto clocking / Automatisches Stempeln aktivieren"
    echo "  stop                 暂停自动打卡 / Disable / Deaktivieren"
    echo "  status               查看状态 / Check status / Status prüfen"
    echo "  checkin              立即手动打上班卡 / Clock in now / Jetzt einstempeln"
    echo "  checkout             立即手动打下班卡 / Clock out now / Jetzt ausstempeln"
    echo "  set-time             从 .env 更新打卡时间 / Update times from .env / Zeiten aus .env aktualisieren"
    echo "  skip YYYY-MM-DD      添加不打卡日期 / Add skip date / Ausnahmedatum hinzufügen"
    echo "  log                  查看打卡日志 / View logs / Logs anzeigen"
    ;;
esac
