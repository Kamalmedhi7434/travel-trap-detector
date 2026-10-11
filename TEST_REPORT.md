# Test & Verification Report

**Environment: Windows 11 | Python 3.12 | Chrome & Edge Desktop**

- **Backend Unit Tests:** All 12 unit tests passed (`tests/test_app.py`).
- **Interactive Workflows:** Successfully verified quote analysis, saving traveller reports, evidence attachment viewing, SQLite data persistence across restarts, and backup export/import.
- **UI & Responsiveness:** Verified on mobile (320px, 390px) and desktop (1280px) viewports with zero horizontal overflow.
- **Offline Functionality:** Verified complete offline workflow with Wi-Fi disconnected — local ML inference, SQLite storage, and Service Worker caching operate seamlessly on localhost.
- **Batch Launchers:** Tested both `start.bat` and `train.bat` on Windows; environment creation, dependency installation, and local serving execute without issues.
- **Security & Integrity:** Input sanitization, local request header checks, and strict file validation verified.
- **Pre-trained Models:** All four models (`fare.joblib`, `risk.joblib`, `anomaly.joblib`, `text.joblib`) load and predict properly.
