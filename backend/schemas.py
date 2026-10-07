from typing import Any

from pydantic import BaseModel, Field


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: list[float] = Field(description="[x1, y1, x2, y2] in image pixels")


class DetectResponse(BaseModel):
    detections: list[Detection]

    # Suggested Spoonacular ingredients, for the user to confirm or edit
    ingredients: list[str]

    # Spoonacular ingredient -> class names that produced it
    sources: dict[str, list[str]]

    # Detected but deliberately not suggested (e.g. "spices", "canned food")
    skipped: list[str]

    # Detected but missing from spoonacular_map.yaml
    unknown: list[str]


class RecipeSearchRequest(BaseModel):
    # The user-confirmed list. Sent to Spoonacular as-is, so it may contain
    # anything the user typed (sugar, chili powder...), not just model classes.
    ingredients: list[str] = Field(min_length=1, max_length=30)
    number: int = Field(default=10, ge=1, le=50)
    ranking: int = Field(default=1, ge=1, le=2, description="1 = use most ingredients, 2 = fewest missing")
    ignore_pantry: bool = True


class RecipeSummary(BaseModel):
    id: int
    title: str
    image: str | None = None
    used_ingredients: list[str]
    missed_ingredients: list[str]
    # Spoonacular ingredient IDs, to mark have / missing on the recipe page
    used_ingredient_ids: list[int] = []
    missed_ingredient_ids: list[int] = []
    likes: int = 0


class RecipeSearchResponse(BaseModel):
    recipes: list[RecipeSummary]
    quota_left: float | None = None


class SuggestionsResponse(BaseModel):
    # Names for the manual-entry autocomplete
    ingredients: list[str]

    # One-tap chips for common ingredients the model can't detect
    often_missed: list[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str | None
    spoonacular_configured: bool
    detail: dict[str, Any] = {}
