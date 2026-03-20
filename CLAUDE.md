# absence-clock

自动通过 absence.io API v2 完成工作日上下班打卡的工具。

## 项目概述

本项目解决的问题：每天手动在 absence.io 上打卡麻烦，通过自动化脚本按时完成打卡，支持跳过节假日，无需人工干预。

**两种运行方式：**
- **GitHub Actions（推荐）**：运行在 GitHub 服务器，无需本机开机
- **macOS launchd**：本地定时任务，需要 Mac 开机并登录

## 文件结构

```
absence_clock.py                     # 核心打卡脚本（Python）
manage.sh                            # macOS 本地管理命令
skip_dates.txt                       # 节假日/不打卡日期列表（YYYY-MM-DD，每行一个）
requirements.txt                     # Python 依赖：requests, requests-hawk, python-dotenv
.env.example                         # 配置模板
.env                                 # 本地配置（不提交 Git）
.github/workflows/absence_clock.yml # GitHub Actions 工作流
launchagents/                        # macOS launchd plist 模板
```

## 核心逻辑

### absence_clock.py

- **认证**：使用 HAWK 认证（`requests-hawk`），从环境变量读取 `ABSENCE_API_ID` / `ABSENCE_API_KEY`
- **userId**：与 `ABSENCE_API_ID` 相同（absence.io 的设计）
- **时区**：统一使用 `Europe/Berlin`，API 请求转换为 UTC ISO 格式
- **跳过逻辑**：启动时先检查 `skip_dates.txt`，命中则直接退出
- **checkin**：调用 `POST /api/v2/timespans/create`，`end` 为 `null`
- **checkout**：先查询今天未关闭的记录，再调用 `PUT /api/v2/timespans/{id}` 填入结束时间
- **412 处理**：收到 412 表示已有未关闭记录（重复触发），静默跳过

### manage.sh

封装常用操作，适用于 macOS launchd 方式：

| 命令 | 说明 |
|------|------|
| `./manage.sh start` | 生成 plist 并加载定时任务 |
| `./manage.sh stop` | 卸载定时任务 |
| `./manage.sh status` | 查看任务是否激活 |
| `./manage.sh checkin` | 立即手动打上班卡 |
| `./manage.sh checkout` | 立即手动打下班卡 |
| `./manage.sh set-time` | 从 `.env` 更新打卡时间并重写 plist |
| `./manage.sh skip YYYY-MM-DD` | 追加不打卡日期到 `skip_dates.txt` |
| `./manage.sh log` | 查看最近打卡日志 |

## 环境变量（.env）

```
ABSENCE_API_ID=your_key_id
ABSENCE_API_KEY=your_key_secret
CHECKIN_TIME=08:30
CHECKOUT_TIME=17:30
```

## 开发注意事项

### 依赖安装

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 手动测试

```bash
python absence_clock.py checkin
python absence_clock.py checkout
```

### GitHub Actions 时区说明

cron 表达式使用 UTC，Berlin 时间需要换算：

- 夏令时（CEST，UTC+2）：`08:30 Berlin` → `06:30 UTC`
- 冬令时（CET，UTC+1）：`08:30 Berlin` → `07:30 UTC`

两条 cron 同时保留，脚本靠 412 响应自动去重。

### skip_dates.txt 格式

每行一个 `YYYY-MM-DD` 日期，`#` 开头为注释：

```
# 2026 年节假日
2026-01-01
2026-04-03
2026-12-25
```

### API 端点

- 创建打卡：`POST https://app.absence.io/api/v2/timespans/create`
- 查询打卡：`POST https://app.absence.io/api/v2/timespans`
- 更新打卡：`PUT https://app.absence.io/api/v2/timespans/{id}`
