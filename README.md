# 🛡️ Entropy (v0.30.0)

![Entropy Logo](./assets/logo.png)

[**Русский**](#russian) | [**English**](#english)

---

<a name="russian"></a>
## 🇷🇺 Описание проекта

**Entropy** — это высокотехнологичное Desktop-приложение для мониторинга и интеллектуальной диагностики VPN-инфраструктуры. Проект ориентирован на обеспечение максимальной скрытности трафика и стабильности серверов в условиях жесткой интернет-цензуры.

### ✨ Ключевые функции

#### 📊 Реальный Мониторинг и Аналитика (v0.30.0)
- **Real-time Dashboard**: Визуализация нагрузки CPU и RAM, а также отслеживание трафика пользователей.
- **Full View Graphs**: Оптимизированные графики с историей до 100 точек (~16 мин), сеткой и реальными временными метками.
- **True Network Metrics**: Прямое чтение PPS из `/proc/net/dev` и расчет Jitter через микро-пинги со стороны сервера.
- **Risk Index**: Умный алгоритм оценки вероятности блокировки на основе волатильности трафика.

#### 🧠 Искусственный Интеллект (AI Bridge)
- **Advanced Model Support**: Интеграция с **OpenAI (GPT-5.2)**, **Claude 4.5**, **Google Gemini** и **OpenRouter**.
- **Autonomous Diagnostics**: Функция Tool Calling позволяет ИИ самостоятельно выполнять SSH-команды для анализа логов и конфигураций (Xray, Marzban, Sing-box).
- **Configurable Limits**: Пользователь может ограничивать количество SSH-запросов ИИ для контроля безопасности и затрат токенов.
- **Context Awareness**: Модель получает полные ТТХ сервера (CPU, OS, RAM) для выдачи точных рекомендаций.

#### 🛠️ Системные Возможности
- **Live Probing Detection**: Анализ `/var/log/auth.log` для выявления реальных попыток брутфорса и сканирования.
- **SSH Auto-Discovery**: Автоматическое определение установленных VPN-панелей и характеристик железа.
- **Persistent Config**: Управление всеми настройками через GUI с сохранением в `config.json`.

---

### 📝 Changelog (История изменений)

- **v0.30.0 (Текущая)**: 
    - Переход на **реальные данные** (PPS, Jitter, Logs). Удаление симуляции.
    - Оптимизация графиков "Full View" (100 точек, Real-time X-Axis).
    - Синхронизация по SSH/SFTP с поддержкой новых типов VPN-панелей.
- **v0.28.0**: Ребрендинг в **Entropy**, новый логотип, стабильный `ConfigManager`.
- **v0.25.0**: Рефакторинг на модульную архитектуру, поддержка нескольких ИИ-провайдеров.
- **v0.20.0**: Внедрение AI Tool Calling — ИИ получил доступ к SSH-диагностике.
- **v0.15.0**: Первый модуль безопасности и графики PPS/Jitter.

---

<a name="english"></a>
## 🇺🇸 Project Overview

**Entropy** is a high-tech Desktop application for monitoring and intelligent diagnostics of VPN infrastructure. The project is focused on ensuring maximum traffic stealth and server stability under strict internet censorship conditions.

### ✨ Key Features

#### 📊 Real Monitoring & Analytics (v0.30.0)
- **Real-time Dashboard**: CPU and RAM load visualization, real-time user traffic tracking.
- **Full View Graphs**: Optimized charts with up to 100 history points (~16 min), grids, and real-time timestamps.
- **True Network Metrics**: Direct PPS reading from `/proc/net/dev` and Jitter calculation via server-side micro-pings.
- **Risk Index**: Smart algorithm for assessing blocking probability based on traffic volatility.

#### 🧠 Artificial Intelligence (AI Bridge)
- **Advanced Model Support**: Integration with **OpenAI (GPT-5.2)**, **Claude 4.5**, **Google Gemini**, and **OpenRouter**.
- **Autonomous Diagnostics**: Tool Calling feature allows the AI to independently execute SSH commands to analyze logs and configurations (Xray, Marzban, Sing-box).
- **Configurable Limits**: Users can set a cap on AI SSH requests for budget control and security oversight.
- **Context Awareness**: The model receives full server specifications (CPU, OS, RAM) to provide precise recommendations.

#### 🛠️ System Capabilities
- **Live Probing Detection**: Parsing `/var/log/auth.log` to identify real brute-force and scanning attempts.
- **SSH Auto-Discovery**: Automatic detection of installed VPN panels and hardware specifications.
- **Persistent Config**: Management of all settings via GUI with saving to `config.json`.

---

### 📝 Changelog (History)

- **v0.30.0 (Current)**: 
    - Transition to **real-time data** (PPS, Jitter, Logs). Removed all simulations.
    - "Full View" graph optimization (100 points, Real-time X-Axis).
    - SSH/SFTP synchronization with support for new VPN panel types.
- **v0.28.0**: Rebranded to **Entropy**, new logo, stable `ConfigManager`.
- **v0.25.0**: Full modular refactoring, multi-LLM provider support.
- **v0.20.0**: Introduction of AI Tool Calling — AI gained SSH diagnostic access.
- **v0.15.0**: Initial Security Module and PPS/Jitter charts.

---

### 🚀 Installation & Usage

1. **Clone repository:**
   ```bash
   git clone https://github.com/bossv/entropy.git
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run:**
   ```bash
   python main.py
   ```

---
*Developed with ❤️ for Digital Freedom.*
