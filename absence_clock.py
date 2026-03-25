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
import mohawk
from dotenv import load_dotenv

# ── 配置 ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
SKIP_DATES_FILE = BASE_DIR / "skip_dates.txt"
BASE_URL = "https://app.absence.io/api/v2"
TZ_BERLIN = ZoneInfo("Europe/Berlin")

load_dotenv(ENV_FILE)


def load_skip_dates():
    """读取 skip_dates.txt，返回日期字符串集合（YYYY-MM-DD）"""
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
    """检查今天是否在跳过日期列表中"""
    today = datetime.now(TZ_BERLIN).strftime("%Y-%m-%d")
    skip_dates = load_skip_dates()
    if today in skip_dates:
        print(f"[跳过] {today} 已在 skip_dates.txt 中，不打卡")
        return True
    return False


def get_credentials():
    api_id = os.environ.get("ABSENCE_API_ID", "").strip()
    api_key = os.environ.get("ABSENCE_API_KEY", "").strip()
    if not api_id or not api_key:
        print("[错误] 缺少 ABSENCE_API_ID 或 ABSENCE_API_KEY，请检查 .env")
        sys.exit(1)
    return {"id": api_id, "key": api_key, "algorithm": "sha256"}


def hawk_request(method, url, credentials, payload=None):
    """用 mohawk 直接构造 Hawk Authorization header 并发送请求"""
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    content_type = "application/json" if payload is not None else ""
    sender = mohawk.Sender(
        credentials,
        url,
        method,
        content=body,
        content_type=content_type,
    )
    headers = {"Authorization": sender.request_header}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    resp = requests.request(method, url, data=body, headers=headers)
    if resp.status_code == 401:
        print(f"[调试] 401 响应头: {dict(resp.headers)}")
        print(f"[调试] Authorization: {sender.request_header[:120]}...")
    return resp


def get_user_id():
    """userId = API Key ID（absence.io 的设计）"""
    user_id = os.environ.get("ABSENCE_API_ID", "").strip()
    if not user_id:
        print("[错误] 缺少 ABSENCE_API_ID")
        sys.exit(1)
    return user_id


def now_berlin():
    return datetime.now(TZ_BERLIN)


def to_utc_iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def tz_offset_str(dt):
    """返回 '+0100' 或 '+0200' 格式的时区偏移"""
    offset_seconds = int(dt.utcoffset().total_seconds())
    sign = "+" if offset_seconds >= 0 else "-"
    h, m = divmod(abs(offset_seconds) // 60, 60)
    return f"{sign}{h:02d}{m:02d}"


def api_post(credentials, path, payload_fn, retries=2):
    """
    payload_fn: 无参可调用，每次调用返回最新 payload dict（确保时间戳实时）
    每次重试都重新生成 Hawk header（新 timestamp + nonce）
    """
    url = f"{BASE_URL}/{path}"
    for attempt in range(1, retries + 1):
        payload = payload_fn() if callable(payload_fn) else payload_fn
        resp = hawk_request("POST", url, credentials, payload)
        if resp.status_code != 401 or attempt == retries:
            return resp
        print(f"[重试] 第 {attempt} 次请求返回 401，响应: {resp.text[:200]}，5秒后重试…")
        time.sleep(5)
    return resp


def checkin(credentials, user_id):
    last_now = [None]

    def make_payload():
        now = now_berlin()
        last_now[0] = now
        return {
            "userId": user_id,
            "start": to_utc_iso(now),
            "end": None,
            "timezoneName": "Europe/Berlin",
            "timezone": tz_offset_str(now),
            "type": "work",
        }

    resp = api_post(credentials, "timespans/create", make_payload)
    now = last_now[0] or now_berlin()

    if resp.status_code == 412:
        print(f"[!] 已有未关闭的打卡记录，跳过重复打卡（{now.strftime('%Y-%m-%d %H:%M')} Berlin）")
        return

    if not resp.ok:
        print(f"[错误] 状态码 {resp.status_code}，响应: {resp.text[:500]}")
    resp.raise_for_status()
    print(f"[✓] 上班打卡成功: {now.strftime('%Y-%m-%d %H:%M')} (Berlin)")


def checkout(credentials, user_id):
    now = now_berlin()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 查找今天未关闭的打卡
    resp = api_post(credentials, "timespans", {
        "filter": {
            "userId": user_id,
            "start": {"$gte": to_utc_iso(today_start)},
            "end": None,
        },
        "limit": 5,
        "skip": 0,
    })
    if not resp.ok:
        print(f"[错误] 查询打卡记录失败，状态码 {resp.status_code}，响应: {resp.text[:500]}")
    resp.raise_for_status()
    timespans = resp.json().get("data", [])

    if not timespans:
        print(f"[!] 未找到今天未关闭的打卡记录（{now.strftime('%Y-%m-%d %H:%M')} Berlin）")
        sys.exit(0)

    ts = timespans[0]
    update_payload = {
        "start": ts["start"],
        "end": to_utc_iso(now),
        "timezoneName": "Europe/Berlin",
        "timezone": tz_offset_str(now),
    }
    resp = hawk_request("PUT", f"{BASE_URL}/timespans/{ts['_id']}", credentials, update_payload)
    if not resp.ok:
        print(f"[错误] 下班打卡失败，状态码 {resp.status_code}，响应: {resp.text[:500]}")
    resp.raise_for_status()
    print(f"[✓] 下班打卡成功: {now.strftime('%Y-%m-%d %H:%M')} (Berlin)")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("checkin", "checkout"):
        print("用法: python absence_clock.py [checkin|checkout]")
        sys.exit(1)

    # 检查今天是否是跳过日期
    if is_skip_today():
        sys.exit(0)

    credentials = get_credentials()
    user_id = credentials["id"]

    if sys.argv[1] == "checkin":
        checkin(credentials, user_id)
    else:
        checkout(credentials, user_id)


if __name__ == "__main__":
    main()
