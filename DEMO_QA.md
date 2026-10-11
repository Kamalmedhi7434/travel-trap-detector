# Frequently Asked Questions & Architecture

**Where are the ML models located?**
The app runs four offline scikit-learn models located in the `models/` directory, managed via `ml.py` and trained via `train.py`:
- **Ridge Regression (`fare.joblib`):** Estimates reasonable baseline travel fares based on city, service type, distance, and day/night factors.
- **Random Forest (`risk.joblib`):** Classifies overall caution levels (Fair, Suspicious, High Risk).
- **Isolation Forest (`anomaly.joblib`):** Detects pricing anomalies and unusual quote ratios.
- **TF-IDF + Logistic Regression (`text.joblib`):** Categorizes report notes into issue patterns (hidden charges, pressure, detour, positive).

**How does the fair price benchmark work?**
The Ridge regression model provides an initial learned baseline range. When users log local paid fares in the Reports tab, the system blends them (70% local report median + 30% ML baseline prediction) once there are at least 3 matching records.

**How does the app function without internet?**
After the first-time package installation, everything runs 100% locally on your computer. The Flask backend is served by Waitress at `http://127.0.0.1:5000`, data is stored in a local SQLite file (`data/travel.db`), and the frontend uses Service Worker caching.

**How is user privacy and data handled?**
All reports, past checks, and uploaded receipt images are stored exclusively on your local machine in SQLite. No data is sent to external servers or cloud APIs. Users can export their local database to a JSON backup or wipe their data anytime.

**How is application security maintained?**
Inputs and file uploads are strictly validated and sanitized (MIME checks, file size limits up to 5 MB, parameter-bound SQL queries). Mutating API routes enforce local origin headers to guard against cross-site requests.

**What tools were used during development?**
Developed and tested on Windows with Python (Flask, scikit-learn, NumPy, SciPy, joblib) and a vanilla JavaScript PWA frontend. AI assisted in error resolution, boosting productivity, and streamlining development, alongside manual testing and Playwright browser tests.
