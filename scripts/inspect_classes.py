import yaml #allows us to read yaml files

with open( #opens file and stores in f
    "../datasets/Fruits-And-Vegetables-Detection-Dataset/LVIS_Fruits_And_Vegetables/data.yaml"
) as f:
    LVIS_data = yaml.safe_load(f) #loads the yaml
    #as a dictionary {"names" = { 0 : "almond".....}} 

print(LVIS_data["names"])
print("Number of classes:", len(LVIS_data["names"]))

with open("../datasets/grozi-3.2k/data.yaml") as f:
    grozi_data = yaml.safe_load(f)

print(grozi_data["names"])
print("Number of Grozi classes: ", len(grozi_data["names"]))