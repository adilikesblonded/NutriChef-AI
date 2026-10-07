# NutriChef AI

> An AI-powered ingredient recognition and recipe recommendation system that detects grocery items from images using a custom-trained YOLOv8 object detection model, then suggests recipes with full nutritional information through a FastAPI backend and a React web app.

---

# Overview

NutriChef AI is a computer vision project that recognizes raw ingredients and common grocery products
and provides complete recipes, with nutritional information, that utilize the ingredients you presented.

The project combines multiple object detection datasets found on the internet, performs preprocessing and label remapping, trains a custom YOLOv8 model, and integrates the detection pipeline with the Spoonacular API to provide recipes and nutritional data.

This project emphasizes real world grocery recognition, making it suitable for applications such as smart kitchens, dietary tracking, and meal planning.

**How it works:**

1. Upload a photo of your ingredients
2. The YOLOv8 model detects what's in it
3. Review the detected items and add anything the model missed
4. Get recipes ranked by how well they match your ingredients
5. Open a recipe for its nutrition breakdown, ingredient checklist and step-by-step method

---

# Features

## Machine Learning

* Custom YOLOv8 object detection model fine-tuned on a combined dataset created from multiple public datasets
* 75 ingredient classes covering fresh produce and packaged grocery products
* Automated dataset preprocessing and label remapping
* Dataset normalization and class merging pipeline
* Dataset analysis tooling (class distribution, bounding box statistics)

## Backend (FastAPI)

* Image upload endpoint that runs the model and returns detections with bounding boxes and confidence scores
* Class-to-ingredient mapping layer that translates model classes into Spoonacular ingredient names (e.g. `chilli` → `chili pepper`) and skips categories too general to search (e.g. `spices`, `canned food`)
* Recipe search and recipe detail endpoints backed by the Spoonacular API
* Ingredient autocomplete list served from local data (~1,000 ingredients, no API quota used)
* On-disk response caching and quota tracking to stay within the Spoonacular free plan
* Clear error handling for invalid images, missing API keys and exceeded quotas

## Web Application (React + Vite)

* Drag-and-drop or click-to-upload for `.jpg`, `.jpeg` and `.png` images
* Photo tips explaining what the model can and can't recognize
* Detected ingredients shown on the photo with bounding boxes, plus editable ingredient cards
* Manual ingredient entry with autocomplete and one-tap chips for commonly missed items (eggs, butter, meat…)
* Recipe ranking preferences: *use most of my ingredients* or *fewest missing items*
* Recipe cards with match percentage and "you have" / "missing" ingredient lists
* Recipe detail page with calories, protein, carbs and fat per serving, a have / need / pantry ingredient checklist, and step-by-step instructions
* Responsive design for phone and desktop

---

# Tech Stack

## Languages

* Python
* JavaScript

## Machine Learning

* Ultralytics YOLOv8
* PyTorch
* OpenCV
* NumPy
* Pandas
* Matplotlib

## Backend

* FastAPI
* Uvicorn
* Pydantic

## Frontend

* React 18
* Vite

## APIs

* Spoonacular API (recipes and nutrition)

## Tools

* Git
* GitHub
* VS Code

---

# Project Architecture

```text
                 ┌──────────────────────────┐
                 │   React Web App (Vite)   │
                 └────────────┬─────────────┘
                              │  image / confirmed ingredients
                              ▼
                 ┌──────────────────────────┐
                 │     FastAPI Backend      │
                 └──┬──────────┬─────────┬──┘
                    │          │         │
                    ▼          ▼         ▼
             YOLOv8 Model   Ingredient   Spoonacular API
             (detection)    Mapping      (recipes + nutrition)
```

Request flow:

```text
Image
   │
   ▼
YOLOv8 Object Detection             POST /detect
   │
   ▼
Detected Classes → Ingredient Names  (spoonacular_map.yaml)
   │
   ▼
User Reviews & Edits Ingredients     (frontend)
   │
   ▼
Matching Recipes                     POST /recipes
   │
   ▼
Recipe Detail + Nutrition            GET /recipes/{id}
```

Detection never calls Spoonacular, so a scan costs no API quota until the user searches for recipes.

---

# Dataset

Current sources include:

* LVIS Fruits & Vegetables
* GroZi Grocery Dataset (filtered and normalized)

Significant preprocessing has been performed to improve dataset quality:

* Normalized class names across datasets
* Remapped annotation IDs
* Removed irrelevant grocery categories
* Merged overlapping food categories
* Generated a unified YOLO-compatible dataset
* Analyzed class distributions for dataset refinement

The dataset currently contains:

* 75 object classes
* Thousands of annotated object instances

### What the model can recognize

Because of where the training data comes from, the model recognizes ingredients in two different ways:

| Ingredient type | Source dataset | Best photographed |
|---|---|---|
| Fruits & vegetables (apple, carrot, onion, tomato…) | LVIS | Loose, spread out |
| Pantry & dairy (milk, coffee, pasta, rice, cereal, yogurt…) | GroZi | In their packaging |

Eggs, meat, fish and individual spices are not yet part of the dataset; the web app lets users add these manually.

---

# Training Pipeline

Current workflow:

1. Collect datasets
2. Normalize class names
3. Merge compatible categories
4. Remap annotation labels
5. Generate YOLO dataset structure
6. Create training configuration
7. Train YOLOv8 model
8. Evaluate performance
9. Analyze errors
10. Refine dataset
11. Retrain

## Iteration 1 Results

YOLOv8s, 100 epochs, AdamW, image size 640:

| Metric | Value |
|---|---|
| mAP50 | 0.366 (best, epoch 82) |
| mAP50-95 | 0.262 |
| Precision | 0.43 |
| Recall | 0.37 |

These results are the baseline for Iteration 2, which focuses on dataset balance rather than hyperparameter tuning (see [Current Challenges](#current-challenges)).

---

# Project Structure

```text
NutriChef-AI/
│
├── analysis/
├── backend/
│   ├── config/
│   ├── spoonacular/
│   ├── detector.py
│   ├── main.py
│   └── schemas.py
├── datasets/
├── frontend/
│   └── src/
├── iterations/
├── metadata/
├── remapped_datasets/
├── runs/
├── scripts/
├── training/
├── .env.example
├── requirements.txt
└── README.md
```

## Folder Breakdown

### `analysis/`

Contains exploratory data analysis (EDA), dataset statistics, class distribution analysis, bounding box analysis, and visualizations used to evaluate dataset quality before and after preprocessing.

---

### `backend/`

The FastAPI application that connects the model to the Spoonacular API.

- `main.py` — API endpoints
- `detector.py` — loads the trained YOLO model and runs inference on uploaded images
- `schemas.py` — request and response models
- `spoonacular/` — Spoonacular API client (with caching and quota tracking), class-to-ingredient mapping, and autocomplete suggestions
- `config/spoonacular_map.yaml` — maps each model class to the ingredient name sent to Spoonacular
- `config/suggestions.yaml` — editable one-tap chips and extra autocomplete entries
- `config/spoonacular_top_1k_ingredients.csv` — Spoonacular's list of common ingredients, used for autocomplete

---

### `datasets/`

Stores the original raw datasets collected from multiple public sources before any preprocessing or label modifications. These datasets are used as the starting point for building the unified training dataset.

---

### `frontend/`

The React + Vite web application. Screens live in `src/screens/` (Welcome, Ingredients, Recipe List, Recipe Detail), and `src/api.js` handles all calls to the backend.

---

### `iterations/`

Maintains records of each major training iteration, including model performance metrics, experiment notes, training curves, and evaluation results. This folder documents the evolution of the project and enables comparison between successive model improvements.

---

### `metadata/`

Contains metadata files required during dataset preprocessing, including class mappings, label remapping information, normalization tables, and other configuration files used to unify multiple datasets. Also stores the resolved Spoonacular ingredient IDs for each class.

---

### `remapped_datasets/`

Stores the processed datasets after class normalization, annotation remapping, and dataset merging. These datasets are converted into a consistent YOLO-compatible format before training.

---

### `runs/`

Automatically generated by Ultralytics during training.

Contains:

- Training logs
- Model checkpoints (`best.pt`, `last.pt`)
- Loss curves
- Precision-Recall curves
- Confusion matrices
- Validation outputs

This folder is primarily used for experimentation and is excluded from version control.

---

### `scripts/`

Contains the project's Python scripts responsible for dataset preprocessing, annotation remapping, dataset merging, and Spoonacular tooling.

Examples include:

- Dataset merging
- Label remapping
- Class normalization
- Dataset inspection
- `spoonacular_demo.py` — try recipe search with hand-typed ingredients
- `verify_spoonacular_map.py` — check that every class maps to the intended Spoonacular ingredient

---

### `training/`

Contains the training and evaluation scripts (`train.py`, `evaluate.py`) and base model weights. This folder centralizes the resources required to reproduce training runs and manage future experiments.

---

# Current Progress

## Completed

* Research and selection of datasets
* Dataset filtering
* Dataset merging pipeline
* Class normalization
* Annotation remapping
* YOLO dataset generation
* Class distribution analysis
* Training configuration setup
* Initial YOLOv8 training pipeline (Iteration 1)
* Spoonacular API integration
* FastAPI backend
* Frontend web application

## In Progress

* Improving dataset balance
* Merging visually similar classes
* Removing underrepresented categories
* Model training and evaluation (Iteration 2)
* Bounding box analysis

## Planned

* Addition of more datasets (proteins, loose dairy, eggs)
* Model deployment
* Performance benchmarking

---

# Current Challenges

The project is actively being refined to improve model performance and robustness.

Current engineering efforts include:
(AFTER ITERATION 1)
* Reducing class imbalance across the dataset — several classes have fewer than 10 training images
* Merging visually similar categories (e.g., different pepper varieties) to improve learnability
* Removing classes with insufficient training examples
* Expanding the dataset with additional protein categories
* Iteratively evaluating model performance and refining the dataset based on results rather than arbitrary hyperparameter tuning

These refinements are expected to improve detection accuracy and model generalization.

Until then, the web app is designed around the model's limits: users review and edit detected ingredients before any recipe search, so a missed or wrong detection never leads straight to a wrong recipe.

---

# Installation

## Prerequisites

* Python 3.10+
* Node.js 18+
* A free Spoonacular API key — sign up at [spoonacular.com/food-api/console](https://spoonacular.com/food-api/console#Profile)

## Setup

```bash
git clone https://github.com/adilikesblonded/NutriChef-AI.git

cd NutriChef-AI

pip install -r requirements.txt

cd frontend
npm install
cd ..
```

Copy `.env.example` to `.env` and add your API key:

```env
SPOONACULAR_API_KEY=your_api_key_here
```

Optional settings in `.env`:

```env
# Use different model weights (defaults to runs/yolov8s_100e-3/weights/best.pt)
MODEL_PATH=runs/<run_name>/weights/best.pt

# Allowed frontend origins (comma-separated)
CORS_ORIGINS=http://localhost:5173
```

> Trained weights and datasets are not committed to the repository. Train a model first (see below) or place your weights at the path set in `MODEL_PATH`.

---

# Usage

## Run the web app

Start the backend and frontend in two terminals from the project root:

```bash
# Terminal 1 — backend
python -m uvicorn backend.main:app --reload
```

```bash
# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## API

With the backend running, interactive API docs are available at **http://127.0.0.1:8000/docs**.

| Endpoint | Description | Uses Spoonacular quota |
|---|---|---|
| `GET /health` | Model and API key status | No |
| `GET /suggestions` | Ingredient autocomplete list and one-tap chips | No |
| `POST /detect` | Upload an image; returns detections and suggested ingredients | No |
| `POST /recipes` | Find recipes for a list of ingredients | Yes |
| `GET /recipes/{id}` | Full recipe with nutrition and instructions | Yes |

## Training

```bash
python training/train.py
```

## Evaluation

```bash
python training/evaluate.py
```

## Spoonacular tools

```bash
# Try recipe search without the model
python scripts/spoonacular_demo.py apple chilli rice

# Show only the class-to-ingredient mapping (no API call)
python scripts/spoonacular_demo.py apple chilli rice --dry-run

# Verify every class mapping against Spoonacular (resumable if the quota runs out)
python scripts/verify_spoonacular_map.py
```

## Spoonacular quota

The free plan allows 150 points per day. Each recipe search and each opened recipe uses roughly one point; responses are cached for an hour so repeated requests are free. Spoonacular's free plan requires attribution, which the web app displays in its footer.

---

# Roadmap

* [x] Collect datasets
* [x] Merge datasets
* [x] Normalize classes
* [x] Remap annotations
* [x] Generate YOLO dataset
* [x] FastAPI backend
* [x] Nutrition API integration
* [x] Web application
* [ ] Improve dataset balance
* [ ] Add protein categories
* [ ] Train production-ready model
* [ ] Deploy application

---

# Future Improvements

* Recognition of loose dairy, eggs, meat and fish
* Dietary filters (vegetarian, vegan, gluten-free…) in recipe search
* Saved recipes and daily calorie tracking
* Meal-level nutritional estimation
* Mobile application
* Barcode scanning
* Real-time webcam detection
* Model quantization for edge devices
* Continuous dataset expansion

---

# License

This project is intended for educational and research purposes.

Recipe and nutrition data provided by [Spoonacular](https://spoonacular.com/food-api).
