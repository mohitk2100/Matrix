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
                print("Connecting to MongoDB Atlas / Remote instance...")
                self.client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
                # Test connection
                self.client.server_info()
                self.db = self.client[DB_NAME]
                self.is_mock = False
                print(" Successfully connected to MongoDB Atlas!")
                return
            except Exception as e:
                print(f" Could not connect to remote MongoDB ({e}). Falling back to in-memory Mock MongoDB.")
        else:
            print("No MONGODB_URI configured. Initializing high-speed in-memory MongoDB (mongomock).")

        self.client = mongomock.MongoClient()
        self.db = self.client[DB_NAME]
        self.is_mock = True

    def _seed_data_if_empty(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        
        # 1. Ingredients
        if self.db.ingredients.count_documents({}) == 0:
            ing_df = pd.read_csv(os.path.join(data_dir, "ingredients.csv"))
            records = ing_df.to_dict(orient="records")
            self.db.ingredients.insert_many(records)
            print(f" Seeded {len(records)} ingredients into MongoDB.")

        # 2. Historical Sales
        if self.db.historical_sales.count_documents({}) == 0:
            sales_df = pd.read_csv(os.path.join(data_dir, "historical_sales.csv"))
            records = sales_df.to_dict(orient="records")
            self.db.historical_sales.insert_many(records)
            print(f" Seeded {len(records)} sales records into MongoDB.")

        # 3. Anomalies Ground Truth
        if self.db.anomalies.count_documents({}) == 0:
            anom_df = pd.read_csv(os.path.join(data_dir, "anomaly_ground_truth.csv"))
            records = anom_df.to_dict(orient="records")
            self.db.anomalies.insert_many(records)
            print(f" Seeded {len(records)} anomaly records into MongoDB.")

        # 4. Festival Scenario (Midnight Curse)
        if self.db.festival_scenario.count_documents({}) == 0:
            fest_df = pd.read_csv(os.path.join(data_dir, "festival_scenario.csv"))
            records = fest_df.to_dict(orient="records")
            self.db.festival_scenario.insert_many(records)
            print(f" Seeded {len(records)} festival scenario records into MongoDB.")

    # ==========================
    # INGREDIENT CRUD
    # ==========================
    def get_ingredients(self):
        """Returns all ingredients sorted by name."""
        return list(self.db.ingredients.find({}, {"_id": 0}).sort("name", 1))

    def get_ingredient(self, name):
        """Finds single ingredient by name (case-insensitive)."""
        return self.db.ingredients.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}}, {"_id": 0})

    def add_ingredient(self, data: dict):
        """Creates a new ingredient document."""
        name = data.get("name", "").strip()
        if not name:
            raise ValueError("Ingredient name cannot be empty")
        if self.get_ingredient(name):
            raise ValueError(f"Ingredient '{name}' already exists")
        
        doc = {
            "name": name,
            "category": data.get("category", "General Alchemy"),
            "current_stock": int(data.get("current_stock", 0)),
            "safety_stock": int(data.get("safety_stock", 10)),
            "supplier": data.get("supplier", "Independent Forager"),
            "lead_time_days": int(data.get("lead_time_days", 3)),
            "unit": data.get("unit", "units")
        }
        self.db.ingredients.insert_one(doc.copy())
        return self.get_ingredient(name)

    def update_ingredient(self, name: str, update_fields: dict):
        """Updates fields of an existing ingredient."""
        ing = self.get_ingredient(name)
        if not ing:
            return None
        clean_update = {}
        for k in ["category", "supplier", "unit"]:
            if k in update_fields:
                clean_update[k] = str(update_fields[k])
        for k in ["current_stock", "safety_stock", "lead_time_days"]:
            if k in update_fields:
                clean_update[k] = max(0, int(update_fields[k]))
        
        if clean_update:
            self.db.ingredients.update_one({"name": ing["name"]}, {"$set": clean_update})
        return self.get_ingredient(ing["name"])

    def delete_ingredient(self, name: str):
        """Deletes an ingredient."""
        ing = self.get_ingredient(name)
        if not ing:
            return False
        res = self.db.ingredients.delete_one({"name": ing["name"]})
        return res.deleted_count > 0

    def update_stock(self, name: str, new_stock: int):
        """Updates exact current stock level."""
        ing = self.get_ingredient(name)
        if not ing:
            return None
        self.db.ingredients.update_one({"name": ing["name"]}, {"$set": {"current_stock": max(0, int(new_stock))}})
        return self.get_ingredient(ing["name"])

    # ==========================
    # SALES & RESTOCK
    # ==========================
    def record_sale(self, product_name: str, quantity: int, date_str: str = None, store_id: str = "HEXLEY-001"):
        """Records a sale transaction and deducts shelf inventory."""
        ing = self.get_ingredient(product_name)
        if not ing:
            raise ValueError(f"Ingredient '{product_name}' not found")
        
        qty = int(quantity)
        if qty <= 0:
            raise ValueError("Sale quantity must be greater than zero")

        new_stock = max(0, ing['current_stock'] - qty)
        self.update_stock(ing['name'], new_stock)

        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        sale_doc = {
            "date": date_str,
            "store_id": store_id,
            "product_name": ing['name'],
            "quantity_sold": qty,
            "created_at": datetime.now().isoformat()
        }
        self.db.historical_sales.insert_one(sale_doc)
        return {
            "status": "success",
            "product_name": ing['name'],
            "units_sold": qty,
            "remaining_stock": new_stock,
            "date": date_str
        }

    def record_restock(self, product_name: str, quantity_added: int):
        """Replenishes shelf inventory."""
        ing = self.get_ingredient(product_name)
        if not ing:
            raise ValueError(f"Ingredient '{product_name}' not found")
        
        qty = int(quantity_added)
        if qty <= 0:
            raise ValueError("Restock quantity must be greater than zero")

        new_stock = ing['current_stock'] + qty
        self.update_stock(ing['name'], new_stock)
        return {
            "status": "success",
            "product_name": ing['name'],
            "quantity_replenished": qty,
            "new_stock": new_stock
        }

    def get_sales_history(self, product_name: str = None, limit: int = None):
        """Fetches sales history with optional product filter and limit."""
        query = {}
        if product_name:
            ing = self.get_ingredient(product_name)
            target = ing['name'] if ing else product_name
            query["product_name"] = target

        cursor = self.db.historical_sales.find(query, {"_id": 0}).sort("date", -1)
        if limit:
            cursor = cursor.limit(int(limit))
        return list(cursor)

    def get_anomalies(self):
        """Fetches isolated ground truth anomalies."""
        return list(self.db.anomalies.find({}, {"_id": 0}))

    def get_festival_scenario(self):
        """Fetches Midnight Curse festival details."""
        return list(self.db.festival_scenario.find({}, {"_id": 0}))

    def get_collections_summary(self):
        """Returns metadata and counts for all collections."""
        return {
            "database_name": DB_NAME,
            "is_mock": self.is_mock,
            "connection_type": "MongoDB Atlas" if not self.is_mock else "In-Memory MongoDB (mongomock)",
            "collections": {
                "ingredients": self.db.ingredients.count_documents({}),
                "historical_sales": self.db.historical_sales.count_documents({}),
                "anomalies": self.db.anomalies.count_documents({}),
                "festival_scenario": self.db.festival_scenario.count_documents({})
            }
        }

    def get_collection_documents(self, collection_name: str, limit: int = 50):
        """Fetches raw documents from a specific collection."""
        valid_cols = ["ingredients", "historical_sales", "anomalies", "festival_scenario"]
        if collection_name not in valid_cols:
            raise ValueError(f"Collection '{collection_name}' not found. Available: {valid_cols}")
        cursor = self.db[collection_name].find({}, {"_id": 0}).limit(limit)
        return list(cursor)

    def reset_demo_data(self):
        """Drops and re-seeds all collections to fresh initial demo state."""
        self.db.ingredients.delete_many({})
        self.db.historical_sales.delete_many({})
        self.db.anomalies.delete_many({})
        self.db.festival_scenario.delete_many({})
        self._seed_data_if_empty()
        return {"status": "success", "message": "Demo datasets re-initialized."}

# Singleton instance
db_instance = PotionDatabase()
