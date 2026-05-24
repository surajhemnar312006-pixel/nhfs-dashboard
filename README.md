# 🇮🇳 NFHS-5 Multi-Dashboard – Streamlit App

## Setup & Run

### 1. Install dependencies
```bash
pip install streamlit plotly pandas xlrd numpy statsmodels
```

### 2. Place data file
Put `NFHS_5_Factsheets_Data.xls` in the same folder as `app.py`.

### 3. Run the dashboard
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## 10 Dashboards Included

| # | Dashboard | Key KPIs |
|---|-----------|----------|
| 1 | Health Performance Analysis | Vaccination, Institutional Births, Health Insurance, Infant Mortality |
| 2 | Women Empowerment Analysis | Literacy, Mobile Phone, Bank Account, Internet Usage |
| 3 | Child Nutrition & Malnutrition | Stunting, Wasting, Underweight, Breastfeeding |
| 4 | Education & Literacy Analysis | Women/Men Literacy, 10+ Yrs Schooling |
| 5 | Sanitation & Public Health | Toilet, Clean Fuel, Drinking Water, Electricity |
| 6 | Vaccination Coverage Analysis | BCG, Polio, Measles, DPT, Full Vaccination |
| 7 | Lifestyle & Health Risk | Tobacco & Alcohol (Men/Women) |
| 8 | Rural vs Urban Development | 8-indicator Rural-Urban comparison |
| 9 | Overall Social Development Index | Composite SDI with Radar chart |
| 10 | Digital Awareness & Development | Internet, Mobile, Bank Account, Gender Gap |

## Features
- **State Filter** – Select any subset of states
- **Your Analysis Notes** – Add your own observations in sidebar
- **Interactive charts** – Hover, zoom, download via Plotly
- **Heatmaps** – Visual comparison of all indicators
- **Ranking Tables** – Sortable, color-coded
- **Trendline Correlations** – OLS regression overlays
- **Gauge Charts** – National KPI gauges (Dashboard 6)
- **Radar Charts** – Multi-dimension state comparison (Dashboard 9)
