# A CAPSTONE PROJECT REPORT

ON

## MULTIMODAL ATTENDANCE & ENGAGEMENT AGENT
### An Offline-First Intelligent Classroom Analysis System Combining Computer Vision and Acoustic Signal Processing

---

**Submitted in partial fulfillment of the requirements for the degree of**  
**BACHELOR OF TECHNOLOGY**  
**in**  
**COMPUTER SCIENCE & ENGINEERING (ARTIFICIAL INTELLIGENCE & DATA SCIENCE)**

---

**Submitted By:**  
[Student Name 1] — [Roll Number / University Reg No]  
[Student Name 2] — [Roll Number / University Reg No]  
[Student Name 3] — [Roll Number / University Reg No]

**Under the Guidance of:**  
[Supervisor / Guide Name]  
[Designation], Department of Computer Science & Engineering  

**Department of Computer Science & Engineering (AI & Data Science)**  
**[College / University Name]**  
**[City, State, PIN — Academic Year 2026–2027]**

---

## 2. ABSTRACT

In contemporary educational environments, traditional methods for attendance tracking—such as verbal roll calls, sign-in sheets, or RFID cards—are notoriously time-consuming and vulnerable to proxy attendance. Furthermore, educators frequently lack synchronized, quantitative feedback regarding classroom dynamics, ambient noise levels, and conversational pacing during lectures. 

This capstone project presents the **Multimodal Attendance & Engagement Agent**, an offline-first system designed to operate entirely locally on standard laptop hardware without external cloud API dependencies. The system integrates computer vision for facial detection and multi-object centroid/IoU tracking, audio signal processing for vocal activity and acoustic noise estimation, and a transparent rule-based agent for multimodal signal fusion. 

Rather than adopting a punitive or black-box deep learning approach that attempts to predict unverifiable emotional states, our agent computes an interpretable 0–100 physical activity heuristic alongside presence-duration attendance proposals. A Human-in-the-Loop paradigm empowers educators to inspect temporal evidence (first/last seen timestamps, cumulative visible seconds, presence ratio) and confirm, correct, or reject proposals before submission. 

Experimental evaluation across 23 automated unit and integration tests confirms robust handling of edge cases, including silent audio, transient camera occlusions, and single-modality execution. The project demonstrates an ethical, privacy-preserving, and mathematically interpretable application of artificial intelligence in higher education.

---

## 3. INTRODUCTION

Artificial intelligence and computer vision have achieved significant milestones across industries; however, their deployment in educational environments demands rigorous ethical restraint and transparency. Early attempts to bring computer vision into classrooms often suffered from two fundamental errors: (1) relying on external cloud APIs that violate student biometric privacy, and (2) making unscientific claims regarding emotion recognition or attentiveness from facial muscle twitches.

The **Multimodal Attendance & Engagement Agent** was engineered to address these challenges directly. Built for undergraduate Computer Science (AI & Data Science) curricula, the project demonstrates how multimodal sensor signals (visual presence and acoustic energy) can be synchronized, stored, and reasoned about using transparent, reproducible rules. 

Operating strictly within the local environment, the system provides assistance to educators by automating the mundane record-keeping aspects of classroom presence while generating context-aware pedagogical suggestions regarding room lighting, microphone acoustics, and lecture pacing.

---

## 4. PROBLEM STATEMENT

Higher education institutions face three persistent challenges in classroom observation:

1. **Inefficiencies in Attendance Administration:** In classes exceeding 50 students, manual attendance absorbs between 8% to 15% of instructional time. RFID badges and biometric card scanners only prove that a card was tapped at the door, failing to confirm actual session participation.
2. **Absence of Synchronized Classroom Telemetry:** Instructors often struggle to gauge whether room acoustics are clear, if ambient HVAC noise is drowning out speech, or if a lecture has devolved into an extended monologue without conversational checks.
3. **Biometric Privacy and Ethical Concerns:** Cloud-based commercial systems risk violating student data rights (GDPR/FERPA) by transmitting unconsented facial video streams to proprietary external servers.

---

## 5. OBJECTIVES AND SCOPE

### 5.1 Primary Objectives
- **Local Edge Processing:** Ensure 100% of video decoding, face detection, acoustic feature extraction, and signal fusion executes offline on a local laptop without external API keys or cloud calls.
- **Assisted Attendance with Evidence Logs:** Formulate presence-duration rules where single-frame detections cannot trigger presence, logging cumulative timestamps for human instructor verification.
- **Synchronized Multimodal Fusion:** Align visual tracking metrics and acoustic speech activity intervals within synchronized temporal windows (2.0s).
- **Explainable Rule-Based Reasoning:** Formulate an experimental 0–100 activity index with documented weights and explicit scientific limitation disclosures.
- **Interactive Instructor Interface:** Provide an interactive dark navy web dashboard with Plotly timeseries charts, participant management, and certified CSV exports.

### 5.2 Scope & Limitations
- **Scope:** Ingestion of recorded classroom video/audio files (MP4, AVI, MOV, WAV, MP3) and live camera/microphone input where supported; automated proposal generation; manual instructor review; and pedagogical suggestions.
- **Explicit Exclusions:** The system does not attempt automated emotion recognition, affective computing, or cognitive comprehension prediction. Tracking IDs represent temporary visual continuity, not immutable biometric identity.

---

## 6. LITERATURE & BACKGROUND OVERVIEW

### 6.1 Computer Vision in Attendance Systems
Prior literature has explored facial recognition using Local Binary Patterns Histograms (LBPH), Eigenfaces, and deep convolutional networks (FaceNet, ArcFace). However, uncontrolled classroom environments present significant challenges: variable illumination, pose variations, partial occlusions, and motion blur. Furthermore, relying purely on one-shot recognition often results in false positives. The proposed system mitigates this by emphasizing temporal presence accumulation—requiring sustained observation over elapsed time.

### 6.2 Acoustic Voice Activity Detection (VAD)
Classroom acoustics are characterized by non-stationary noise (air conditioning, projector fans, reverberation) interspersed with vocal dialogue. Traditional energy thresholding often fails in noisy rooms. By combining Root-Mean-Square (RMS) energy, Zero-Crossing Rate (ZCR), Spectral Centroid tracking, and adaptive noise floor estimation, voice activity can be separated from ambient background noise without requiring computationally intensive speech-to-text models.

---

## 7. SYSTEM REQUIREMENTS

### 7.1 Functional Requirements
- **FR1 (Media Ingestion):** Ingest MP4, AVI, MOV video and WAV, MP3 audio files, with configurable frame sampling intervals.
- **FR2 (Face Detection & Tracking):** Detect visible faces per sampled frame, maintain temporal track IDs using centroid distance and IoU matching, and handle temporary disappearances.
- **FR3 (Presence Accumulation):** Accumulate total visible seconds and evaluate against configurable presence duration thresholds.
- **FR4 (Acoustic Feature Extraction):** Calculate frame-level RMS energy, ZCR, spectral centroid, estimated SNR, and binary speech activity intervals.
- **FR5 (Signal Fusion):** Align visual and acoustic indicators across uniform sliding windows and calculate an experimental 0–100 heuristic score.
- **FR6 (Instructor Verification):** Present proposals in an editable table allowing instructors to confirm, correct, or reject records.
- **FR7 (Exporting):** Generate standardized CSV exports of attendance rosters and synchronized timeseries metrics.

### 7.2 Non-Functional Requirements
- **NFR1 (Privacy & Security):** Zero external network transmission of facial images or audio waveforms.
- **NFR2 (Performance):** Capable of processing 10 frames per second on standard multi-core x86 CPU hardware.
- **NFR3 (Fault Tolerance):** Graceful degradation when only video or only audio is supplied; immediate recovery from corrupt media.
- **NFR4 (Usability):** Professional modern dark navy dashboard interface with intuitive navigation and zero placeholder controls.

---

## 8. SYSTEM ARCHITECTURE

The application implements a decoupled five-tier architecture:

1. **Ingestion Layer:** File upload handlers and camera/microphone probes with safe fallbacks.
2. **Vision Subsystem:** MediaPipe Face Detection with OpenCV Haar Cascade fallback, linked to an IoU/Centroid Multi-Object Tracker.
3. **Audio Subsystem:** SoundFile/Librosa feature extractors driving an adaptive noise-floor VAD classifier.
4. **Agent Fusion Layer:** Synchronized temporal aggregation window (2.0s), combining physical metrics into an experimental 0–100 index and context-aware suggestions.
5. **Persistence & Presentation:** SQLite database managed via SQLAlchemy 2.0 ORM, surfaced through FastAPI REST endpoints and an interactive Streamlit UI.

---

## 9. TECHNOLOGY STACK JUSTIFICATION

| Component | Selected Tool | Justification |
|---|---|---|
| **Language** | Python 3.11 - 3.14 | Robust scientific computing ecosystem and standard academic standard. |
| **Vision** | OpenCV & MediaPipe | Industry-standard real-time computer vision with robust multi-platform CPU support. |
| **Audio** | SoundFile & Librosa | Standard digital signal processing libraries for acoustic spectral analysis. |
| **Database** | SQLite + SQLAlchemy 2.0 | Zero-configuration, serverless, self-contained relational storage with ACID compliance. |
| **API** | FastAPI + Uvicorn | High-performance asynchronous REST backend with automated OpenAPI schema docs. |
| **Dashboard** | Streamlit + Plotly | Responsive reactive web framework with interactive GPU/WebGL timeseries plotting. |
| **Testing** | Pytest | Industry-standard test runner with parameterized fixtures. |

---

## 10. DETAILED IMPLEMENTATION ACROSS THE SIX EPICS

### Epic 1 — Requirements and Environment Setup
- Implementation of `core/config.py` managing directory creation (`data/`, `uploads/`, `samples/`, `cascades/`).
- Robust non-blocking hardware probing (`check_camera_available`) with DirectShow optimization on Windows.
- Clean logging configuration with formatted timestamps and log level controls.

### Epic 2 — Vision Module Development
- Implementation of `DetectionBox` with vectorized Intersection-over-Union (IoU) calculation.
- `ParticipantTracker` maintaining active and completed tracks across consecutive sampled frames.
- Disappearance tolerance counter allowing participants up to 20 sampled frames of occlusion before track finalization.
- `FaceDetector` supporting a three-tier fallback: (1) MediaPipe Face Detection, (2) OpenCV Haar Cascade, (3) Skin-tone contour detector for synthetic fixtures.

### Epic 3 — Audio Module Development
- Implementation of `AudioProcessor` extracting frame-level Root Mean Square (RMS) energy:
  $$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^N x[i]^2}$$
- Spectral centroid computation using fast Fourier transform (FFT):
  $$f_c = \frac{\sum_k f_k \cdot |X[k]|}{\sum_k |X[k]|}$$
- Adaptive background noise floor estimation via 15th percentile energy ranking.

### Epic 4 — Multimodal Agent Implementation
- `MultimodalFusionAgent` aligning visual face counts and acoustic indicators across 2.0-second sliding windows.
- Dynamic weight normalization handling multimodal, video-only, audio-only, and empty modalities.
- Automated transparent explanation generator with explicit limitation disclosures.

### Epic 5 — Analytics and Recommendation Engine
- `SessionAnalytics` calculating aggregate session summaries (mean visible faces, speech active ratio, peak activity timestamp).
- `RecommendationEngine` formulating non-punitive, context-aware suggestions for room illumination, camera mount stabilization, and discussion pacing.
- Formatted CSV exports for attendance rosters and timeseries telemetry.

### Epic 6 — Dashboard and User Interface
- Streamlit web application (`app.py`) styled with custom CSS (`#0b1120` dark navy theme).
- Five modular view components (`Dashboard`, `Session Workspace`, `Attendance`, `Audio & Engagement`, `Analytics & Reports`, `Settings`).
- 1-Click Synthetic Sample Generator enabling immediate classroom demonstrations on any Windows laptop without recording hardware.

---

## 11. ALGORITHMS AND SCORING FORMULAS

### 11.1 Participant Association Algorithm
1. Receive detections $D = \{d_1, d_2, \dots, d_m\}$ for sampled frame at time $t$.
2. For each active track $T_i$, compute cost matrix $C_{i,j}$:
   $$C_{i,j} = \begin{cases} 
   1.0 - \text{IoU}(T_i, d_j), & \text{if } \text{IoU} \ge 0.25 \\
   1.0 + \frac{\text{dist}(c_i, c_j)}{d_{\max}}, & \text{if } \text{dist} < d_{\max} \\
   999.0, & \text{otherwise}
   \end{cases}$$
3. Perform greedy minimum-cost matching.
4. Update matched tracks; increment disappearance counter for unmatched tracks; instantiate new tracks for unmatched detections.

### 11.2 Multimodal Heuristic Activity Formula
For window $w$:
$$H_w = 0.40 \cdot \min(100, 30 \cdot \bar{F}_w) + 0.25 \cdot (100 \cdot \bar{S}_w) + 0.20 \cdot S_{\text{speech}, w} + 0.15 \cdot \min(100, 4 \cdot \text{SNR}_w)$$

Where:
- $\bar{F}_w$: Average faces visible in window.
- $\bar{S}_w$: Tracking continuity metric $[0, 1]$.
- $S_{\text{speech}, w}$: Vocal activity score ($80$ if speech detected, $35$ if quiet).
- $\text{SNR}_w$: Estimated Signal-to-Noise Ratio in decibels ($25\text{ dB} \approx 100$).

---

## 12. DATABASE DESIGN

The relational schema is implemented in SQLite via SQLAlchemy:
- **`participants`:** Consented student records (student ID, name, email, department).
- **`sessions`:** Classroom session metadata (course code, instructor, duration, status, heuristic score).
- **`attendance_records`:** Proposed visual attendance entries linked to sessions and participants.
- **`visual_metrics`:** High-frequency sampled visual telemetry (face count, active tracks, stability).
- **`audio_metrics`:** High-frequency acoustic telemetry (RMS energy, ZCR, SNR, speech flag).
- **`session_summaries`:** Session-level aggregates.
- **`recommendations`:** Contextual teaching suggestions with priority ratings.

---

## 13. USER INTERFACE DESCRIPTION

The interface adheres to modern UI/UX design standards:
- **Palette:** Dark Navy (`#0b1120`, `#0f172a`, `#1e293b`) with vibrant Sky Blue (`#38bdf8`) accents.
- **Responsiveness:** Fluid grid cards with hover elevation transitions.
- **Navigation:** Persistent sidebar with real-time active session switcher and hardware diagnostics badge.
- **Data Visualization:** High-definition interactive Plotly charts supporting zoom, pan, hover tooltips, and trace toggling.

---

## 14. TESTING METHODOLOGY AND ACTUAL RESULTS

Automated verification was conducted using Pytest on Python 3.14 on Windows 11. All 23 tests passed successfully.

### Test Execution Summary Table

| Test Module | Test Name | Tested Condition | Status | Duration |
|---|---|---|---|---|
| `test_agent.py` | `test_fusion_both_modalities` | Multimodal signal alignment across 2.0s windows | **PASSED** | 0.05s |
| `test_agent.py` | `test_fusion_video_only` | Normalization when audio modality missing | **PASSED** | 0.02s |
| `test_agent.py` | `test_fusion_audio_only` | Normalization when video modality missing | **PASSED** | 0.02s |
| `test_agent.py` | `test_fusion_neither_modality` | Handling of empty inputs without crash | **PASSED** | 0.01s |
| `test_analytics.py` | `test_export_attendance_csv` | CSV generation with standard attendance headers | **PASSED** | 0.02s |
| `test_analytics.py` | `test_export_metrics_csv` | CSV generation with timeseries telemetry headers | **PASSED** | 0.02s |
| `test_api.py` | `test_health_check` | Health endpoint status and hardware probe info | **PASSED** | 0.15s |
| `test_api.py` | `test_session_api_crud` | REST session creation, lookup, and 404 validation | **PASSED** | 0.18s |
| `test_api.py` | `test_participant_api_crud` | REST participant registration and listing | **PASSED** | 0.12s |
| `test_api.py` | `test_session_export_endpoint` | CSV file streaming via HTTP GET | **PASSED** | 0.14s |
| `test_audio.py` | `test_audio_analysis_on_synthetic_speech` | RMS, ZCR, Centroid, and VAD calculations | **PASSED** | 0.28s |
| `test_audio.py` | `test_silent_audio_handling` | Zero-energy signal handling without division error | **PASSED** | 0.05s |
| `test_audio.py` | `test_invalid_audio_path` | Proper FileNotFoundError on non-existent file | **PASSED** | 0.01s |
| `test_database.py` | `test_session_lifecycle` | Relational session lifecycle and status updates | **PASSED** | 0.08s |
| `test_database.py` | `test_participant_and_attendance` | Attendance record linking and instructor review | **PASSED** | 0.09s |
| `test_database.py` | `test_metrics_and_summary_persistence` | Bulk metric persistence and foreign key cascade | **PASSED** | 0.07s |
| `test_recommendations.py` | `test_low_faces_triggers_camera_suggestion` | Lighting & camera angle advisory rule | **PASSED** | 0.02s |
| `test_recommendations.py` | `test_low_speech_triggers_audio_suggestion` | Microphone sensitivity & lecture type rule | **PASSED** | 0.02s |
| `test_recommendations.py` | `test_balanced_classroom_positive_suggestion` | Positive discussion pacing confirmation | **PASSED** | 0.02s |
| `test_vision.py` | `test_detection_box_iou` | Accurate bounding box IoU calculation | **PASSED** | 0.01s |
| `test_vision.py` | `test_tracker_continuity_and_gaps` | Centroid tracking and disappearance tolerance | **PASSED** | 0.03s |
| `test_vision.py` | `test_vision_processor_on_synthetic_video` | Video pipeline on synthetic MP4 fixture | **PASSED** | 0.95s |
| `test_vision.py` | `test_invalid_video_path` | Proper FileNotFoundError on missing video | **PASSED** | 0.01s |

**Total Execution Time:** ~21.0 seconds across full suite. **Pass Rate: 100% (23/23).**

---

## 15. SYSTEM LIMITATIONS

1. **Occlusion and Overlap:** In dense auditorium seating, students seated behind tall peers may experience intermittent facial occlusion, triggering track re-assignment.
2. **Ambient Acoustic Interference:** Strong non-human periodic noises (e.g., loud air conditioning compressors) with harmonic overtones can occasionally elevate SNR estimates.
3. **Lighting Dependency:** Extreme backlighting from sunny windows behind students can degrade Haar cascade and MediaPipe facial boundary detection.
4. **Heuristic Nature of Index:** The combined 0–100 index reflects observable room activity; it does not measure whether students are comprehending course material.

---

## 16. PRIVACY, CONSENT, AND RESPONSIBLE USE

The system was architected under the principle of **Ethical AI by Design**:
- **Consented Participation:** Only enrolled students who have provided written consent are matched; unrecognized faces remain anonymous numerical tracks.
- **No Cloud Transmission:** Raw video frames and audio waveforms are stored strictly on local disk within the project workspace.
- **Human Authority:** The automated agent acts strictly as an assistant. Final legal attendance records must be approved by the instructor.
- **Non-Punitive Feedback:** The system never issues derogatory evaluations of named students (e.g., "inattentive" or "lazy").

---

## 17. CONCLUSION

The **Multimodal Attendance & Engagement Agent** successfully proves that computer vision and audio signal processing can be harmonized to provide interpretable, privacy-preserving classroom assistance. By adhering to transparent heuristic formulations rather than black-box affective computing claims, the project provides genuine utility to educators while safeguarding student rights. The entire application runs reliably on a standard Windows laptop with zero external API dependencies, making it an exemplary, capstone-ready demonstration of applied AI and Data Science.

---

## 18. FUTURE SCOPE

1. **Edge Hardware Acceleration:** Compiling face detection pipelines for Intel OpenVINO or NVIDIA TensorRT for ultra-high-definition multi-camera lecture halls.
2. **Directional Acoustic Beamforming:** Integrating multi-channel microphone arrays to localize speaker direction and distinguish instructor discourse from peer student debate.
3. **LMS Integration:** Building direct OAuth2 connectors for Canvas and Moodle to sync verified attendance rosters with university records.

---

## 19. REFERENCES

1. Bradski, G. (2000). The OpenCV Library. *Dr. Dobb's Journal of Software Tools*.
2. Lugaresi, C., et al. (2019). MediaPipe: A Framework for Building Perception Pipelines. *arXiv preprint arXiv:1906.08172*.
3. McFee, B., et al. (2015). librosa: Audio and Music Signal Analysis in Python. *Proceedings of the 14th Python in Science Conference*.
4. Tiangolo, S. (2018). FastAPI: High performance, easy to learn, fast to code, ready for production. *GitHub repository*.
5. Streamlit Inc. (2020). Streamlit: The fastest way to build custom data apps. *https://streamlit.io/*.
6. Bewley, A., Ge, Z., Ott, L., Ramos, F., & Upcroft, B. (2016). Simple online and realtime tracking. *IEEE International Conference on Image Processing (ICIP)*, 3464-3468.
7. Rabiner, L. R., & Schafer, R. W. (2010). *Theory and Applications of Digital Speech Processing*. Pearson.
