### 🐞 Bug Fixes
- **GitHub Permissions**: Added explicit `contents: write` permissions to the workflow to allow automatic release creation (Fixes 403 Forbidden).
- **Build System**: Added `Pillow` dependency for automatic icon conversion.
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
