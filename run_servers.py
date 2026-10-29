"""Convenience Runner for FastAPI backend and Streamlit dashboard on Windows."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

from core.config import config, logger


def start_api() -> subprocess.Popen:
    """Launch FastAPI backend server."""
    logger.info("Starting FastAPI backend on http://%s:%d ...", config.api_host, config.api_port)
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        config.api_host,
        "--port",
        str(config.api_port),
    ]
    return subprocess.Popen(cmd)


def start_streamlit() -> subprocess.Popen:
    """Launch Streamlit frontend application."""
    logger.info("Starting Streamlit dashboard on http://localhost:%d ...", config.streamlit_port)
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(config.streamlit_port),
        "--server.headless",
        "true",
    ]
    return subprocess.Popen(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multimodal Attendance & Engagement Agent Runner")
    parser.add_argument(
        "--mode",
        choices=["both", "api", "dashboard"],
        default="dashboard",
        help="Target service to run (default: dashboard)",
    )
    args = parser.parse_args()

    procs = []
    try:
        if args.mode in ["both", "api"]:
            procs.append(start_api())
            time.sleep(1.5)

        if args.mode in ["both", "dashboard"]:
            procs.append(start_streamlit())

        logger.info("Service(s) launched. Press Ctrl+C to terminate.")
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        logger.info("Terminating running services...")
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
