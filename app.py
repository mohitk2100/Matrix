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
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-warning {
        background-color: #f59e0b;
        color: black;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-healthy {
        background-color: #10b981;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
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
    st.info(f"**Database:** {db_badge}\n\n**FastAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)")

# Sidebar Controls: The Midnight Curse Toggle
st.sidebar.image("https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=400&q=80", caption="Whispering Woods at Midnight")
st.sidebar.markdown("### 🌕 The Midnight Curse")
st.sidebar.caption("Hack-O-Lantern Slide 16 Challenge Twist")
curse_active = st.sidebar.toggle("🔥 ACTIVATE FULL MOON FESTIVAL", value=False, help="Triples demand (3x) for Moonflower, Phoenix Feather, and Enchanted Mushroom!")

if curse_active:
    st.sidebar.error("🚨 **FULL MOON CURSE ACTIVE!**\nDemand for 3 ingredients has tripled! Depletion countdowns accelerated.")
else:
    st.sidebar.success("🌙 Normal Synodic Demand Rhythm")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏬 Shop Metadata")
st.sidebar.text("Store ID: HEXLEY-001\nCoven: Begur Hobli Outpost\nBackend: FastAPI + MongoDB")

# Fetch Current Prophecy & Inventory
prophecies = engine.get_forecast_and_depletion(curse_active=curse_active)
prophecy_df = pd.DataFrame(prophecies)
ingredients = db_instance.get_ingredients()
ing_df = pd.DataFrame(ingredients)

# High Level Metric Cards
total_stock = ing_df['current_stock'].sum() if not ing_df.empty else 0
critical_count = len(prophecy_df[prophecy_df['status'].isin(['CRITICAL_DEFICIT', 'IMMINENT_STOCKOUT'])]) if not prophecy_df.empty else 0
avg_depletion = prophecy_df['days_until_depletion'].median() if not prophecy_df.empty else 0

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
    "🍃 6. MongoDB Cloud & Admin"
])

# ==========================================
# TAB 1: Track Stock (Full CRUD & Sales)
# ==========================================
with tab_stock:
    st.subheader("📦 Cauldron & Cupboard Inventory Tracking")
    st.caption("Add new ingredients, adjust stock, delete items, and record customer purchases.")

    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        st.markdown("#### Current Master Catalog")
        if not ing_df.empty:
            display_cols = ['name', 'category', 'current_stock', 'safety_stock', 'unit', 'lead_time_days', 'supplier']
            st.dataframe(ing_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.warning("Catalog is empty. Reset demo data in the MongoDB tab.")

    with col_t2:
        st.markdown("#### ⚡ Record Customer Purchase")
        with st.form("sale_form"):
            item_names = ing_df['name'].unique() if not ing_df.empty else []
            selected_item = st.selectbox("Ingredient Sold", item_names)
            sale_qty = st.number_input("Quantity Sold", min_value=1, max_value=500, value=5)
            record_btn = st.form_submit_button("Record Sale & Deduct Stock")

            if record_btn and selected_item:
                try:
                    res = db_instance.record_sale(selected_item, sale_qty)
                    st.success(f" Recorded sale of {sale_qty} units of {selected_item}! Remaining stock: {res['remaining_stock']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sale failed: {e}")

    st.divider()

    # Expandable CRUD Management Section
    crud_expander = st.expander("🛠️ Advanced Inventory Management (Add, Edit, Delete Ingredients)", expanded=False)
    with crud_expander:
        c1, c2, c3 = st.columns(3)

        # 1. Add New Ingredient
        with c1:
            st.markdown("##### ➕ Add New Ingredient")
            with st.form("add_ing_form"):
                new_name = st.text_input("Ingredient Name", placeholder="e.g. Wolfsbane")
                new_cat = st.selectbox("Category", ["Flora & Herbs", "Roots & Bark", "Minerals & Gems", "Mythical Fauna", "Essences & Liquids", "Fungi & Spores"])
                new_stock = st.number_input("Starting Stock", min_value=0, max_value=5000, value=100)
                new_safety = st.number_input("Safety Stock Threshold", min_value=1, max_value=1000, value=25)
                new_supplier = st.text_input("Supplier Coven", value="Shadowbrook Herbalists")
                new_lead = st.number_input("Lead Time (Days)", min_value=1, max_value=30, value=3)
                new_unit = st.text_input("Unit of Measure", value="bundles")
                submit_add = st.form_submit_button("Add to Master Catalog")

                if submit_add:
                    try:
                        db_instance.add_ingredient({
                            "name": new_name,
                            "category": new_cat,
                            "current_stock": new_stock,
                            "safety_stock": new_safety,
                            "supplier": new_supplier,
                            "lead_time_days": new_lead,
                            "unit": new_unit
                        })
                        st.success(f" Added '{new_name}' to inventory!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        # 2. Direct Stock Adjustment
        with c2:
            st.markdown("##### 📝 Adjust Current Stock")
            if not ing_df.empty:
                adj_item = st.selectbox("Select Item", ing_df['name'].unique(), key="adj_item_select")
                curr_val = int(ing_df[ing_df['name'] == adj_item]['current_stock'].values[0])
                new_val = st.number_input("New Exact Stock Level", min_value=0, max_value=10000, value=curr_val)
                if st.button("Apply Stock Level", key="apply_stock_btn"):
                    db_instance.update_stock(adj_item, new_val)
                    st.success(f" Updated {adj_item} stock to {new_val} units!")
                    st.rerun()

        # 3. Delete Ingredient
        with c3:
            st.markdown("##### 🗑️ Remove Ingredient")
            if not ing_df.empty:
                del_item = st.selectbox("Select Item to Delete", ing_df['name'].unique(), key="del_item_select")
                if st.button("🚨 Permanently Delete", key="del_btn"):
                    db_instance.delete_ingredient(del_item)
                    st.warning(f" Removed '{del_item}' from inventory!")
                    st.rerun()

# ==========================================
# TAB 2: Prophecy (Runout Predictions)
# ==========================================
with tab_prophecy:
    st.subheader("🔮 Prophecy: Predicting Depletion Dates & Runout Timelines")
    st.markdown("""
    *Madam Hexley's demand forecasting model analyzes 180-day historical consumption patterns, weekend market spikes, and the Midnight Curse to foretell exactly when each ingredient will be exhausted.*
    """)

    prophecy_view = prophecy_df[['product_name', 'category', 'current_stock', 'projected_daily_demand', 'days_until_depletion', 'depletion_date', 'lead_time_days', 'status', 'risk_message']]
    
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

    # 14-Day Demand Projection Graph
    st.divider()
    st.markdown("#### 📅 14-Day Day-by-Day Future Demand Projection")
    target_fc_item = st.selectbox("Inspect Multi-Day Demand Curve for Ingredient", ing_df['name'].unique())
    fc_data = engine.get_multi_day_forecast(target_fc_item, days=14, curse_active=curse_active)

    if fc_data:
        fc_df = pd.DataFrame(fc_data["daily_projections"])
        fig_fc = px.bar(
            fc_df,
            x='date',
            y='expected_demand',
            color='day_of_week',
            title=f"14-Day Expected Demand for {target_fc_item} (Base: {fc_data['base_demand']} / Multiplier: {fc_data['curse_multiplier']}x)",
            template="plotly_dark"
        )
        st.plotly_chart(fig_fc, use_container_width=True)

# ==========================================
# TAB 3: Restock Spell (Optimization)
# ==========================================
with tab_restock:
    st.subheader("✨ Restock Spell: Intelligent Reorder Recommendations")
    st.markdown("""
    *Calculates dynamic Reorder Points (ROP) factoring in supplier transit lead times, safety stocks, and demand surges.*
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
    *Our statistical Z-score detector scans daily consumption patterns to isolate panic buying, rogue resurrection rituals, and regional crises.*
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
# TAB 6: MongoDB Cloud & Admin Reset
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

        st.divider()
        st.markdown("#### 🔄 Reset Demo State")
        st.caption("Drop changes and re-seed all collections back to the pristine Hack-O-Lantern demo dataset.")
        if st.button("Reset to Pristine Demo Datasets"):
            db_instance.reset_demo_data()
            st.success(" Demo datasets restored to initial state!")
            st.rerun()

st.markdown("---")
st.caption("🧙 Madam Hexley's Potion Pantry • Hack-O-Lantern Hackathon Track 01 • Built with Python, MongoDB, FastAPI & Streamlit")
