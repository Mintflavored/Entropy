# 🛡️ Entropy (v0.43.2)

[![Version](https://img.shields.io/badge/version-0.43.2-blue.svg)](https://github.com/Mintflavored/Entropy/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

![Entropy Logo](./assets/logo.png)

[**English**](#english) | [**Русский**](#russian)

---

<a name="english"></a>
## 🇺🇸 Project Overview

**Entropy** is a high-tech Desktop application for monitoring and intelligent diagnostics of VPN infrastructure. The project is focused on ensuring maximum traffic stealth and server stability under strict internet censorship conditions.

### ✨ Key Features

#### 📊 Real Monitoring & Analytics
- **Real-time Dashboard**: CPU and RAM load visualization, real-time user traffic tracking.
- **Full View Graphs**: Charts with up to 100 history points (~16 min) and real-time timestamps.
- **True Network Metrics**: Direct PPS reading from `/proc/net/dev` and Jitter calculation via micro-pings.
- **Risk Index**: Smart algorithm for assessing blocking probability based on traffic volatility.

#### 🧠 Artificial Intelligence (AI Bridge)
- **EAII (Entropy AI Index)**: Autonomous monitoring with periodic analysis and response capabilities.
- **Multi-Provider Support**: Integration with **OpenAI**, **Claude**, **Google Gemini**, and **OpenRouter**.
- **Autonomous Diagnostics**: AI independently executes SSH commands to analyze logs and configs.
- 🌐 **Multi-language**: Full support for Russian and English languages.
- **Configurable Limits**: Control over AI SSH request count for security and token budgeting.

#### 🛠️ System Capabilities
- **EAII Settings UI**: Interface for configuring EAII parameters (interval, autostart, etc.).
- **Live Probing Detection**: Parsing `/var/log/auth.log` to identify brute-force attempts.
- **SSH Auto-Discovery**: Automatic detection of VPN panels and server hardware specs.
- **Persistent Config**: All settings saved to `config.json`.

---

### 🚀 Installation & Setup

#### Step 1: VPS Setup (Server-side)

The dashboard requires a monitoring script installed on your VPS:

```bash
# 1. Create folder and copy the monitoring script
mkdir -p /root/monitoring
# Upload monitor.py from scripts/server/ to /root/monitoring/

# 2. Install dependencies
apt update && apt install python3-pip -y
pip3 install psutil

# 3. Configure auto-start via Systemd
# Copy entropy-monitor.service from scripts/server/ to /etc/systemd/system/
systemctl daemon-reload
systemctl enable entropy-monitor
systemctl start entropy-monitor
```

#### Step 2: Run Desktop Application (Client)

```bash
# 1. Clone repository
git clone https://github.com/Mintflavored/entropy.git
cd entropy

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure connection
# Copy .env.example to .env and fill in your VPS SSH credentials

# 4. Run the application
python main.py
```

> **Pre-built .exe**: You can also download the bundled executable from the [Releases](https://github.com/Mintflavored/Entropy/releases) section. The archive includes a `server/` folder with ready-to-use monitoring scripts for your VPS.

---

### 📝 Changelog

| Version | Changes |
|---------|---------|
| **v0.42.0** | **Creation and implementation of the module EAIS (Entropy Artificial Intelligence Sandbox)**: Introduced the Entropy Artificial Intelligence Sandbox (EAIS) for autonomous VPN configuration testing. Features parallel processing, batch config dispatching, Fast-Fail checks, dynamic payload generation, and deep TCP/kernel tuning (BBR pacing, notsent_lowat). |
| **v0.33.0** | **UI/UX Redesign**: Complete interface overhaul with modern design and improved usability. |
| **v0.32.0** | **EAII (Entropy Artificial Intelligence Index)**: Autonomous monitoring with the ability to periodically analyze and respond. |
| **v0.31.0** | **Multi-language Support**: Added full Russian and English interface localization. |
| **v0.30.0** | Transition to real-time data (PPS, Jitter, Logs). Removed simulations. Graph optimization. |
| **v0.28.0** | Rebranded to **Entropy**, new logo, stable `ConfigManager`. |
| **v0.25.0** | Modular architecture, multi-LLM provider support. |
| **v0.20.0** | AI Tool Calling — AI gained SSH diagnostic access. |
| **v0.15.0** | SSH Terminal integration and basic VPS monitoring. |
| **v0.10.0** | Initial prototype: GUI for network stats and basic configuration. |
| **v0.1.0**  | Project initialization. |

---

<a name="russian"></a>
## 🇷🇺 Описание проекта

**Entropy** — это высокотехнологичное Desktop-приложение для мониторинга и интеллектуальной диагностики VPN-инфраструктуры. Проект ориентирован на обеспечение максимальной скрытности трафика и стабильности серверов в условиях жесткой интернет-цензуры.

### ✨ Ключевые функции

#### 📊 Реальный Мониторинг и Аналитика
- **Real-time Dashboard**: Визуализация нагрузки CPU и RAM, отслеживание трафика пользователей.
- **Full View Graphs**: Графики с историей до 100 точек (~16 мин) и реальными временными метками.
- **True Network Metrics**: Прямое чтение PPS из `/proc/net/dev` и расчет Jitter через микро-пинги.
- **Risk Index**: Умный алгоритм оценки вероятности блокировки на основе волатильности трафика.

#### 🧠 Искусственный Интеллект (AI Bridge)
- **EAII (Entropy AI Index)**: Автономный мониторинг с возможностью периодического анализа и реагирования.
- **Multi-Provider Support**: Интеграция с **OpenAI**, **Claude**, **Google Gemini** и **OpenRouter**.
- **Autonomous Diagnostics**: ИИ самостоятельно выполняет SSH-команды для анализа логов и конфигов.
- 🌐 **Multi-language**: Полная поддержка русского и английского языков.
- **Configurable Limits**: Контроль количества SSH-запросов ИИ для безопасности и экономии токенов.

#### 🛠️ Системные Возможности
- **EAII Settings UI**: Интерфейс для настройки параметров EAII (интервал, автозапуск и т. д.).
- **Live Probing Detection**: Анализ `/var/log/auth.log` для выявления брутфорс-атак.
- **SSH Auto-Discovery**: Автоматическое определение VPN-панелей и характеристик сервера.
- **Persistent Config**: Все настройки сохраняются в `config.json`.

---

### 🚀 Установка и Запуск

#### Шаг 1: Настройка VPS (Серверная часть)

Для работы дашборда необходимо установить скрипт мониторинга на ваш VPS:

```bash
# 1. Создайте папку и скопируйте скрипт мониторинга
mkdir -p /root/monitoring
# Загрузите monitor.py из scripts/server/ в /root/monitoring/

# 2. Установите зависимости
apt update && apt install python3-pip -y
pip3 install psutil

# 3. Настройте автозапуск через Systemd
# Скопируйте entropy-monitor.service из scripts/server/ в /etc/systemd/system/
systemctl daemon-reload
systemctl enable entropy-monitor
systemctl start entropy-monitor
```

#### Шаг 2: Запуск Desktop-приложения (Клиент)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/Mintflavored/entropy.git
cd entropy

# 2. Установите зависимости Python
pip install -r requirements.txt

# 3. Настройте подключение
# Скопируйте .env.example в .env и заполните SSH-данные вашего VPS

# 4. Запустите приложение
python main.py
```

> **Готовый .exe**: Вы также можете скачать собранный исполняемый файл из раздела [Releases](https://github.com/Mintflavored/Entropy/releases). Архив уже содержит папку `server/` с готовыми скриптами для VPS.

---

### 📝 История изменений (Changelog)

| Версия | Изменения |
|--------|-----------|
| **v0.42.0** | **Создание и внедрение модуля EAIS (Entropy Artificial Intelligence Sandbox)**: Автономная ИИ-песочница для подбора VPN-конфигураций. Внедрено распараллеливание запросов, Batch-применение SSH конфигов, Fast-Fail пинги и умное изменение размеров тестов на слабых каналах. Открыт доступ к параметрам ядра TCP. |
| **v0.33.0** | **UI/UX Redesign**: Полный редизайн интерфейса с современным дизайном и улучшенной юзабилити. |
| **v0.32.0** | **EAII (Entropy Artificial Intelligence Index)**: Автономный мониторинг с возможностью периодического анализа и реагирования. |
| **v0.31.0** | **Многоязычная поддержка**: Добавлена полная локализация на русский и английский языки. |
| **v0.30.0** | Переход на реальные данные (PPS, Jitter, Logs). Удаление симуляции. Оптимизация графиков. |
| **v0.28.0** | Ребрендинг в **Entropy**, новый логотип, стабильный `ConfigManager`. |
| **v0.25.0** | Модульная архитектура, поддержка нескольких ИИ-провайдеров. |
| **v0.20.0** | AI Tool Calling — ИИ получил доступ к SSH-диагностике. |
| **v0.15.0** | Интеграция SSH-терминала и базовый мониторинг VPS. |
| **v0.10.0** | Первоначальный прототип: GUI для сетевой статистики и базовая конфигурация. |
| **v0.1.0** | Инициализация проекта. |

---

*Developed with ❤️ for Digital Freedom.*
