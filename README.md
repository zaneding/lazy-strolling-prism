# absence-clock

通过 absence.io API v2 在周一至周五 08:00 / 17:00 自动完成上下班打卡。

**支持两种运行方式：**
- ☁️ **GitHub Actions**（推荐）：运行在 GitHub 服务器上，**不依赖电脑是否开机**
- 🖥️ **macOS launchd**：本地定时任务，需要电脑开机且已登录

---

## ☁️ 方式一：GitHub Actions（推荐）

即使电脑关机，GitHub 服务器也会按时自动打卡。

### 配置步骤

**1. 在 GitHub 仓库添加 Secrets**

进入仓库页面 → Settings → Secrets and variables → Actions → New repository secret，添加：

| Secret 名称 | 值 |
|------------|---|
| `ABSENCE_API_ID` | 你的 API Key ID |
| `ABSENCE_API_KEY` | 你的 API Key Secret |

> **如何获取 API Key**：登录 absence.io → 头像 → Einstellungen → API Schlüssel → 生成新密钥

**2. 推送代码即自动启用**

只要仓库中存在 `.github/workflows/absence_clock.yml`，GitHub Actions 就会按计划自动运行。

**3. 手动触发测试**

仓库页面 → Actions → absence.io 自动打卡 → Run workflow → 选择 checkin 或 checkout

### 运行时间（自动适配夏令时）

| 操作 | Berlin 时间 | UTC 时间 |
|------|------------|---------|
| 上班打卡 | 08:00 | 06:00（夏）/ 07:00（冬）|
| 下班打卡 | 17:00 | 15:00（夏）/ 16:00（冬）|

> 夏令时（CEST/UTC+2）和冬令时（CET/UTC+1）均已覆盖，重复触发时脚本自动跳过。

---

## 🖥️ 方式二：macOS launchd（本地）

> **注意**：电脑关机或休眠时任务会被跳过，不会补跑。

### 配置步骤

**1. 克隆并安装依赖**

```bash
git clone https://github.com/zaneding/lazy-strolling-prism.git
cd lazy-strolling-prism

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. 配置凭证**

```bash
cp .env.example .env
# 编辑 .env，填入 ABSENCE_API_ID 和 ABSENCE_API_KEY
```

**3. 加载定时任务**

```bash
cp launchagents/com.absence.checkin.plist ~/Library/LaunchAgents/
cp launchagents/com.absence.checkout.plist ~/Library/LaunchAgents/

./manage.sh start
```

### 日常管理

```bash
./manage.sh start      # 启用自动打卡
./manage.sh stop       # 暂停自动打卡
./manage.sh status     # 查看定时任务是否激活
./manage.sh checkin    # 立即手动打上班卡
./manage.sh checkout   # 立即手动打下班卡
./manage.sh log        # 查看最近打卡日志
```

---

## 文件结构

```
.
├── absence_clock.py                        # 核心打卡脚本
├── manage.sh                               # 本地管理脚本
├── requirements.txt                        # Python 依赖
├── .env.example                            # 凭证模板
├── .env                                    # 凭证配置（不提交到 Git）
├── .github/
│   └── workflows/
│       └── absence_clock.yml               # GitHub Actions 自动打卡
└── launchagents/
    ├── com.absence.checkin.plist           # macOS 上班定时任务
    └── com.absence.checkout.plist         # macOS 下班定时任务
```

## API 说明

使用 [absence.io API v2](https://app.absence.io/api-docs)，认证方式为 Hawk SHA256。

- 上班：`POST /api/v2/timespans/create`
- 查询今日记录：`POST /api/v2/timespans`
- 下班：`PUT /api/v2/timespans/{id}`
