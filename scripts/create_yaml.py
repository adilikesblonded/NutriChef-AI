import json
from pathlib import Path

metadata_dir = Path("../metadata")
dataset_dir = Path("../datasets/final_food_dataset")

id_to_class_path = metadata_dir / "id_to_class.json"
yaml_path = dataset_dir / "data.yaml"

with open(id_to_class_path, "r") as f:
    id_to_class = json.load(f)

# Convert JSON keys to integers and sort them
id_to_class = {
    int(k): v
    for k, v in id_to_class.items()
}

with open(yaml_path, "w") as f:

    f.write(f"path: {dataset_dir.resolve()}\n")
    f.write("train: images/train\n")
    f.write("val: images/val\n")
    f.write("test: images/test\n\n")

    f.write("names:\n")

    for class_id in sorted(id_to_class):
        f.write(f"  {class_id}: {id_to_class[class_id]}\n")

print(f"Created {yaml_path}")