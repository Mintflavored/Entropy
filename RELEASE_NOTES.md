# Entropy v0.33.0 Release Notes

### 🎨 UI/UX Redesign
- **PySide6/QML Migration**: Complete interface overhaul from PyQt6 to modern QML engine.
- **Premium Design**: Monochrome icons, smooth animations, smart margins across all views.
- **App Branding**: Logo added to window icon, navigation dock, and Dashboard header.
- **Enhanced Dashboard**: Charts now display current value (colored), min/avg/max stats, and time period indicator.
- **Localized Subtitles**: Card subtitles and chart labels fully translated (RU/EN).

### 🤖 AI Module
- **EAII Settings UI**: Interval slider, autostart toggle, and periodic analysis timer.
- **VPN-Aware Prompt**: EAII now understands VPN context — doesn't flag normal VPN traffic as threat.
- **Signal Stability**: Fixed PyQt6→PySide6 signal chain for reliable EAII→UI communication.
- **Logic Separation**: EAII (background monitoring) and Interactive AI (deep SSH diagnostics) work independently.

### 📊 Security Engine
- **Mathematical Risk Calculation**: Improved security index formula with weighted factors for PPS, Jitter, and brute-force attempts.
- **Real-time Metrics**: Enhanced entropy-based risk scoring with dynamic thresholds.

### 🛠️ Technical Changes
- Resolved all Qt 6 warnings by switching to Fusion style.
- Updated CI/CD pipelines for PySide6 architecture.
- Optimized project structure (removed legacy PyQt6 code).

---
*Generated automatically for the Entropy system*
