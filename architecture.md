<!--
# Architecture

## Data Flow
1. Raw retail transactions (Excel)
2. Cleaning and validation pipeline (Python)
3. KPI engine (monthly and country-level outputs)
4. Insight evidence generation (analysis outputs)
5. Excel pivots and reporting (next step)

## Key Outputs
- Cleaned transaction sample (for review)
- Monthly KPI tables (overall and by country)
- Evidence tables supporting insights
- Written insights summary
-->
# Architecture

This project builds an end-to-end decision intelligence reporting layer from raw retail transactions to validated KPIs, evidence-backed insights, and an executive-style Excel dashboard.

The emphasis is on correctness and traceability: every dashboard metric is derived from a documented cleaning process and reconciled against Python-generated KPI outputs.

---

## Components

### 1) Raw Data
- Source: Online Retail II transactional dataset (Excel format)
- Input columns used (core):
  - `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`, `source_sheet`

### 2) Cleaning and Validation (Python)
Scripts standardize and validate the dataset before KPI computation:
- remove cancelled invoices (invoice IDs starting with `C`)
- remove invalid quantities and prices (must be > 0)
- drop rows with missing customer IDs
- parse dates and validate date range
- drop exact full-row duplicates
- keep business-key duplicates (Invoice + StockCode + InvoiceDate) but track volume as a data quality signal

Validation checks confirm:
- zero cancelled invoices after cleaning
- no non-positive quantities or prices
- no missing customer IDs
- all dates parse successfully

### 3) KPI Engine (Python)
Two KPI tables are generated:
- `kpi_monthly.csv`: month-level KPIs
- `kpi_monthly_country.csv`: month-by-country KPIs

KPIs include:
- Revenue, Orders, Active Customers, Units Sold, AOV
- Month-over-month growth metrics for key measures (where applicable)

### 4) Evidence Outputs (Analysis)
Analysis outputs support written insights and make findings reproducible:
- top revenue months
- country revenue concentration
- fastest growing countries
- revenue driver correlations

### 5) Excel Reporting Layer
Excel consumes the KPI CSV outputs and produces:
- KPI cards with month selection
- pivot tables for year and country breakdowns
- trend charts for revenue and customer activity
- country comparison charts (including an “excluding UK” view to address distribution skew)

Excel formulas (date-based lookups) compute:
- previous month values
- month-over-month growth

### 6) Documentation Layer
Markdown docs capture:
- data inventory
- cleaning rules
- KPI definitions
- insights and validation notes

---

## Data Flow

1. Raw Excel transactions  
2. Python cleaning + validation  
3. KPI computation (monthly and monthly-by-country)  
4. Analysis outputs for evidence  
5. Excel pivots + formulas + dashboard  
6. Final: dashboard screenshot + documented insights

---

## Key Outputs

- Cleaned transaction sample (committed for review)
- Processed KPI tables in `data/processed`
- Excel dashboard in `excel/`
- Insights document grounded in computed evidence outputs
- Cleaning and validation rules to ensure reproducibility
