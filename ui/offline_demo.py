from pathlib import Path
from textwrap import dedent

import pandas as pd
import streamlit as st


PRIMARY_CSV = Path("data/results/backend_outputs.csv")
FALLBACK_CSV = Path("data/presentation_refinement_table.csv")


st.set_page_config(
    page_title="Empathy2 Pipeline Demo",
    layout="wide",
)


def load_data():
    path = PRIMARY_CSV if PRIMARY_CSV.exists() else FALLBACK_CSV
    if not path.exists():
        st.error(
            "No demo CSV found. Expected data/results/backend_outputs.csv "
            "or data/presentation_refinement_table.csv."
        )
        st.stop()

    df = pd.read_csv(path).fillna("")
    if "scenario_type" not in df.columns and "type" in df.columns:
        df["scenario_type"] = df["type"]
    if "case_id" not in df.columns:
        df["case_id"] = [f"case_{index + 1}" for index in range(len(df))]
    return df, path


def value(row, column, default=""):
    if column not in row.index:
        return default
    item = row.get(column, default)
    return default if pd.isna(item) else item


def card(title, body, background, border):
    st.markdown(
        dedent(
            f"""
        <div class="demo-card" style="background:{background}; border-color:{border};">
            <div class="card-title">{title}</div>
            <div class="card-body">{body or "Not available for this run."}</div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )


def badge(label, tone="red"):
    class_name = "badge-good" if tone == "green" else "badge-bad"
    st.markdown(
        f'<span class="badge {class_name}">{label}</span>',
        unsafe_allow_html=True,
    )


def split_failures(text):
    if not text:
        return []
    normalized = str(text).replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def show_failure_badges(title, failures, passed_value=""):
    st.markdown(f"**{title}**")
    passed = str(passed_value).strip().lower()
    if not failures and passed in {"true", "1", "yes"}:
        badge("passed", "green")
        return
    if not failures:
        badge("no failures listed", "green")
        return
    for failure in failures:
        badge(failure, "red")


df, source_path = load_data()

st.markdown(
    dedent(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .source-note {
            color: #5f6b7a;
            font-size: 0.9rem;
            margin-bottom: 1.25rem;
        }
        .demo-card {
            border: 1px solid;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            min-height: 10rem;
            box-shadow: 0 1px 2px rgba(24, 35, 54, 0.06);
        }
        .top-card {
            background: #f8fafc;
            border: 1px solid #d9e2ec;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin: 0.5rem 0 1.25rem;
        }
        .card-title {
            color: #253041;
            font-size: 0.84rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            margin-bottom: 0.65rem;
        }
        .card-body {
            color: #1e293b;
            font-size: 1rem;
            line-height: 1.55;
            white-space: pre-wrap;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.75rem;
            margin: 0.5rem 0 1.25rem;
        }
        .metric {
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 0.75rem 0.85rem;
            background: #ffffff;
        }
        .metric-label {
            color: #64748b;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        .metric-value {
            color: #172033;
            font-size: 0.98rem;
            font-weight: 600;
            overflow-wrap: anywhere;
        }
        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.25rem 0.6rem;
            margin: 0.15rem 0.25rem 0.15rem 0;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .badge-bad {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        .badge-good {
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        .takeaway {
            margin-top: 1.5rem;
            padding: 1rem 1.1rem;
            border-radius: 14px;
            border: 1px solid #cbd5e1;
            background: #f8fafc;
            color: #172033;
            font-size: 1.05rem;
            font-weight: 700;
            text-align: center;
        }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

scenario_options = ["All"]
if "scenario_type" in df.columns:
    scenario_options += sorted(
        scenario for scenario in df["scenario_type"].astype(str).unique() if scenario
    )

selected_scenario = st.sidebar.selectbox("Filter by scenario type", scenario_options)
filtered = df
if selected_scenario != "All":
    filtered = df[df["scenario_type"].astype(str) == selected_scenario]

case_ids = filtered["case_id"].astype(str).tolist()
selected_case_id = st.sidebar.selectbox("Select case_id", case_ids)
row = filtered[filtered["case_id"].astype(str) == selected_case_id].iloc[0]

st.title("Empathy2 Pipeline Demo")
st.markdown(f'<div class="source-note">Reading from {source_path}</div>', unsafe_allow_html=True)

st.markdown("### User Input")
st.markdown(
    dedent(
        f"""
    <div class="top-card">
        <div class="card-body">{value(row, "user_message", "No user message available.")}</div>
    </div>
    """
    ),
    unsafe_allow_html=True,
)

st.markdown("### Understanding")
understanding_columns = [
    ("Primary emotion", "primary_emotion"),
    ("Secondary emotion", "secondary_emotion"),
    ("Intent", "intent"),
    ("Scenario tier", "scenario_tier"),
    ("Support need", "support_need"),
    ("Safety flag", "safety_flag"),
    ("Implicit", "is_implicit"),
    ("Emotion intensity", "emotion_intensity"),
    ("Crisis detected", "crisis_detected"),
]
available_understanding = [
    (label, column)
    for label, column in understanding_columns
    if column in row.index and str(value(row, column)).strip()
]

if available_understanding:
    metrics = []
    for label, column in available_understanding:
        metrics.append(
            dedent(
                f"""
            <div class="metric">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value(row, column)}</div>
            </div>
            """
            )
        )
    st.markdown(f'<div class="metric-grid">{"".join(metrics)}</div>', unsafe_allow_html=True)
else:
    st.info("Understanding output not available for this run.")

if "understanding_json" in row.index and str(value(row, "understanding_json")).strip():
    with st.expander("Raw understanding JSON"):
        st.code(value(row, "understanding_json"), language="json")

st.markdown("### Response Comparison")
baseline_col, anchor_col, refined_col = st.columns(3)
with baseline_col:
    card(
        "Baseline",
        value(row, "baseline_response"),
        background="#eff6ff",
        border="#bfdbfe",
    )
with anchor_col:
    card(
        "Anchor Draft",
        value(row, "anchor_response"),
        background="#fff7ed",
        border="#fed7aa",
    )
with refined_col:
    card(
        "Refined Final Response",
        value(row, "refined_anchor_response"),
        background="#f0fdf4",
        border="#bbf7d0",
    )

st.markdown("### Validation")
validation_col_a, validation_col_b = st.columns(2)
with validation_col_a:
    show_failure_badges(
        "Anchor failure types",
        split_failures(value(row, "anchor_failure_types")),
    )
with validation_col_b:
    show_failure_badges(
        "Remaining after refinement",
        split_failures(value(row, "refined_failure_types")),
        passed_value=value(row, "refined_passed"),
    )

st.markdown(
    dedent(
        """
    <div class="takeaway">
        From expressive but unstable empathy → controlled and validated empathy.
    </div>
    """
    ),
    unsafe_allow_html=True,
)
