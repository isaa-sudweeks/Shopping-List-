"""Pydantic schemas for request/response payloads."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class IngredientPayload(BaseModel):
    name: str
    quantity: float
    unit: Optional[str] = None


class RecipeCreate(BaseModel):
    title: str
    ingredients: list[IngredientPayload]
    instructions: Optional[str] = None
    source_url: Optional[HttpUrl | str] = Field(default=None)


class RecipeOut(BaseModel):
    id: str
    title: str
    instructions: Optional[str]
    source_url: Optional[str]
    ingredients: list[IngredientPayload]


class InventoryCreate(BaseModel):
    name: str
    quantity: float
    unit: Optional[str] = None
    expires_on: Optional[date] = None


class InventoryOut(BaseModel):
    id: str
    name: str
    quantity: float
    unit: Optional[str]
    expires_on: Optional[date]


class InventoryConsumeRequest(BaseModel):
    quantity: float


class InventoryConsumeResponse(BaseModel):
    id: str
    name: str
    quantity: float | None = None
    removed: bool = False


class RecipeScrapeRequest(BaseModel):
    url: HttpUrl


class MealPlanEntryCreate(BaseModel):
    day: str
    meal: str
    recipe_id: str
    servings: float = 1.0


class MealPlanCreate(BaseModel):
    week_start: date
    entries: list[MealPlanEntryCreate]


class MealPlanEntryOut(BaseModel):
    day: str
    meal: str
    recipe_id: str
    servings: float
    recipe_title: str


class MealPlanOut(BaseModel):
    id: str
    week_start: date
    entries: list[MealPlanEntryOut]


class ShoppingListItem(BaseModel):
    name: str
    quantity: float
    unit: Optional[str] = None


class ShoppingListResponse(BaseModel):
    week_start: date
    items: list[ShoppingListItem]
