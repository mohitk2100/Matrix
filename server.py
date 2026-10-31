from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from db import db_instance
from prophecy_engine import ProphecyEngine

app = FastAPI(
    title="🧙‍♀️ Madam Hexley's Potion Pantry API",
    description="Production REST API for Track 01: Smart Inventory & Demand Prediction (Hack-O-Lantern Hackathon)",
    version="1.2.0"
)

# Enable CORS for web and client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ProphecyEngine(db_instance)

# Server-side state for the Midnight Curse
server_state = {
    "curse_active": False
}

# ==========================
# Pydantic Request Models
# ==========================
class IngredientCreate(BaseModel):
    name: str = Field(..., example="Wolfsbane Blossom")
    category: str = Field(default="Flora & Herbs", example="Flora & Herbs")
    current_stock: int = Field(default=100, ge=0, example=100)
    safety_stock: int = Field(default=25, ge=0, example=25)
    supplier: str = Field(default="Shadowbrook Herbalists", example="Shadowbrook Herbalists")
    lead_time_days: int = Field(default=4, gt=0, example=4)
    unit: str = Field(default="bundles", example="bundles")

class IngredientUpdate(BaseModel):
    category: Optional[str] = None
    current_stock: Optional[int] = Field(default=None, ge=0)
    safety_stock: Optional[int] = Field(default=None, ge=0)
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = Field(default=None, gt=0)
    unit: Optional[str] = None

class StockPatch(BaseModel):
    new_stock: int = Field(..., ge=0, example=150)

class SaleCreate(BaseModel):
    product_name: str = Field(..., example="Moonflower")
    quantity: int = Field(..., gt=0, example=5)
    store_id: Optional[str] = Field(default="HEXLEY-001", example="HEXLEY-001")
    date: Optional[str] = Field(default=None, example="2026-11-01")

class RestockCreate(BaseModel):
    product_name: str = Field(..., example="Phoenix Feather")
    quantity: int = Field(..., gt=0, example=50)

class CurseToggle(BaseModel):
    activate: bool = Field(..., example=True)

# ==========================
# 1. Health & Meta Routes
# ==========================
@app.get("/", tags=["Health & Meta"])
def root():
    return {
        "status": "online",
        "service": "Potion Pantry Smart Inventory Engine",
        "version": "1.2.0",
        "database": "MongoDB Atlas" if not db_instance.is_mock else "In-Memory MongoDB (mongomock)",
        "curse_active": server_state["curse_active"],
        "docs_url": "/docs"
    }

@app.get("/api/health", tags=["Health & Meta"])
def health_check():
    return {
        "status": "healthy",
        "database_connected": True,
        "database_type": "MongoDB Atlas" if not db_instance.is_mock else "mongomock (In-Memory)",
        "collection_counts": {
            "ingredients": db_instance.db.ingredients.count_documents({}),
            "historical_sales": db_instance.db.historical_sales.count_documents({}),
            "anomalies": db_instance.db.anomalies.count_documents({}),
            "festival_scenario": db_instance.db.festival_scenario.count_documents({})
        },
        "curse_active": server_state["curse_active"]
    }

# ==========================
# 2. Track Stock (Inventory CRUD)
# ==========================
@app.get("/api/inventory", tags=["Track Stock (CRUD)"])
def list_ingredients():
    """Retrieve full master ingredient catalog."""
    return {"ingredients": db_instance.get_ingredients()}

@app.get("/api/inventory/{name}", tags=["Track Stock (CRUD)"])
def get_ingredient(name: str):
    """Retrieve details for a single ingredient."""
    ing = db_instance.get_ingredient(name)
    if not ing:
        raise HTTPException(status_code=404, detail=f"Ingredient '{name}' not found")
    return ing

@app.post("/api/inventory", status_code=status.HTTP_201_CREATED, tags=["Track Stock (CRUD)"])
def create_ingredient(req: IngredientCreate):
    """Add a new ingredient to Madam Hexley's catalog."""
    try:
        new_item = db_instance.add_ingredient(req.model_dump())
        return {"status": "created", "ingredient": new_item}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/inventory/{name}", tags=["Track Stock (CRUD)"])
def update_ingredient_details(name: str, req: IngredientUpdate):
    """Update fields of an existing ingredient."""
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = db_instance.update_ingredient(name, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Ingredient '{name}' not found")
    return {"status": "updated", "ingredient": updated}

@app.patch("/api/inventory/{name}/stock", tags=["Track Stock (CRUD)"])
def set_ingredient_stock(name: str, req: StockPatch):
    """Quick manual update to current stock level."""
    updated = db_instance.update_stock(name, req.new_stock)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Ingredient '{name}' not found")
    return {"status": "stock_updated", "ingredient": updated}

@app.delete("/api/inventory/{name}", tags=["Track Stock (CRUD)"])
def delete_ingredient(name: str):
    """Remove an ingredient from the catalog."""
    deleted = db_instance.delete_ingredient(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Ingredient '{name}' not found")
    return {"status": "deleted", "name": name}

# ==========================
# 3. Sales Tracking & History
# ==========================
@app.post("/api/sales", status_code=status.HTTP_201_CREATED, tags=["Sales & Transactions"])
def record_customer_sale(sale: SaleCreate):
    """
    Quest Requirement: Record what was sold.
    Logs the transaction and automatically decrements stock in MongoDB.
    """
    try:
        res = db_instance.record_sale(
            product_name=sale.product_name,
            quantity=sale.quantity,
            date_str=sale.date,
            store_id=sale.store_id
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sales", tags=["Sales & Transactions"])
def get_sales_history(product_name: Optional[str] = None, limit: Optional[int] = Query(default=100, le=2000)):
    """Retrieve sales transaction records with optional product filtering."""
    history = db_instance.get_sales_history(product_name=product_name, limit=limit)
    return {"total_records": len(history), "sales": history}

# ==========================
# 4. Prophecy & Forecasting
# ==========================
@app.get("/api/prophecy", tags=["Prophecy (Forecasting)"])
def get_prophecy(curse: Optional[bool] = None):
    """
    Quest Requirement: Prophecy – predict which ingredients run out, and when.
    Calculates depletion dates and stockout risk under normal or 3x festival curse conditions.
    """
    active_curse = server_state["curse_active"] if curse is None else curse
    prophecies = engine.get_forecast_and_depletion(curse_active=active_curse)
    return {
        "curse_active": active_curse,
        "total_ingredients_monitored": len(prophecies),
        "prophecies": prophecies
    }

@app.get("/api/prophecy/forecast/{product_name}", tags=["Prophecy (Forecasting)"])
def get_multi_day_product_forecast(product_name: str, days: int = Query(default=14, ge=1, le=60)):
    """Get day-by-day projected demand with weekend gathering weighting."""
    fc = engine.get_multi_day_forecast(product_name, days=days, curse_active=server_state["curse_active"])
    if not fc:
        raise HTTPException(status_code=404, detail=f"Ingredient '{product_name}' not found")
    return fc

# ==========================
# 5. Restock Spell (Optimization)
# ==========================
@app.get("/api/restock/recommendations", tags=["Restock Spell"])
def get_restock_recommendations():
    """
    Quest Requirement: Restock spell – recommend how much to reorder.
    Calculates dynamic Reorder Point (ROP = (Demand * LeadTime) + SafetyStock).
    """
    prophecies = engine.get_forecast_and_depletion(curse_active=server_state["curse_active"])
    recommendations = [
        {
            "product_name": p["product_name"],
            "supplier": p["supplier"],
            "lead_time_days": p["lead_time_days"],
            "current_stock": p["current_stock"],
            "reorder_point": p["reorder_point"],
            "recommended_order_quantity": p["recommended_reorder_qty"],
            "unit": p["unit"],
            "urgency": p["status"],
            "action_needed": p["recommended_reorder_qty"] > 0
        }
        for p in prophecies
    ]
    return {"recommendations": recommendations}

@app.post("/api/restock/order", tags=["Restock Spell"])
def dispatch_restock_order(req: RestockCreate):
    """Replenishes stock for an ingredient."""
    try:
        res = db_instance.record_restock(req.product_name, req.quantity)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================
# 6. Strange Happenings (Anomalies)
# ==========================
@app.get("/api/anomalies", tags=["Strange Happenings"])
def detect_consumption_anomalies(z_threshold: float = Query(default=2.8, ge=1.5, le=5.0)):
    """
    Quest Requirement: Flag unusual consumption.
    Detects consumption spikes and returns validation metrics against Whispering Woods ground truth.
    """
    return engine.detect_anomalies(z_threshold=z_threshold)

# ==========================
# 7. Midnight Curse (Slide 16 Twist)
# ==========================
@app.get("/api/curse", tags=["Midnight Curse"])
def get_curse_status():
    """Returns current Midnight Curse toggle state and scenario details."""
    return {
        "curse_active": server_state["curse_active"],
        "curse_description": "Full Moon Harvest Festival: Demand for Moonflower, Phoenix Feather, and Enchanted Mushroom triples (3.0x).",
        "scenario": db_instance.get_festival_scenario()
    }

@app.post("/api/curse/toggle", tags=["Midnight Curse"])
def toggle_midnight_curse(toggle: CurseToggle):
    """Activate or deactivate the Full Moon 3x demand surge."""
    server_state["curse_active"] = toggle.activate
    return {
        "curse_active": server_state["curse_active"],
        "message": "🔥 Full Moon Festival activated! Demand tripled for 3 ingredients." if toggle.activate else "🌙 Returned to standard demand rhythm."
    }

# ==========================
# 8. Crystal Ball Analytics
# ==========================
@app.get("/api/analytics/crystal-ball", tags=["Crystal Ball"])
def get_crystal_ball_analytics():
    """High-level summary metrics, category distribution, and top sellers."""
    return engine.get_crystal_ball_summary()

# ==========================
# 9. Admin Demo Reset
# ==========================
@app.post("/api/admin/reset", tags=["Admin"])
def reset_to_demo_state():
    """Resets all collections back to clean initial demo state for fresh presentations."""
    res = db_instance.reset_demo_data()
    server_state["curse_active"] = False
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
