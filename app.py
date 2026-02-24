"""
Campaign Optimization Tool — Streamlit UI
Digital Turbine AdOps Optimizer
"""

import streamlit as st
import pandas as pd
from optimizer import run_optimization, letter_to_index

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Campaign Optimizer",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── STYLING ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Wider centered layout */
.block-container { max-width: 820px; padding-top: 2rem; padding-bottom: 3rem; }

/* Section cards */
div[data-testid="stVerticalBlock"] > div:has(> .section-card) {
    background: #f8fafd;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    border: 1px solid #e3eaf3;
}

/* File uploader — bigger drop zone */
div[data-testid="stFileUploader"] > label { font-weight: 600; font-size: 0.95rem; }
div[data-testid="stFileUploaderDropzone"] { min-height: 110px; }

/* Primary button */
div[data-testid="stButton"] > button[kind="primary"] {
    font-size: 1.05rem;
    height: 3.2rem;
    border-radius: 8px;
}

/* Metric labels */
div[data-testid="stMetric"] label { font-size: 0.75rem !important; }

h1 { color: #1a3a6b; }
h2 { color: #1a3a6b; margin-top: 0 !important; }
hr { margin: 1.4rem 0; border-color: #d0dcea; }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────

st.title("🎯 Campaign Optimizer")
st.caption("Upload your files, enter your goals, and get instant bid recommendations.")
st.divider()

# ─── SECTION 1: FILE UPLOADS ──────────────────────────────────────────────────

st.subheader("1  Upload Your Data Files")

col1, col2 = st.columns(2)
with col1:
    internal_file = st.file_uploader(
        "**Internal Campaign Data**  *(Excel .xlsx)*",
        type=["xlsx", "xls"],
        help="The platform export with campaign metrics (bids, fill rate, installs, etc.)",
    )
    if internal_file:
        st.success(f"✅  {internal_file.name}", icon=None)

with col2:
    advertiser_file = st.file_uploader(
        "**Advertiser Performance Report**  *(CSV)*",
        type=["csv"],
        help="The advertiser's report containing ROAS / ROI data",
    )
    if advertiser_file:
        st.success(f"✅  {advertiser_file.name}", icon=None)

# ─── LOAD CSV COLUMNS FOR SMART DROPDOWNS ─────────────────────────────────────

adv_cols = []
if advertiser_file:
    try:
        _preview = pd.read_csv(advertiser_file)
        advertiser_file.seek(0)
        adv_cols = _preview.columns.tolist()
    except Exception:
        st.warning("⚠️  Could not read the CSV — please make sure it is a valid CSV file.")

def _auto_idx(patterns, cols, fallback=0):
    """Return the index of the first column whose name matches any pattern."""
    for p in patterns:
        for i, c in enumerate(cols):
            if p.lower() in c.lower():
                return i
    return fallback

st.divider()

# ─── SECTION 2: KPI GOALS ─────────────────────────────────────────────────────

st.subheader("2  Set Your KPI Goals")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Main KPI")
    if adv_cols:
        main_default = _auto_idx(["d7", "roas d7", "roi d7", "d 7"], adv_cols, 0)
        main_kpi_col = st.selectbox(
            "Which column is the main KPI?",
            adv_cols,
            index=main_default,
            key="main_col_select",
            help="Select the column that represents your primary performance metric",
        )
        main_col_idx = adv_cols.index(main_kpi_col)
    else:
        main_col_letter = st.text_input(
            "Column letter in the CSV (e.g. I)",
            value="I",
            help="Open your CSV and identify the column letter for your main KPI",
        )
        main_col_idx = letter_to_index(main_col_letter.strip()) if main_col_letter.strip() else 8

    main_kpi_target = st.number_input(
        "Target  (%)",
        min_value=0.1,
        max_value=500.0,
        value=10.0,
        step=0.5,
        key="main_target",
        help="e.g. enter 10 for a 10% ROAS/ROI target",
    )

with col2:
    st.markdown("##### Secondary KPI")
    if adv_cols:
        sec_default = _auto_idx(["d30", "d14", "roas d3", "roi d3", "d 30"], adv_cols, 1)
        if sec_default == main_default:
            sec_default = (main_default + 1) % max(len(adv_cols), 1)
        sec_kpi_col = st.selectbox(
            "Which column is the secondary KPI?",
            adv_cols,
            index=sec_default,
            key="sec_col_select",
            help="Select the column for your secondary performance metric",
        )
        sec_col_idx = adv_cols.index(sec_kpi_col)
    else:
        sec_col_letter = st.text_input(
            "Column letter in the CSV (e.g. K)",
            value="K",
            help="Open your CSV and identify the column letter for your secondary KPI",
        )
        sec_col_idx = letter_to_index(sec_col_letter.strip()) if sec_col_letter.strip() else 10

    sec_kpi_target = st.number_input(
        "Target  (%)",
        min_value=0.1,
        max_value=500.0,
        value=5.0,
        step=0.5,
        key="sec_target",
        help="e.g. enter 5 for a 5% ROAS/ROI target",
    )

st.markdown("##### How important is the Main KPI compared to the Secondary KPI?")
main_weight = st.select_slider(
    "KPI weight",
    options=[50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100],
    value=80,
    format_func=lambda x: f"Main  {x}%  /  Secondary  {100 - x}%",
    label_visibility="collapsed",
    help="80/20 is the standard split — adjust only if directed",
)
st.caption(
    f"The optimizer will weight the **Main KPI at {main_weight}%** "
    f"and the **Secondary KPI at {100 - main_weight}%** when scoring each campaign."
)

st.divider()

# ─── SECTION 3: OPTIMIZATION SETTINGS ────────────────────────────────────────

st.subheader("3  Optimization Settings")

col1, col2 = st.columns(2)

with col1:
    opt_type_choice = st.radio(
        "**Optimization goal**",
        ["Scale", "Performance", "Other"],
        help=(
            "Scale = grow volume aggressively  |  "
            "Performance = prioritize ROI efficiency"
        ),
    )
    if opt_type_choice == "Other":
        opt_type_custom = st.text_input(
            "Describe your goal",
            placeholder="e.g. Maintain volume while hitting target ROAS",
        )
        opt_type = opt_type_custom.strip() if opt_type_custom.strip() else "Other"
    else:
        opt_type = opt_type_choice

with col2:
    duration_choice = st.radio(
        "**Report covers the last...**",
        ["30 days", "60 days", "Other"],
    )
    if duration_choice == "Other":
        duration_custom = st.text_input(
            "Specify duration",
            placeholder="e.g. 14 days",
        )
        report_duration = f"Last {duration_custom.strip()}" if duration_custom.strip() else "Other"
    else:
        report_duration = f"Last {duration_choice}"

notes = st.text_area(
    "**Additional notes or constraints**  *(optional)*",
    placeholder=(
        "e.g. Advertiser wants to scale but keep performance — "
        "no single campaign should spend more than $100/day. "
        "Need at least 50 installs per week."
    ),
    height=100,
    help="Any special instructions the optimizer should be aware of (saved to the output file)",
)

st.divider()

# ─── RUN BUTTON ───────────────────────────────────────────────────────────────

files_ready = internal_file is not None and advertiser_file is not None

if not files_ready:
    st.info("👆  Upload both files above to enable the optimizer.", icon="ℹ️")

run_clicked = st.button(
    "🚀  Run Optimization",
    type="primary",
    disabled=not files_ready,
    use_container_width=True,
)

# ─── RESULTS ──────────────────────────────────────────────────────────────────

if run_clicked and files_ready:
    # Reset file pointers before passing to optimizer
    internal_file.seek(0)
    advertiser_file.seek(0)

    with st.spinner("Analyzing campaigns and calculating bid recommendations…"):
        try:
            excel_bytes, summary = run_optimization(
                internal_path=internal_file,
                advertiser_path=advertiser_file,
                kpi_col_idx_d7=main_col_idx,
                kpi_col_idx_d2nd=sec_col_idx,
                kpi_d7=main_kpi_target / 100.0,
                kpi_d2nd=sec_kpi_target / 100.0,
                w_d7=main_weight / 100.0,
                w_d2nd=(100 - main_weight) / 100.0,
                optimization_type=opt_type,
                report_duration=report_duration,
                notes=notes,
            )

            st.success("Optimization complete!", icon="✅")
            st.divider()

            # ── Summary metrics ───────────────────────────────────────────────
            st.subheader("Results Summary")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Campaigns processed", summary["total_rows"])
            m2.metric("Actions recommended", summary["actioned"])
            m3.metric("No action needed", summary["disregarded"])
            m4.metric("Daily cap flags", summary["daily_cap"])

            if summary.get("excluded") or summary.get("dropped_nulls"):
                st.caption(
                    f"ℹ️  {summary.get('excluded', 0)} rows excluded (OM Push / Notifications)  •  "
                    f"{summary.get('dropped_nulls', 0)} rows skipped (missing data)"
                )

            # ── Segment breakdown ─────────────────────────────────────────────
            seg = summary.get("segment_breakdown", {})
            if seg:
                st.markdown("**Performance segments:**")
                seg_icons = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}
                seg_order = ["green", "yellow", "orange", "red"]
                seg_cols = st.columns(len(seg_order))
                for i, key in enumerate(seg_order):
                    count = seg.get(key, 0)
                    seg_cols[i].metric(
                        f"{seg_icons.get(key, '⚪')} {key.capitalize()}",
                        count,
                    )

            # ── Action breakdown ──────────────────────────────────────────────
            action_bd = summary.get("action_breakdown", {})
            if action_bd:
                st.markdown("**Actions breakdown:**")
                sorted_actions = sorted(action_bd.items(), key=lambda x: -x[1])
                for action, count in sorted_actions:
                    pct = round(count / summary["actioned"] * 100) if summary["actioned"] else 0
                    st.markdown(f"- **{action}** — {count} rows ({pct}%)")

            st.divider()

            # ── Download button ───────────────────────────────────────────────
            st.download_button(
                label="📥  Download Results  (Excel)",
                data=excel_bytes,
                file_name="optimization_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"Something went wrong: {e}", icon="❌")
            with st.expander("Error details"):
                st.exception(e)
