"""Recipe scraping utilities."""

from __future__ import annotations

import json
import re
from fractions import Fraction
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup


COMMON_UNITS = {
    "g",
    "gram",
    "grams",
    "kg",
    "ml",
    "l",
    "litre",
    "litres",
    "liter",
    "liters",
    "cup",
    "cups",
    "tsp",
    "teaspoon",
    "teaspoons",
    "tbsp",
    "tablespoon",
    "tablespoons",
    "ounce",
    "ounces",
    "oz",
    "lb",
    "lbs",
    "pound",
    "pounds",
    "clove",
    "cloves",
    "count",
    "piece",
    "pieces",
    "pinch",
}


def fetch_recipe_from_url(url: str) -> dict[str, Any] | None:
    """Download and parse a recipe from the provided URL."""
    with httpx.Client(follow_redirects=True, timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")
    json_ld_recipe = _extract_json_ld_recipe(soup)
    if json_ld_recipe:
        return _convert_recipe(json_ld_recipe, url)

    return _fallback_extract(soup, url)


def _extract_json_ld_recipe(soup: BeautifulSoup) -> Optional[dict[str, Any]]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        recipe = _locate_recipe_node(data)
        if recipe:
            return recipe
    return None


def _locate_recipe_node(data: Any) -> Optional[dict[str, Any]]:
    if isinstance(data, dict):
        if data.get("@type") in {"Recipe", ["Recipe"]}:
            return data
        if "@graph" in data:
            for node in data["@graph"]:
                recipe = _locate_recipe_node(node)
                if recipe:
                    return recipe
    elif isinstance(data, list):
        for item in data:
            recipe = _locate_recipe_node(item)
            if recipe:
                return recipe
    return None


def _convert_recipe(raw: dict[str, Any], url: str) -> dict[str, Any]:
    title = raw.get("name") or "Untitled Recipe"
    instructions = _extract_instructions(raw.get("recipeInstructions"))
    ingredients = raw.get("recipeIngredient") or raw.get("ingredients") or []
    parsed_ingredients = [_parse_ingredient(item) for item in ingredients]
    return {
        "title": title,
        "instructions": instructions,
        "ingredients": parsed_ingredients,
        "source_url": url,
    }


def _fallback_extract(soup: BeautifulSoup, url: str) -> dict[str, Any] | None:
    title_tag = soup.find("h1") or soup.find("title")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)
    ingredient_nodes = soup.select("li.ingredient, .ingredients li")
    if not ingredient_nodes:
        return None
    parsed_ingredients = [_parse_ingredient(node.get_text(" ", strip=True)) for node in ingredient_nodes]
    instructions_nodes = soup.select("li.instruction, .instructions li, .direction")
    instructions = "\n".join(node.get_text(" ", strip=True) for node in instructions_nodes) or None
    return {
        "title": title,
        "instructions": instructions,
        "ingredients": parsed_ingredients,
        "source_url": url,
    }


def _extract_instructions(raw_instructions: Any) -> Optional[str]:
    if not raw_instructions:
        return None
    if isinstance(raw_instructions, str):
        return raw_instructions.strip()
    if isinstance(raw_instructions, list):
        steps = []
        for step in raw_instructions:
            if isinstance(step, dict):
                text = step.get("text") or step.get("@type")
            else:
                text = str(step)
            if text:
                steps.append(text.strip())
        return "\n".join(steps) if steps else None
    if isinstance(raw_instructions, dict):
        return raw_instructions.get("text")
    return None


def _parse_ingredient(ingredient: Any) -> dict[str, Any]:
    if isinstance(ingredient, dict):
        name = ingredient.get("name") or ingredient.get("text") or ""
    else:
        name = str(ingredient)
    name = name.strip()
    quantity, unit, item_name = _split_quantity_unit(name)
    return {"name": item_name, "quantity": quantity, "unit": unit}


def _split_quantity_unit(text: str) -> tuple[float, Optional[str], str]:
    tokens = text.split()
    if not tokens:
        return 1.0, None, ""

    quantity = 1.0
    unit: Optional[str] = None
    remainder_tokens = tokens[:]

    first = tokens[0]
    quantity_candidate = _parse_numeric(first)
    if quantity_candidate is not None:
        quantity = quantity_candidate
        remainder_tokens = tokens[1:]
        if remainder_tokens:
            potential_unit = remainder_tokens[0].lower().rstrip(".,")
            if potential_unit in COMMON_UNITS:
                unit = remainder_tokens[0]
                remainder_tokens = remainder_tokens[1:]
    return quantity, unit, " ".join(remainder_tokens).strip() or text


def _parse_numeric(value: str) -> Optional[float]:
    value = value.strip()
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        pass
    mixed = re.match(r"^(\d+)\s+(\d+/\d+)$", value)
    if mixed:
        whole, fraction = mixed.groups()
        return float(whole) + float(Fraction(fraction))
    return None
