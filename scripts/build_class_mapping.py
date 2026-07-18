import json
#normalized_lvis and normalized_grozi ----> final class list
#------> class_to_id.json and id_to_class.json

with open("../metadata/normalized_lvis.json") as f:
    lvis_classes = json.load(f)
with open("../metadata/normalized_grozi.json") as f:
    grozi_classes = json.load(f)

#union of both lists
all_classes = sorted(set(lvis_classes)|set(grozi_classes))

# Class to ID mapping
class_to_id={}
for i,cls in enumerate(all_classes):
    class_to_id[cls]=i


# ID to class Mapping
id_to_class={}
for cls,i in class_to_id.items():
    id_to_class[i]=cls

# Save the mappings
with open('../metadata/class_to_id.json','w') as f:
    json.dump(class_to_id,f,indent=4)
with open('../metadata/id_to_class.json','w') as f:
    json.dump(id_to_class,f,indent=4)

print(f"Total classes: {len(all_classes)}")

print("\nFinal Classes:\n")
for i, cls in enumerate(all_classes):
    print(f"{i}: {cls}")

