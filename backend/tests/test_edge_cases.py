import datetime
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def client():
    from app.main import create_app
    app = create_app(testing=True)
    return TestClient(app)

def test_create_recipe_invalid_data(client):
    # Missing required fields
    response = client.post("/recipes", json={"title": "Incomplete Recipe"})
    assert response.status_code == 422

def test_scrape_recipe_invalid_url(client):
    response = client.post("/recipes/scrape", json={"url": "not-a-url"})
    # Pydantic validation might catch this as invalid URL format, or it might fail later
    # Depending on validation, it could be 422 or 400. Let's assume 422 for bad format or 400 for logic.
    # Given the schema likely uses HttpUrl, it's probably 422.
    assert response.status_code in (400, 422)

def test_scrape_recipe_failure(client, monkeypatch):
    def mock_scrape_fail(url: str):
        return None

    from app.services import recipe_scraper
    monkeypatch.setattr(recipe_scraper, "fetch_recipe_from_url", mock_scrape_fail)

    response = client.post("/recipes/scrape", json={"url": "https://example.com/fail"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Unable to extract recipe from URL"

def test_inventory_duplicate_item_updates_quantity(client):
    item = {
        "name": "Apples",
        "quantity": 5,
        "unit": "count",
        "expires_on": datetime.date.today().isoformat(),
    }
    
    # First add
    resp1 = client.post("/inventory", json=item)
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]
    
    # Second add (same name)
    resp2 = client.post("/inventory", json=item)
    assert resp2.status_code == 201
    id2 = resp2.json()["id"]
    
    assert id1 == id2
    assert resp2.json()["quantity"] == 10

def test_consume_inventory_invalid_id(client):
    response = client.post("/inventory/non-existent-id/consume", json={"quantity": 1})
    assert response.status_code == 404

def test_consume_inventory_more_than_available(client):
    # Add item first
    item = {"name": "Bread", "quantity": 1, "unit": "loaf"}
    resp = client.post("/inventory", json=item)
    item_id = resp.json()["id"]
    
    # Consume more than available
    consume_resp = client.post(f"/inventory/{item_id}/consume", json={"quantity": 5})
    # The current logic allows consuming more, it just deletes the item. 
    # Let's verify it deletes the item.
    assert consume_resp.status_code == 200
    assert consume_resp.json()["removed"] is True
    
    # Verify it's gone
    get_resp = client.get("/inventory")
    items = get_resp.json()
    assert not any(i["id"] == item_id for i in items)

def test_create_meal_plan_invalid_recipe(client):
    payload = {
        "week_start": datetime.date.today().isoformat(),
        "entries": [
            {
                "day": "monday",
                "meal": "dinner",
                "recipe_id": "non-existent-id",
                "servings": 2
            }
        ]
    }
    response = client.post("/meal-plans", json=payload)
    assert response.status_code == 404

def test_get_shopping_list_no_meal_plan(client):
    # Ensure no meal plan exists for a far future date
    future_date = (datetime.date.today() + datetime.timedelta(days=3650)).isoformat()
    response = client.get("/shopping-list", params={"week_start": future_date})
    assert response.status_code == 404

def test_consume_meal_plan_invalid_plan(client):
    response = client.post("/meal-plans/non-existent-plan/consume", json={"day": "monday", "meal": "dinner"})
    # Should probably be 404 because plan doesn't exist, or 404 because entry doesn't exist
    # The endpoint logic queries MealPlanEntry directly by plan_id.
    assert response.status_code == 404

def test_consume_meal_plan_invalid_entry(client):
    # Create a plan first
    # Need a recipe first
    recipe_resp = client.post("/recipes", json={
        "title": "Toast", 
        "ingredients": [{"name": "Bread", "quantity": 1}],
        "instructions": "Toast it"
    })
    recipe_id = recipe_resp.json()["id"]
    
    plan_resp = client.post("/meal-plans", json={
        "week_start": datetime.date.today().isoformat(),
        "entries": [{"day": "monday", "meal": "breakfast", "recipe_id": recipe_id, "servings": 1}]
    })
    plan_id = plan_resp.json()["id"]
    
    # Try to consume a different meal
    response = client.post(f"/meal-plans/{plan_id}/consume", json={"day": "tuesday", "meal": "dinner"})
    assert response.status_code == 404
