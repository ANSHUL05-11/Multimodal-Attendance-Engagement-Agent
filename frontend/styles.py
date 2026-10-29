"""Modern Dark Navy CSS styles and HTML UI helpers for Streamlit."""

from __future__ import annotations

import streamlit as st

CUSTOM_CSS = """
<style>
/* Base Dark Navy Theme */
.stApp {
    background-color: #0b1120;
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}

/* Metric / Stat Card */
.stat-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.stat-card:hover {
    border-color: #38bdf8;
    transform: translateY(-2px);
}
.stat-label {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    margin-bottom: 6px;
}
.stat-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #38bdf8;
}
.stat-sub {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 4px;
}

/* Header & Accent Cards */
.accent-card {
    background: #1e293b;
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 15px 0;
}

/* Badges / Status Pills */
.badge-present {
    background-color: rgba(16, 185, 129, 0.2);
    color: #34d399;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(16, 185, 129, 0.4);
}
.badge-partial {
    background-color: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(245, 158, 11, 0.4);
}
.badge-uncertain {
    background-color: rgba(239, 68, 68, 0.2);
    color: #f87171;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(239, 68, 68, 0.4);
}
.badge-confirmed {
    background-color: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(59, 130, 246, 0.4);
}

/* Recommendation Cards */
.rec-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
}
.rec-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 6px;
}
.rec-obs {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-bottom: 8px;
}
.rec-sug {
    font-size: 0.9rem;
    color: #38bdf8;
    background: #0f172a;
    padding: 8px 12px;
    border-radius: 6px;
    border-left: 3px solid #38bdf8;
}

/* Buttons */
.stButton>button {
    background-color: #2563eb;
    color: white;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    padding: 8px 16px;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    background-color: #1d4ed8;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* Tables */
div[data-testid="stDataFrame"] {
    border: 1px solid #334155;
    border-radius: 8px;
    overflow: hidden;
}
</style>
"""


def apply_custom_theme() -> None:
    """Inject modern dark navy CSS into Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_stat_card(label: str, value: str, sub: str = "") -> str:
    """Return HTML snippet for a sleek KPI card."""
    return f"""
    <div class="stat-card">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
        <div class="stat-sub">{sub}</div>
    </div>
    """
