import sys
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_all():
    print("🧙 Starting Comprehensive API Route Audit for Madam Hexley's Potion Pantry...")
    passed = 0
    total = 0

    def assert_test(desc, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ FAILED: {desc} -> {details}")
            sys.exit(1)

    # 1. Root & Health
    r = client.get("/")
    assert_test("GET / (Website Index HTML)", r.status_code == 200 and "Potion Pantry" in r.text)

    r = client.get("/api/info")
    assert_test("GET /api/info (Root Meta)", r.status_code == 200 and r.json()["service"] == "Potion Pantry Smart Inventory Engine")

    r = client.get("/api/health")
    assert_test("GET /api/health", r.status_code == 200 and r.json()["database_connected"] is True)

    # 2. Inventory Listing
    r = client.get("/api/inventory")
    assert_test("GET /api/inventory", r.status_code == 200 and len(r.json()["ingredients"]) >= 10)

    # 3. Single Ingredient Retrieval
    r = client.get("/api/inventory/Moonflower")
    assert_test("GET /api/inventory/Moonflower", r.status_code == 200 and r.json()["category"] == "Flora & Herbs")

    # 4. Create New Ingredient (CRUD: Add)
    test_ing = {
        "name": "Ghost Orchid",
        "category": "Flora & Herbs",
        "current_stock": 50,
        "safety_stock": 15,
        "supplier": "Phantom Hollow Harvesters",
        "lead_time_days": 5,
        "unit": "petals"
    }
    r = client.post("/api/inventory", json=test_ing)
    assert_test("POST /api/inventory (Add Ingredient)", r.status_code == 201 and r.json()["ingredient"]["name"] == "Ghost Orchid")

    # 5. Update Ingredient Details (CRUD: Update)
    r = client.put("/api/inventory/Ghost Orchid", json={"safety_stock": 20})
    assert_test("PUT /api/inventory/{name} (Update Details)", r.status_code == 200 and r.json()["ingredient"]["safety_stock"] == 20)

    # 6. Patch Stock (CRUD: Update Stock)
    r = client.patch("/api/inventory/Ghost Orchid/stock", json={"new_stock": 75})
    assert_test("PATCH /api/inventory/{name}/stock", r.status_code == 200 and r.json()["ingredient"]["current_stock"] == 75)

    # 7. Record Sale (Track Stock: Record what was sold)
    sale_payload = {"product_name": "Ghost Orchid", "quantity": 10}
    r = client.post("/api/sales", json=sale_payload)
    assert_test("POST /api/sales (Deduct Stock & Log Sale)", r.status_code == 201 and r.json()["remaining_stock"] == 65)

    # 8. Sales History
    r = client.get("/api/sales?product_name=Ghost Orchid&limit=10")
    assert_test("GET /api/sales (Fetch Sales History)", r.status_code == 200 and len(r.json()["sales"]) >= 1)

    # 9. Restock Order (Replenishment)
    r = client.post("/api/restock/order", json={"product_name": "Ghost Orchid", "quantity": 30})
    assert_test("POST /api/restock/order (Replenish Stock)", r.status_code == 200 and r.json()["new_stock"] == 95)

    # 10. Delete Ingredient (CRUD: Delete)
    r = client.delete("/api/inventory/Ghost Orchid")
    assert_test("DELETE /api/inventory/{name} (Remove Ingredient)", r.status_code == 200 and r.json()["status"] == "deleted")

    # 11. Prophecy (Runout Predictions)
    r = client.get("/api/prophecy")
    assert_test("GET /api/prophecy (Normal)", r.status_code == 200 and len(r.json()["prophecies"]) >= 10)

    # 12. Multi-day Forecast Charting Data
    r = client.get("/api/prophecy/forecast/Moonflower?days=7")
    assert_test("GET /api/prophecy/forecast/{name}", r.status_code == 200 and len(r.json()["daily_projections"]) == 7)

    # 13. Restock Recommendations & ROP
    r = client.get("/api/restock/recommendations")
    assert_test("GET /api/restock/recommendations", r.status_code == 200 and len(r.json()["recommendations"]) >= 10)

    # 14. Strange Happenings (Anomaly Detection)
    r = client.get("/api/anomalies?z_threshold=2.8")
    data = r.json()
    assert_test("GET /api/anomalies (Outbreak Detection)", r.status_code == 200 and data["metrics"]["true_positives"] == 5 and data["metrics"]["f1_score"] == 1.0)

    # 15. Midnight Curse Status & Toggle
    r = client.get("/api/curse")
    assert_test("GET /api/curse (Scenario Status)", r.status_code == 200 and len(r.json()["scenario"]) == 10)

    r = client.post("/api/curse/toggle", json={"activate": True})
    assert_test("POST /api/curse/toggle (Activate 3x Surge)", r.status_code == 200 and r.json()["curse_active"] is True)

    # Verify Prophecy under Curse reflects the 3x surge
    r = client.get("/api/prophecy")
    moonflower = next(p for p in r.json()["prophecies"] if p["product_name"] == "Moonflower")
    assert_test("Curse Impact Verified (Moonflower 3x Multiplier)", moonflower["curse_multiplier"] == 3.0 and moonflower["status"] == "IMMINENT_STOCKOUT")

    # Deactivate Curse
    r = client.post("/api/curse/toggle", json={"activate": False})
    assert_test("POST /api/curse/toggle (Deactivate)", r.status_code == 200 and r.json()["curse_active"] is False)

    # 16. Crystal Ball Analytics
    r = client.get("/api/analytics/crystal-ball")
    assert_test("GET /api/analytics/crystal-ball", r.status_code == 200 and "category_distribution" in r.json())

    # 17. Admin Demo Reset
    r = client.post("/api/admin/reset")
    assert_test("POST /api/admin/reset", r.status_code == 200 and r.json()["status"] == "success")

    print(f"\n🔮 AUDIT COMPLETE: {passed}/{total} routes passed with 100% success!")

if __name__ == "__main__":
    test_all()

