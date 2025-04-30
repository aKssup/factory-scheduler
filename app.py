# app.py -- GUI

import streamlit as st
import pandas as pd
from scheduler import (
    load_and_prepare,
    compute_coverage,
    build_priority,
    build_schedule,
    to_excel
)

st.set_page_config(page_title="Factory Scheduler", layout="wide")
st.title("Tulkoff Factory Scheduler")
st.markdown(
    "Upload your 'Cases Needed' Excel file and configure parameters "
    "to generate a professional production schedule."
)

# Sidebar controls
st.sidebar.header("Configuration")
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx","xls"])
start_date     = st.sidebar.date_input("Start date", pd.to_datetime("2025-04-16").date())
end_date       = st.sidebar.date_input("End date",   pd.to_datetime("2025-04-18").date())
pallet_size    = st.sidebar.number_input("Pallet size",      min_value=1, value=130,  step=10)
daily_capacity = st.sidebar.number_input("Daily capacity",   min_value=1, value=3500, step=100)
max_products   = st.sidebar.number_input("Max products/day", min_value=1, value=8,    step=1)

if uploaded_file:
    # 1) Load & filter data
    df, df_filt = load_and_prepare(uploaded_file, start_date, end_date)

    # 2) Compute simple product coverage
    total_products   = df['order_id'].nunique()
    covered_products = df_filt['order_id'].nunique()
    coverage_pct     = (covered_products / total_products * 100) if total_products else 0

    st.subheader("Input Coverage")
    st.write(
        f"For date range {start_date} to {end_date}, "
        f"we cover {covered_products}/{total_products} products "
        f"({coverage_pct:.1f}% of the Tub line products from this day's Cases Needed)."
    )

    # 3) Build and show order priorities
    df_priority = build_priority(df_filt)
    st.subheader("Order Priorities")
    st.dataframe(df_priority)

    # 4) Build schedule and day summary
    sched_df, day_summary = build_schedule(
        df_priority, pallet_size, daily_capacity, max_products
    )
    days_needed = int(day_summary['day'].max()) if not day_summary.empty else 0

    st.subheader(f"Production Schedule (Business Days needed: {days_needed})")
    st.dataframe(sched_df)

    st.subheader("Day Summary")
    st.dataframe(day_summary)

    # 5) Allow download of results
    excel_data = to_excel({
        'Priorities': df_priority,
        'Schedule':   sched_df,
        'DaySummary': day_summary
    })
    st.download_button(
        "📥 Download Results as Excel",
        data=excel_data,
        file_name="schedule_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Please upload an Excel file to begin.")
