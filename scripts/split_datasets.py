from pathlib import Path
import shutil
import random

image_dir = Path('../datasets/final_food_dataset/images')
label_dir = Path('../datasets/final_food_dataset/labels')

for task in ["train","test","val"]:
    (image_dir/task).mkdir(parents=True,exist_ok=True)
    (label_dir/task).mkdir(parents=True,exist_ok=True)
    # makes the train test and validation dirs

images=[]
for image in image_dir.rglob('*'):
    if image.is_file() and image.suffix.lower() in [".jpg",".jpeg",".png"]:
        images.append(image)
    
print(f"found {len(images)} images in the merged dataset")

# Shuffle the dataset to get rid of bias
random.seed(120) # promotes reproducability 
# the same random sequence can be reproduced
random.shuffle(images)

# Train - 80% Test - 10% val - 10%
total_size = len(images)

train_size = int(total_size * 0.8)
val_size = int(total_size * 0.1)

train_images = images[:train_size]
val_images = images[train_size:train_size+val_size]
test_images = images[train_size+val_size:]

print(f"Train files {len(train_images)}")
print(f"Validation files {len(val_images)}")
print(f"Test files {len(test_images)}")

def create_task_files(files,task):
    # copies image/label pair
    for image_path in files:
        
        label_path = label_dir/f"{image_path.stem}.txt"
        # Path functions
        # suffix -> returns only the file extension
        # stem -> returns file name without extension
        # the image and label files have the same names
        # with different extensions

        if not label_path.exists():
            continue

        shutil.move(image_path,
                     image_dir/task/image_path.name)
        
        shutil.move(label_path,
                     label_dir/task/label_path.name)
        
    
create_task_files(train_images,"Train")
create_task_files(val_images,'Val')
create_task_files(test_images,'Test')

print('dataset split successfully')


