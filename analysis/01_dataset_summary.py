from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent 
#gives the grandparent directory of the current file

dataset = ROOT / 'datasets' / 'final_food_dataset'

img_extensions = ['jpg','jpeg','png']

splits = ['train','val','test']

report_folder = ROOT / 'analysis' / 'reports'
report_folder.mkdir(parents=True,exist_ok=True)

def get_images(folder):
    images=[]

    for ext in img_extensions:
        images.extend(folder.rglob(f'*.{ext}'))
        #extend adds mulitple items to the list
        #glob returns all the items in the folder
        #that match the pattern
        
    return images


def summarize_split(split):

    image_dir = dataset / 'images' / split
    label_dir = dataset / 'labels' / split

    image_files = get_images(image_dir)
    label_files = list(label_dir.glob('*.txt'))

    image_names = {img.stem for img in image_files}
    label_names = {label.stem for label in label_files}

    missing_labels = image_names - label_names
    orphan_labels = label_names - image_names

    empty_labels = 0

    total_objects = 0
    # one image can contain multiple objects
    # each object can be a banana an apple etc
    # labels are of the form
    # 0-> class x_centre, y_centre,width,height
    # each line in a label file corresponds to an object

    max_objects = 0
    min_objects = float("inf")

    object_counter = Counter()
    image_counter = Counter()

    for label_file in label_files:

        lines = label_file.read_text().strip().splitlines()

        if len(lines) == 0:
            empty_labels += 1
            continue

        total_objects += len(lines)

        max_objects = max(max_objects, len(lines))
        min_objects = min(min_objects, len(lines))

        classes_in_image = set()

        for line in lines:

            values = line.split()

            if len(values) != 5:
                continue

            class_id = int(values[0])

            object_counter[class_id] += 1

            classes_in_image.add(class_id)

        for class_id in classes_in_image:

            image_counter[class_id] += 1

    if min_objects == float("inf"):
        min_objects = 0

    average_objects = (
        total_objects / len(image_files)
        if image_files else 0
    )

    sorted(image_counter.items())

    return {
        "images": len(image_files),
        "labels": len(label_files),
        "missing_labels": len(missing_labels),
        "orphan_labels": len(orphan_labels),
        "empty_labels": empty_labels,
        "objects": total_objects,
        "avg_objects": average_objects,
        "max_objects": max_objects,
        "min_objects": min_objects,
        "object_counter": object_counter,
        "image_counter": image_counter,
    }


def main():

    total_images = 0
    total_objects = 0

    overall_object_counter = Counter()
    overall_image_counter = Counter()

    print("=" * 70)
    print("NUTRICHEF AI DATASET SUMMARY")
    print("=" * 70)

    for split in splits:

        stats = summarize_split(split)

        total_images += stats["images"]
        total_objects += stats["objects"]

        overall_object_counter.update(stats["object_counter"])
        overall_image_counter.update(stats["image_counter"])

        print(f"\n[{split.upper()}]")

        print(f"Images               : {stats['images']}")
        print(f"Label Files          : {stats['labels']}")
        print(f"Objects              : {stats['objects']}")

        print(f"Missing Labels       : {stats['missing_labels']}")
        print(f"Orphan Labels        : {stats['orphan_labels']}")
        print(f"Empty Label Files    : {stats['empty_labels']}")

        print(f"Average Objects/Image: {stats['avg_objects']:.2f}")
        print(f"Maximum Objects/Image: {stats['max_objects']}")
        print(f"Minimum Objects/Image: {stats['min_objects']}")

    print("\n" + "=" * 70)

    print("OVERALL DATASET")

    print(f"Total Images         : {total_images}")
    print(f"Total Objects        : {total_objects}")
    print(f"Unique Classes       : {len(overall_object_counter)}")

    class_ids = sorted(overall_object_counter.keys())

    print(f"Class IDs            : {class_ids}")

    expected = set(range(max(class_ids) + 1))
    missing = sorted(expected - set(class_ids))

    print(f"Missing Class IDs    : {missing}")

    print("=" * 70)

    # save report folder

    report_path = report_folder / "class_summary.csv"

    with open(report_path, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "Class ID",
            "Images",
            "Objects",
            "Objects per Image"
        ])

        for class_id in sorted(overall_object_counter.keys()):

            images = overall_image_counter[class_id]
            objects = overall_object_counter[class_id]

            opi = (
                objects / images
                if images != 0
                else 0
            )

            writer.writerow([
                class_id,
                images,
                objects,
                round(opi, 2)
            ])

    print(f"\nClass summary saved to:\n{report_path}")


if __name__ == "__main__":
    main()