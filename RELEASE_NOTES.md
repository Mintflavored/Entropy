### 🚀 New Features
- **CI/CD Automation**: Integrated GitHub Actions for automated building and cross-platform releases.
- **Unit Testing**: Implemented a testing suite for core modules (`ConfigManager`, `LocalizationManager`).
- **Release Template**: Added support for `RELEASE_NOTES.md` to streamline the release documentation process.

### 🐞 Bug Fixes
- Fixed `ModuleNotFoundError` during CI execution by correctly setting `PYTHONPATH`.
- Resolved dependency resolution issues in the automated runner.

### 🛠️ Technical Changes
- Upgraded Python environment to **3.14.2** for GitHub Actions workflows.
- Optimized `.gitignore` to handle test caches and binary artifacts.

---
*Generated automatically for the Entropy system*
