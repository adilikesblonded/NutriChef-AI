"""
Check backend/config/spoonacular_map.yaml against the model and Spoonacular.

1. Coverage: every class in data.yaml has an entry in the map (free, offline)
2. Resolution: every query resolves to a sensible Spoonacular ingredient
   (one ingredient search per mapped class, ~70 requests -- fits the free
   daily quota, and results are cached for an hour)

Resolved IDs are saved to metadata/spoonacular_ingredient_ids.json for
later nutrition lookups. Re-running skips classes already resolved, so a
run cut short by the quota can be continued the next day.

    python scripts/verify_spoonacular_map.py              # coverage + resolution
    python scripts/verify_spoonacular_map.py --offline    # coverage only
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.spoonacular import IngredientMapper, SpoonacularClient, SpoonacularError

OUTPUT_PATH = ROOT / "metadata" / "spoonacular_ingredient_ids.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="only check coverage")
    args = parser.parse_args()

    mapper = IngredientMapper()

    coverage = mapper.check_coverage()
    print("Coverage")
    print(f"  classes missing from map: {coverage['missing_from_map'] or 'none'}")
    print(f"  map entries not in model: {coverage['not_in_model'] or 'none'}")

    if args.offline:
        return

    try:
        client = SpoonacularClient()
    except SpoonacularError as e:
        sys.exit(f"\nError: {e}")

    # Resume from a previous (possibly partial) run instead of re-querying
    resolved = {}
    if OUTPUT_PATH.exists():
        resolved = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    unresolved = []

    print("\nResolution  (* = Spoonacular name differs from query, check it)")
    for class_name, query in sorted(mapper.class_map.items()):
        if query is None:
            print(f"  {class_name:<18} skipped")
            continue

        previous = resolved.get(class_name)
        if previous and previous["query"] == query:
            flag = "" if previous["name"].lower() == query.lower() else " *"
            print(f"  {class_name:<18} -> {query:<18} = {previous['name']} (id {previous['id']}){flag}  [saved]")
            continue

        # Stay under the free plan's per-second rate limit
        time.sleep(1)

        try:
            match = client.search_ingredient(query)
        except SpoonacularError as e:
            print(f"\nStopped early: {e}")
            print("Progress is saved -- re-run later to continue from here.")
            break

        if match is None:
            unresolved.append(class_name)
            print(f"  {class_name:<18} -> {query:<18} NO MATCH")
            continue

        flag = "" if match["name"].lower() == query.lower() else " *"
        print(f"  {class_name:<18} -> {query:<18} = {match['name']} (id {match['id']}){flag}")
        resolved[class_name] = {
            "query": query,
            "id": match["id"],
            "name": match["name"],
        }

    OUTPUT_PATH.write_text(json.dumps(resolved, indent=4), encoding="utf-8")
    print(f"\nSaved {len(resolved)} ingredient IDs to {OUTPUT_PATH.relative_to(ROOT)}")

    if unresolved:
        print(f"Unresolved: {', '.join(unresolved)}")
    if client.quota_left is not None:
        print(f"Quota left today: {client.quota_left:g} points")


if __name__ == "__main__":
    main()
