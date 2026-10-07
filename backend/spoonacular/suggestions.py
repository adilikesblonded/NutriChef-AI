"""
Builds the ingredient suggestion lists for the frontend.

Everything here is local data, so serving suggestions costs no API quota.
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

from backend.spoonacular.mapping import IngredientMapper

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
DEFAULT_TOP_1K_PATH = CONFIG_DIR / "spoonacular_top_1k_ingredients.csv"
DEFAULT_SUGGESTIONS_PATH = CONFIG_DIR / "suggestions.yaml"


def _clean(names) -> list[str]:
    return [" ".join(str(n).lower().split()) for n in names if n and str(n).strip()]


def load_top_ingredients(csv_path: Path = DEFAULT_TOP_1K_PATH) -> list[str]:
    with open(csv_path, "r", encoding="utf-8") as f:
        return _clean(row["name"] for row in csv.DictReader(f, delimiter=";"))


def build_suggestions(
    mapper: IngredientMapper,
    top_1k_path: Path = DEFAULT_TOP_1K_PATH,
    suggestions_path: Path = DEFAULT_SUGGESTIONS_PATH,
) -> dict[str, list[str]]:
    with open(suggestions_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    mapped = [q for q in mapper.class_map.values() if q]
    ingredients = set(load_top_ingredients(top_1k_path))
    ingredients.update(_clean(mapped))
    ingredients.update(_clean(config.get("extra", [])))

    return {
        "ingredients": sorted(ingredients),
        "often_missed": _clean(config.get("often_missed", [])),
    }
