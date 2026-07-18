import yaml
import json

#normalize all the class names 
NORMALIZE = {
    "Strawberry": "strawberry",
    "Tomato": "tomato",
    "bean curd/tofu": "tofu",
    "bell pepper/capsicum": "bell pepper",
    "cantaloup/cantaloupe": "cantaloupe",
    "chickpea/garbanzo": "chickpea",
    "coconut/cocoanut": "coconut",
    "edible corn/corn/maize": "corn",
    "cucumber/cuke": "cucumber",
    "date/date fruit": "date",
    "eggplant/aubergine": "eggplant",
    "fig/fig fruit": "fig",
    "garlic/ail": "garlic",
    "ginger/gingerroot": "ginger",
    "green onion/spring onion/scallion": "spring onion",
    "orange/orange fruit": "orange",
    "pea/pea food": "pea",
    "radish/daikon": "radish",
    "zucchini/courgette": "zucchini",
    "kiwi fruit": "kiwi",
    "mandarin orange": "orange",
    "clementine": "orange",

    "cayenne/cayenne spice/cayenne pepper/cayenne pepper spice/red pepper/red pepper":
        "red pepper",

    "chili/chili vegetable/chili pepper/chili pepper vegetable/chilli/chilli vegetable/chilly/chilly":
        "chilli"
}

GROZI_NORMALIZE = {
    "Bakery": "bread",
    "Canned": "canned food",
    "Cereals": "cereal",
    "Cheese": "cheese",
    "Coffee": "coffee",
    "DriedFruitsAndNuts": "nuts",
    "Milk": "milk",
    "Oil-Vinegar": "cooking oil",
    "Pasta": "pasta",
    "Rice": "rice",
    "Sauce": "sauce",
    "Soups": "soup",
    "Spices": "spices",
    "Spreads": "spread",
    "Tea": "tea",
    "Yoghurt": "yogurt"
}

# Read both yaml files
with open(
    "../datasets/Fruits-And-Vegetables-Detection-Dataset/LVIS_Fruits_And_Vegetables/data.yaml"
) as f:
    lvis_data = yaml.safe_load(f)


with open(
    "../datasets/grozi-3.2k/data.yaml"
) as f:
    grozi_data = yaml.safe_load(f)


# Extract class names
lvis_classes = list(lvis_data["names"].values())
    #because the lvis classes are stores as a dict
grozi_classes = grozi_data["names"]
    #grozi classes already stored as a list

# Normalize LVIS and Grozi classes
normalized_lvis=[]
#append all classes of lvis and grozi to seperate lists
for cls in lvis_classes:
    normalized_name = NORMALIZE.get(cls,cls.lower())
    #dict.get(key,default)
    normalized_lvis.append(normalized_name)

normalized_grozi=[]
for cls in grozi_classes:
    normalized_name = GROZI_NORMALIZE.get(cls)
     #gets the value if it exists else returns None
    if normalized_name is not None:
        normalized_grozi.append(normalized_name)


# Remove duplicates using a set and sort
normalized_lvis = sorted(set(normalized_lvis))
normalized_grozi = sorted(set(normalized_grozi))

print("LVIS CLASSES\n")
print(normalized_lvis)
print("GROZI CLASSES\n")
print(normalized_grozi)

# Save the normalized class list to json
with open(
    "../metadata/normalized_lvis.json","w"
) as f:
    json.dump(normalized_lvis,f,indent=4)

    # "w" is the write param
with open(
    "../metadata/normalized_grozi.json","w"
) as f:
    json.dump(normalized_grozi,f,indent=4)
