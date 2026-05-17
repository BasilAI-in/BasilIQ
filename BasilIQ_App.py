import streamlit as st
import pandas as pd
import os

from dotenv import load_dotenv

from openai import OpenAI

st.set_page_config(layout="wide")

# ===== COMPACT UI =====
st.markdown("""
<style>

/* ===== FIX TOP SPACING ===== */
.block-container {
    padding-top: 2.5rem !important;   /* increased */
    padding-bottom: 0rem;
}

/* Prevent title clipping */
h1, h2, h3 {
    margin-top: 0.4rem !important;
    margin-bottom: 0.2rem !important;
}

/* Optional: slightly reduce title size so it fits nicely */
h2 {
    font-size: 24px !important;
}

/* KPI CARDS */
.kpi-card {
    padding:6px;
    border-radius:6px;
    text-align:center;
    background:#f8fff8;
    line-height:1.1;
}

.kpi-title {
    font-size:10px;
    color:gray;
}

.kpi-value {
    font-size:14px;
    font-weight:bold;
}

/* Compact text */
.small-text {
    font-size:11px;
}

</style>
""", unsafe_allow_html=True)

# ===== USER =====
current_user = {
    "name": "Test User",
    "company_name": "ABC Manufacturing",
    "plan": "premium"
}

if "ai_usage" not in st.session_state:
    st.session_state.ai_usage = 0

ai_limit = {"free":100,"starter":5,"premium":1000}

# ===== SIDEBAR =====
st.sidebar.title("🌿 BasilIQ")
st.sidebar.write(current_user["name"])
st.sidebar.write(current_user["company_name"])
st.sidebar.write(f"Plan: {current_user['plan']}")
st.sidebar.write(f"AI Used: {st.session_state.ai_usage}/{ai_limit[current_user['plan']]}")

# ===== MAIN HEADER =====
st.markdown("""
<div style="line-height:1.3;">
    <div style="font-size:26px; font-weight:700;">
        🌿 BasilIQ - Sales Intelligence
    </div>
    <div style="height:4px;"></div>
    <div style="font-size:12px; color:#6c757d;">
        Grow a healthier business with BasilIQ.
    </div>
</div>
""", unsafe_allow_html=True)

# SPACE AFTER HEADER (before uploader)
st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

load_dotenv()

print(os.getenv("OPENAI_API_KEY"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.info("🌿 BasilIQ Beta: We’re continuously improving the platform. Usage may be limited during testing. Feedback is welcome at admin@basilai.in")

st.write("Download the sample format and upload your data")

# Download button
with open("BasilIQ_Sample_Template.xlsx", "rb") as file:
    st.download_button(
        label="📥 Download Sample Excel",
        data=file,
        file_name="BasilIQ_Sample_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
file = st.file_uploader("Upload File", type=["csv","xlsx"])

st.success("🔒 Your data is secure. Files are not stored after analysis.")

if file:

    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

    df.columns = df.columns.str.strip().str.lower().str.replace(" ","_")

    df["date"] = pd.to_datetime(df["date"])
    df["sales_value"] = df["qty"] * df["unit_price"]

    # ===== KPIs =====
    total_sales = df["sales_value"].sum()

    invoice_col = next((c for c in df.columns if c in ["invoice_no","order_id","bill_no"]), None)
    total_orders = df[invoice_col].nunique() if invoice_col else len(df)

    total_revenue = (df["qty"] * df["unit_price"]).sum()
    
    df["Profit"] = (df["unit_price"] - df["cost"]) * df["qty"]
    total_profit = df["Profit"].sum()

    margin_pct = (total_profit / total_sales) * 100

    avg_order = total_sales / total_orders
    active_days = df["date"].nunique()
    daily_avg = total_sales / active_days

    from_date = df["date"].min()
    to_date = df["date"].max()

    # ===== PERIOD =====
    df["period"] = df["date"].dt.to_period("M")
    ps = df.groupby("period")["sales_value"].sum().sort_index()

    growth = 0
    if len(ps)>1:
        growth = ((ps.iloc[-1]-ps.iloc[-2])/ps.iloc[-2])*100 if ps.iloc[-2]!=0 else 0

    # ===== PRODUCTS =====
    prod = df.groupby("product")["sales_value"].sum().sort_values(ascending=False)

    top_product = prod.index[0]
    top_pct = (prod.iloc[0]/total_sales)*100
    top3_pct = (prod.head(3).sum()/total_sales)*100

    top3_names = ", ".join(prod.head(3).index)
    bottom3_names = ", ".join(prod.tail(3).index)

    # ===== HEALTH =====
    std_pct = (ps.std()/ps.mean())*100 if ps.mean()!=0 else 0

    health = max(0,min(100,(growth*2)+(30-top_pct)+(30-std_pct)))


    # ===== MAIN GRID =====
    left, right = st.columns([2.2,1])

    # ===== CHART =====
    with left:
    # ===== KPI ROW =====
        def card(t,v):
            return f"<div class='kpi-card'><div class='kpi-title'>{t}</div><div class='kpi-value'>{v}</div></div>"
        
        def CardForHealth(title, value, bg="#f8fff8", color="#000"):
            return f"""
            <div style="
                padding:6px;
                border-radius:6px;
                text-align:center;
                background:{bg};
                line-height:1.1;
            ">
                <div style="font-size:10px; color:gray;">{title}</div>
                <div style="font-size:14px; font-weight:bold; color:{color};">
                    {value}
                </div>
            </div>
            """

        if health >= 75:
            health_bg = "#d4edda"   # green
            health_icon = "🟢"
        elif health >= 50:
            health_bg = "#fff3cd"   # yellow
            health_icon = "🟡"
        else:
            health_bg = "#f8d7da"   # red
            health_icon = "🔴"

        cols0 = st.columns(2)
        cols0[0].markdown(f"""
        <div style="
            padding:8px;
            border-radius:8px;
            text-align:center;
            background:{health_bg};
        ">
            <div style="font-size:16px; color:black;">
                Business Health Score: {health_icon} {health:.0f} / 100
            </div>
        </div>
        """, unsafe_allow_html=True)

        cols0[1].markdown(f"""**Period:** {from_date.strftime('%d %b %Y')} → {to_date.strftime('%d %b %Y')}""")

        cols = st.columns(3)

        cols[0].markdown(card("Total Revenue",f"₹{total_revenue:,.0f}"),True)
        cols[1].markdown(card("Total Profit",f"₹{total_profit:,.0f}"),True)
        cols[2].markdown(card("Margin % ",f"₹{margin_pct:,.0f}"),True)

        cols1 = st.columns(3)

        cols1[0].markdown(card("# of Orders",total_orders),True)
        cols1[1].markdown(card("Avg Sales/Order",f"₹{avg_order:,.0f}"),True)
        cols1[2].markdown(card("Avg Sales/Day",f"₹{daily_avg:,.0f}"),True)

        st.markdown("### 📈 Sales Trend")
        chart = ps.copy()
        chart.index = chart.index.astype(str)
        st.line_chart(chart, height=260)

    # ===== RIGHT PANEL =====
    with right:

        st.markdown("### 📦 Products Insights")
        st.markdown(f"<div class='small-text'><b>Top 3 Products:</b> {top3_names}</div>", True)
        st.markdown(f"<div class='small-text'><b>Bottom 3 Products:</b> {bottom3_names}</div>", True)
        st.markdown(f"<div class='small-text'><b>Top 3 Products %:</b> {top_pct}</div>", True)
        st.markdown(f"<div class='small-text'><b>Top 3 Products Contribution:</b> {top3_pct}</div>", True)

        #st.markdown(card("Top 3 Product %",f"{top_pct:.1f}%"),True)
        #st.markdown(card("Top 3 Contribution %",f"{top3_pct:.1f}%"),True)
        #st.markdown(card("Days",active_days),True)

        st.markdown("---")

        st.markdown("### 🧠 Actions")

        insights = []
        if growth > 10:
            insights.append(f"Sales up {growth:.1f}%")
        elif growth < -10:
            insights.append(f"Sales down {abs(growth):.1f}%")

        for i in insights:
            st.markdown(f"<div class='small-text'>• {i}</div>", True)

        st.markdown("---")

    # ===== AI =====
    summary_data = f"""
    Total Sales: {total_sales}
    Total Orders: {total_orders}
    Growth: {growth:.2f}%
    Top Product: {top_product}
    """

    prompt = f"""
    Analyze the business performance.

    {summary_data}

    Respond STRICTLY in this format:

    Key Problem: <one short line>
    Opportunity: <one short line>
    Actions:
    - High: <most important action>
    - Medium: <next action>
    - Low: <least priority action>
    Risk: <what happens if not fixed>
    Impact: <benefit if actions are taken>

    Rules:
    - No markdown symbols like **
    - Keep each line under 12 words
    - Be specific and practical
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a business expert."},
            {"role": "user", "content": prompt}
        ]
    )

    txt = response.choices[0].message.content

    key_problem, opportunity = "", ""
    high_action, medium_action, low_action = "", "", ""
    risk, impact = "", ""

    for line in txt.split("\n"):
        l = line.lower()

        if "problem" in l:
            key_problem = line.split(":",1)[-1].strip()

        elif "opportunity" in l:
            opportunity = line.split(":",1)[-1].strip()

        elif "high" in l:
            high_action = line.split(":",1)[-1].strip()

        elif "medium" in l:
            medium_action = line.split(":",1)[-1].strip()

        elif "low" in l:
            low_action = line.split(":",1)[-1].strip()

        elif "risk" in l:
            risk = line.split(":",1)[-1].strip()

        elif "impact" in l:
            impact = line.split(":",1)[-1].strip()

        if not high_action:
            high_action = "Improve declining sales immediately"

        if not medium_action:
            medium_action = "Focus on top-performing products"

        if not low_action:
            low_action = "Optimize pricing strategy"
    
    st.info("🌿 AI-Powered Business Insights")
    st.caption("AI-generated recommendations based on uploaded sales data.")
    
    c1, c2, c3 = st.columns(3)

    # Column 1
    c1.write("**Key Problem**")
    c1.write(key_problem)

    c1.write("**Opportunity**")
    c1.write(opportunity)

    # Column 2 (Actions)
    c2.write("**🔴 High Priority**")
    c2.write(high_action)

    c2.write("**🟡 Medium Priority**")
    c2.write(medium_action)

    c2.write("**🟢 Low Priority**")
    c2.write(low_action)

    # Column 3 (Risk & Impact)
    c3.write("**⚠️ Risk**")
    c3.write(risk)

    c3.write("**📈 Impact**")
    c3.write(impact)

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

st.markdown("For queries or support: Admin@basilai.in")

with st.expander("📘 BasilIQ User Manual & KPI Logic"):

    st.markdown("""

## 🌿 BasilIQ User Manual

### 📌 About BasilIQ

BasilIQ is an AI-powered Sales Intelligence platform designed to help businesses analyze sales data, monitor business performance, identify risks, and generate actionable recommendations using AI.

The platform converts raw Excel sales data into meaningful business insights including:

- Revenue analysis
- Profitability analysis
- Product performance
- Sales trends
- Business Health Score
- AI-generated insights & actions

---

## 📥 Supported Input File Format

Upload Excel file (.xlsx) containing sales transaction data.

### Recommended Columns

| Column | Description |
|---|---|
| Date | Transaction / Order Date |
| Product | Product Name |
| Quantity | Units Sold |
| Revenue / Sales | Sales Value |
| Cost | Product Cost (Optional) |
| Invoice Number | Unique Order Number (Optional) |

---

## ⚠️ Important Rules

- One row should represent one transaction
- Date format should be consistent
- Revenue values should be numeric
- Avoid blank rows and merged cells
- Cost column is required for Profit & Margin analysis

---

## 📊 KPI Definitions & Calculation Logic

---

### 💰 Revenue

Represents total sales value generated.

#### Formula

Revenue = Sum of all Sales Values

---

### 📦 Total Orders

Represents total number of orders.

#### Logic

- If Invoice Number exists:
    Count unique invoices

- Otherwise:
    Count total rows

---

### 💵 Average Order Value

Average revenue generated per order.

#### Formula

Average Order Value =
Revenue / Total Orders

---

### 📈 Daily Average Sales

Average sales generated per active day.

#### Formula

Daily Average Sales =
Revenue / Active Days

---

### 💰 Total Profit

Represents earnings after deducting cost.

#### Formula

Profit =
Revenue - Cost

Total Profit =
Sum of all profits

---

### 📊 Margin %

Represents profitability percentage.

#### Formula

Margin % =
(Total Profit / Revenue) × 100

---

### 🥇 Top Product Contribution %

Shows dependency on highest-selling product.

#### Formula

Top Product % =
(Top Product Revenue / Total Revenue) × 100

#### Interpretation

- Higher percentage = higher dependency risk
- Lower percentage = healthier distribution

---

### 🏆 Top 3 Contribution %

Shows revenue concentration among top 3 products.

#### Formula

Top 3 Contribution % =
(Top 3 Products Revenue / Total Revenue) × 100

#### Interpretation

| Contribution % | Meaning |
|---|---|
| >60% | High Dependency Risk |
| 40–60% | Moderate Risk |
| <40% | Healthy Diversification |

---

## 📈 Sales Trend Analysis

BasilIQ automatically analyzes sales trends over time.

#### Time Grouping Logic

- Short duration → Monthly trend
- Medium duration → Quarterly trend
- Long duration → Yearly trend

---

### 📉 Sales Growth %

Measures latest period performance compared to previous period.

#### Formula

Sales Growth % =
((Current Period Revenue - Previous Period Revenue)
 / Previous Period Revenue) × 100

---

### 📌 Growth Interpretation

| Growth % | Meaning |
|---|---|
| Positive | Sales Up |
| Negative | Sales Down |
| Zero | Stable |

---

## 🧠 Business Health Score (0–100)

Business Health Score is BasilIQ’s overall business performance indicator.

The score combines:

- Sales Growth
- Product Dependency
- Sales Stability

---

### 1️⃣ Growth Score (40 Points)

Measures sales growth trend.

#### Logic

- Positive growth increases score
- Negative growth reduces score

---

### 2️⃣ Dependency Score (30 Points)

Measures dependency on few products.

#### Logic

- Lower dependency = higher score
- Higher dependency = lower score

---

### 3️⃣ Consistency Score (30 Points)

Measures stability of sales performance.

#### Logic

- Stable sales = higher score
- Highly fluctuating sales = lower score

---

### 📌 Final Formula

Business Health Score =
Growth Score +
Dependency Score +
Consistency Score

Final score is normalized between 0–100.

---

## 🚨 Business Health Score Interpretation

| Score | Interpretation |
|---|---|
| 75–100 | Healthy Business |
| 50–74 | Moderate Risk |
| Below 50 | Business Needs Attention |

---

## 📦 Product Insights

BasilIQ identifies:

- Top Performing Products
- Low Performing Products
- Product Dependency Risks
- Revenue Concentration

---

## 🧠 AI Insights

AI-generated recommendations help identify:

- Key Problems
- Growth Opportunities
- Business Risks
- Suggested Actions

---

## ⚡ Actions Logic

Actions are generated based on KPI performance and trend analysis.

---

### 📉 Sales Down Action

Triggered when latest period sales are lower than previous period.

### Formula

Sales Change % =
((Current Period Revenue - Previous Period Revenue)
 / Previous Period Revenue) × 100

#### Example Output

- "Sales down by 11.5%"
- "Review weak-performing products"
- "Increase sales & marketing activities"

---

### 📈 Sales Up Action

Triggered when latest period sales are higher than previous period.

#### Example Output

- "Sales increased by 18.2%"
- "Focus on scaling top-performing products"
- "Maintain growth momentum"

---

### ⚠️ High Dependency Risk Action

Triggered when Top 3 Contribution % is very high.

#### Example Output

- "Business heavily depends on few products"
- "Diversify product portfolio"

---

### 💰 Low Margin Action

Triggered when Margin % is low.

#### Example Output

- "Profitability is weak"
- "Review pricing and cost structure"

---

## ⚠️ Important Notes

- Better data quality improves insight accuracy
- Profit analysis requires Cost data
- AI insights are recommendation-based
- This is currently a beta version

---

## 💬 Feedback & Support

For feedback, suggestions, or support:

📧 admin@basilai.in

🌿 https://basilai.in

    """)

