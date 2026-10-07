"""
Maps YOLO class names to Spoonacular ingredient names.

The model and Spoonacular speak different vocabularies: the model emits
dataset class names ("chilli", "canned food"), Spoonacular expects
ingredient names ("chili pepper"). This module is the single place that
translation happens.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAP_PATH = ROOT / "backend" / "config" / "spoonacular_map.yaml"
DEFAULT_DATA_YAML = ROOT / "datasets" / "final_food_dataset" / "data.yaml"


@dataclass
class MappedIngredients:
    """Result of mapping a set of detected classes."""

    # Spoonacular ingredient names, de-duplicated, in first-seen order
    ingredients: list[str] = field(default_factory=list)

    # Spoonacular ingredient name -> class names that produced it
    sources: dict[str, list[str]] = field(default_factory=dict)

    # Classes deliberately not sent to Spoonacular (mapped to null)
    skipped: list[str] = field(default_factory=list)

    # Classes missing from the map entirely (map needs updating)
    unknown: list[str] = field(default_factory=list)


class IngredientMapper:

    def __init__(self, map_path: Path = DEFAULT_MAP_PATH):
        self.map_path = Path(map_path)
        self.class_map = self._load(self.map_path)

    @staticmethod
    def _load(map_path: Path) -> dict[str, str | None]:
        with open(map_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        class_map = {}
        for class_name, query in raw.items():
            if query is not None and not isinstance(query, str):
                raise ValueError(
                    f"{map_path}: '{class_name}' must map to a string or null, "
                    f"got {query!r}"
                )
            class_map[str(class_name).strip().lower()] = (
                query.strip() if query else None
            )
        return class_map

    def map_classes(self, class_names: Iterable[str]) -> MappedIngredients:
        result = MappedIngredients()

        for name in class_names:
            key = name.strip().lower()

            if key not in self.class_map:
                if key not in result.unknown:
                    result.unknown.append(key)
                continue

            query = self.class_map[key]
            if query is None:
                if key not in result.skipped:
                    result.skipped.append(key)
                continue

            if query not in result.sources:
                result.ingredients.append(query)
                result.sources[query] = []
            if key not in result.sources[query]:
                result.sources[query].append(key)

        return result

    def map_detections(
        self,
        detections: Iterable[tuple[str, float]],
        min_confidence: float = 0.4,
    ) -> MappedIngredients:
        """Map (class_name, confidence) pairs, dropping low-confidence ones."""
        return self.map_classes(
            name for name, confidence in detections
            if confidence >= min_confidence
        )

    def check_coverage(self, data_yaml: Path = DEFAULT_DATA_YAML) -> dict[str, list[str]]:
        """Compare the map against the model's class list."""
        with open(data_yaml, "r", encoding="utf-8") as f:
            names = yaml.safe_load(f)["names"]

        model_classes = {
            str(n).strip().lower()
            for n in (names.values() if isinstance(names, dict) else names)
        }
        mapped = set(self.class_map)

        return {
            "missing_from_map": sorted(model_classes - mapped),
            "not_in_model": sorted(mapped - model_classes),
        }
