from pathlib import Path
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import yaml


ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "datasets" / "final_food_dataset"
DATA_YAML = DATASET / "data.yaml"

REPORT_DIR = ROOT / "analysis" / "reports"
PLOT_DIR = ROOT / "analysis" / "plots"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]
SPLITS = ["train", "val", "test"]

# Load the class names
with open(DATA_YAML, "r") as f:
    data = yaml.safe_load(f)

names = data["names"]

# Handle both list and dict formats
if isinstance(names, dict):
    CLASS_NAMES = {int(k): v for k, v in names.items()}
else:
    CLASS_NAMES = {i: name for i, name in enumerate(names)}

NUM_CLASSES = len(CLASS_NAMES)

#counters
object_counter = Counter()
image_counter = Counter()

total_images = 0
total_objects = 0


for split in SPLITS:

    image_dir = DATASET / "images" / split
    label_dir = DATASET / "labels" / split

    image_files = []

    for ext in IMAGE_EXTENSIONS:
        image_files.extend(image_dir.glob(f"*{ext}"))

    total_images += len(image_files)

    for label_file in label_dir.glob("*.txt"):

        lines = label_file.read_text().strip().splitlines()

        if len(lines) == 0:
            continue

        classes_in_image = set()

        for line in lines:

            values = line.split()

            if len(values) != 5:
                continue

            class_id = int(values[0])

            object_counter[class_id] += 1
            total_objects += 1

            classes_in_image.add(class_id)

        for cls in classes_in_image:
            image_counter[cls] += 1

#build the dataframe

rows = []

for class_id in range(NUM_CLASSES):

    images = image_counter[class_id]
    objects = object_counter[class_id]

    rows.append({
        "Class ID": class_id,
        "Class Name": CLASS_NAMES[class_id],
        "Images": images,
        "Objects": objects,
        "Objects/Image":
            round(objects / images, 2) if images else 0,

        "% Images":
            round(images / total_images * 100, 2),

        "% Objects":
            round(objects / total_objects * 100, 2)
    })

df = pd.DataFrame(rows)

df = df.sort_values(
    by="Objects",
    ascending=False
).reset_index(drop=True)

df.insert(0, "Rank", range(1, len(df)+1))

# save the final output to a csv file

csv_path = REPORT_DIR / "class_distribution.csv"

df.to_csv(csv_path, index=False)

print(df)

print(f"\nSaved CSV to:\n{csv_path}")

# statistics calculation
largest = df.iloc[0]["Objects"]
smallest = df[df["Objects"] > 0]["Objects"].min()

ratio = largest / smallest

print("\n==============================")
print("DATASET STATISTICS")
print("==============================")

print(f"Largest Class : {largest}")
print(f"Smallest Class: {smallest}")
print(f"Imbalance Ratio: {ratio:.1f}:1")

# 1) objects per class

plt.figure(figsize=(18,7))

plt.bar(
    df["Class Name"],
    df["Objects"]
)

plt.xticks(rotation=90)

plt.title("Objects per Class")

plt.tight_layout()

plt.savefig(PLOT_DIR / "objects_per_class.png")

plt.close()

#images per class

plt.figure(figsize=(18,7))

plt.bar(
    df["Class Name"],
    df["Images"]
)

plt.xticks(rotation=90)

plt.title("Images containing each Class")

plt.tight_layout()

plt.savefig(PLOT_DIR / "images_per_class.png")

plt.close()

# TOP 20

top20 = df.head(20)

plt.figure(figsize=(12,6))

plt.bar(
    top20["Class Name"],
    top20["Objects"]
)

plt.xticks(rotation=60)

plt.title("Top 20 Most Common Classes")

plt.tight_layout()

plt.savefig(PLOT_DIR / "top20_classes.png")

plt.close()

# Bottom 20

bottom20 = df.tail(20)

plt.figure(figsize=(12,6))

plt.bar(
    bottom20["Class Name"],
    bottom20["Objects"]
)

plt.xticks(rotation=60)

plt.title("Bottom 20 Rarest Classes")

plt.tight_layout()

plt.savefig(PLOT_DIR / "bottom20_classes.png")

plt.close()

# Long tail

plt.figure(figsize=(12,6))

plt.plot(
    range(1, len(df)+1),
    df["Objects"],
    marker="o"
)

plt.xlabel("Class Rank")

plt.ylabel("Objects")

plt.title("Long Tail Distribution")

plt.grid(True)

plt.tight_layout()

plt.savefig(PLOT_DIR / "long_tail_distribution.png")

plt.close()

print("\nPlots saved to:")
print(PLOT_DIR)