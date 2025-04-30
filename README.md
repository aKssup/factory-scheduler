# Tulkoff Condiments Factory Scheduler

This repository contains a Streamlit-based scheduling tool for managing condenser production at a condiments factory. It consists of two main modules:

- **`scheduler.py`** (backend): data processing and scheduling logic
- **`app.py`** (frontend): Streamlit GUI that ties everything together

---

## 🚀 1. Getting Started

### Prerequisites
- Python 3.8+
- [Streamlit](https://streamlit.io/) framework
- Your virtual environment (provided in this repo)

### Installation & Run
1. **Activate the virtual environment** (bundled in this repo)  
   - **macOS / Linux**  
     ```bash
     source ./venv/bin/activate
     ```  
   - **Windows (PowerShell)**  
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```

2. **Install dependencies** (if needed)  
   If you wish to regenerate a fresh environment, you can install dependencies manually:
   ```bash
   pip install streamlit pandas openpyxl
   ```

3. **Launch the app**  
   ```bash
   streamlit run app.py
   ```

   This will open a browser window at `http://localhost:8501` with the scheduler GUI.

---

## 🖥️ 2. GUI Overview & Features

When the app loads, you’ll see a clean, three-column layout and a sidebar with configuration options.

### Sidebar Controls
- **Upload Excel file**: Choose your _"Cases Needed"_ report (`.xlsx` or `.xls`).
- **Start / End Date**: Pick the scheduling window (e.g. 2025-04-16 through 2025-04-18).  
- **Pallet Size**: Number of cases per pallet (default 130).  
- **Daily Capacity**: Maximum cases you can run in a single business day (default 3500).  
- **Max Products/Day**: Cap on distinct products per day (default 8).

All inputs are editable on‑the‑fly—just update and the GUI will re-compute automatically.

### Main Display Panels
Once you upload a file and select your parameters, the app computes and displays:

1. **Input Coverage**  
   A sentence summary:
   > For date range *2025-04-16* to *2025-04-18*, we cover *X/Y* products (*Z.Z%* of the Tub line).

2. **Order Priorities**  
   A table showing each `order_id` and `product_name`, with:
   - **priority_date**: earliest due date in your window  
   - **source_date**: the actual date cases needed were aggregated from  
   - **cases_needed**: positive total number of cases to schedule

3. **Production Schedule**  
   A detailed table with columns:
   - **day**: business-day index (1, 2, 3…)  
   - **date**: actual calendar date (skips weekends)  
   - **order_id**, **product_name**
   - **pallets**: number of 130‑case pallets scheduled that day  
   - **cases_scheduled**: total cases (= pallets × pallet_size)

4. **Day Summary**  
   A high‑level view per business day, with:
   - **day**, **date**  
   - **total_pallets**, **total_cases**  
   - **num_products**: count of distinct products run that day  
   - **leftover_cases**: unused capacity remaining

### Interactive Features
- **Sortable Columns**: Click any column header to sort ascending/descending.  
- **Column Search/Filter**: Use the table UI to search or filter specific rows.  
- **Dynamic Inputs**: Change dates, pallet size, capacity, or max products — the schedule updates instantly.  
- **File Swap**: Upload a different "Cases Needed" file at any time to re-run with new data.

### Exporting Results
At the bottom, click **📥 Download Results as Excel** to export:
- Coverage summary  
- Order Priorities  
- Detailed Schedule  
- Day Summary  

---

*Built for Tulkoff Condiments Factory — streamlining your production planning with a simple, interactive scheduler!*
