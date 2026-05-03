from pathlib import Path

import pandas as pd
import streamlit as st


CSV_CANDIDATES = [
    Path("data/results/final_with_refinement.csv"),
    Path("data/results/backend_outputs.csv"),
    Path("data/presentation_refinement_table.csv"),
]

RESPONSE_COLUMNS = {
    "Baseline": "baseline_response",
    "Anchor Draft": "anchor_response",
    "Refined Final Response": "refined_anchor_response",
}


st.set_page_config(
    page_title="Empathy2 Pipeline Demo",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def read_csv(path):
    return pd.read_csv(path).fillna("")


def choose_source():
    for path in CSV_CANDIDATES:
        if path.exists():
            return path
    st.error(
        "No demo CSV found. Expected data/results/final_with_refinement.csv, "
        "data/results/backend_outputs.csv, or data/presentation_refinement_table.csv."
    )
    st.stop()


def normalize_dataframe(df):
    df = df.copy()

    if "scenario_type" not in df.columns:
        if "type" in df.columns:
            df["scenario_type"] = df["type"]
        elif "scenario_tier" in df.columns:
            df["scenario_type"] = df["scenario_tier"]
        else:
            df["scenario_type"] = "unknown"

    if "case_id" not in df.columns:
        df["case_id"] = [f"case_{index + 1}" for index in range(len(df))]

    if "anchor_response" not in df.columns:
        if "reply" in df.columns:
            df["anchor_response"] = df["reply"]
        else:
            df["anchor_response"] = ""

    for column in [
        "user_message",
        "baseline_response",
        "refined_anchor_response",
        "anchor_failure_types",
        "refined_failure_types",
        "refined_passed",
    ]:
        if column not in df.columns:
            df[column] = ""

    return df


def value(row, column, default=""):
    if column not in row.index:
        return default
    item = row.get(column, default)
    if pd.isna(item) or str(item).strip() == "":
        return default
    return item


def split_failures(text):
    if not text:
        return []
    normalized = str(text).replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def show_response_box(title, body, state):
    if body:
        if state == "baseline":
            st.info(body)
        elif state == "anchor":
            st.warning(body)
        else:
            st.success(body)
    else:
        st.caption("Not available for this run.")


def show_failure_block(title, failures, passed_value=""):
    st.markdown(f"**{title}**")
    passed = str(passed_value).strip().lower()
    if failures:
        for failure in failures:
            st.error(failure, icon="!")
    elif passed in {"true", "1", "yes"}:
        st.success("passed", icon="✓")
    else:
        st.success("no failures listed", icon="✓")


def show_understanding(row):
    fields = [
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
    available = [(label, column) for label, column in fields if value(row, column)]

    if not available:
        st.info("Understanding output not available for this run.")
        return

    columns = st.columns(3)
    for index, (label, column) in enumerate(available):
        with columns[index % 3]:
            st.metric(label, value(row, column))

    raw = value(row, "understanding_json")
    if raw:
        with st.expander("Raw understanding JSON"):
            st.code(raw, language="json")


source_path = choose_source()
df = normalize_dataframe(read_csv(source_path))

scenario_values = sorted(
    scenario for scenario in df["scenario_type"].astype(str).unique() if scenario
)
scenario_options = ["All"] + scenario_values

st.sidebar.caption(f"Source: {source_path}")
selected_scenario = st.sidebar.selectbox("Filter by scenario type", scenario_options)

filtered = df
if selected_scenario != "All":
    filtered = df[df["scenario_type"].astype(str) == selected_scenario]

if filtered.empty:
    st.warning("No rows match the selected filter.")
    st.stop()

case_ids = filtered["case_id"].astype(str).tolist()
selected_case_id = st.sidebar.selectbox("Select case_id", case_ids)
row = filtered[filtered["case_id"].astype(str) == selected_case_id].iloc[0]

st.title("Empathy2 Pipeline Demo")
st.caption(f"Reading from {source_path}")

if source_path.name == "backend_outputs.csv":
    st.warning(
        "This is raw backend output. Run `python -m scripts.run_full_eval_pipeline "
        "--skip-backend --raw-output data/results/backend_outputs.csv` to generate "
        "`final_with_refinement.csv` for the full comparison view."
    )

st.subheader("User Input")
with st.container(border=True):
    st.write(value(row, "user_message", "No user message available."))

st.subheader("Understanding")
show_understanding(row)

st.subheader("Response Comparison")
baseline_col, anchor_col, refined_col = st.columns(3)

with baseline_col:
    st.markdown("**Baseline**")
    show_response_box("Baseline", value(row, "baseline_response"), "baseline")

with anchor_col:
    st.markdown("**Anchor Draft**")
    show_response_box("Anchor Draft", value(row, "anchor_response"), "anchor")

with refined_col:
    st.markdown("**Refined Final Response**")
    show_response_box("Refined Final Response", value(row, "refined_anchor_response"), "refined")

st.subheader("Validation")
validation_col_a, validation_col_b = st.columns(2)
with validation_col_a:
    show_failure_block(
        "Anchor failure types",
        split_failures(value(row, "anchor_failure_types")),
    )
with validation_col_b:
    show_failure_block(
        "Remaining after refinement",
        split_failures(value(row, "refined_failure_types")),
        passed_value=value(row, "refined_passed"),
    )

st.divider()
st.markdown("**From expressive but unstable empathy -> controlled and validated empathy.**")
