import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NFHS-5 India Health Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .section-header {
        background: linear-gradient(90deg, #1565c0, #0288d1);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        font-size: 1.15rem;
        font-weight: 700;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        border-top: 3px solid #42a5f5;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .kpi-value { font-size: 1.8rem; font-weight: 800; color: #fff; }
    .kpi-label { font-size: 0.72rem; color: #90caf9; margin-top: 4px; }
    .kpi-sub   { font-size: 0.68rem; color: #64b5f6; margin-top: 2px; }
    .sidebar-note {
        background: #1a3a5c;
        border-left: 3px solid #42a5f5;
        padding: 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        color: #b0bec5;
        margin-top: 10px;
    }
    [data-testid="stSidebar"] { background: #0d1b2a; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e3a5f;
        border-radius: 6px 6px 0 0;
        color: #90caf9;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1565c0 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df_raw = pd.read_excel("NFHS_5_Factsheets_Data.xls", engine="xlrd", header=None)
    headers = [str(c).strip() for c in df_raw.iloc[0].tolist()]
    data = df_raw.iloc[1:].copy()
    data.columns = headers
    for col in data.columns[2:]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    total  = data[data.iloc[:, 1].astype(str).str.strip() == "Total"].copy().reset_index(drop=True)
    total.columns = headers
    total  = total.rename(columns={total.columns[0]: "State", total.columns[1]: "Area"})

    states = total[total["State"] != "India"].copy().reset_index(drop=True)
    india  = total[total["State"] == "India"].iloc[0]

    # Rural / Urban slices for Dashboard 8
    rural_india = data[(data.iloc[:, 0].astype(str).str.strip() == "India") &
                       (data.iloc[:, 1].astype(str).str.strip() == "Rural")].iloc[0]
    urban_india = data[(data.iloc[:, 0].astype(str).str.strip() == "India") &
                       (data.iloc[:, 1].astype(str).str.strip() == "Urban")].iloc[0]
    rural_india.index = headers
    urban_india.index = headers

    return total, states, india, rural_india, urban_india, headers

total_df, states_df, india_row, rural_india, urban_india, all_headers = load_data()

# ─── COLUMN LOOKUP ────────────────────────────────────────────────────────────
def fc(keywords, df=None):
    """Return first column name containing any keyword (case-insensitive)."""
    src = (df if df is not None else states_df).columns.tolist()
    for kw in keywords:
        for c in src:
            if kw.lower() in c.lower():
                return c
    return None

COL = {
    # Healthcare
    "vacc_full":     fc(["fully vaccinated based on information from either"]),
    "inst_birth":    fc(["Institutional births (in the 5 years before"]),
    "health_ins":    fc(["health insurance/financing"]),
    "infant_mort":   fc(["Infant mortality rate"]),
    "neonatal_mort": fc(["Neonatal mortality rate"]),
    "u5_mort":       fc(["Under-five mortality rate"]),
    "anc_visits":    fc(["at least 4 antenatal"]),
    "postnatal":     fc(["postnatal care from a doctor"]),
    # Women empowerment
    "women_lit":     fc(["Women (age 15-49) who are literate"]),
    "men_lit":       fc(["Men (age 15-49) who are literate"]),
    "women_internet":fc(["Women (age 15-49)  who have ever used the internet"]),
    "men_internet":  fc(["Men (age 15-49)  who have ever used the internet"]),
    "bank_account":  fc(["bank or savings account that they themselves use"]),
    "mobile_phone":  fc(["mobile phone that they themselves use"]),
    "women_paid":    fc(["worked in the last 12 months and were paid in cash"]),
    "own_house":     fc(["owning a house and/or land"]),
    "hh_decisions":  fc(["participate in three household decisions"]),
    "child_marriage":fc(["Women age 20-24 years married before age 18"]),
    # Nutrition
    "stunted":       fc(["stunted (height-for-age)"]),
    "wasted":        fc(["wasted (weight-for-height)18"]),
    "underweight":   fc(["underweight (weight-for-age)"]),
    "breastfeed":    fc(["breastfed within one hour of birth"]),
    "excl_bf":       fc(["exclusively breastfed"]),
    "adequate_diet": fc(["Total children age 6-23 months receiving an adequate diet"]),
    # Sanitation
    "toilet":        fc(["improved sanitation facility"]),
    "clean_fuel":    fc(["clean fuel for cooking"]),
    "drinking_water":fc(["improved drinking-water source"]),
    "electricity":   fc(["living in households with electricity"]),
    # Vaccination
    "vacc_card":     fc(["fully vaccinated based on information from vaccination card only"]),
    "bcg":           fc(["received BCG"]),
    "polio":         fc(["received 3 doses of polio"]),
    "measles":       fc(["first dose of measles"]),
    "dpt":           fc(["3 doses of penta or DPT"]),
    "vit_a":         fc(["received a vitamin A dose"]),
    # Lifestyle – exact column partial match
    "tobacco_w":     fc(["Women age 15 years and above who use any kind of tobacco"]),
    "tobacco_m":     fc(["Men age 15 years and above who use any kind of tobacco"]),
    "alcohol_w":     fc(["Women age 15 years and above who consume alcohol"]),
    "alcohol_m":     fc(["Men age 15 years and above who consume alcohol"]),
    # Anaemia
    "anaemia_child": fc(["Children age 6-59 months who are anaemic"]),
    "anaemia_women": fc(["Non-pregnant women age 15-49 years who are anaemic"]),
    # Misc
    "tfr":           fc(["Total Fertility Rate"]),
    "women_10yr":    fc(["Women (age 15-49)  with 10 or more years of schooling"]),
    "men_10yr":      fc(["Men (age 15-49)  with 10 or more years of schooling"]),
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def safe_val(val, decimals=1, suffix="%"):
    try:
        return f"{round(float(val), decimals)}{suffix}"
    except:
        return "N/A"

def kpi(label, value, sub=""):
    return f"""<div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
    </div>"""

def sh(text, icon=""):
    st.markdown(f'<div class="section-header">{icon} {text}</div>', unsafe_allow_html=True)

LAYOUT = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
              font_color="white", margin=dict(l=10,r=10,t=40,b=10))

def h_bar(df, state_col, val_col, title, cscale="Blues", height=550):
    d = df[[state_col, val_col]].dropna().sort_values(val_col)
    fig = px.bar(d, x=val_col, y=state_col, orientation="h",
                 color=val_col, color_continuous_scale=cscale,
                 title=title, height=height)
    fig.update_layout(**LAYOUT, showlegend=False)
    return fig

def heatmap(df, cols_dict, title, cscale="RdYlGn", height=550):
    h = df[["State"] + list(cols_dict.values())].dropna().set_index("State")
    h.columns = list(cols_dict.keys())
    fig = px.imshow(h, aspect="auto", color_continuous_scale=cscale,
                    title=title, height=height)
    fig.update_layout(**LAYOUT)
    return fig

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Flag_of_India.svg/320px-Flag_of_India.svg.png", width=110)
    st.markdown("## 🏥 NFHS-5 Dashboard")
    st.markdown("**National Family Health Survey – 5**  \n*(2019–21)*")
    st.markdown("---")

    dashboard = st.selectbox("📊 Select Dashboard", [
        "1️⃣  Health Performance Analysis",
        "2️⃣  Women Empowerment Analysis",
        "3️⃣  Child Nutrition & Malnutrition",
        "4️⃣  Education & Literacy Analysis",
        "5️⃣  Sanitation & Public Health",
        "6️⃣  Vaccination Coverage Analysis",
        "7️⃣  Lifestyle & Health Risk",
        "8️⃣  Rural vs Urban Development",
        "9️⃣  Overall Social Development Index",
        "🔟  Digital Awareness & Development",
    ])

    st.markdown("### 🔍 Filter by State")
    all_states = sorted(states_df["State"].unique().tolist())
    sel_states = st.multiselect("Select States (empty = all)", options=all_states, default=[])
    plot_df = states_df[states_df["State"].isin(sel_states)].copy() if sel_states else states_df.copy()

    st.markdown(f'<div class="sidebar-note">📌 Showing <b>{len(plot_df)}</b> states/UTs</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### ✍️ Your Analysis Notes")
    user_note = st.text_area("Add observations / insights", placeholder="Type here...", height=110)
    if user_note:
        st.success("✅ Notes saved!")

# ─── TITLE ────────────────────────────────────────────────────────────────────
title_map = {
    "1": "Health Performance Analysis",
    "2": "Women Empowerment Analysis",
    "3": "Child Nutrition & Malnutrition",
    "4": "Education & Literacy Analysis",
    "5": "Sanitation & Public Health",
    "6": "Vaccination Coverage Analysis",
    "7": "Lifestyle & Health Risk",
    "8": "Rural vs Urban Development",
    "9": "Overall Social Development Index",
    "🔟": "Digital Awareness & Development",
}
d_num = dashboard[0]
st.markdown(f"# 🇮🇳 NFHS-5 | {dashboard}")
st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
# D1 – HEALTH PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
if d_num == "1":
    sh("Key Health Indicators – India National Average", "📋")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Full Vaccination (%)", safe_val(india_row[COL["vacc_full"]]), "Children 12-23 months"), unsafe_allow_html=True)
    c2.markdown(kpi("Institutional Births (%)", safe_val(india_row[COL["inst_birth"]]), "Last 5 years"), unsafe_allow_html=True)
    c3.markdown(kpi("Health Insurance (%)", safe_val(india_row[COL["health_ins"]]), "Any HH member"), unsafe_allow_html=True)
    c4.markdown(kpi("Infant Mortality Rate", safe_val(india_row[COL["infant_mort"]], suffix=" /1000"), "Per 1000 live births"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    c5.markdown(kpi("Neonatal Mortality", safe_val(india_row[COL["neonatal_mort"]], suffix=" /1000"), "Per 1000 live births"), unsafe_allow_html=True)
    c6.markdown(kpi("Under-5 Mortality", safe_val(india_row[COL["u5_mort"]], suffix=" /1000"), "Per 1000 live births"), unsafe_allow_html=True)
    c7.markdown(kpi("4+ ANC Visits (%)", safe_val(india_row[COL["anc_visits"]]), "Antenatal care"), unsafe_allow_html=True)
    c8.markdown(kpi("Postnatal Care (%)", safe_val(india_row[COL["postnatal"]]), "Within 2 days"), unsafe_allow_html=True)

    sh("State-wise Comparison – Institutional Births & Vaccination", "🏆")
    cl, cr = st.columns(2)
    with cl:
        st.plotly_chart(h_bar(plot_df,"State",COL["inst_birth"],"Institutional Births by State (%)","Blues"), use_container_width=True)
    with cr:
        st.plotly_chart(h_bar(plot_df,"State",COL["vacc_full"],"Full Vaccination by State (%)","Greens"), use_container_width=True)

    sh("Mortality Rates & Healthcare Ranking", "📉")
    cl2, cr2 = st.columns(2)
    with cl2:
        dm = plot_df[["State", COL["neonatal_mort"], COL["infant_mort"], COL["u5_mort"]]].dropna()
        dm.columns = ["State","Neonatal","Infant","Under-5"]
        dm_m = dm.melt("State", var_name="Indicator", value_name="Rate")
        fig = px.bar(dm_m, x="State", y="Rate", color="Indicator", barmode="group",
                     title="Mortality Rates by State (per 1000 live births)",
                     height=460, color_discrete_sequence=["#ffca28","#ef5350","#b71c1c"])
        fig.update_layout(**LAYOUT, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    with cr2:
        rdf = plot_df[["State", COL["inst_birth"], COL["vacc_full"],
                       COL["health_ins"], COL["infant_mort"]]].dropna().copy()
        rdf.columns = ["State","Inst Births","Vaccination","Health Ins","Infant Mort"]
        rdf["Health Score"] = (rdf["Inst Births"]*0.3 + rdf["Vaccination"]*0.3 +
                               rdf["Health Ins"]*0.2 + (100-rdf["Infant Mort"])*0.2).round(1)
        rdf = rdf.sort_values("Health Score", ascending=False).reset_index(drop=True)
        rdf.index += 1; rdf.index.name = "Rank"
        st.markdown("#### 🥇 Healthcare Ranking Table")
        st.dataframe(rdf.style.background_gradient(cmap="Blues", subset=["Health Score"]),
                     use_container_width=True, height=430)

    sh("Healthcare Indicators Heatmap", "🔥")
    st.plotly_chart(heatmap(plot_df, {
        "Inst Births": COL["inst_birth"],
        "Vaccination": COL["vacc_full"],
        "Health Ins":  COL["health_ins"],
        "ANC 4+":      COL["anc_visits"],
        "Postnatal":   COL["postnatal"],
    }, "Healthcare Heatmap by State", "RdYlGn", height=600), use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D2 – WOMEN EMPOWERMENT
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "2":
    sh("Women Empowerment – National KPIs", "👩")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Women Literacy (%)", safe_val(india_row[COL["women_lit"]]), "Age 15-49"), unsafe_allow_html=True)
    c2.markdown(kpi("Mobile Phone Usage (%)", safe_val(india_row[COL["mobile_phone"]]), "Own/use"), unsafe_allow_html=True)
    c3.markdown(kpi("Bank Account (%)", safe_val(india_row[COL["bank_account"]]), "Self-use"), unsafe_allow_html=True)
    c4.markdown(kpi("Internet Usage (%)", safe_val(india_row[COL["women_internet"]]), "Ever used"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    c5.markdown(kpi("Paid Employment (%)", safe_val(india_row[COL["women_paid"]]), "Paid in cash"), unsafe_allow_html=True)
    c6.markdown(kpi("House/Land Ownership (%)", safe_val(india_row[COL["own_house"]]), "Alone or jointly"), unsafe_allow_html=True)
    c7.markdown(kpi("HH Decision-Making (%)", safe_val(india_row[COL["hh_decisions"]]), "3+ decisions"), unsafe_allow_html=True)
    c8.markdown(kpi("Child Marriage (%)", safe_val(india_row[COL["child_marriage"]]), "Before age 18"), unsafe_allow_html=True)

    sh("Literacy & Internet Usage by State", "📈")
    cl, cr = st.columns(2)
    with cl:
        st.plotly_chart(h_bar(plot_df,"State",COL["women_lit"],"Women Literacy by State (%)","Purples"), use_container_width=True)
    with cr:
        sd = plot_df[["State", COL["women_internet"], COL["men_internet"]]].dropna()
        sd.columns = ["State","Women Internet","Men Internet"]
        fig = px.scatter(sd, x="Women Internet", y="Men Internet", text="State",
                         color="Women Internet", color_continuous_scale="Viridis",
                         title="Women vs Men Internet Usage (%)", height=500,
                         trendline="ols")
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    sh("Empowerment Scorecard & Top/Bottom States", "🏅")
    cl2, cr2 = st.columns(2)
    with cl2:
        ed = plot_df[["State", COL["women_lit"], COL["mobile_phone"],
                      COL["bank_account"], COL["women_internet"], COL["women_paid"]]].dropna().copy()
        ed.columns = ["State","Literacy","Mobile","Bank","Internet","Paid"]
        ed["Empowerment Score"] = (ed["Literacy"]*0.25 + ed["Mobile"]*0.2 +
                                   ed["Bank"]*0.2 + ed["Internet"]*0.2 + ed["Paid"]*0.15).round(1)
        ed = ed.sort_values("Empowerment Score")
        fig = px.bar(ed, x="Empowerment Score", y="State", orientation="h",
                     color="Empowerment Score", color_continuous_scale="Purples",
                     title="Women Empowerment Composite Score", height=600)
        fig.update_layout(**LAYOUT, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cr2:
        top5 = ed.tail(5).assign(Group="Top 5")
        bot5 = ed.head(5).assign(Group="Bottom 5")
        tb = pd.concat([top5, bot5])
        fig = px.bar(tb, x="Empowerment Score", y="State", color="Group", orientation="h",
                     color_discrete_map={"Top 5":"#66bb6a","Bottom 5":"#ef5350"},
                     title="Top 5 vs Bottom 5 States", height=360)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

        bins = pd.cut(plot_df[COL["women_internet"]].dropna(),
                      bins=[0,20,40,60,80,100],
                      labels=["0-20%","20-40%","40-60%","60-80%","80-100%"])
        pie_d = bins.value_counts().reset_index()
        pie_d.columns = ["Range","States"]
        fig2 = px.pie(pie_d, values="States", names="Range",
                      title="States by Women Internet Usage Band",
                      color_discrete_sequence=px.colors.sequential.Purples_r, height=310)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D3 – CHILD NUTRITION
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "3":
    sh("Child Nutrition – National KPIs", "🍼")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Stunting (%)", safe_val(india_row[COL["stunted"]]), "Children under 5"), unsafe_allow_html=True)
    c2.markdown(kpi("Wasting (%)", safe_val(india_row[COL["wasted"]]), "Children under 5"), unsafe_allow_html=True)
    c3.markdown(kpi("Underweight (%)", safe_val(india_row[COL["underweight"]]), "Children under 5"), unsafe_allow_html=True)
    c4.markdown(kpi("Early Breastfeeding (%)", safe_val(india_row[COL["breastfeed"]]), "Within 1 hr of birth"), unsafe_allow_html=True)

    sh("Malnutrition Comparison by State", "📊")
    cl, cr = st.columns(2)
    with cl:
        nd = plot_df[["State", COL["stunted"], COL["wasted"], COL["underweight"]]].dropna()
        nd.columns = ["State","Stunted","Wasted","Underweight"]
        nd = nd.sort_values("Stunted", ascending=False)
        fig = go.Figure()
        for col_n, clr in [("Stunted","#ef5350"),("Wasted","#ff7043"),("Underweight","#ffca28")]:
            fig.add_trace(go.Bar(name=col_n, x=nd["State"], y=nd[col_n], marker_color=clr))
        fig.update_layout(**LAYOUT, barmode="group", xaxis_tickangle=-45,
                          legend=dict(orientation="h"), title="Malnutrition Indicators by State (%)", height=480)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        st.plotly_chart(heatmap(plot_df, {
            "Stunted":      COL["stunted"],
            "Wasted":       COL["wasted"],
            "Underweight":  COL["underweight"],
            "Adequate Diet":COL["adequate_diet"],
        }, "Child Nutrition Heatmap (Green=Better)", "RdYlGn_r", height=480), use_container_width=True)

    sh("Nutrition vs Sanitation & Breastfeeding", "🔗")
    cl2, cr2 = st.columns(2)
    with cl2:
        sc = plot_df[["State", COL["stunted"], COL["toilet"]]].dropna()
        sc.columns = ["State","Stunting %","Toilet Access %"]
        fig = px.scatter(sc, x="Toilet Access %", y="Stunting %", text="State",
                         trendline="ols", color="Stunting %", color_continuous_scale="Reds",
                         title="Stunting vs Toilet Access", height=420)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with cr2:
        bf = plot_df[["State", COL["breastfeed"], COL["excl_bf"], COL["adequate_diet"]]].dropna()
        bf.columns = ["State","Early BF","Exclusive BF","Adequate Diet"]
        bf = bf.sort_values("Early BF", ascending=False)
        fig = px.bar(bf, x="State", y=["Early BF","Exclusive BF","Adequate Diet"],
                     barmode="group", height=420,
                     color_discrete_sequence=["#42a5f5","#66bb6a","#ffa726"],
                     title="Breastfeeding & Adequate Diet (%)")
        fig.update_layout(**LAYOUT, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    sh("State Ranking – Malnutrition (Lower = Better)", "📋")
    rn = plot_df[["State", COL["stunted"], COL["wasted"], COL["underweight"]]].dropna()
    rn.columns = ["State","Stunted %","Wasted %","Underweight %"]
    rn["Avg Malnutrition"] = rn[["Stunted %","Wasted %","Underweight %"]].mean(axis=1).round(1)
    rn = rn.sort_values("Avg Malnutrition").reset_index(drop=True)
    rn.index += 1; rn.index.name = "Rank"
    st.dataframe(rn.style.background_gradient(cmap="RdYlGn_r", subset=["Avg Malnutrition"]),
                 use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D4 – EDUCATION & LITERACY
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "4":
    sh("Education & Literacy – National KPIs", "📚")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Women Literacy (%)", safe_val(india_row[COL["women_lit"]]), "Age 15-49"), unsafe_allow_html=True)
    c2.markdown(kpi("Men Literacy (%)", safe_val(india_row[COL["men_lit"]]), "Age 15-49"), unsafe_allow_html=True)
    c3.markdown(kpi("Women 10+ Yrs School (%)", safe_val(india_row[COL["women_10yr"]]), "Age 15-49"), unsafe_allow_html=True)
    c4.markdown(kpi("Men 10+ Yrs School (%)", safe_val(india_row[COL["men_10yr"]]), "Age 15-49"), unsafe_allow_html=True)

    sh("Male vs Female Literacy by State", "⚖️")
    cl, cr = st.columns(2)
    with cl:
        ld = plot_df[["State", COL["women_lit"], COL["men_lit"]]].dropna()
        ld.columns = ["State","Women Lit","Men Lit"]
        ld["Gap"] = (ld["Men Lit"] - ld["Women Lit"]).round(1)
        ld = ld.sort_values("Gap", ascending=False)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Men",   x=ld["State"], y=ld["Men Lit"],   marker_color="#42a5f5"))
        fig.add_trace(go.Bar(name="Women", x=ld["State"], y=ld["Women Lit"], marker_color="#f06292"))
        fig.update_layout(**LAYOUT, barmode="group", xaxis_tickangle=-45,
                          legend=dict(orientation="h"),
                          title="Male vs Female Literacy by State (%)", height=460)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        fig = px.scatter(ld, x="Women Lit", y="Men Lit", text="State",
                         color="Gap", color_continuous_scale="RdBu_r",
                         size=ld["Gap"].abs()+1,
                         trendline="ols", title="Literacy Gap: Men vs Women", height=460)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    sh("Literacy Rankings & Literacy→Internet Correlation", "🏆")
    cl2, cr2 = st.columns(2)
    with cl2:
        rank_l = ld.copy()
        rank_l["Avg Literacy"] = ((rank_l["Women Lit"] + rank_l["Men Lit"]) / 2).round(1)
        rank_l = rank_l.sort_values("Avg Literacy", ascending=False).reset_index(drop=True)
        rank_l.index += 1; rank_l.index.name = "Rank"
        st.markdown("#### Literacy Ranking Table")
        st.dataframe(rank_l[["State","Women Lit","Men Lit","Gap","Avg Literacy"]]
                     .style.background_gradient(cmap="Greens", subset=["Avg Literacy"]),
                     use_container_width=True, height=470)
    with cr2:
        cd = plot_df[["State", COL["women_lit"], COL["women_internet"]]].dropna()
        cd.columns = ["State","Literacy %","Internet Usage %"]
        fig = px.scatter(cd, x="Literacy %", y="Internet Usage %", text="State",
                         trendline="ols", color="Internet Usage %",
                         color_continuous_scale="Viridis",
                         title="Women Literacy vs Internet Usage", height=470)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D5 – SANITATION & PUBLIC HEALTH
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "5":
    sh("Sanitation & Public Health – National KPIs", "🚿")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Improved Toilet (%)", safe_val(india_row[COL["toilet"]]), "Improved sanitation"), unsafe_allow_html=True)
    c2.markdown(kpi("Clean Cooking Fuel (%)", safe_val(india_row[COL["clean_fuel"]]), "Households"), unsafe_allow_html=True)
    c3.markdown(kpi("Improved Water (%)", safe_val(india_row[COL["drinking_water"]]), "Drinking water source"), unsafe_allow_html=True)
    c4.markdown(kpi("Electricity Access (%)", safe_val(india_row[COL["electricity"]]), "Households"), unsafe_allow_html=True)

    sh("Sanitation Scorecard & Heatmap", "🗺️")
    cl, cr = st.columns(2)
    with cl:
        sd = plot_df[["State", COL["toilet"], COL["clean_fuel"],
                      COL["drinking_water"], COL["electricity"]]].dropna()
        sd.columns = ["State","Toilet","Clean Fuel","Water","Electricity"]
        sd["Sanitation Index"] = sd[["Toilet","Clean Fuel","Water","Electricity"]].mean(axis=1).round(1)
        sd = sd.sort_values("Sanitation Index")
        fig = px.bar(sd, x="Sanitation Index", y="State", orientation="h",
                     color="Sanitation Index", color_continuous_scale="Blues",
                     title="Sanitation Index by State", height=600)
        fig.update_layout(**LAYOUT, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        st.plotly_chart(heatmap(plot_df, {
            "Toilet":      COL["toilet"],
            "Clean Fuel":  COL["clean_fuel"],
            "Drinking Water": COL["drinking_water"],
            "Electricity": COL["electricity"],
        }, "Sanitation Indicators Heatmap", "RdYlGn", height=600), use_container_width=True)

    sh("Sanitation → Health Outcome Correlations", "🔬")
    cl2, cr2 = st.columns(2)
    with cl2:
        s1 = plot_df[["State", COL["toilet"], COL["stunted"]]].dropna()
        s1.columns = ["State","Toilet %","Stunting %"]
        fig = px.scatter(s1, x="Toilet %", y="Stunting %", text="State",
                         trendline="ols", color="Stunting %",
                         color_continuous_scale="Reds",
                         title="Toilet Access vs Child Stunting", height=400)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with cr2:
        s2 = plot_df[["State", COL["clean_fuel"], COL["infant_mort"]]].dropna()
        s2.columns = ["State","Clean Fuel %","Infant Mortality"]
        fig = px.scatter(s2, x="Clean Fuel %", y="Infant Mortality", text="State",
                         trendline="ols", color="Infant Mortality",
                         color_continuous_scale="Oranges",
                         title="Clean Fuel vs Infant Mortality", height=400)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    sh("Rural vs Urban Sanitation Gap (India)", "🏘️")
    san_items = {"Toilet (%)": COL["toilet"], "Clean Fuel (%)": COL["clean_fuel"],
                 "Water (%)": COL["drinking_water"], "Electricity (%)": COL["electricity"]}
    r_vals = [float(rural_india[c]) if c and not pd.isna(rural_india[c]) else 0 for c in san_items.values()]
    u_vals = [float(urban_india[c]) if c and not pd.isna(urban_india[c]) else 0 for c in san_items.values()]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Rural", x=list(san_items.keys()), y=r_vals,
                         marker_color="#66bb6a", text=[f"{v:.1f}%" for v in r_vals], textposition="outside"))
    fig.add_trace(go.Bar(name="Urban", x=list(san_items.keys()), y=u_vals,
                         marker_color="#42a5f5", text=[f"{v:.1f}%" for v in u_vals], textposition="outside"))
    fig.update_layout(**LAYOUT, barmode="group",
                      title="Rural vs Urban Sanitation (India National)", height=380,
                      legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D6 – VACCINATION COVERAGE
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "6":
    sh("Vaccination Coverage – National KPIs", "💉")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Full Vaccination (%)", safe_val(india_row[COL["vacc_full"]]), "12-23 months"), unsafe_allow_html=True)
    c2.markdown(kpi("BCG Coverage (%)", safe_val(india_row[COL["bcg"]]), "12-23 months"), unsafe_allow_html=True)
    c3.markdown(kpi("Polio 3 Doses (%)", safe_val(india_row[COL["polio"]]), "12-23 months"), unsafe_allow_html=True)
    c4.markdown(kpi("Measles MCV1 (%)", safe_val(india_row[COL["measles"]]), "12-23 months"), unsafe_allow_html=True)

    sh("Vaccination Progress by State", "📊")
    cl, cr = st.columns(2)
    with cl:
        st.plotly_chart(h_bar(plot_df,"State",COL["vacc_full"],"Full Vaccination Coverage (%)","Greens",600), use_container_width=True)
    with cr:
        vd = plot_df[["State", COL["vacc_full"], COL["bcg"],
                      COL["polio"], COL["measles"], COL["dpt"]]].dropna()
        vd.columns = ["State","Full Vacc","BCG","Polio","Measles","DPT"]
        top5 = vd.sort_values("Full Vacc", ascending=False).head(5)
        bot5 = vd.sort_values("Full Vacc", ascending=True).head(5)
        tb = pd.concat([top5.assign(Group="Best 5"), bot5.assign(Group="Worst 5")])
        tm = tb.melt(["State","Group"], var_name="Vaccine", value_name="Coverage %")
        fig = px.bar(tm, x="State", y="Coverage %", color="Vaccine",
                     barmode="group", facet_col="Group",
                     title="Vaccine Coverage – Best & Worst 5 States", height=500,
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(**LAYOUT, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    sh("National Vaccination Gauges & Heatmap", "📈")
    cl2, cr2 = st.columns(2)
    with cl2:
        val = float(india_row[COL["vacc_full"]])
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=val,
            title={"text":"Full Vaccination – India (%)","font":{"color":"white","size":15}},
            delta={"reference":90,"increasing":{"color":"#66bb6a"},"decreasing":{"color":"#ef5350"}},
            number={"suffix":"%","font":{"color":"white"}},
            gauge={
                "axis":{"range":[0,100],"tickcolor":"white"},
                "bar":{"color":"#42a5f5"},
                "steps":[{"range":[0,50],"color":"#c62828"},
                         {"range":[50,75],"color":"#f9a825"},
                         {"range":[75,100],"color":"#2e7d32"}],
                "threshold":{"line":{"color":"white","width":3},"value":90}
            }
        ))
        fig.update_layout(height=330, paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

        # Low-performing alert
        low = plot_df[["State", COL["vacc_full"]]].dropna()
        low.columns = ["State","Full Vacc %"]
        low = low[low["Full Vacc %"] < 75].sort_values("Full Vacc %")
        if not low.empty:
            st.warning(f"⚠️ **{len(low)} states** below 75% full vaccination!")
            st.dataframe(low, use_container_width=True, hide_index=True)
        else:
            st.success("✅ All states ≥ 75% full vaccination!")

    with cr2:
        vd2 = plot_df[["State", COL["bcg"], COL["polio"],
                       COL["measles"], COL["dpt"], COL["vacc_full"]]].dropna()
        vd2.columns = ["State","BCG","Polio","Measles","DPT","Full Vacc"]
        heat_v = vd2.set_index("State")
        fig = px.imshow(heat_v, aspect="auto", color_continuous_scale="YlGn",
                        title="Vaccination Coverage Heatmap", height=520)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D7 – LIFESTYLE & HEALTH RISK
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "7":
    sh("Lifestyle & Health Risk – National KPIs", "⚠️")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Tobacco – Women (%)", safe_val(india_row[COL["tobacco_w"]]), "Age 15+"), unsafe_allow_html=True)
    c2.markdown(kpi("Tobacco – Men (%)", safe_val(india_row[COL["tobacco_m"]]), "Age 15+"), unsafe_allow_html=True)
    c3.markdown(kpi("Alcohol – Women (%)", safe_val(india_row[COL["alcohol_w"]]), "Age 15+"), unsafe_allow_html=True)
    c4.markdown(kpi("Alcohol – Men (%)", safe_val(india_row[COL["alcohol_m"]]), "Age 15+"), unsafe_allow_html=True)

    sh("Consumption Comparison by State", "📊")
    cl, cr = st.columns(2)
    with cl:
        rd = plot_df[["State", COL["tobacco_w"], COL["tobacco_m"],
                      COL["alcohol_w"], COL["alcohol_m"]]].dropna()
        rd.columns = ["State","Tobacco W","Tobacco M","Alcohol W","Alcohol M"]
        rd = rd.sort_values("Tobacco M", ascending=False)
        fig = go.Figure()
        pairs = [("Tobacco M","#ef5350"),("Tobacco W","#f48fb1"),
                 ("Alcohol M","#7e57c2"),("Alcohol W","#ce93d8")]
        for col_n, clr in pairs:
            fig.add_trace(go.Bar(name=col_n, x=rd["State"], y=rd[col_n], marker_color=clr))
        fig.update_layout(**LAYOUT, barmode="group", xaxis_tickangle=-45,
                          legend=dict(orientation="h"),
                          title="Tobacco & Alcohol Use by State (%)", height=480)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        avg = rd[["Tobacco W","Tobacco M","Alcohol W","Alcohol M"]].mean()
        fig = go.Figure(go.Pie(
            labels=avg.index, values=avg.values.round(2),
            hole=0.45,
            marker=dict(colors=["#f48fb1","#ef5350","#ce93d8","#7e57c2"])
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                          title="Average Consumption Mix (National)", height=480)
        st.plotly_chart(fig, use_container_width=True)

    sh("Risk Indicators – Trend & Correlation", "🔗")
    cl2, cr2 = st.columns(2)
    with cl2:
        rl = plot_df[["State", COL["tobacco_m"], COL["men_lit"]]].dropna()
        rl.columns = ["State","Tobacco Men %","Men Literacy %"]
        fig = px.scatter(rl, x="Men Literacy %", y="Tobacco Men %", text="State",
                         trendline="ols", color="Tobacco Men %", color_continuous_scale="Reds",
                         title="Male Literacy vs Tobacco Use", height=400)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with cr2:
        ra = plot_df[["State", COL["alcohol_m"], COL["men_lit"]]].dropna()
        ra.columns = ["State","Alcohol Men %","Men Literacy %"]
        fig = px.scatter(ra, x="Men Literacy %", y="Alcohol Men %", text="State",
                         trendline="ols", color="Alcohol Men %", color_continuous_scale="Purples",
                         title="Male Literacy vs Alcohol Use", height=400)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    sh("Risk Indicator Dashboard – Top Affected States", "🏴")
    cl3, cr3 = st.columns(2)
    with cl3:
        top_tob = rd.nlargest(10,"Tobacco M")[["State","Tobacco M","Tobacco W"]]
        fig = px.bar(top_tob.melt("State"), x="value", y="State", color="variable",
                     orientation="h", title="Top 10 States – Tobacco Use (%)",
                     color_discrete_map={"Tobacco M":"#ef5350","Tobacco W":"#f48fb1"},
                     height=400)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with cr3:
        top_alc = rd.nlargest(10,"Alcohol M")[["State","Alcohol M","Alcohol W"]]
        fig = px.bar(top_alc.melt("State"), x="value", y="State", color="variable",
                     orientation="h", title="Top 10 States – Alcohol Use (%)",
                     color_discrete_map={"Alcohol M":"#7e57c2","Alcohol W":"#ce93d8"},
                     height=400)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D8 – RURAL vs URBAN
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "8":
    sh("Rural vs Urban Development – National KPIs (India)", "🏘️")

    def ru(row, col):
        try:
            return float(row[col]) if col else None
        except:
            return None

    compare = {
        "Institutional Births": (ru(rural_india, COL["inst_birth"]),  ru(urban_india, COL["inst_birth"])),
        "Women Literacy":        (ru(rural_india, COL["women_lit"]),   ru(urban_india, COL["women_lit"])),
        "Toilet Facility":       (ru(rural_india, COL["toilet"]),      ru(urban_india, COL["toilet"])),
        "Women Internet":        (ru(rural_india, COL["women_internet"]),ru(urban_india, COL["women_internet"])),
        "Bank Account":          (ru(rural_india, COL["bank_account"]),ru(urban_india, COL["bank_account"])),
        "Clean Fuel":            (ru(rural_india, COL["clean_fuel"]),  ru(urban_india, COL["clean_fuel"])),
        "Full Vaccination":      (ru(rural_india, COL["vacc_full"]),   ru(urban_india, COL["vacc_full"])),
        "Mobile Phone (W)":      (ru(rural_india, COL["mobile_phone"]),ru(urban_india, COL["mobile_phone"])),
    }

    cols_kpi = st.columns(4)
    for i, (label, (rv, uv)) in enumerate(list(compare.items())[:4]):
        diff = (uv or 0) - (rv or 0)
        cols_kpi[i].markdown(kpi(label,
            f"R:{safe_val(rv)} | U:{safe_val(uv)}",
            f"Urban leads by +{diff:.1f}%"), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    cols_kpi2 = st.columns(4)
    for i, (label, (rv, uv)) in enumerate(list(compare.items())[4:]):
        diff = (uv or 0) - (rv or 0)
        cols_kpi2[i].markdown(kpi(label,
            f"R:{safe_val(rv)} | U:{safe_val(uv)}",
            f"Urban leads by +{diff:.1f}%"), unsafe_allow_html=True)

    sh("Clustered Column Chart – Rural vs Urban", "📊")
    labels_ = list(compare.keys())
    rv_list = [v[0] for v in compare.values()]
    uv_list = [v[1] for v in compare.values()]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Rural", x=labels_, y=rv_list, marker_color="#66bb6a",
                         text=[f"{v:.1f}%" if v else "" for v in rv_list], textposition="outside"))
    fig.add_trace(go.Bar(name="Urban", x=labels_, y=uv_list, marker_color="#42a5f5",
                         text=[f"{v:.1f}%" if v else "" for v in uv_list], textposition="outside"))
    fig.update_layout(**LAYOUT, barmode="group", legend=dict(orientation="h"),
                      title="Rural vs Urban – Key Development Indicators (India)", height=460)
    st.plotly_chart(fig, use_container_width=True)

    sh("Urban-Rural Gap Analysis", "📐")
    gap_df = pd.DataFrame({
        "Indicator": labels_,
        "Rural": rv_list,
        "Urban": uv_list
    }).dropna()
    gap_df["Gap"] = (gap_df["Urban"] - gap_df["Rural"]).round(1)
    gap_df = gap_df.sort_values("Gap", ascending=False)
    cl, cr = st.columns(2)
    with cl:
        fig = px.bar(gap_df, x="Gap", y="Indicator", orientation="h",
                     color="Gap", color_continuous_scale="RdYlGn",
                     title="Urban–Rural Gap (Urban Advantage)", height=400)
        fig.update_layout(**LAYOUT, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        # Difference chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=gap_df["Indicator"], y=gap_df["Rural"],
                                 mode="markers+lines", name="Rural", marker=dict(color="#66bb6a", size=10)))
        fig.add_trace(go.Scatter(x=gap_df["Indicator"], y=gap_df["Urban"],
                                 mode="markers+lines", name="Urban", marker=dict(color="#42a5f5", size=10)))
        for _, row in gap_df.iterrows():
            fig.add_shape(type="line",
                          x0=row["Indicator"], x1=row["Indicator"],
                          y0=row["Rural"], y1=row["Urban"],
                          line=dict(color="grey", width=1.5, dash="dot"))
        fig.update_layout(**LAYOUT, title="Dumbbell: Rural vs Urban (%)", height=400,
                          xaxis_tickangle=-30, legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D9 – SOCIAL DEVELOPMENT INDEX
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "9":
    sh("Overall Social Development Index – Composite Score", "🌟")

    raw = plot_df[["State",
                   COL["women_lit"], COL["women_internet"],
                   COL["inst_birth"], COL["vacc_full"], COL["infant_mort"],
                   COL["bank_account"],
                   COL["stunted"],
                   COL["toilet"], COL["clean_fuel"],
                   ]].dropna().copy()
    raw.columns = ["State","WomenLit","WomenNet","InstBirth","Vacc","InfMort",
                   "BankAcc","Stunted","Toilet","CleanFuel"]

    raw["Edu Score"]    = (raw["WomenLit"]*0.6 + raw["WomenNet"]*0.4).round(1)
    raw["Health Score"] = (raw["InstBirth"]*0.4 + raw["Vacc"]*0.3 + (100-raw["InfMort"])*0.3).round(1)
    raw["Emp Score"]    = (raw["BankAcc"]*0.5 + raw["WomenNet"]*0.5).round(1)
    raw["Nutr Score"]   = (100 - raw["Stunted"]).round(1)
    raw["San Score"]    = (raw["Toilet"]*0.5 + raw["CleanFuel"]*0.5).round(1)
    raw["SDI"]          = (raw["Edu Score"]*0.20 + raw["Health Score"]*0.25 +
                           raw["Emp Score"]*0.20 + raw["Nutr Score"]*0.15 +
                           raw["San Score"]*0.20).round(1)
    raw = raw.sort_values("SDI", ascending=False).reset_index(drop=True)
    raw.index += 1; raw.index.name = "Rank"

    cl, cr = st.columns([3, 2])
    with cl:
        fig = px.bar(raw.reset_index(), x="SDI", y="State", orientation="h",
                     color="SDI", color_continuous_scale="RdYlGn",
                     title="🌟 Social Development Index by State (0–100)", height=680)
        fig.update_layout(**LAYOUT, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        st.markdown("#### 🥇 Top 5 States")
        st.dataframe(raw.head(5)[["State","SDI"]], use_container_width=True, hide_index=True)
        st.markdown("#### ⚠️ Bottom 5 States")
        st.dataframe(raw.tail(5)[["State","SDI"]], use_container_width=True, hide_index=True)

        dims = ["Edu Score","Health Score","Emp Score","Nutr Score","San Score"]
        fig_r = go.Figure()
        colours = ["#42a5f5","#66bb6a","#ffa726"]
        for i, (_, row) in enumerate(raw.head(3).iterrows()):
            vals = [row[d] for d in dims] + [row[dims[0]]]
            fig_r.add_trace(go.Scatterpolar(r=vals, theta=dims+[dims[0]],
                                            fill="toself", name=row["State"],
                                            line=dict(color=colours[i])))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            title="Top 3 States – Radar Chart", height=360,
            paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=True)
        st.plotly_chart(fig_r, use_container_width=True)

    sh("Full State Scorecard", "📋")
    disp = raw.reset_index()[["Rank","State","Edu Score","Health Score","Emp Score",
                               "Nutr Score","San Score","SDI"]]
    st.dataframe(disp.style.background_gradient(cmap="RdYlGn", subset=["SDI"]),
                 use_container_width=True, height=520)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ══════════════════════════════════════════════════════════════════════════════
# D10 – DIGITAL AWARENESS
# ══════════════════════════════════════════════════════════════════════════════
elif d_num == "🔟":
    sh("Digital Awareness & Social Development – National KPIs", "💻")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("Women Internet (%)", safe_val(india_row[COL["women_internet"]]), "Ever used"), unsafe_allow_html=True)
    c2.markdown(kpi("Men Internet (%)", safe_val(india_row[COL["men_internet"]]), "Ever used"), unsafe_allow_html=True)
    c3.markdown(kpi("Women Mobile Phone (%)", safe_val(india_row[COL["mobile_phone"]]), "Own/use"), unsafe_allow_html=True)
    c4.markdown(kpi("Bank Account (%)", safe_val(india_row[COL["bank_account"]]), "Women self-use"), unsafe_allow_html=True)

    sh("Digital Access by State", "🗺️")
    cl, cr = st.columns(2)
    with cl:
        dd = plot_df[["State", COL["women_internet"], COL["men_internet"], COL["mobile_phone"]]].dropna()
        dd.columns = ["State","Women Internet","Men Internet","Mobile Phone (W)"]
        dd = dd.sort_values("Women Internet", ascending=False)
        fig = go.Figure()
        for col_n, clr in [("Men Internet","#42a5f5"),("Women Internet","#f06292"),("Mobile Phone (W)","#66bb6a")]:
            fig.add_trace(go.Bar(name=col_n, x=dd["State"], y=dd[col_n], marker_color=clr))
        fig.update_layout(**LAYOUT, barmode="group", xaxis_tickangle=-45,
                          legend=dict(orientation="h"),
                          title="Digital Access by State (%)", height=480)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        dd["Digital Gender Gap"] = (dd["Men Internet"] - dd["Women Internet"]).round(1)
        dg = dd.sort_values("Digital Gender Gap", ascending=False)
        fig = px.bar(dg, x="Digital Gender Gap", y="State", orientation="h",
                     color="Digital Gender Gap", color_continuous_scale="RdYlGn_r",
                     title="Digital Gender Gap: Men – Women Internet (%)", height=480)
        fig.update_layout(**LAYOUT, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    sh("Digital Awareness → Social Outcome Correlations", "🔗")
    cl2, cr2 = st.columns(2)
    with cl2:
        s1 = plot_df[["State", COL["women_internet"], COL["bank_account"]]].dropna()
        s1.columns = ["State","Internet %","Bank Account %"]
        fig = px.scatter(s1, x="Internet %", y="Bank Account %", text="State",
                         trendline="ols", color="Bank Account %", color_continuous_scale="Viridis",
                         title="Women Internet → Bank Account Ownership", height=420)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with cr2:
        s2 = plot_df[["State", COL["women_internet"], COL["inst_birth"]]].dropna()
        s2.columns = ["State","Internet %","Institutional Births %"]
        fig = px.scatter(s2, x="Internet %", y="Institutional Births %", text="State",
                         trendline="ols", color="Institutional Births %", color_continuous_scale="Blues",
                         title="Women Internet → Institutional Births", height=420)
        fig.update_traces(textposition="top center", textfont_size=8)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    sh("Digital Score Ranking – Top vs Bottom States", "🏆")
    dr = plot_df[["State", COL["women_internet"], COL["men_internet"],
                  COL["mobile_phone"], COL["bank_account"]]].dropna().copy()
    dr.columns = ["State","Women Net","Men Net","Mobile","Bank"]
    dr["Digital Score"] = (dr["Women Net"]*0.35 + dr["Men Net"]*0.25 +
                           dr["Mobile"]*0.2 + dr["Bank"]*0.2).round(1)
    dr = dr.sort_values("Digital Score", ascending=False)

    cl3, cr3 = st.columns(2)
    with cl3:
        top5d = dr.head(5).assign(Group="Top 5")
        bot5d = dr.tail(5).assign(Group="Bottom 5")
        tb_d = pd.concat([top5d, bot5d])
        fig = px.bar(tb_d, x="Digital Score", y="State", color="Group", orientation="h",
                     color_discrete_map={"Top 5":"#42a5f5","Bottom 5":"#ef5350"},
                     title="Top 5 vs Bottom 5 – Digital Score", height=400)
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with cr3:
        dr_rank = dr.reset_index(drop=True)
        dr_rank.index += 1; dr_rank.index.name = "Rank"
        st.markdown("#### Digital Score Ranking Table")
        st.dataframe(dr_rank[["State","Women Net","Men Net","Mobile","Bank","Digital Score"]]
                     .style.background_gradient(cmap="Blues", subset=["Digital Score"]),
                     use_container_width=True, height=400)

    if user_note:
        st.info(f"📝 **Your Analysis:** {user_note}")


# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#546e7a;font-size:0.78rem;'>"
    "📊 NFHS-5 Multi-Dashboard | Data: National Family Health Survey 5 (2019–21) | "
    "Ministry of Health & Family Welfare, Government of India"
    "</div>", unsafe_allow_html=True
)
