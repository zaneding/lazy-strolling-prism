#!/usr/bin/env python3
"""
absence.io 自动打卡脚本

用法:
  python absence_clock.py checkin   # 打卡上班
  python absence_clock.py checkout  # 打卡下班

跳过日期: 在 skip_dates.txt 中每行写一个日期（YYYY-MM-DD），当天不打卡。
"""

import sys
import os
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

import requests
from requests_hawk import HawkAuth
from dotenv import load_dotenv

# ── 配置 ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
SKIP_DATES_FILE = BASE_DIR / "skip_dates.txt"
BASE_URL = "https://app.absence.io/api/v2"
TZ_BERLIN = ZoneInfo("Europe/Berlin")

load_dotenv(ENV_FILE)


def load_skip_dates():
    if not SKIP_DATES_FILE.exists():
        return set()
    lines = SKIP_DATES_FILE.read_text(encoding="utf-8").splitlines()
    dates = set()
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            dates.add(line)
    return dates


def is_skip_today():
    today = datetime.now(TZ_BERLIN).strftime("%Y-%m-%d")
    skip_dates = load_skip_dates()
    if today in skip_dates:
        print(f"[跳过] {today} 已在 skip_dates.txt 中，不打卡")
        return True
    return False


def get_auth():
    api_id = os.environ.get("ABSENCE_API_ID", "").strip()
    api_key = os.environ.get("ABSENCE_API_KEY", "").strip()
    if not api_id or not api_key:
        print("[错误] 缺少 ABSENCE_API_ID 或 ABSENCE_API_KEY")
        sys.exit(1)
    return HawkAuth(id=api_id, key=api_key, algorithm="sha256", always_hash_content=False)


def get_user_id():
    return os.environ.get("ABSENCE_API_ID", "").strip()


def now_berlin():
    return datetime.now(TZ_BERLIN)


def to_utc_iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def tz_offset_str(dt):
    offset_seconds = int(dt.utcoffset().total_seconds())
    sign = "+" if offset_seconds >= 0 else "-"
    h, m = divmod(abs(offset_seconds) // 60, 60)
    return f"{sign}{h:02d}{m:02d}"


def post(auth, path, payload):
    resp = requests.post(
        f"{BASE_URL}/{path}",
        data=json.dumps(payload),
        auth=auth,
        headers={"Content-Type": "application/json"},
    )
    return resp


def checkin(auth, user_id):
    now = now_berlin()
    payload = {
        "userId": user_id,
        "start": to_utc_iso(now),
        "end": None,
        "timezoneName": "Europe/Berlin",
        "timezone": tz_offset_str(now),
        "type": "work",
    }
    resp = post(auth, "timespans/create", payload)

    if resp.status_code == 412:
        print(f"[!] 已有未关闭的打卡记录，跳过（{now.strftime('%Y-%m-%d %H:%M')} Berlin）")
        return

    if not resp.ok:
        print(f"[错误] 上班打卡失败 {resp.status_code}: {resp.text[:500]}")
    resp.raise_for_status()
    print(f"[✓] 上班打卡成功: {now.strftime('%Y-%m-%d %H:%M')} (Berlin)")


def checkout(auth, user_id):
    clock_dt = now_berlin()
    today_start = clock_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    resp = post(auth, "timespans", {
        "filter": {
            "userId": user_id,
            "start": {"$gte": to_utc_iso(today_start)},
            "end": None,
        },
        "limit": 5,
        "skip": 0,
    })
    if not resp.ok:
        print(f"[错误] 查询打卡记录失败 {resp.status_code}: {resp.text[:500]}")
    resp.raise_for_status()
    timespans = resp.json().get("data", [])

    if not timespans:
        print(f"[!] 未找到今天未关闭的打卡记录（{clock_dt.strftime('%Y-%m-%d %H:%M')} Berlin）")
        sys.exit(0)

    ts = timespans[0]
    update_payload = {
        "start": ts["start"],
        "end": to_utc_iso(clock_dt),
        "timezoneName": "Europe/Berlin",
        "timezone": tz_offset_str(clock_dt),
    }
    put_url = f"{BASE_URL}/timespans/{ts['_id']}"
    print(f"[调试] PUT {put_url}")
    print(f"[调试] payload: {json.dumps(update_payload)}")
    resp = requests.put(
        put_url,
        data=json.dumps(update_payload),
        auth=auth,
        headers={"Content-Type": "application/json"},
    )
    print(f"[调试] 响应 {resp.status_code}: {resp.text[:1000]}")
    if not resp.ok:
        print(f"[错误] 下班打卡失败 {resp.status_code}: {resp.text[:500]}")
    resp.raise_for_status()
    print(f"[✓] 下班打卡成功: {clock_dt.strftime('%Y-%m-%d %H:%M')} (Berlin)")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("checkin", "checkout"):
        print("用法: python absence_clock.py [checkin|checkout]")
        sys.exit(1)

    if is_skip_today():
        sys.exit(0)

    auth = get_auth()
    user_id = get_user_id()

    if sys.argv[1] == "checkin":
        checkin(auth, user_id)
    else:
        checkout(auth, user_id)


if __name__ == "__main__":
    main()
