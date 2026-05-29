import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db.connection import engine

if not st.session_state.get("logged_in"):
    st.switch_page("pages/0_Login.py")
    st.stop()

admin_id=st.session_state["admin_id"]
business_name = st.session_state["business_name"]
username      = st.session_state["username"]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
* { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #f8f9fb; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none !important; }
 
[data-testid="stSidebar"] {
    background-color: #0f0f0f !important;
    border-right: 1px solid #1a1a1a;
}
[data-testid="stSidebar"] * { color: #9ca3af !important; }
[data-testid="stSidebarContent"] .stButton > button {
    background:#161616 !important;border:1px solid #222 !important;
    color:#6b7280 !important;border-radius:8px !important;
    font-size:13px !important;width:100% !important;
    padding:9px 14px !important;transition:all 0.2s !important;
}
[data-testid="stSidebarContent"] .stButton > button:hover {
    border-color:#6366f1 !important;color:#6366f1 !important;
}
[data-testid="stSidebar"] a {
    color:#6b7280 !important;font-size:13px !important;
    text-decoration:none !important;display:block !important;
    padding:8px 12px !important;border-radius:8px !important;
    transition:all 0.2s !important;margin-bottom:2px !important;
}
[data-testid="stSidebar"] a:hover {
    color:#6366f1 !important;background:#161616 !important;
}
.page-title {
    font-size:22px;font-weight:600;color:#111827;
    letter-spacing:-0.5px;margin:0 0 4px;
}
.page-sub { font-size:13px;color:#6b7280;margin:0 0 8px; }
.section-label {
    font-size:11px;font-weight:500;color:#9ca3af;
    text-transform:uppercase;letter-spacing:0.8px;
    margin:24px 0 12px;
}
.sql-tag {
    display:inline-block;background:#ecfdf5;
    border:1px solid #a7f3d0;border-radius:4px;
    padding:2px 8px;font-size:11px;color:#065f46;
    font-weight:500;margin-left:8px;vertical-align:middle;
}
[data-testid="metric-container"] {
    background:white !important;border:1px solid #f3f4f6 !important;
    border-radius:12px !important;padding:18px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricLabel"] {
    font-size:12px !important;color:#6b7280 !important;
    font-weight:400 !important;
}
[data-testid="stMetricValue"] {
    font-size:24px !important;font-weight:600 !important;
    color:#111827 !important;
}
[data-testid="stDataFrame"] {
    border-radius:10px !important;
    border:1px solid #f3f4f6 !important;
    overflow:hidden !important;
}
.stSelectbox > div > div {
    background:white !important;border:1px solid #e5e7eb !important;
    border-radius:8px !important;font-size:13px !important;
}
.stAlert { border-radius:8px !important;font-size:13px !important; }
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown(f"""
    <div style="padding:20px 4px 16px">
        <div style="display:flex;align-items:center;gap:10px;
                    margin-bottom:14px">
            <div style="width:36px;height:36px;
                        background:linear-gradient(135deg,#6366f1,#10b981);
                        border-radius:9px;display:flex;
                        align-items:center;justify-content:center;
                        font-size:16px">📊</div>
            <div>
                <div style="font-size:13px;font-weight:500;
                            color:#e5e5e5">{business_name}</div>
                <div style="font-size:11px;color:#4b5563;
                            margin-top:1px">@{username}</div>
            </div>
        </div>
        <div style="height:1px;background:#1a1a1a;
                    margin-bottom:14px"></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px;color:#374151;text-transform:uppercase;
                letter-spacing:0.8px;font-weight:500;padding:0 4px;
                margin-bottom:6px">Menu</div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Upload_Data.py",   label="📂  Upload Data")
    st.page_link("pages/3_Dashboard.py",     label="📊  Dashboard")
    st.page_link("pages/4_Ask_AI.py",        label="🤖  Ask AI")
    st.page_link("pages/5_Upload_History.py",label="📋  Upload History")
    st.markdown("""
    <div style="height:1px;background:#1a1a1a;margin:14px 0"></div>
    """, unsafe_allow_html=True)
    if st.button("← Sign out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/0_Login.py")

st.markdown("""
<p class="page-title">Dashboard
    <span class="sql-tag">SQL powered</span>
</p>
<p class="page-sub">All metrics calculated directly in MySQL</p>
""", unsafe_allow_html=True)

today=pd.Timestamp.today()
col_f1,col_f2=st.columns([2,4])
with col_f1:
    period=st.selectbox(
        "period",
        ["This Month","Last Month",
         "This Year","All Time","Custom Range"],
         index=0,label_visibility="collapsed"
    )

if period=="This Month":
    start=today.replace(day=1); end=today
elif period=="Last Month":
    start=(today.replace(day=1)-pd.Timedelta(days=1)).replace(day=1)
    end=today.replace(day=1)-pd.Timedelta(days=1)
elif period=="This Year":
    start=today.replace(month=1,day=1); end=today
elif period=="All Time":
    start=pd.Timestamp("2000-01-01"); end=today
else:
    with col_f2:
        c1,c2=st.columns(2)
        start=pd.Timestamp(c1.date_input("From",today.replace(day=1)))
        end=pd.Timestamp(c2.date_input("To",today))

p=(admin_id,start.date(),end.date())

def chart_style(fig, title=""):
    fig.update_layout(
        title=title, title_font_size=14,
        title_font_color="#111827",
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=40,b=20,l=10,r=10),
        font=dict(family="DM Sans",size=12,color="#6b7280")
    )
    return fig

try:
    kpi=pd.read_sql("""
    SELECT
        COALESCE(SUM(total_amount),0) AS total_revenue,
        COUNT(*) AS total_orders,
        COALESCE(AVG(total_amount),0) AS avg_order_value
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    """, engine,params=p)

    total_revenue=float(kpi["total_revenue"].iloc[0])
    total_orders=int(kpi["total_orders"].iloc[0])
    avg_order=float(kpi["avg_order_value"].iloc[0])

    prev_month=(today.month-1) or 12
    prev_year=today.year if today.month>1 else today.year-1

    this_m=float(pd.read_sql("""
        SELECT COALESCE(SUM(total_amount),0) AS rev
        FROM sales_full_view
        WHERE admin_id=%s
        AND MONTH(sale_date)=%s AND YEAR(sale_date)=%s
    """,engine,params=(admin_id,today.month,today.year))["rev"].iloc[0])

    last_m=float(pd.read_sql("""
        SELECT COALESCE(SUM(total_amount),0) AS rev
        FROM sales_full_view
        WHERE admin_id=%s
        AND MONTH(sale_date)=%s AND YEAR(sale_date)=%s
        """,engine,params=(admin_id,prev_month,prev_year))["rev"].iloc[0])
    
    growth=round(((this_m-last_m)/last_m)*100,1) if last_m>0 else 0

    top_prod=pd.read_sql("""
    SELECT  product_name,
            SUM(quantity) AS total_qty
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    GROUP BY product_name
    ORDER BY total_qty DESC
    LIMIT 1                             
    """, engine,params=p)
    top_product=top_prod["product_name"].iloc[0]\
            if not top_prod.empty else "N/A"
    
    top_cust=pd.read_sql("""
    SELECT customer_name,
        SUM(total_amount) AS total_spent
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    GROUP BY customer_name
    ORDER BY total_spent DESC
    LIMIT 1
    """,engine,params=p)

    top_customer=top_cust["customer_name"].iloc[0]\
                 if not top_cust.empty else "N/A"
    
    today_cnt=int(pd.read_sql("""
    SELECT COUNT(*) AS cnt FROM sales_full_view
    WHERE admin_id=%s AND sale_date=%s
    """,engine,params=(admin_id,today.date()))["cnt"].iloc[0])

    monthly_df=pd.read_sql("""
    SELECT 
        DATE_FORMAT(sale_date,'%%Y-%%m') AS month,
        SUM(total_amount) AS revenue
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    GROUP BY DATE_FORMAT(sale_date,'%%Y-%%m')
    ORDER BY month                   
    """,engine,params=p)

    cat_df=pd.read_sql("""
        SELECT 
            category,
            SUM(total_amount) AS revenue
        FROM sales_full_view
        WHERE admin_id=%s
        AND sale_date BETWEEN %s AND %s
        GROUP BY category
        ORDER BY revenue DESC
    """,engine,params=p)

    top_prods=pd.read_sql("""
    SELECT 
        product_name,
        SUM(quantity) AS total_qty
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    GROUP BY product_name
    ORDER BY total_qty DESC
    LIMIT 8
    """,engine, params=p)

    top_custs=pd.read_sql("""
    SELECT customer_name,
          SUM(total_amount) AS revenue
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    GROUP BY customer_name
    ORDER BY revenue DESC
    LIMIT 8
    """, engine, params=p)

    daily_df=pd.read_sql("""
    SELECT 
        sale_date,
        SUM(total_amount) AS revenue,
        COUNT(*) AS orders
    FROM sales_full_view
    WHERE admin_id=%s
    AND    sale_date BETWEEN %s AND %s
    GROUP BY sale_date
    ORDER BY sale_date
    """,engine,params=p)

    pay_df=pd.read_sql("""
    SELECT
        payment_mode,
        SUM(total_amount) AS revenue,
        COUNT(*) AS orders
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    GROUP BY payment_mode
    ORDER BY revenue DESC
    """,engine,params=p)

    status_df=pd.read_sql("""
    SELECT 
        order_status,
        COUNT(*) AS total_orders,
        SUM(total_amount) AS revenue
    FROM sales_full_view
    WHERE admin_id=%s
    AND sale_date BETWEEN %s AND %s
    GROUP BY order_status
    """, engine,params=p)

    recent_df = pd.read_sql("""
        SELECT
            sale_date,
            customer_name,
            product_name,
            category,
            quantity,
            unit_price,
            total_amount,
            payment_mode,
            order_status
        FROM   sales_full_view
        WHERE  admin_id=%s
        AND    sale_date BETWEEN %s AND %s
        ORDER  BY sale_date DESC
        LIMIT  100
    """, engine, params=p)
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if total_orders == 0:
    st.info("No data found. Upload your Excel file first.")
    st.stop()

st.markdown('<div class="section-label">Key metrics</div>',
            unsafe_allow_html=True)
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total revenue",
          f"₹{total_revenue:,.0f}",
          f"{growth:+.1f}% vs last month")
c2.metric("Total orders",    f"{total_orders:,}")
c3.metric("Avg order value", f"₹{avg_order:,.0f}")
c4.metric("Top product",     top_product)
c5.metric("Top customer",    top_customer)


if today_cnt == 0:
    st.warning("No sales recorded today")
if last_m > 0 and this_m < last_m*0.7:
    st.error(f"Revenue dropped {round((1-this_m/last_m)*100)}% vs last month")


st.markdown('<div class="section-label">Revenue overview</div>',
            unsafe_allow_html=True)
col1,col2 = st.columns(2)

with col1:
    if not monthly_df.empty:
        fig1 = px.bar(monthly_df, x="month", y="revenue",
                      labels={"month":"","revenue":"Revenue (₹)"})
        fig1.update_traces(marker_color="#6366f1",marker_line_width=0)
        fig1 = chart_style(fig1,"Monthly revenue")
        fig1.update_layout(
            xaxis=dict(showgrid=False,tickangle=-30),
            yaxis=dict(showgrid=True,gridcolor="#f3f4f6")
        )
        st.plotly_chart(fig1, use_container_width=True)

with col2:
    if not cat_df.empty:
        fig2 = px.pie(cat_df, values="revenue", names="category",
                      hole=0.45,
                      color_discrete_sequence=[
                          "#6366f1","#10b981","#f59e0b",
                          "#ef4444","#3b82f6","#8b5cf6"
                      ])
        fig2.update_layout(
            title="Sales by category",
            title_font_size=14,title_font_color="#111827",
            paper_bgcolor="white",
            margin=dict(t=40,b=20,l=10,r=10),
            font=dict(family="DM Sans",size=12)
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown('<div class="section-label">Product & customer breakdown</div>',
            unsafe_allow_html=True)
col3,col4 = st.columns(2)
 
with col3:
    if not top_prods.empty:
        fig3 = px.bar(top_prods, x="total_qty", y="product_name",
                      orientation="h",
                      labels={"total_qty":"Units sold","product_name":""})
        fig3.update_traces(marker_color="#10b981",marker_line_width=0)
        fig3 = chart_style(fig3,"Top products by quantity")
        fig3.update_layout(
            xaxis=dict(showgrid=True,gridcolor="#f3f4f6"),
            yaxis=dict(showgrid=False,autorange="reversed")
        )
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    if not top_custs.empty:
        fig4 = px.bar(top_custs, x="revenue", y="customer_name",
                      orientation="h",
                      labels={"revenue":"Revenue (₹)","customer_name":""})
        fig4.update_traces(marker_color="#f59e0b",marker_line_width=0)
        fig4 = chart_style(fig4,"Top customers by revenue")
        fig4.update_layout(
            xaxis=dict(showgrid=True,gridcolor="#f3f4f6"),
            yaxis=dict(showgrid=False,autorange="reversed")
        )
        st.plotly_chart(fig4, use_container_width=True)

st.markdown('<div class="section-label">Daily sales trend</div>',
            unsafe_allow_html=True)
if not daily_df.empty:
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=daily_df["sale_date"], y=daily_df["revenue"],
        mode="lines",
        line=dict(color="#6366f1",width=2),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.08)",
        name="Revenue"
    ))
    fig5.update_layout(
        plot_bgcolor="white",paper_bgcolor="white",
        margin=dict(t=20,b=20,l=10,r=10),
        font=dict(family="DM Sans",size=12,color="#6b7280"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True,gridcolor="#f3f4f6",
                   title="Revenue (₹)")
    )
    st.plotly_chart(fig5, use_container_width=True)

st.markdown('<div class="section-label">Payment & order breakdown</div>',
            unsafe_allow_html=True)
col5,col6 = st.columns(2)
 
with col5:
    if not pay_df.empty:
        fig6 = px.pie(pay_df, values="revenue", names="payment_mode",
                      color_discrete_sequence=[
                          "#6366f1","#10b981","#f59e0b",
                          "#ef4444","#3b82f6"
                      ])
        fig6.update_layout(
            title="Payment mode",
            title_font_size=14,title_font_color="#111827",
            paper_bgcolor="white",
            margin=dict(t=40,b=20,l=10,r=10),
            font=dict(family="DM Sans",size=12)
        )
        st.plotly_chart(fig6, use_container_width=True)

with col6:
    if not status_df.empty:
        fig7 = px.bar(status_df, x="order_status", y="total_orders",
                      labels={"order_status":"Status",
                               "total_orders":"Orders"},
                      color_discrete_sequence=["#10b981"])
        fig7 = chart_style(fig7,"Order status")
        fig7.update_layout(
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True,gridcolor="#f3f4f6")
        )
        st.plotly_chart(fig7, use_container_width=True)
    
st.markdown('<div class="section-label">Recent sales records</div>',
            unsafe_allow_html=True)
if not recent_df.empty:
    st.dataframe(recent_df, use_container_width=True, hide_index=True)
 

    



