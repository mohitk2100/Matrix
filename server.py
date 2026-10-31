from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from db import db_instance
from prophecy_engine import ProphecyEngine

app = FastAPI(
    title="🧙 Madam Hexley's Potion Pantry API",
    description="Official Backend API for Track 01: Smart Inventory & Demand Prediction (Hack-O-Lantern Hackathon)",
    version="1.0.0"
)

# Enable CORS for any frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ProphecyEngine(db_instance)

# Pydantic Schemas
class SaleRequest(BaseModel):
    product_name: str
    quantity: int
    store_id: Optional[str] = "HEXLEY-001"
    date: Optional[str] = None

class RestockRequest(BaseModel):
    product_name: str
    quantity: int

class StockUpdateRequest(BaseModel):
    product_name: str
    new_stock: int

# Endpoints
@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Potion Pantry Smart Inventory Backend",
        "database": "MongoDB Atlas" if not db_instance.is_mock else "In-Memory MongoDB (mongomock)",
        "endpoints": {
            "swagger_docs": "/docs",
            "inventory": "/api/inventory",
            "prophecy": "/api/prophecy",
            "anomalies": "/api/anomalies",
            "curse": "/api/curse"
        }
    }

@app.get("/api/inventory")
def get_inventory():
    """Track Stock: returns master catalog with current stock and safety levels."""
    return {"ingredients": db_instance.get_ingredients()}

@app.post("/api/inventory/sale")
def record_sale(sale: SaleRequest):
    """Track Stock: records units sold and automatically decrements stock."""
    res = db_instance.record_sale(
        product_name=sale.product_name,
        quantity=sale.quantity,
        date_str=sale.date,
        store_id=sale.store_id
    )
    return res

@app.post("/api/inventory/restock")
def restock_item(req: RestockRequest):
    """Restock Spell: adds replenishment units to cupboard stock."""
    res = db_instance.record_restock(req.product_name, req.quantity)
    if not res:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return res

@app.post("/api/inventory/update")
def update_stock(req: StockUpdateRequest):
    """Track Stock: manually updates stock quantity."""
    res = db_instance.update_stock(req.product_name, req.new_stock)
    return res

@app.get("/api/prophecy")
def get_prophecy(curse_active: bool = False):
    """
    Prophecy & Restock Spell:
    Predicts which ingredients run out and when (days until depletion).
    Calculates Reorder Point (ROP) and recommended restock quantity.
    """
    results = engine.get_forecast_and_depletion(curse_active=curse_active)
    return {
        "curse_active": curse_active,
        "prophecies": results
    }

@app.get("/api/anomalies")
def get_anomalies(z_threshold: float = 2.8):
    """
    Strange Happenings:
    Flags unusual consumption spikes and returns validation metrics against Whispering Woods ground truth.
    """
    return engine.detect_anomalies(z_threshold=z_threshold)

@app.get("/api/curse/scenario")
def get_curse_scenario():
    """Midnight Curse: details on the Full Moon Harvest Festival 3x surge."""
    return {"scenario": db_instance.get_festival_scenario()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
