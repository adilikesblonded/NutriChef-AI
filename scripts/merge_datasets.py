from pathlib import Path
import shutil #copying files

output_images = Path('../datasets/final_food_dataset/images')
output_labels = Path('../datasets/final_food_dataset/labels')

output_images.mkdir(parents=True,exist_ok=True)
output_labels.mkdir(parents=True,exist_ok=True)

# Merge Dataset
def merge_dataset(image_dir,
                  label_dir,
                  prefix): #prefix to avoid name collision while merging
    
    image_dir=Path(image_dir)
    label_dir=Path(label_dir)

    count=0

    for image_file in image_dir.rglob('*'):
        #loops through every image
        if image_file.suffix.lower() not in [
            '.jpg','.jpeg','.png'
        ]:
            continue #skip all non img files
        relative_path = image_file.relative_to(image_dir)
        #gets the relative path for example
        
        new_suffix = "_".join(relative_path.parts).replace(image_file.suffix,"")
        #joins the split of relative path with an underscore 
        #and removes the .jpg at the end
        #train/0001.jpg  --> train_0001

        new_name = f"{prefix}_{new_suffix}"

        label_file = (label_dir/relative_path.with_suffix('.txt'))
        #since the train and label files only differ in suffix

        if not label_file.exists():
            continue
        if label_file.stat().st_size == 0:
            continue #skip empty labels

        new_image = (
            output_images /
            f"{new_name}{image_file.suffix}"
        )

        new_label = (
            output_labels /
            f"{new_name}.txt"
        ) #create the new image and new label paths

        shutil.copy2(
            image_file,
            new_image
        ) #copy the image
        shutil.copy2(
            label_file,
            new_label
        ) #copy the label

        count+=1
        print( f"{prefix}: copied {count} samples")


merge_dataset(
    "../datasets/Fruits-And-Vegetables-Detection-Dataset/LVIS_Fruits_And_Vegetables/images",
    "../remapped_datasets/lvis/labels",
    "lvis"
)


merge_dataset(
    "../datasets/grozi-3.2k/train/images",
    "../remapped_datasets/grozi/labels",
    "grozi"
)



    