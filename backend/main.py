"""
NutriChef AI backend.

Flow:
    GET  /suggestions     ingredient names for manual entry (local data, no quota)
    POST /detect         image -> detections + suggested ingredients (no Spoonacular call)
    (user confirms / edits the ingredient list in the frontend)
    POST /recipes         confirmed ingredients -> matching recipes
    GET  /recipes/{id}    full recipe with nutrition

Run from the project root:
    python -m uvicorn backend.main:app --reload

Deployed on Render with the ONNX model -- see render.yaml.

Interactive docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.detector import Detector, InvalidImageError
from backend.rate_limit import RateLimiter
from backend.schemas import (
    DetectResponse,
    HealthResponse,
    RecipeSearchRequest,
    RecipeSearchResponse,
    RecipeSummary,
    SuggestionsResponse,
)
from backend.spoonacular import (
    IngredientMapper,
    QuotaExceededError,
    SpoonacularClient,
    SpoonacularError,
    build_suggestions,
)

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

logger = logging.getLogger("nutrichef")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}

# Shared services, created once at startup
services: dict = {}

# Requests that cost Spoonacular quota, per visitor per hour (0 disables)
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "30"))
recipe_limiter = RateLimiter(RATE_LIMIT_PER_HOUR) if RATE_LIMIT_PER_HOUR > 0 else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    services["mapper"] = IngredientMapper()
    services["suggestions"] = build_suggestions(services["mapper"])

    try:
        services["detector"] = Detector()
    except Exception as e:
        logger.error("Model failed to load: %s", e)
        services["detector_error"] = str(e)

    # A missing key shouldn't stop /detect from working
    try:
        services["spoonacular"] = SpoonacularClient()
    except SpoonacularError as e:
        logger.warning("Spoonacular disabled: %s", e)
        services["spoonacular_error"] = str(e)

    yield
    services.clear()


app = FastAPI(title="NutriChef AI", version="0.1.0", lifespan=lifespan)

# Frontend dev servers by default. In production set CORS_ORIGINS to the
# deployed frontend, e.g. CORS_ORIGINS="https://nutrichef.vercel.app", and
# optionally CORS_ORIGIN_REGEX to also allow Vercel preview deployments.
CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_detector() -> Detector:
    if "detector" not in services:
        raise HTTPException(503, f"Model not loaded: {services.get('detector_error')}")
    return services["detector"]


def get_spoonacular() -> SpoonacularClient:
    if "spoonacular" not in services:
        raise HTTPException(503, f"Spoonacular not configured: {services.get('spoonacular_error')}")
    return services["spoonacular"]


def spoonacular_http_error(e: SpoonacularError) -> HTTPException:
    if isinstance(e, QuotaExceededError):
        return HTTPException(
            429,
            "Spoonacular's daily limit has been used up. Try again tomorrow — "
            "searches already run today still work.",
        )
    return HTTPException(502, str(e))


def limit_quota_use(request: Request) -> None:
    """Dependency for endpoints that spend Spoonacular quota."""
    if recipe_limiter is None:
        return
    # Behind Render's proxy, uvicorn --proxy-headers puts the visitor's IP here
    client = request.client.host if request.client else "unknown"
    retry_after = recipe_limiter.hit(client)
    if retry_after:
        minutes = max(1, round(retry_after / 60))
        raise HTTPException(
            429,
            f"Too many recipe requests. Please try again in about {minutes} "
            f"minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(retry_after)},
        )


# ---------- Endpoints ----------
# Defined with plain `def` so FastAPI runs them in a thread pool: both YOLO
# inference and the Spoonacular requests are blocking calls.

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health", response_model=HealthResponse)
def health():
    detector = services.get("detector")
    return HealthResponse(
        status="ok" if detector and "spoonacular" in services else "degraded",
        model_loaded=detector is not None,
        model_path=str(detector.model_path) if detector else None,
        spoonacular_configured="spoonacular" in services,
        detail={
            k: v for k, v in services.items() if k.endswith("_error")
        },
    )


@app.get("/suggestions", response_model=SuggestionsResponse)
def suggestions():
    # Built from local files at startup -- no Spoonacular quota used
    return services["suggestions"]


@app.post("/detect", response_model=DetectResponse)
def detect(
    image: UploadFile = File(...),
    min_confidence: float = Query(0.4, ge=0.05, le=0.95),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, f"Unsupported file type: {image.content_type}")

    image_bytes = image.file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image larger than 10 MB")

    try:
        detections = get_detector().detect(image_bytes, min_confidence=min_confidence)
    except InvalidImageError as e:
        raise HTTPException(400, str(e))

    mapped = services["mapper"].map_classes(d["class_name"] for d in detections)

    return DetectResponse(
        detections=detections,
        ingredients=mapped.ingredients,
        sources=mapped.sources,
        skipped=mapped.skipped,
        unknown=mapped.unknown,
    )


@app.post("/recipes", response_model=RecipeSearchResponse, dependencies=[Depends(limit_quota_use)])
def search_recipes(request: RecipeSearchRequest):
    client = get_spoonacular()

    # De-duplicate case-insensitively, keep order; drop blanks
    seen = set()
    ingredients = []
    for item in request.ingredients:
        name = item.strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            ingredients.append(name)
    if not ingredients:
        raise HTTPException(422, "No ingredients given")

    try:
        results = client.find_recipes_by_ingredients(
            ingredients,
            number=request.number,
            ranking=request.ranking,
            ignore_pantry=request.ignore_pantry,
        )
    except SpoonacularError as e:
        raise spoonacular_http_error(e)

    recipes = [
        RecipeSummary(
            id=r["id"],
            title=r["title"],
            image=r.get("image"),
            used_ingredients=[i["name"] for i in r.get("usedIngredients", [])],
            missed_ingredients=[i["name"] for i in r.get("missedIngredients", [])],
            used_ingredient_ids=[i["id"] for i in r.get("usedIngredients", []) if "id" in i],
            missed_ingredient_ids=[i["id"] for i in r.get("missedIngredients", []) if "id" in i],
            likes=r.get("likes", 0),
        )
        for r in results
    ]
    return RecipeSearchResponse(recipes=recipes, quota_left=client.quota_left)


@app.get("/recipes/{recipe_id}", dependencies=[Depends(limit_quota_use)])
def recipe_details(recipe_id: int, include_nutrition: bool = True):
    try:
        return get_spoonacular().get_recipe_information(
            recipe_id, include_nutrition=include_nutrition
        )
    except SpoonacularError as e:
        raise spoonacular_http_error(e)
