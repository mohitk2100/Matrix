import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import pymongo
import mongomock

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = os.getenv("MONGODB_DB_NAME", "potion_pantry")

class PotionDatabase:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False
        self._init_connection()
        self._seed_data_if_empty()

    def _init_connection(self):
        if MONGODB_URI:
            try:
                print(f"Connecting to MongoDB Atlas / Remote instance...")
                self.client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
                # Test connection
                self.client.server_info()
                self.db = self.client[DB_NAME]
                self.is_mock = False
                print(" Successfully connected to MongoDB!")
                return
            except Exception as e:
                print(f" Could not connect to remote MongoDB ({e}). Falling back to in-memory Mock MongoDB.")
        else:
            print("No MONGODB_URI set in .env. Initializing high-speed in-memory MongoDB (mongomock).")

        self.client = mongomock.MongoClient()
        self.db = self.client[DB_NAME]
        self.is_mock = True

    def _seed_data_if_empty(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        
        # 1. Seed Ingredients
        if self.db.ingredients.count_documents({}) == 0:
            ing_df = pd.read_csv(os.path.join(data_dir, "ingredients.csv"))
            records = ing_df.to_dict(orient="records")
            self.db.ingredients.insert_many(records)
            print(f" Seeded {len(records)} ingredients into MongoDB.")

        # 2. Seed Historical Sales
        if self.db.historical_sales.count_documents({}) == 0:
            sales_df = pd.read_csv(os.path.join(data_dir, "historical_sales.csv"))
            records = sales_df.to_dict(orient="records")
            self.db.historical_sales.insert_many(records)
            print(f" Seeded {len(records)} sales records into MongoDB.")

        # 3. Seed Anomalies Ground Truth
        if self.db.anomalies.count_documents({}) == 0:
            anom_df = pd.read_csv(os.path.join(data_dir, "anomaly_ground_truth.csv"))
            records = anom_df.to_dict(orient="records")
            self.db.anomalies.insert_many(records)
            print(f" Seeded {len(records)} anomaly records into MongoDB.")

        # 4. Seed Festival Scenario (Midnight Curse)
        if self.db.festival_scenario.count_documents({}) == 0:
            fest_df = pd.read_csv(os.path.join(data_dir, "festival_scenario.csv"))
            records = fest_df.to_dict(orient="records")
            self.db.festival_scenario.insert_many(records)
            print(f" Seeded {len(records)} festival scenario records into MongoDB.")

    # CRUD Operations
    def get_ingredients(self):
        return list(self.db.ingredients.find({}, {"_id": 0}))

    def get_ingredient(self, name):
        return self.db.ingredients.find_one({"name": name}, {"_id": 0})

    def update_stock(self, name, new_stock):
        self.db.ingredients.update_one({"name": name}, {"$set": {"current_stock": int(new_stock)}})
        return self.get_ingredient(name)

    def record_sale(self, product_name, quantity, date_str=None, store_id="HEXLEY-001"):
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        quantity = int(quantity)
        # Deduct stock
        ing = self.get_ingredient(product_name)
        if ing:
            new_stock = max(0, ing['current_stock'] - quantity)
            self.update_stock(product_name, new_stock)

        # Log sale
        sale_doc = {
            "date": date_str,
            "store_id": store_id,
            "product_name": product_name,
            "quantity_sold": quantity,
            "created_at": datetime.now().isoformat()
        }
        self.db.historical_sales.insert_one(sale_doc)
        return {"status": "success", "new_stock": new_stock if ing else None}

    def record_restock(self, product_name, quantity_added):
        ing = self.get_ingredient(product_name)
        if not ing:
            return None
        new_stock = ing['current_stock'] + int(quantity_added)
        self.update_stock(product_name, new_stock)
        return {"product_name": product_name, "new_stock": new_stock}

    def get_sales_history(self, product_name=None):
        query = {"product_name": product_name} if product_name else {}
        return list(self.db.historical_sales.find(query, {"_id": 0}))

    def get_anomalies(self):
        return list(self.db.anomalies.find({}, {"_id": 0}))

    def get_festival_scenario(self):
        return list(self.db.festival_scenario.find({}, {"_id": 0}))

# Singleton instance
db_instance = PotionDatabase()
