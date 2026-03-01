# Entropy v0.42.5 — Hotfix Release

### � Bug Fix
- **Config Persistence**: Fixed a critical bug where all user settings (VPS connection, AI keys, language, etc.) were reset to defaults after every restart of the installed `.exe`.
  - **Root Cause**: `ConfigManager` used a relative path `config.json`, which in PyInstaller frozen mode resolved to a volatile temporary directory (`_MEI*`) that is recreated on each launch.
  - **Fix**: Config and local database are now stored in `%APPDATA%/Entropy/` — a persistent, user-writable location.

---
*Hotfix for [v0.42.4](https://github.com/Mintflavored/Entropy/releases/tag/v0.42.4)*
