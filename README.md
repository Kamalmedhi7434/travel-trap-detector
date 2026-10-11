# Travel Trap Detector

**An offline travel fraud and price anomaly detector built with Python, Flask, SQLite, and scikit-learn.**

Travel Trap Detector runs entirely locally on your Windows PC. It lets travellers verify travel and transit quotes, estimate fair pricing ranges, detect suspicious price markups or tourist traps, attach evidence/receipts, and spot local fare anomalies without relying on any external APIs or cloud services.

> **Note on Training Data:** The models train and predict locally. Initial baseline models are trained on realistic synthetic travel datasets to demonstrate the offline ML pipeline. All prediction boundaries and metrics are documented below.

---

## 1. Quick Start on Windows

### Prerequisites
- Windows 10 or 11
- Python 3.10, 3.11, 3.12, or 3.13 (Tested on Windows 11 with Python 3.12)
- Modern web browser (Chrome or Edge)
- Internet connection is only required once during the initial setup to install dependencies. After that, everything runs 100% offline.

### Running the App
1. Clone or extract this repository to a folder on your Windows PC.
2. Double-click **`start.bat`**.
   - On the first run, it automatically creates an isolated virtual environment (`.venv`) and installs the dependencies from `requirements.txt`.
   - It then launches the local server using Waitress.
3. Open your browser and go to:
   ```text
   http://127.0.0.1:5000
   ```
4. Keep the command prompt window open while using the app. Press `Ctrl + C` or close the window when you want to stop the server.

### Running Manually via Command Prompt
```cmd
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

### Retraining Models Locally
The project comes with pre-trained models in `models/`. If you want to retrain the models from scratch:
1. Stop the running app (`Ctrl + C`).
2. Double-click **`train.bat`** (or run `.venv\Scripts\python.exe train.py`).
3. The script will generate training data, fit all 4 machine learning models, print evaluation metrics, and save new `.joblib` files.
4. Restart `start.bat`.

---

## 2. Architecture Overview

```text
Browser (Vanilla HTML5 / CSS3 / JavaScript PWA)
                     |
                     | Local HTTP requests (127.0.0.1:5000)
                     v
      Flask Backend (served by Waitress)
             |                      |
             v                      v
      SQLite Database          scikit-learn ML Pipeline (ml.py)
      (data/travel.db)         - Ridge (Fare estimation)
      - User reports           - Random Forest (Risk score)
      - Checked quotes         - Isolation Forest (Price anomaly)
      - File evidence          - TF-IDF + Logistic Reg (Text classifier)
```

- **Frontend:** Lightweight, responsive single-page PWA built with semantic HTML5, clean CSS, and modern vanilla JavaScript. No heavy frontend frameworks, no CDN dependencies, and zero tracking scripts.
- **Backend:** Flask web server running on Waitress WSGI. Handles input validation, local database operations, and machine learning inference.
- **Database:** Single local SQLite database (`data/travel.db`) created automatically on first launch.
- **Offline / Local First:** Everything runs on `127.0.0.1`. No data leaves your machine.

---

## 3. Features & User Guide

### 1. Fare & Risk Check
Select a city, service type (auto rickshaw, taxi, airport cab, tour guide, boat ride, hotel room), enter the quantity (km, hours, or nights), and quoted price. You can also toggle common red flags like unclear extras, payment pressure, route detours, or missing receipts.
- **Fair / Suspicious / High Risk Verdict:** Predicted by our Random Forest classifier.
- **Fair Price Band:** Estimated typical rupee range based on distance/service rates.
- **Caution Index:** Numerical risk score (0–100) reflecting model confidence.
- **Reason Breakdown:** Clear bullet points detailing whether the quote is inflated, flags selected, or similar local complaints exist.

### 2. Local Price Benchmarking
When travellers submit verified paid fares under **Reports**, the system calculates a trimmed median for that specific city and service. When at least 3 local reports are available, the app automatically blends the community median with the model estimate (**70% local median + 30% model prediction**).

### 3. Tourist Trap Educational Guide
The **Explore** tab includes a built-in catalog of common tourist traps (unmetered rides, commission shop detours, aggressive payment pressure, destination switches, and unpriced menus) with practical tips on how to handle each situation.

### 4. Community Reports & File Evidence
Travellers can log an experience as a fair fare, complaint, or review:
- Attach receipts, photos, or documents (PNG, JPG, WebP, PDF up to 5 MB) stored directly in SQLite.
- Built-in text analysis categorizes complaint notes and highlights key trigger keywords.
- View and download uploaded evidence directly from the browser.

### 5. Location Insights & Anomaly Detection
Filter by city and transit type to view local report summaries, complaint clusters, and price anomalies detected by the Isolation Forest model.

### 6. Data Privacy & Backup
- **Export Data:** Download all saved reports and evidence attachments as a single JSON backup.
- **Import Data:** Restore previously exported records with duplicate prevention.
- **Erase Data:** One-click reset to delete all local history and evidence from SQLite.

---

## 4. The 4 Machine Learning Models

| Model | Algorithm | File | Role |
|---|---|---|---|
| **Fare Estimator** | Ridge Regression | `models/fare.joblib` | Predicts expected price based on city, service type, distance/duration, and day/night rates. |
| **Risk Classifier** | Random Forest (90 trees) | `models/risk.joblib` | Classifies quotes into Fair, Suspicious, or High Risk based on price ratio, red flag inputs, and local complaints. |
| **Price Anomaly** | Isolation Forest (100 trees) | `models/anomaly.joblib` | Unsupervised anomaly detector that identifies unusual price deviations independent of classification rules. |
| **Text Classifier** | TF-IDF + Logistic Regression | `models/text.joblib` | Classifies complaint descriptions into categories (hidden charges, pressure, detour, positive) and extracts key influential terms. |

---

## 5. Model Evaluation & Metrics

The baseline models were trained using deterministic random seed 42. Metrics on held-out test splits:

| Metric | Result | Notes |
|---|---:|---|
| **Fare MAE** | ₹211.28 | Mean absolute error across diverse service types and scales. |
| **Fare 90th Percentile Relative Error** | 16.53% | Error on held-out synthetic test instances. |
| **Risk Classifier Accuracy** | 99.77% | High alignment with multi-factor risk scoring rules. |
| **Text Classifier Accuracy** | 37.50% | Small baseline sample (40 sentences). The app handles low-confidence text gracefully by marking it as *unclear*. |

---

## 6. Demo Walkthrough / Quick Test Scenarios

Try these quick presets in the app to test different behaviors:

1. **Fair Scenario ("A fair city ride"):**
   - Click the preset button: Guwahati, 5 km auto, ₹140 quoted.
   - Result: Returns a **Fair** verdict with a normal price band and low caution index.
2. **Suspicious Scenario ("A quote worth questioning"):**
   - Click the preset button: Jaipur, 12 km taxi, ₹420 with "Unclear extras" checked.
   - Result: Returns a **Suspicious** verdict, highlighting the markup and warning flags.
3. **High-Risk Scenario ("Pressure + a huge markup"):**
   - Click the preset button: Goa, 4-hour guide, ₹3,500 with high pressure and detour flags.
   - Result: Returns a **High Risk** verdict with elevated caution score.
4. **Community Learning Test:**
   - Under Reports, submit 3 paid fares for Guwahati Auto (5 km) at ₹180, ₹185, and ₹190.
   - Re-check a ₹200 quote: The result updates to display a blended benchmark combining ML prediction and local traveller records.
5. **Offline Mode Test:**
   - Disconnect Wi-Fi on your PC while keeping the server running.
   - Run a price check and submit a report with an image. Everything runs locally without connection drops.

---

## 7. Project File Structure

```text
travel-trap-detector/
├── app.py                 # Flask application routes, validation, and SQLite storage
├── ml.py                  # Model loading and inference helper functions
├── train.py               # Dataset generation and training script for all 4 models
├── start.bat              # One-click Windows setup and launch script
├── train.bat              # One-click Windows model training script
├── index.html             # Single-page interface with 5 tab views
├── style.css              # Custom styling, dark/light theme accents, responsive layout
├── app.js                 # Frontend application logic, API calls, state management
├── data.js                # City references, base costs, and educational trap cards
├── sw.js                  # Service Worker for local static caching
├── manifest.webmanifest   # PWA manifest
├── requirements.txt       # Core Python dependencies
├── requirements-lock.txt  # Pinned dependency versions
├── CITATIONS.md           # Third-party library citations and licenses
├── QUICK_START.md         # Brief setup reference
├── TEST_REPORT.md         # Test verification summary
├── data/                  # Training datasets and SQLite database location
├── icons/                 # PWA shield icons and app logos
├── models/                # Trained .joblib model files and metrics.json
├── tests/
│   ├── test_app.py        # Python backend unit tests (12 tests)
│   └── ui.spec.js         # Playwright end-to-end browser tests
└── THIRD_PARTY_LICENSES/  # License texts for bundled dependencies
```

---

## 8. API Endpoints

All mutating requests require the custom header `X-Travel-App: local` to prevent unauthorized cross-origin requests.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/state` | Returns saved reports, recent checks, model metrics, and area anomaly counts |
| `POST` | `/api/analyze` | Evaluates quote, runs ML models, applies local benchmarks, saves check |
| `POST` | `/api/reports` | Saves a new traveller report and optional evidence file to SQLite |
| `DELETE` | `/api/reports/<id>` | Deletes a report and associated evidence attachment |
| `DELETE` | `/api/checks/<id>` | Deletes an individual check from history |
| `GET` | `/api/evidence/<id>` | Serves stored evidence image or triggers PDF download |
| `GET` | `/api/export` | Exports all reports and evidence into a single JSON backup |
| `POST` | `/api/import` | Validates and imports a JSON backup file |
| `DELETE` | `/api/data` | Clears all stored user records from the local database |

---

## 9. Verification & Testing

### Running Backend Unit Tests
```cmd
.venv\Scripts\python.exe -m unittest discover -s tests -v
```
All **12 tests** run against an isolated temporary SQLite database and verify:
- Model loading and prediction logic
- All three risk categories (Fair, Suspicious, High Risk)
- Input validation and boundary handling
- Benchmark calculation and report blending
- Isolation Forest anomaly detection
- Backup export and all-or-nothing import validation
- Local origin header security checks
- Evidence file integrity and deletion

### Platform Verification
Tested and verified on **Windows 11** with **Python 3.12**, running on **Google Chrome** and **Microsoft Edge**. Both batch launch scripts (`start.bat` and `train.bat`) execute cleanly.

---

## 10. References & Acknowledgments

All open-source dependencies, licenses, and references are detailed in [CITATIONS.md](CITATIONS.md).
