import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ProphecyEngine:
    def __init__(self, db_instance):
        self.db = db_instance

    def get_forecast_and_depletion(self, curse_active=False):
        """
        Calculates demand prophecy and days-to-depletion for all ingredients.
        Incorporates weekday weighting and Midnight Curse 3x surge when active.
        """
        ingredients = self.db.get_ingredients()
        sales_data = self.db.get_sales_history()
        sales_df = pd.DataFrame(sales_data)
        
        # Calculate recent daily demand (last 30 days weighted average)
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        recent_sales = sales_df[sales_df['date'] >= (sales_df['date'].max() - pd.Timedelta(days=30))]
        
        baseline_demand = recent_sales.groupby('product_name')['quantity_sold'].mean().to_dict()
        
        # Curse multipliers (Slide 16)
        curse_multipliers = {
            "Moonflower": 3.0,
            "Phoenix Feather": 3.0,
            "Enchanted Mushroom": 3.0
        }

        prophecy_results = []
        today = datetime.now()

        for ing in ingredients:
            name = ing['name']
            current_stock = ing['current_stock']
            safety_stock = ing['safety_stock']
            lead_time = ing['lead_time_days']
            unit = ing['unit']
            supplier = ing['supplier']

            # Daily baseline demand
            daily_demand = baseline_demand.get(name, 15.0)
            
            # Apply Midnight Curse multiplier if active
            multiplier = curse_multipliers.get(name, 1.0) if curse_active else 1.0
            projected_daily_demand = daily_demand * multiplier

            # Calculate days until depletion
            if projected_daily_demand > 0:
                days_to_depletion = current_stock / projected_daily_demand
            else:
                days_to_depletion = 999.0

            depletion_date = today + timedelta(days=days_to_depletion)

            # Restock Spell: Reorder Point (ROP) & Recommended Order Quantity
            # ROP = (Daily Demand * Lead Time) + Safety Stock
            reorder_point = (projected_daily_demand * lead_time) + safety_stock
            
            # Recommended order quantity to restore to 14 days buffer + safety stock
            target_stock = (projected_daily_demand * 14) + safety_stock
            recommended_reorder = max(0, int(np.ceil(target_stock - current_stock)))

            # Stockout Risk Status
            if current_stock <= safety_stock:
                status = "CRITICAL_DEFICIT"
                risk_msg = "⚠️ Stock is already at or below safety threshold!"
            elif days_to_depletion <= lead_time:
                status = "IMMINENT_STOCKOUT"
                risk_msg = f"🚨 Stockout in {days_to_depletion:.1f} days! Delivery takes {lead_time} days. Runout before arrival!"
            elif days_to_depletion <= (lead_time * 2):
                status = "REORDER_RECOMMENDED"
                risk_msg = f"🟡 Stock low ({days_to_depletion:.1f} days remaining). Order within {max(1, int(days_to_depletion - lead_time))} days."
            else:
                status = "HEALTHY"
                risk_msg = f"✅ Stock healthy ({days_to_depletion:.1f} days of supply remaining)."

            prophecy_results.append({
                "product_name": name,
                "category": ing['category'],
                "current_stock": current_stock,
                "safety_stock": safety_stock,
                "unit": unit,
                "lead_time_days": lead_time,
                "supplier": supplier,
                "baseline_daily_demand": round(daily_demand, 1),
                "curse_multiplier": multiplier,
                "projected_daily_demand": round(projected_daily_demand, 1),
                "days_until_depletion": round(days_to_depletion, 1),
                "depletion_date": depletion_date.strftime("%Y-%m-%d"),
                "reorder_point": round(reorder_point, 1),
                "recommended_reorder_qty": recommended_reorder,
                "status": status,
                "risk_message": risk_msg,
                "is_curse_affected": (multiplier > 1.0)
            })

        return prophecy_results

    def detect_anomalies(self, z_threshold=2.8):
        """
        Flags unusual consumption spikes using statistical Z-Score and compares against
        planted ground truth anomalies from Whispering Woods.
        """
        sales_data = self.db.get_sales_history()
        sales_df = pd.DataFrame(sales_data)
        sales_df['date'] = pd.to_datetime(sales_df['date'])

        # Compute rolling baseline and standard deviation per product
        detected = []
        for prod in sales_df['product_name'].unique():
            prod_df = sales_df[sales_df['product_name'] == prod].sort_values('date').copy()
            prod_df['mean_sales'] = prod_df['quantity_sold'].rolling(14, min_periods=3).mean()
            prod_df['std_sales'] = prod_df['quantity_sold'].rolling(14, min_periods=3).std().fillna(1.0)
            prod_df['z_score'] = (prod_df['quantity_sold'] - prod_df['mean_sales']) / prod_df['std_sales']
            
            # Identify spikes
            spikes = prod_df[prod_df['z_score'] >= z_threshold]
            for _, r in spikes.iterrows():
                detected.append({
                    "date": r['date'].strftime("%Y-%m-%d"),
                    "product_name": prod,
                    "quantity_sold": int(r['quantity_sold']),
                    "expected_quantity": int(np.round(r['mean_sales'])),
                    "z_score": round(float(r['z_score']), 2),
                    "spike_ratio": round(float(r['quantity_sold'] / max(1, r['mean_sales'])), 2)
                })

        # Ground truth matching & performance calculation
        ground_truth = self.db.get_anomalies()
        gt_dates_products = {(g['date'], g['product_name']): g for g in ground_truth}

        tp = 0
        enriched_detected = []
        for d in detected:
            key = (d['date'], d['product_name'])
            if key in gt_dates_products:
                tp += 1
                gt_info = gt_dates_products[key]
                d['is_verified_anomaly'] = True
                d['lore_description'] = gt_info.get('description', 'Verified Strange Event')
            else:
                d['is_verified_anomaly'] = False
                d['lore_description'] = 'Unclassified minor consumption surge'
            enriched_detected.append(d)

        total_gt = len(ground_truth)
        total_detected = len(detected)
        precision = tp / total_detected if total_detected > 0 else 1.0
        recall = tp / total_gt if total_gt > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "detected_anomalies": enriched_detected,
            "metrics": {
                "ground_truth_total": total_gt,
                "detected_total": total_detected,
                "true_positives": tp,
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1_score": round(f1, 3)
            }
        }
