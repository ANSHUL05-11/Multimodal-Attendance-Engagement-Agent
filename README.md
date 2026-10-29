# Multimodal Attendance & Engagement Agent

A classroom observation prototype that combines computer vision,
audio-signal features, and transparent rule-based analysis to help
educators review session presence and classroom activity.
**Live Demo:** [Live Demo](https://multimodal-attendance-engagement-agent-e2pdxdh94umcc3gdtjon6k.streamlit.app/)
https://multimodal-attendance-engagement-agent-e2pdxhd94umcc3gdtjon6k.streamlit.app/\
**GitHub repository:**
https://github.com/ANSHUL05-11/Multimodal-Attendance-Engagement-Agent\
**Demo video:** *Add your YouTube or Google Drive link here after
recording.*

> **Important:** This is an educational prototype. Attendance outputs
> are proposals that require human verification. Engagement scores are
> experimental signal/activity heuristics, not validated measurements of
> attention, emotion, learning, or academic performance.

## Features

-   **Classroom dashboard:** View session summaries and available
    attendance and analytics records.
-   **Presence-based attendance support:** Use visible-presence
    observations over time to create candidate attendance records for
    review.
-   **Audio signal analysis:** Analyze audio features such as signal
    energy and other available acoustic indicators.
-   **Multimodal analysis:** Combine available visual and audio
    indicators into experimental session-level summaries.
-   **Rule-based recommendations:** Produce explainable suggestions
    based on observed signals and configured thresholds.
-   **Analytics and exports:** Review session data and export supported
    reports.
-   **Local-first development:** Run the application on your own
    computer for testing and demonstrations.

Features available in a deployment depend on its installed dependencies,
runtime environment, and configured input sources. Verify each workflow
before relying on it in a presentation.

## Application screenshots

Add screenshots of your own running application here. Suggested
screenshots:

1.  Dashboard with a sample session.
2.  Session Workspace after processing a test input.
3.  Attendance review screen.
4.  Audio analysis and analytics report.

For example, save screenshots under `docs/screenshots/` and reference
them with Markdown image links.

## Technology stack

-   **Language:** Python
-   **Dashboard:** Streamlit
-   **Computer vision:** OpenCV; optional vision dependencies may vary
    by environment
-   **Audio processing:** NumPy and the audio libraries specified in
    `requirements.txt`
-   **API (optional):** FastAPI and Uvicorn
-   **Storage:** SQLite and SQLAlchemy
-   **Data and charts:** Pandas and Plotly
-   **Testing:** Pytest

The exact dependency versions are defined in `requirements.txt`.

## Project structure

``` text
.
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── run_servers.py             # Optional combined server runner, if configured
├── generate_samples.py        # Synthetic demo sample generator, if included
├── seed_demo_data.py          # Demo database seeder, if included
├── backend/                   # API code
├── core/                      # Vision, audio, agent, and analytics modules
├── database/                  # Database models and persistence
├── frontend/                  # Dashboard UI components
├── tests/                     # Automated tests
├── docs/                      # Project documentation
└── data/                      # Local data and sample assets, if present
```

Some optional files or directories may not be present in every version
of the repository. Check the repository before running optional
commands.

## Run locally on Windows

### 1. Clone the repository

``` powershell
git clone https://github.com/ANSHUL05-11/Multimodal-Attendance-Engagement-Agent.git
cd Multimodal-Attendance-Engagement-Agent
```

### 2. Create and activate a virtual environment

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt instead:

``` bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If installation fails, read the error and check the Python version and
platform compatibility of the package named in the error. Avoid
installing multiple OpenCV wheel variants together; use the single
variant appropriate to your environment.

### 4. Start the dashboard

``` powershell
python -m streamlit run app.py
```

Open the local URL printed in the terminal, normally:

`http://localhost:8501`

Keep the terminal open while using the local application. Press `Ctrl+C`
in that terminal to stop it.

### 5. Optional: start the API

If the backend entry point exists and the project requires it, open a
second terminal in the project directory and run:

``` powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

API documentation, when the server starts successfully:

`http://127.0.0.1:8000/docs`

If the API is not needed by the dashboard, this step may be skipped.

## Testing

Run the test suite from the repository root:

``` powershell
python -m pytest tests/ -v
```

Record the actual test summary in your project report or demo. Do not
describe tests as passing unless you have run them against the current
commit.

For a manual smoke test:

1.  Launch the dashboard and check that the main page loads.
2.  Navigate through each sidebar section.
3.  Create or load a clearly labelled synthetic demo session, if
    supported.
4.  Test CSV import/export where available.
5.  Try an audio sample and confirm the app handles unsupported or empty
    input gracefully.
6.  Verify the displayed values and recommendations against the input
    data.
7.  Check the logs for errors and document any features that remain
    incomplete.

## Synthetic test data

For testing, use synthetic or consented inputs only. Synthetic CSVs can
help exercise session records, attendance calculations, engagement
summaries, and rule-based recommendation logic. A generated tone/noise
WAV file can test audio upload and signal processing, but it is not
speech and cannot validate speech recognition.

The sample values are not real student records. Synthetic engagement
scores are only test values and should not be interpreted as real
attention measurements. A CSV dataset alone cannot test face detection;
that requires a compatible video or image input.

## Deployment

The hosted demo is available at the live-demo link above. A hosted
application runs in the hosting provider's environment, not on the
visitor's computer. Hardware-dependent features such as local webcam or
microphone access may behave differently online than they do when
running locally. Test the deployed workflows separately and document any
limitations.

To redeploy after pushing a code change, open the app in Streamlit
Community Cloud and check the deployment status and logs.

## Privacy, ethics, and limitations

-   Obtain appropriate consent before recording or processing people.
-   Use synthetic data or consented sample media in public
    demonstrations.
-   Do not commit real student recordings, identifiable attendance data,
    secrets, API keys, local databases containing personal information,
    or virtual-environment folders to GitHub.
-   Treat detected visual presence as an observation, not proof of
    identity or attendance.
-   Require educator review before finalizing attendance records.
-   Engagement indicators are experimental heuristics and are not
    validated assessments of cognitive attention, emotion, or learning.
-   Results can be affected by lighting, camera position, occlusion,
    background noise, device quality, and dependency availability.
-   Do not use this prototype as the sole basis for grading,
    disciplinary action, or other high-impact decisions.

## Future improvements

-   Add a one-click synthetic sample-data loader.
-   Add clearer validation messages for unsupported media and missing
    dependencies.
-   Expand unit and integration tests for empty inputs and edge cases.
-   Improve accessibility and document supported browsers and devices.
-   Add privacy-preserving retention controls and explicit consent
    workflows.

## Project links

-   **Live demo:**
    https://multimodal-attendance-engagement-agent-e2pdxhd94umcc3gdtjon6k.streamlit.app/
-   **Source code:**
    https://github.com/ANSHUL05-11/Multimodal-Attendance-Engagement-Agent
-   **Demo video:** *Replace this line with the actual video URL after
    uploading your recording.*

## Acknowledgements

Built as an educational capstone project to explore computer vision,
audio-signal processing, data analytics, and explainable rule-based
assistance for classroom observation.
