"""
Try the Spoonacular layer with hand-typed class names (no model needed).

    python scripts/spoonacular_demo.py apple chilli rice spices
    python scripts/spoonacular_demo.py apple chilli rice --dry-run
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.spoonacular import IngredientMapper, SpoonacularClient, SpoonacularError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("classes", nargs="+", help="YOLO class names, e.g. apple chilli")
    parser.add_argument("--number", type=int, default=5, help="recipes to return")
    parser.add_argument("--dry-run", action="store_true", help="only show the mapping")
    args = parser.parse_args()

    mapped = IngredientMapper().map_classes(args.classes)

    print("Mapping")
    for query, classes in mapped.sources.items():
        print(f"  {', '.join(classes):<20} -> {query}")
    if mapped.skipped:
        print(f"  skipped (not sent): {', '.join(mapped.skipped)}")
    if mapped.unknown:
        print(f"  unknown (not in map): {', '.join(mapped.unknown)}")

    if args.dry_run or not mapped.ingredients:
        return

    try:
        client = SpoonacularClient()
        recipes = client.find_recipes_by_ingredients(mapped.ingredients, number=args.number)
    except SpoonacularError as e:
        sys.exit(f"\nError: {e}")

    print(f"\nRecipes ({len(recipes)})")
    for recipe in recipes:
        used = ", ".join(i["name"] for i in recipe.get("usedIngredients", []))
        missed = ", ".join(i["name"] for i in recipe.get("missedIngredients", []))
        print(f"  [{recipe['id']}] {recipe['title']}")
        print(f"      uses:    {used or '-'}")
        print(f"      missing: {missed or '-'}")

    if client.quota_left is not None:
        print(f"\nQuota left today: {client.quota_left:g} points")


if __name__ == "__main__":
    main()
