"""FastAPI application factory."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import Settings
from .database import create_engine_from_settings, create_session_factory, init_database
from .models import InventoryItem, MealPlan, MealPlanEntry, Recipe, RecipeIngredient
from .schemas import (
    IngredientPayload,
    InventoryConsumeRequest,
    InventoryConsumeResponse,
    InventoryCreate,
    InventoryOut,
    MealPlanCreate,
    MealPlanEntryOut,
    MealPlanOut,
    RecipeCreate,
    RecipeOut,
    RecipeScrapeRequest,
    ShoppingListItem,
    ShoppingListResponse,
)
from .services import recipe_scraper


def normalize_name(name: str) -> str:
    return name.strip().lower()


def create_app(*, testing: bool = False) -> FastAPI:
    settings = Settings()
    settings = settings.model_copy(update={"testing": testing})

    engine = create_engine_from_settings(settings, testing=testing)
    init_database(engine)
    SessionLocal = create_session_factory(engine)

    app = FastAPI(title="Shopping List Assistant", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_db() -> Session:
        with SessionLocal() as session:
            yield session

    app.dependency_overrides = {}

    @app.post("/recipes", response_model=RecipeOut, status_code=201)
    def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db)):
        recipe = Recipe(title=payload.title, instructions=payload.instructions, source_url=payload.source_url)
        db.add(recipe)
        for ingredient in payload.ingredients:
            recipe.ingredients.append(
                RecipeIngredient(
                    name=ingredient.name,
                    normalized_name=normalize_name(ingredient.name),
                    quantity=ingredient.quantity,
                    unit=ingredient.unit,
                )
            )
        db.commit()
        db.refresh(recipe)
        return serialize_recipe(recipe)

    @app.post("/recipes/scrape", response_model=RecipeOut, status_code=201)
    def scrape_recipe(request: RecipeScrapeRequest, db: Session = Depends(get_db)):
        scraped = recipe_scraper.fetch_recipe_from_url(str(request.url))
        if not scraped:
            raise HTTPException(status_code=400, detail="Unable to extract recipe from URL")

        payload = RecipeCreate(**scraped)
        return create_recipe(payload, db)

    @app.get("/recipes", response_model=list[RecipeOut])
    def list_recipes(db: Session = Depends(get_db)):
        recipes = db.query(Recipe).all()
        return [serialize_recipe(recipe) for recipe in recipes]

    @app.post("/inventory", response_model=InventoryOut, status_code=201)
    def add_inventory_item(payload: InventoryCreate, db: Session = Depends(get_db)):
        normalized = normalize_name(payload.name)
        existing = db.query(InventoryItem).filter_by(normalized_name=normalized).one_or_none()
        if existing:
            existing.quantity += payload.quantity
            existing.unit = payload.unit or existing.unit
            existing.expires_on = payload.expires_on or existing.expires_on
            db.commit()
            db.refresh(existing)
            return serialize_inventory(existing)

        item = InventoryItem(
            name=payload.name,
            normalized_name=normalized,
            quantity=payload.quantity,
            unit=payload.unit,
            expires_on=payload.expires_on,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return serialize_inventory(item)

    @app.get("/inventory", response_model=list[InventoryOut])
    def list_inventory(db: Session = Depends(get_db)):
        items = db.query(InventoryItem).order_by(InventoryItem.name).all()
        return [serialize_inventory(item) for item in items]

    @app.post("/inventory/{item_id}/consume", response_model=InventoryConsumeResponse)
    def consume_inventory(item_id: str, payload: InventoryConsumeRequest, db: Session = Depends(get_db)):
        item = db.get(InventoryItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item.quantity -= payload.quantity
        if item.quantity <= 0:
            db.delete(item)
            db.commit()
            return InventoryConsumeResponse(id=item_id, name=item.name, removed=True)
        db.commit()
        db.refresh(item)
        return InventoryConsumeResponse(id=item.id, name=item.name, quantity=item.quantity, removed=False)

    @app.post("/meal-plans", response_model=MealPlanOut, status_code=201)
    def create_meal_plan(payload: MealPlanCreate, db: Session = Depends(get_db)):
        plan = (
            db.query(MealPlan)
            .filter(MealPlan.week_start == payload.week_start)
            .one_or_none()
        )
        if plan:
            plan.entries.clear()
        else:
            plan = MealPlan(week_start=payload.week_start)
            db.add(plan)
        db.flush()
        for entry in payload.entries:
            recipe = db.get(Recipe, entry.recipe_id)
            if not recipe:
                raise HTTPException(status_code=404, detail=f"Recipe {entry.recipe_id} not found")
            plan.entries.append(
                MealPlanEntry(
                    day=entry.day.lower(),
                    meal=entry.meal.lower(),
                    recipe_id=recipe.id,
                    servings=entry.servings,
                )
            )
        db.commit()
        db.refresh(plan)
        return serialize_meal_plan(plan)

    @app.get("/meal-plans", response_model=MealPlanOut | None)
    def get_meal_plan(week_start: date, db: Session = Depends(get_db)):
        plan = (
            db.query(MealPlan)
            .filter(MealPlan.week_start == week_start)
            .one_or_none()
        )
        if not plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")
        return serialize_meal_plan(plan)

    @app.get("/shopping-list", response_model=ShoppingListResponse)
    def generate_shopping_list(week_start: date, db: Session = Depends(get_db)):
        plan = (
            db.query(MealPlan)
            .filter(MealPlan.week_start == week_start)
            .one_or_none()
        )
        if not plan:
            raise HTTPException(status_code=404, detail="Meal plan not found")

        required = defaultdict(float)
        units: dict[tuple[str, str | None], str | None] = {}
        for entry in plan.entries:
            recipe = entry.recipe
            if not recipe:
                continue
            for ingredient in recipe.ingredients:
                key = (ingredient.normalized_name, ingredient.unit or "")
                units[key] = ingredient.unit
                required[key] += ingredient.quantity * entry.servings

        inventory_totals = defaultdict(float)
        for item in db.query(InventoryItem).all():
            key = (item.normalized_name, item.unit or "")
            inventory_totals[key] += item.quantity

        items: list[ShoppingListItem] = []
        for key, needed_qty in required.items():
            available = inventory_totals.get(key, 0.0)
            deficit = needed_qty - available
            if deficit > 0:
                normalized_name, unit_key = key
                # Recover display name by looking up any recipe ingredient or inventory item
                display_name = find_display_name(normalized_name, db)
                items.append(
                    ShoppingListItem(
                        name=display_name,
                        quantity=round(deficit, 2),
                        unit=units.get(key),
                    )
                )

        return ShoppingListResponse(week_start=week_start, items=items)

    @app.post("/meal-plans/{plan_id}/consume")
    def consume_meal(plan_id: str, payload: dict, db: Session = Depends(get_db)):
        day = payload.get("day")
        meal = payload.get("meal")
        if not day or not meal:
            raise HTTPException(status_code=400, detail="day and meal are required")
        entry = (
            db.query(MealPlanEntry)
            .filter(
                MealPlanEntry.meal_plan_id == plan_id,
                MealPlanEntry.day == day.lower(),
                MealPlanEntry.meal == meal.lower(),
            )
            .one_or_none()
        )
        if not entry:
            raise HTTPException(status_code=404, detail="Meal plan entry not found")
        for ingredient in entry.recipe.ingredients:
            consume_inventory_by_name(
                db,
                ingredient.normalized_name,
                ingredient.quantity * entry.servings,
            )
        db.commit()
        return {"status": "ok"}

    return app


def serialize_recipe(recipe: Recipe) -> RecipeOut:
    return RecipeOut(
        id=recipe.id,
        title=recipe.title,
        instructions=recipe.instructions,
        source_url=recipe.source_url,
        ingredients=[
            IngredientPayload(name=i.name, quantity=i.quantity, unit=i.unit)
            for i in recipe.ingredients
        ],
    )


def serialize_inventory(item: InventoryItem) -> InventoryOut:
    return InventoryOut(
        id=item.id,
        name=item.name,
        quantity=item.quantity,
        unit=item.unit,
        expires_on=item.expires_on,
    )


def serialize_meal_plan(plan: MealPlan) -> MealPlanOut:
    entries = [
        MealPlanEntryOut(
            day=entry.day,
            meal=entry.meal,
            recipe_id=entry.recipe_id,
            servings=entry.servings,
            recipe_title=entry.recipe.title if entry.recipe else "",
        )
        for entry in plan.entries
    ]
    return MealPlanOut(id=plan.id, week_start=plan.week_start, entries=entries)


def consume_inventory_by_name(db: Session, normalized_name: str, quantity: float) -> None:
    item = (
        db.query(InventoryItem)
        .filter(InventoryItem.normalized_name == normalized_name)
        .one_or_none()
    )
    if not item:
        return
    item.quantity -= quantity
    if item.quantity < 0:
        item.quantity = 0


def find_display_name(normalized_name: str, db: Session) -> str:
    item = (
        db.query(InventoryItem)
        .filter(InventoryItem.normalized_name == normalized_name)
        .one_or_none()
    )
    if item:
        return item.name
    ingredient = (
        db.query(RecipeIngredient)
        .filter(RecipeIngredient.normalized_name == normalized_name)
        .first()
    )
    if ingredient:
        return ingredient.name
    return normalized_name


app = create_app()
