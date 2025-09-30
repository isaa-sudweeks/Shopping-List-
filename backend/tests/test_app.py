import datetime
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client():
    from app.main import create_app
    app = create_app(testing=True)
    return TestClient(app)


def test_scrape_recipe_and_persist(client, monkeypatch):
    sample_recipe = {
        "title": "Test Pasta",
        "ingredients": [
            {"name": "pasta", "quantity": 200, "unit": "g"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
        ],
        "instructions": "Boil pasta. Toss with oil.",
        "source_url": "https://example.com/recipe",
    }

    def mock_scrape(url: str):
        assert url == sample_recipe["source_url"]
        return sample_recipe

    from app.services import recipe_scraper
    monkeypatch.setattr(recipe_scraper, "fetch_recipe_from_url", mock_scrape)

    response = client.post("/recipes/scrape", json={"url": sample_recipe["source_url"]})
    assert response.status_code == 201
    body = response.json()
    recipe_id = body["id"]
    assert body["title"] == sample_recipe["title"]
    assert len(body["ingredients"]) == 2

    list_response = client.get("/recipes")
    assert list_response.status_code == 200
    recipes = list_response.json()
    assert any(r["id"] == recipe_id for r in recipes)


def test_inventory_lifecycle(client):
    new_item = {
        "name": "Milk",
        "quantity": 2,
        "unit": "liters",
        "expires_on": datetime.date.today().isoformat(),
    }

    response = client.post("/inventory", json=new_item)
    assert response.status_code == 201
    item_id = response.json()["id"]

    listing = client.get("/inventory")
    assert listing.status_code == 200
    items = listing.json()
    assert any(item["id"] == item_id for item in items)

    consume_resp = client.post(f"/inventory/{item_id}/consume", json={"quantity": 1})
    assert consume_resp.status_code == 200
    assert consume_resp.json()["quantity"] == 1

    consume_resp = client.post(f"/inventory/{item_id}/consume", json={"quantity": 1})
    assert consume_resp.status_code == 200
    assert consume_resp.json()["removed"] is True

    listing = client.get("/inventory")
    assert listing.status_code == 200
    assert all(item["id"] != item_id for item in listing.json())


def test_meal_plan_and_shopping_list(client):
    # Seed inventory and recipes
    inventory_payload = {
        "name": "Eggs",
        "quantity": 4,
        "unit": "count",
        "expires_on": datetime.date.today().isoformat(),
    }
    client.post("/inventory", json=inventory_payload)

    recipe_payload = {
        "title": "Omelette",
        "ingredients": [
            {"name": "Eggs", "quantity": 6, "unit": "count"},
            {"name": "Cheese", "quantity": 100, "unit": "g"},
        ],
        "instructions": "Whisk eggs, cook with cheese.",
        "source_url": None,
    }
    recipe_response = client.post("/recipes", json=recipe_payload)
    assert recipe_response.status_code == 201
    recipe_id = recipe_response.json()["id"]

    plan_payload = {
        "week_start": datetime.date.today().isoformat(),
        "entries": [
            {
                "day": "monday",
                "meal": "dinner",
                "recipe_id": recipe_id,
                "servings": 1,
            }
        ],
    }
    plan_response = client.post("/meal-plans", json=plan_payload)
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["id"]

    list_response = client.get(
        "/shopping-list",
        params={"week_start": plan_payload["week_start"]},
    )
    assert list_response.status_code == 200
    shopping_items = list_response.json()["items"]

    eggs_item = next(item for item in shopping_items if item["name"].lower() == "eggs")
    assert eggs_item["quantity"] == 2
    assert eggs_item["unit"] == "count"

    cheese_item = next(item for item in shopping_items if item["name"].lower() == "cheese")
    assert cheese_item["quantity"] == 100

    consume_response = client.post(f"/meal-plans/{plan_id}/consume", json={"day": "monday", "meal": "dinner"})
    assert consume_response.status_code == 200

    inventory = client.get("/inventory").json()
    eggs_in_stock = next(item for item in inventory if item["name"].lower() == "eggs")
    assert eggs_in_stock["quantity"] == 0

    cheese_stock = [item for item in inventory if item["name"].lower() == "cheese"]
    assert not cheese_stock
