# Multimodal Attendance & Engagement Agent

An offline-first intelligent classroom analysis system combining computer vision for face presence tracking, acoustic speech activity detection, and transparent rule-based signal fusion.

---

## 🚀 Key Features

- **Presence-Based Attendance:** Tracks cumulative visible presence duration and generates proposals for instructor review.
- **Audio Signal Analysis:** Extracts RMS energy, zero-crossing rate (ZCR), spectral centroid, and background noise level.
- **Multimodal Signal Fusion:** Aligns video and audio signals across synchronized time windows into an experimental 0–100 heuristic index.
- **Pedagogical Insights:** Context-aware teaching suggestions for room illumination, microphone placement, and discussion pacing.
- **Privacy First & Offline:** Runs 100% locally on CPU without external cloud APIs or biometric transmissions.
- **Interactive Dashboard:** Modern dark navy Streamlit dashboard with Plotly charts and certified CSV exports.

---

## 🛠️ Tech Stack

- **Language:** Python 3.11 – 3.14
- **Computer Vision:** OpenCV, MediaPipe
- **Audio Processing:** Librosa, SoundFile, SciPy, NumPy
- **Backend & Database:** FastAPI, Uvicorn, SQLite, SQLAlchemy
- **Frontend:** Streamlit, Plotly, Pandas
- **Testing:** Pytest (23 unit & integration tests)

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Demo Samples & Seed Database (Optional)
```bash
python generate_samples.py
python seed_demo_data.py
```

### 3. Launch Dashboard
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Launch FastAPI Server (Optional)
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 5. Run Automated Tests
```bash
pytest tests/ -v
```

---

## 📂 Project Structure

```text
├── app.py                      # Main Streamlit web application
├── run_servers.py              # Runner script for API & dashboard
├── generate_samples.py         # Synthetic sample video & audio generator
├── seed_demo_data.py           # Demo database seeder
├── backend/                    # FastAPI REST API endpoints
├── core/                       # Vision, Audio, Agent, and Analytics modules
├── database/                   # SQLite database models & repository
├── frontend/                   # UI components and dark navy styling
├── tests/                      # Automated Pytest suite (23 passing tests)
├── docs/                       # Architecture & College Project Report
└── data/                       # Local database, cascades, and sample media
```

---

## 🔒 Ethical & Privacy Notice

- **No Cloud Transmission:** All audio and video streams are processed strictly on local hardware.
- **Human Authority:** Facial presence is treated as circumstantial evidence; final attendance confirmation rests with the educator.
- **Experimental Heuristic:** The engagement score is an experimental physical activity indicator, not a validated measurement of cognitive attention or emotion.
