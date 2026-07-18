import json
from pathlib import Path
import yaml

from normalize_classes import NORMALIZE,GROZI_NORMALIZE

with open('../metadata/class_to_id.json') as f:
    class_to_id=json.load(f) #loads as a dict

# Load original class names
with open('../datasets/Fruits-And-Vegetables-Detection-Dataset/LVIS_Fruits_And_Vegetables/data.yaml') as f:
    lvis_class = yaml.safe_load(f)

with open('../datasets/grozi-3.2k/data.yaml') as f:
    grozi_class = yaml.safe_load(f)

lvis_names = lvis_class["names"]
grozi_names = grozi_class["names"]

def remap_lvis_labels(old_id):
    old_name = lvis_names[(int)(old_id)]
    normalized_name = NORMALIZE.get(old_name,
                                    old_name.lower())
    #this fetches the value that the old name has
    #been normalized to
    return class_to_id[normalized_name] #returns the ID of the normalized class


def remap_grozi_labels(old_id):
    old_name = grozi_names[(int)(old_id)]
    normalized_name = GROZI_NORMALIZE.get(old_name)
    if normalized_name is None:
        return None
        
    return class_to_id[normalized_name]


def remap_folder(input_dir,
                 output_dir,
                 remap_function):
    

    
    input_dir = Path(input_dir) #converts string to path
    output_dir = Path(output_dir)



    output_dir.mkdir(parents=True,exist_ok=True)
    #creates output folder if it doesnt exist
    #if it exists exists_ok prevents error

    for label_file in input_dir.rglob("*.txt"):
        # rglob recursively searches all subdirectories
        #searches all files that end in .txt
        #(label files)

        new_lines=[] #store new labels
        with open(label_file) as f:
            lines = f.readlines() # 35 0.6 0.85

        for line in lines:
            parts = line.strip().split()
            # makes it into a list with each part
            # as a section of the label
            #{ 35, 0.4, 0.86}

            old_id = int(parts[0])
            new_id = remap_function(old_id)
            if new_id is None:
                continue
            parts[0] = str(new_id)

            new_lines.append(" ".join(parts))

        if not new_lines:
            continue

        relative_path = label_file.relative_to(input_dir)
        output_file = output_dir / relative_path

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(output_file, "w") as f:
            f.write(
                "\n".join(new_lines)
            )

remap_folder(
    "../datasets/Fruits-And-Vegetables-Detection-Dataset/LVIS_Fruits_And_Vegetables/labels",
    "../remapped_datasets/lvis/labels",
    remap_lvis_labels
)

remap_folder(
    "../datasets/grozi-3.2k/train/labels",
    "../remapped_datasets/grozi/labels",
    remap_grozi_labels
)

print("finished remapping labels")


