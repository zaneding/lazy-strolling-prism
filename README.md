# absence-clock

自动 absence.io 打卡 · Auto clock-in/out for absence.io · Automatisches Stempeln für absence.io

[中文](#-中文) | [English](#-english) | [Deutsch](#-deutsch)

---

## 🇨🇳 中文

通过 absence.io API v2 在工作日自动完成上下班打卡。

**支持两种运行方式：**
- ☁️ **GitHub Actions**（推荐）：运行在 GitHub 服务器上，**不依赖电脑是否开机**
- 🖥️ **macOS launchd**：本地定时任务，需要电脑开机且已登录

### ⚙️ 初始配置

**1. 获取 API Key**

登录 absence.io → 头像 → Einstellungen → API Schlüssel → 生成新密钥，复制 Key ID 和 Key Secret。

**2. 方式一：GitHub Actions（推荐）**

进入仓库页面 → Settings → Secrets and variables → Actions → New repository secret，添加：

| Secret 名称 | 说明 |
|------------|------|
| `ABSENCE_API_ID` | API Key ID |
| `ABSENCE_API_KEY` | API Key Secret |

推送代码后自动生效，无需其他操作。

**3. 方式二：macOS launchd**

```bash
git clone https://github.com/zaneding/lazy-strolling-prism.git
cd lazy-strolling-prism

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# 用文本编辑器打开 .env，填入 API 凭证和打卡时间
./manage.sh start
```

### 🕐 自定义打卡时间

**GitHub Actions：**

编辑 `.github/workflows/absence_clock.yml` 中的 cron 表达式（使用 UTC 时间）：

```
# 上班 08:30 Berlin → 夏令时 06:30 UTC，冬令时 07:30 UTC
- cron: '30 6 * * 1-5'   # 夏令时
- cron: '30 7 * * 1-5'   # 冬令时
```

> 两条 cron 都保留，脚本会自动跳过重复触发（412 响应）。

**macOS launchd：**

在 `.env` 中修改打卡时间，然后执行 `set-time` 重新加载：

```bash
# 编辑 .env
CHECKIN_TIME=08:30
CHECKOUT_TIME=17:30

# 重新加载配置
./manage.sh set-time
./manage.sh stop && ./manage.sh start
```

### 📅 设置不打卡日期

在 `skip_dates.txt` 中每行写一个日期，当天不会自动打卡：

```
# 示例
2026-12-25
2026-01-01
2026-04-03
```

或使用命令快捷添加：

```bash
./manage.sh skip 2026-12-25
```

### 🔧 日常管理（macOS launchd）

```bash
./manage.sh start               # 启用自动打卡
./manage.sh stop                # 暂停自动打卡
./manage.sh status              # 查看定时任务是否激活
./manage.sh checkin             # 立即手动打上班卡
./manage.sh checkout            # 立即手动打下班卡
./manage.sh set-time            # 从 .env 重新加载打卡时间
./manage.sh skip 2026-12-25     # 添加不打卡日期
./manage.sh log                 # 查看最近打卡日志
```

### 📁 文件结构

```
.
├── absence_clock.py                     # 核心打卡脚本
├── manage.sh                            # 本地管理脚本
├── skip_dates.txt                       # 不打卡日期列表
├── requirements.txt                     # Python 依赖
├── .env.example                         # 配置模板
├── .env                                 # 本地配置（不提交 Git）
├── .github/workflows/absence_clock.yml # GitHub Actions 工作流
└── launchagents/                        # macOS 定时任务配置
```

---

## 🇬🇧 English

Automatically clock in and out on absence.io via API v2 on weekdays.

**Two ways to run:**
- ☁️ **GitHub Actions** (recommended): runs on GitHub's servers — **works even when your computer is off**
- 🖥️ **macOS launchd**: local scheduled task — requires your Mac to be on and logged in

### ⚙️ Initial Setup

**1. Get your API Key**

Log in to absence.io → profile avatar → Einstellungen → API Schlüssel → generate a new key. Copy the Key ID and Key Secret.

**2. Option A: GitHub Actions (recommended)**

Go to your repository → Settings → Secrets and variables → Actions → New repository secret, and add:

| Secret name | Description |
|------------|-------------|
| `ABSENCE_API_ID` | Your API Key ID |
| `ABSENCE_API_KEY` | Your API Key Secret |

GitHub Actions activates automatically once the code is pushed — nothing else needed.

**3. Option B: macOS launchd**

```bash
git clone https://github.com/zaneding/lazy-strolling-prism.git
cd lazy-strolling-prism

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Open .env and fill in your API credentials and clock times
./manage.sh start
```

### 🕐 Customize Clock Times

**GitHub Actions:**

Edit the cron expressions in `.github/workflows/absence_clock.yml` (times in UTC):

```
# Check-in at 08:30 Berlin → 06:30 UTC (summer), 07:30 UTC (winter)
- cron: '30 6 * * 1-5'   # summer (CEST, UTC+2)
- cron: '30 7 * * 1-5'   # winter (CET, UTC+1)
```

> Keep both cron lines — the script automatically skips duplicate triggers (412 response).

**macOS launchd:**

Edit `.env` with your desired times, then reload:

```bash
# In .env
CHECKIN_TIME=08:30
CHECKOUT_TIME=17:30

# Reload
./manage.sh set-time
./manage.sh stop && ./manage.sh start
```

### 📅 Add Skip Dates

Add dates to `skip_dates.txt` (one per line) — no clocking will happen on those days:

```
# Examples
2026-12-25
2026-01-01
2026-04-03
```

Or use the shortcut command:

```bash
./manage.sh skip 2026-12-25
```

### 🔧 Day-to-Day Management (macOS launchd)

```bash
./manage.sh start               # Enable automatic clocking
./manage.sh stop                # Disable automatic clocking
./manage.sh status              # Check if tasks are active
./manage.sh checkin             # Clock in manually right now
./manage.sh checkout            # Clock out manually right now
./manage.sh set-time            # Reload clock times from .env
./manage.sh skip 2026-12-25     # Add a skip date
./manage.sh log                 # View recent clock logs
```

### 📁 File Structure

```
.
├── absence_clock.py                     # Core clocking script
├── manage.sh                            # Local management script
├── skip_dates.txt                       # Dates to skip
├── requirements.txt                     # Python dependencies
├── .env.example                         # Config template
├── .env                                 # Local config (not committed to Git)
├── .github/workflows/absence_clock.yml # GitHub Actions workflow
└── launchagents/                        # macOS scheduled task configs
```

---

## 🇩🇪 Deutsch

Automatisches Ein- und Ausstempeln auf absence.io über die API v2 an Wochentagen.

**Zwei Betriebsmöglichkeiten:**
- ☁️ **GitHub Actions** (empfohlen): läuft auf GitHub-Servern — **funktioniert auch wenn dein Computer ausgeschaltet ist**
- 🖥️ **macOS launchd**: lokale geplante Aufgabe — erfordert, dass dein Mac eingeschaltet und angemeldet ist

### ⚙️ Ersteinrichtung

**1. API-Schlüssel holen**

Bei absence.io anmelden → Profilbild → Einstellungen → API Schlüssel → neuen Schlüssel generieren. Key ID und Key Secret kopieren.

**2. Option A: GitHub Actions (empfohlen)**

Zum Repository → Settings → Secrets and variables → Actions → New repository secret, folgendes hinzufügen:

| Secret-Name | Beschreibung |
|------------|--------------|
| `ABSENCE_API_ID` | Deine API Key ID |
| `ABSENCE_API_KEY` | Dein API Key Secret |

GitHub Actions wird automatisch aktiv, sobald der Code gepusht ist — kein weiterer Schritt nötig.

**3. Option B: macOS launchd**

```bash
git clone https://github.com/zaneding/lazy-strolling-prism.git
cd lazy-strolling-prism

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env mit API-Zugangsdaten und Stempelzeiten bearbeiten
./manage.sh start
```

### 🕐 Stempelzeiten anpassen

**GitHub Actions:**

Die Cron-Ausdrücke in `.github/workflows/absence_clock.yml` bearbeiten (Angabe in UTC):

```
# Einstempeln 08:30 Berlin → 06:30 UTC (Sommer), 07:30 UTC (Winter)
- cron: '30 6 * * 1-5'   # Sommerzeit (CEST, UTC+2)
- cron: '30 7 * * 1-5'   # Winterzeit (CET, UTC+1)
```

> Beide Cron-Zeilen behalten — das Skript überspringt doppelte Ausführungen automatisch (412-Antwort).

**macOS launchd:**

In `.env` die gewünschten Zeiten eintragen und neu laden:

```bash
# In .env
CHECKIN_TIME=08:30
CHECKOUT_TIME=17:30

# Neu laden
./manage.sh set-time
./manage.sh stop && ./manage.sh start
```

### 📅 Ausnahmetage festlegen

Daten in `skip_dates.txt` eintragen (ein Datum pro Zeile) — an diesen Tagen wird nicht gestempelt:

```
# Beispiele
2026-12-25
2026-01-01
2026-04-03
```

Oder schnell per Befehl hinzufügen:

```bash
./manage.sh skip 2026-12-25
```

### 🔧 Alltagsverwaltung (macOS launchd)

```bash
./manage.sh start               # Automatisches Stempeln aktivieren
./manage.sh stop                # Automatisches Stempeln deaktivieren
./manage.sh status              # Status der geplanten Aufgaben prüfen
./manage.sh checkin             # Jetzt manuell einstempeln
./manage.sh checkout            # Jetzt manuell ausstempeln
./manage.sh set-time            # Stempelzeiten aus .env neu laden
./manage.sh skip 2026-12-25     # Ausnahmedatum hinzufügen
./manage.sh log                 # Aktuelle Stempel-Logs anzeigen
```

### 📁 Dateistruktur

```
.
├── absence_clock.py                     # Kern-Stempelskript
├── manage.sh                            # Lokales Verwaltungsskript
├── skip_dates.txt                       # Liste der Ausnahmetage
├── requirements.txt                     # Python-Abhängigkeiten
├── .env.example                         # Konfigurationsvorlage
├── .env                                 # Lokale Konfiguration (nicht in Git)
├── .github/workflows/absence_clock.yml # GitHub Actions Workflow
└── launchagents/                        # macOS geplante Aufgaben
```
