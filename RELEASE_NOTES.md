### 🚀 New Features
- **CI/CD Finalization**: Release process is now fully automated via GitHub Actions.
- **Unit Testing**: Core logic verification is integrated into the build pipeline.

### 🐞 Bug Fixes
- **Build System**: Added `Pillow` dependency to handle automatic `.png` to `.ico` conversion for the Windows executable icon.
- **Workflow Stability**: Resolved the "correct format" icon error in PyInstaller.

### 🚀 New Features
- **CI/CD Finalization**: Release process is now fully automated via GitHub Actions.

### 🐞 Bug Fixes
- Fixed `ModuleNotFoundError` during CI execution by correctly setting `PYTHONPATH`.
- Resolved dependency resolution issues in the automated runner.

### 🛠️ Technical Changes
- Upgraded Python environment to **3.14.2** for GitHub Actions workflows.
- Optimized `.gitignore` to handle test caches and binary artifacts.

---
*Generated automatically for the Entropy system*
