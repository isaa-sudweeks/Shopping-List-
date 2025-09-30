"""Database models for the shopping backend."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Recipe(Base, TimestampMixin):
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(255))
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    recipe: Mapped[Recipe] = relationship("Recipe", back_populates="ingredients")


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("normalized_name", name="uq_inventory_normalized_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expires_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class MealPlan(Base, TimestampMixin):
    __tablename__ = "meal_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    week_start: Mapped[date] = mapped_column(Date, index=True)

    entries: Mapped[list["MealPlanEntry"]] = relationship(
        "MealPlanEntry", back_populates="plan", cascade="all, delete-orphan"
    )


class MealPlanEntry(Base, TimestampMixin):
    __tablename__ = "meal_plan_entries"
    __table_args__ = (
        UniqueConstraint("meal_plan_id", "day", "meal", name="uq_plan_day_meal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    meal_plan_id: Mapped[str] = mapped_column(ForeignKey("meal_plans.id", ondelete="CASCADE"))
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    day: Mapped[str] = mapped_column(String(20))
    meal: Mapped[str] = mapped_column(String(20))
    servings: Mapped[float] = mapped_column(Float, default=1.0)

    plan: Mapped[MealPlan] = relationship("MealPlan", back_populates="entries")
    recipe: Mapped[Recipe] = relationship("Recipe")
