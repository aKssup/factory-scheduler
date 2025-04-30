# scheduler.py -- Backend

import pandas as pd
import math
from io import BytesIO
from pandas.tseries.offsets import BusinessDay 

def load_and_prepare(file, start_date, end_date):
    """
    Reads the Excel file, trims to the 'tub' section, selects relevant columns,
    forward-fills, converts dates, and filters by date range.
    Returns the full df and the date-filtered df_filt.
    """
    df = pd.read_excel(file)
    stop_idx = df[df.iloc[:,1] == "GALLON"].index[0]
    df = df.iloc[7:stop_idx].dropna(how='all')

    df = df.iloc[:, [2, 3, 5, 9]]
    df.columns = ['order_id', 'product_name', 'ship_date', 'cases_needed']
    df[['order_id','product_name']] = df[['order_id','product_name']].ffill()
    df['ship_date'] = pd.to_datetime(df['ship_date'], errors='coerce')

    mask = (
        df['ship_date'].dt.date >= start_date
    ) & (
        df['ship_date'].dt.date <= end_date
    )
    df_filt = df.loc[mask].reset_index(drop=True)
    return df, df_filt

def compute_coverage(df, df_filt):
    """
    Computes overall and per-product coverage.
    Returns cov_df, overall_pct, total_rows, filtered_rows.
    """
    total_rows    = len(df)
    filtered_rows = len(df_filt)
    overall_pct   = (filtered_rows / total_rows * 100) if total_rows else 0

    tot_counts = df['order_id'].value_counts().rename('total')
    fil_counts = df_filt['order_id'].value_counts().rename('filtered')
    cov = pd.concat([tot_counts, fil_counts], axis=1).fillna(0)
    cov['coverage_pct'] = (cov['filtered'] / cov['total'] * 100).round(1)
    cov_df = cov.reset_index().rename(columns={'index':'order_id'})
    return cov_df, overall_pct, total_rows, filtered_rows

def build_priority(df_filt):
    """
    For each order, record:
      - priority_date: earliest ship_date
      - source_date:   last ship_date in the range (aggregated row)
      - cases_needed:  last cases_needed (aggregated)
    Returns df_priority.
    """
    df_sorted = df_filt.sort_values(['order_id','ship_date'])
    df_priority = df_sorted.groupby(
        ['order_id','product_name'], as_index=False
    ).agg(
        priority_date=('ship_date','first'),
        source_date  =('ship_date','last'),
        cases_needed =('cases_needed','last')
    )
    # Display positive numbers with abs()
    df_priority['cases_needed'] = df_priority['cases_needed'].abs()
    return df_priority

def build_schedule(df_priority, pallet_size=130, daily_capacity=3500, max_products=8):
    """
    Flatten into pallets, sort by (priority_date, needed desc),
    then greedily assign to days subject to capacity & max distinct products.
    Returns:
      sched_df   — detailed per-day schedule with 'date' merged in
      day_summary — per-day totals, leftover, num_products, and 'date'
    """
    df2 = df_priority.copy()
    df2['needed'] = df2['cases_needed'].abs()
    df2['n_pal']  = df2['needed'].apply(lambda x: math.ceil(x / pallet_size))

    # sort by due-date priority, then highest demand first
    df2 = df2.sort_values(['priority_date','needed'], ascending=[True, False])

    # flatten to individual pallets
    pallets = []
    for _, row in df2.iterrows():
        for _ in range(int(row['n_pal'])):
            pallets.append((row['order_id'], row['product_name'], pallet_size))

    schedule = []
    day, cap, prod_set = 1, daily_capacity, set()
    for oid, pname, cases in pallets:
        if cases > cap or (oid not in prod_set and len(prod_set) >= max_products):
            day += 1
            cap = daily_capacity
            prod_set.clear()
        schedule.append((day, oid, pname, cases))
        cap -= cases
        prod_set.add(oid)

    # detailed schedule
    sched_df = (
        pd.DataFrame(schedule, columns=['day','order_id','product_name','cases'])
          .groupby(['day','order_id','product_name'], as_index=False)
          .agg(pallets=('cases','count'),
               cases_scheduled=('cases','sum'))
    )

    # day-level summary
    day_summary = sched_df.groupby('day', as_index=False).agg(
        total_pallets=('pallets','sum'),
        total_cases=('cases_scheduled','sum'),
        num_products=('order_id','nunique')
    )
    day_summary['leftover_cases'] = daily_capacity - day_summary['total_cases']

    # map day->calendar date
    base_date = df_priority['priority_date'].min().date()
    day_summary['date'] = day_summary['day'].apply(
        lambda d: (base_date + pd.Timedelta(days=d-1)).strftime('%Y-%m-%d')
    )

    # start from the earliest priority_date (as a Timestamp)
    base_date = df_priority['priority_date'].min()
    # business day offset: Day 1 = base_date, Day 2 = next business day, etc.
    day_summary['date'] = day_summary['day'].apply(
        lambda d: (base_date + BusinessDay(d-1)).strftime('%Y-%m-%d')
    )

    # merge date into sched_df, reorder columns
    sched_df = sched_df.merge(
        day_summary[['day','date']],
        on='day', how='left'
    )
    sched_df = sched_df[
        ['day','date','order_id','product_name','pallets','cases_scheduled']
    ]
    day_summary = day_summary[
        ['day','date','total_pallets','total_cases','num_products','leftover_cases']
    ]
    return sched_df, day_summary

def to_excel(dfs: dict) -> bytes:
    """
    Write multiple DataFrames to an in-memory Excel file.
    dfs: {sheet_name: DataFrame}
    """
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        for name, df in dfs.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return out.getvalue()
