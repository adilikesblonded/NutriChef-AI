"""
Thin wrapper around the Spoonacular REST API.

- Reads the API key from .env (SPOONACULAR_API_KEY)
- Caches GET responses on disk so repeated requests don't burn quota
- Tracks the remaining daily quota from response headers

API docs: https://spoonacular.com/food-api/docs
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = ROOT / ".cache" / "spoonacular"

PLACEHOLDER_KEYS = {"", "your_api_key_here"}


class SpoonacularError(Exception):
    pass


class QuotaExceededError(SpoonacularError):
    pass


class SpoonacularClient:

    BASE_URL = "https://api.spoonacular.com"

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | None = DEFAULT_CACHE_DIR,
        cache_ttl: int = 3600,
        timeout: float = 10.0,
    ):
        load_dotenv(ROOT / ".env")
        self.api_key = (api_key or os.getenv("SPOONACULAR_API_KEY") or "").strip()

        if self.api_key in PLACEHOLDER_KEYS:
            raise SpoonacularError(
                "SPOONACULAR_API_KEY is not set. Add your key to the .env file "
                "(get one at https://spoonacular.com/food-api/console#Profile)."
            )

        # Spoonacular's terms limit how long data may be stored, so keep
        # the TTL short; set cache_dir=None to disable caching entirely.
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.cache_ttl = cache_ttl
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers["x-api-key"] = self.api_key

        self.quota_used: float | None = None
        self.quota_left: float | None = None

    # ---------- Recipes ----------

    def find_recipes_by_ingredients(
        self,
        ingredients: list[str],
        number: int = 10,
        ranking: int = 1,
        ignore_pantry: bool = True,
    ) -> list[dict[str, Any]]:
        """
        ranking=1 maximises used ingredients, ranking=2 minimises missing ones.
        """
        if not ingredients:
            return []

        return self._get("/recipes/findByIngredients", {
            "ingredients": ",".join(ingredients),
            "number": number,
            "ranking": ranking,
            "ignorePantry": str(ignore_pantry).lower(),
        })

    def get_recipe_information(
        self,
        recipe_id: int,
        include_nutrition: bool = True,
    ) -> dict[str, Any]:
        return self._get(f"/recipes/{recipe_id}/information", {
            "includeNutrition": str(include_nutrition).lower(),
        })

    # ---------- Ingredients ----------

    def search_ingredient(self, query: str) -> dict[str, Any] | None:
        """Return Spoonacular's best match ({id, name, image}) or None."""
        data = self._get("/food/ingredients/search", {
            "query": query,
            "number": 1,
        })
        results = data.get("results", [])
        return results[0] if results else None

    def get_ingredient_information(
        self,
        ingredient_id: int,
        amount: float = 1,
        unit: str = "serving",
    ) -> dict[str, Any]:
        return self._get(f"/food/ingredients/{ingredient_id}/information", {
            "amount": amount,
            "unit": unit,
        })

    # ---------- HTTP + cache ----------

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        cache_path = self._cache_path(path, params)

        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached

        try:
            response = self.session.get(
                self.BASE_URL + path, params=params, timeout=self.timeout
            )
        except requests.RequestException as e:
            raise SpoonacularError(f"Request to {path} failed: {e}") from e

        self._update_quota(response)

        if response.status_code == 401:
            raise SpoonacularError("Spoonacular rejected the API key (401). Check .env.")
        if response.status_code == 402:
            raise QuotaExceededError("Spoonacular daily quota exceeded (402).")
        if response.status_code == 429:
            raise QuotaExceededError("Spoonacular rate limit hit (429). Slow down.")
        if not response.ok:
            raise SpoonacularError(
                f"Spoonacular {path} returned {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        self._write_cache(cache_path, data)
        return data

    def _update_quota(self, response: requests.Response) -> None:
        for header, attr in (
            ("X-API-Quota-Used", "quota_used"),
            ("X-API-Quota-Left", "quota_left"),
        ):
            value = response.headers.get(header)
            if value is not None:
                try:
                    setattr(self, attr, float(value))
                except ValueError:
                    pass

    def _cache_path(self, path: str, params: dict[str, Any]) -> Path | None:
        if self.cache_dir is None:
            return None
        key = json.dumps([path, sorted(params.items())], default=str)
        digest = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _read_cache(self, cache_path: Path | None) -> Any:
        if cache_path is None or not cache_path.exists():
            return None
        try:
            entry = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if time.time() - entry.get("saved_at", 0) > self.cache_ttl:
            return None
        return entry.get("data")

    def _write_cache(self, cache_path: Path | None, data: Any) -> None:
        if cache_path is None:
            return
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"saved_at": time.time(), "data": data}),
            encoding="utf-8",
        )
