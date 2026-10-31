import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv

from db import db_instance
from prophecy_engine import ProphecyEngine

load_dotenv()

engine = ProphecyEngine(db_instance)

# Streamlit Page Config
st.set_page_config(
    page_title="Potion Pantry | Madam Hexley's Smart Shop",
    page_icon="🧙‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Halloween Apothecary Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Inter:wght@400;600&display=swap');
    
    .shop-title {
        font-family: 'Cinzel', serif;
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #c084fc 0%, #f59e0b 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    .shop-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 20px;
    }
    .badge-critical {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warning {
        background-color: #f59e0b;
        color: black;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-healthy {
        background-color: #10b981;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 20px;
        font-weight: 600;
        border-radius: 8px 8px 0px 0px;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar Header
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown('<h1 class="shop-title">🧙‍♀️ Potion Pantry – Madam Hexley\'s Shop</h1>', unsafe_allow_html=True)
    st.markdown('<p class="shop-subtitle">Track 01: Smart Inventory & Demand Prediction • Hack-O-Lantern Hackathon</p>', unsafe_allow_html=True)
with col_head2:
    db_badge = "🟢 MongoDB Atlas" if not db_instance.is_mock else "⚡ In-Memory MongoDB (mongomock)"
    st.info(f"**Database:** {db_badge}\n\n**API Backend:** [http://localhost:8000/docs](http://localhost:8000/docs)")

# Sidebar Controls: The Midnight Curse Toggle
st.sidebar.image("https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=400&q=80", caption="Midnight over Whispering Woods")
st.sidebar.markdown("### 🌕 The Midnight Curse")
st.sidebar.caption("Hack-O-Lantern Slide 16 Challenge Twist")
curse_active = st.sidebar.toggle("🔥 ACTIVATE FULL MOON FESTIVAL", value=False, help="Triples demand (3x) for Moonflower, Phoenix Feather, and Enchanted Mushroom!")

if curse_active:
    st.sidebar.error("🚨 **FULL MOON CURSE ACTIVE!**\nDemand for 3 ingredients has tripled! Depletion countdowns accelerated.")
else:
    st.sidebar.success("🌙 Normal Synodic Demand Rhythm")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏬 Store Profile")
st.sidebar.text("Store ID: HEXLEY-001\nCoven: Begur Hobli Outpost\nModel: Seasonality + Rolling Z-Score")

# Fetch Current Prophecy & Inventory
prophecies = engine.get_forecast_and_depletion(curse_active=curse_active)
prophecy_df = pd.DataFrame(prophecies)
ingredients = db_instance.get_ingredients()
ing_df = pd.DataFrame(ingredients)

# High Level Metric Cards
total_stock = ing_df['current_stock'].sum()
critical_count = len(prophecy_df[prophecy_df['status'].isin(['CRITICAL_DEFICIT', 'IMMINENT_STOCKOUT'])])
avg_depletion = prophecy_df['days_until_depletion'].median()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Shelf Units", f"{total_stock:,} items")
with m2:
    st.metric("Stockout Emergencies", f"{critical_count} items", delta="-Risk" if critical_count > 0 else "Safe", delta_color="inverse")
with m3:
    st.metric("Median Supply Buffer", f"{avg_depletion:.1f} days")
with m4:
    mult_label = "3.0x Surge (Active)" if curse_active else "1.0x Normal"
    st.metric("Festival Multiplier", mult_label)

# Main Quest Tabs
tab_stock, tab_prophecy, tab_restock, tab_strange, tab_analytics, tab_mongo = st.tabs([
    "📦 1. Track Stock (CRUD)",
    "🔮 2. Prophecy (Runout)",
    "✨ 3. Restock Spell",
    "🚨 4. Strange Happenings",
    "🔮 5. Crystal Ball (Charts)",
    "🍃 6. MongoDB Cloud"
])

# ==========================================
# TAB 1: Track Stock & Real-Time Sales
# ==========================================
with tab_stock:
    st.subheader("📦 Cauldron & Cupboard Inventory Tracking")
    st.caption("Add stock, update safety levels, and record customer purchases.")

    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        st.markdown("#### Current Shelf Catalog")
        display_cols = ['name', 'category', 'current_stock', 'safety_stock', 'unit', 'lead_time_days', 'supplier']
        st.dataframe(ing_df[display_cols], use_container_width=True, hide_index=True)

    with col_t2:
        st.markdown("#### ⚡ Record Customer Sale")
        with st.form("sale_form"):
            selected_item = st.selectbox("Ingredient Sold", ing_df['name'].unique())
            sale_qty = st.number_input("Quantity Sold", min_value=1, max_value=200, value=5)
            record_btn = st.form_submit_button("Record Sale & Deduct Stock")

            if record_btn:
                res = db_instance.record_sale(selected_item, sale_qty)
                st.success(f" Recorded sale of {sale_qty} units of {selected_item}! New Stock: {res['new_stock']}")
                st.rerun()

    st.divider()
    
    # Quick Stock Adjustment / Manual Update
    st.markdown("#### 🛠️ Direct Stock Adjustment")
    adj_col1, adj_col2, adj_col3 = st.columns(3)
    with adj_col1:
        adj_item = st.selectbox("Select Item to Adjust", ing_df['name'].unique(), key="adj_item")
    with adj_col2:
        curr_val = int(ing_df[ing_df['name'] == adj_item]['current_stock'].values[0])
        new_val = st.number_input("New Exact Stock Level", min_value=0, max_value=2000, value=curr_val)
    with adj_col3:
        st.write("")
        st.write("")
        if st.button("Apply Stock Update"):
            db_instance.update_stock(adj_item, new_val)
            st.success(f" Updated {adj_item} stock to {new_val} units!")
            st.rerun()

# ==========================================
# TAB 2: Prophecy (Runout Predictions)
# ==========================================
with tab_prophecy:
    st.subheader("🔮 Prophecy: Predicting Runout Dates & Days to Depletion")
    st.markdown("""
    *Madam Hexley's divination model analyzes 180-day consumption trends, weekend market spikes, and the Midnight Curse to foretell exactly when each ingredient will be exhausted.*
    """)

    prophecy_view = prophecy_df[['product_name', 'category', 'current_stock', 'projected_daily_demand', 'days_until_depletion', 'depletion_date', 'lead_time_days', 'status', 'risk_message']]
    
    # Color-coded display
    st.dataframe(
        prophecy_view,
        column_config={
            "days_until_depletion": st.column_config.ProgressColumn(
                "Days Until Runout",
                help="Days of stock remaining before shelves are empty",
                format="%.1f days",
                min_value=0,
                max_value=30
            ),
            "status": st.column_config.TextColumn("Prophecy Risk Level")
        },
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # Visual Depletion Timeline
    st.markdown("#### ⏳ Imminent Stockout Countdown (Days Remaining)")
    sorted_prophecy = prophecy_df.sort_values('days_until_depletion', ascending=True)
    
    bar_colors = []
    for _, r in sorted_prophecy.iterrows():
        if r['days_until_depletion'] <= r['lead_time_days']:
            bar_colors.append('#ef4444') # Red
        elif r['days_until_depletion'] <= r['lead_time_days'] * 2:
            bar_colors.append('#f59e0b') # Amber
        else:
            bar_colors.append('#10b981') # Green

    fig_dep = go.Figure(go.Bar(
        x=sorted_prophecy['days_until_depletion'],
        y=sorted_prophecy['product_name'],
        orientation='h',
        marker=dict(color=bar_colors),
        text=[f"{v:.1f}d (Lead: {l}d)" for v, l in zip(sorted_prophecy['days_until_depletion'], sorted_prophecy['lead_time_days'])],
        textposition='outside'
    ))
    fig_dep.update_layout(
        title="Days Remaining vs Supplier Lead Time (Red = Stockout Before Delivery Can Arrive!)",
        xaxis_title="Days of Inventory Remaining",
        yaxis_title="Ingredient",
        template="plotly_dark",
        height=450
    )
    st.plotly_chart(fig_dep, use_container_width=True)

# ==========================================
# TAB 3: Restock Spell (Optimization)
# ==========================================
with tab_restock:
    st.subheader("✨ Restock Spell: Intelligent Reorder Recommendations")
    st.markdown("""
    *Restock calculations use dynamic Reorder Points (ROP) factoring in supplier transit lead times, coven safety stock, and demand surges.*
    $$\\text{Reorder Point (ROP)} = (\\text{Daily Demand} \\times \\text{Lead Time Days}) + \\text{Safety Stock}$$
    """)

    restock_cols = ['product_name', 'supplier', 'lead_time_days', 'current_stock', 'reorder_point', 'recommended_reorder_qty', 'unit', 'status']
    st.dataframe(prophecy_df[restock_cols], use_container_width=True, hide_index=True)

    st.divider()

    # One-Click Restock Dispatcher
    st.markdown("#### 🦅 Dispatch Coven Courier / Expedite Restock")
    r1, r2, r3 = st.columns(3)
    with r1:
        order_item = st.selectbox("Ingredient to Replenish", prophecy_df['product_name'].unique(), key="restock_select")
        item_data = prophecy_df[prophecy_df['product_name'] == order_item].iloc[0]
    with r2:
        recommended = int(item_data['recommended_reorder_qty'])
        order_qty = st.number_input(f"Quantity to Order ({item_data['unit']})", min_value=5, max_value=2000, value=max(20, recommended))
    with r3:
        st.write("")
        st.write("")
        if st.button("✨ Cast Restock Spell (Receive Delivery)"):
            res = db_instance.record_restock(order_item, order_qty)
            st.success(f"🧙 Replenished {order_qty} units of {order_item}! New stock: {res['new_stock']}")
            st.rerun()

# ==========================================
# TAB 4: Strange Happenings (Anomaly Detection)
# ==========================================
with tab_strange:
    st.subheader("🚨 Strange Happenings: Whispering Woods Anomaly Radar")
    st.markdown("""
    *Our statistical Z-score detector scans sales patterns to isolate panic buying, rogue resurrection rituals, and regional crises.*
    """)

    z_thresh = st.slider("Anomaly Sensitivity (Z-Score Threshold)", min_value=2.0, max_value=4.5, value=2.8, step=0.1)
    anomaly_results = engine.detect_anomalies(z_threshold=z_thresh)
    metrics = anomaly_results['metrics']

    # Performance Metrics Cards (Scored directly by hackathon judges!)
    am1, am2, am3, am4 = st.columns(4)
    with am1:
        st.metric("Planted Outbreaks", f"{metrics['ground_truth_total']} Events")
    with am2:
        st.metric("Anomalies Caught", f"{metrics['true_positives']} Verified")
    with am3:
        st.metric("Model Precision", f"{metrics['precision']*100:.1f}%")
    with am4:
        st.metric("Model Recall (Score)", f"{metrics['recall']*100:.1f}%")

    st.divider()

    # Detailed Verified Outbreak Log
    st.markdown("#### 📜 Isolated Lore Anomaly Catalog")
    for anom in anomaly_results['detected_anomalies']:
        if anom.get('is_verified_anomaly'):
            with st.expander(f"📍 **{anom['date']}** – {anom['product_name']} (Spike: {anom['spike_ratio']}x | Sold: {anom['quantity_sold']} vs Normal: {anom['expected_quantity']})", expanded=True):
                st.markdown(f"**Lore Root Cause:** *{anom['lore_description']}*")
                st.markdown(f"**Statistical Deviation:** `Z-Score = {anom['z_score']}` | **Status:** `Verified Outbreak`")

# ==========================================
# TAB 5: Crystal Ball (Interactive Charts)
# ==========================================
with tab_analytics:
    st.subheader("🔮 Crystal Ball: 180-Day Sales Demand & Coven Trends")

    sales_history = db_instance.get_sales_history()
    sales_df = pd.DataFrame(sales_history)
    sales_df['date'] = pd.to_datetime(sales_df['date'])

    selected_chart_prods = st.multiselect(
        "Select Ingredients to Project",
        options=sorted(sales_df['product_name'].unique()),
        default=["Moonflower", "Dragon Root", "Phoenix Feather", "Enchanted Mushroom"]
    )

    if selected_chart_prods:
        filt = sales_df[sales_df['product_name'].isin(selected_chart_prods)].sort_values('date')
        fig_trend = px.line(
            filt,
            x='date',
            y='quantity_sold',
            color='product_name',
            title="180-Day Daily Sales Trajectory by Ingredient",
            template="plotly_dark",
            height=450
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # Weekday Coven Pattern
    st.markdown("#### 🌙 Weekly Demand Waves (Coven Market Rhythm)")
    sales_df['day_name'] = sales_df['date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow = sales_df.groupby('day_name')['quantity_sold'].mean().reindex(day_order).reset_index()

    fig_dow = px.bar(
        dow,
        x='day_name',
        y='quantity_sold',
        color='quantity_sold',
        color_continuous_scale='Magma',
        template="plotly_dark",
        title="Average Consumption by Day of Week: Fri/Sat/Sun Gathering Surges"
    )
    st.plotly_chart(fig_dow, use_container_width=True)

# ==========================================
# TAB 6: MongoDB Cloud Connection
# ==========================================
with tab_mongo:
    st.subheader("🍃 MongoDB Database & Storage Inspector")
    st.markdown("Configure and inspect Madam Hexley's NoSQL database collections.")

    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        st.markdown("#### 📡 Current Connection Status")
        if not db_instance.is_mock:
            st.success(" Connected to Live Remote MongoDB!")
            st.text(f"URI: {os.getenv('MONGODB_URI', '')[:20]}...")
        else:
            st.info(" Running on Embedded In-Memory MongoDB (mongomock).\nAll collections are pre-seeded and fully operational in memory!")

        st.markdown("#### 🔗 Connect to MongoDB Atlas (Optional)")
        atlas_uri_input = st.text_input("Enter MongoDB Atlas Connection String (`mongodb+srv://...`)", type="password")
        if st.button("Save & Connect to Atlas"):
            if atlas_uri_input:
                # Update .env
                with open(".env", "a") as f:
                    f.write(f"\nMONGODB_URI={atlas_uri_input}\n")
                st.success("Saved MONGODB_URI to .env! Restarting connection...")
                st.rerun()

    with col_m2:
        st.markdown("#### 📊 Collection Record Counts")
        st.json({
            "ingredients": db_instance.db.ingredients.count_documents({}),
            "historical_sales": db_instance.db.historical_sales.count_documents({}),
            "anomalies": db_instance.db.anomalies.count_documents({}),
            "festival_scenario": db_instance.db.festival_scenario.count_documents({})
        })

st.markdown("---")
st.caption("🧙 Madam Hexley's Potion Pantry • Hack-O-Lantern Hackathon Track 01 • Built with Python, MongoDB, FastAPI & Streamlit")
