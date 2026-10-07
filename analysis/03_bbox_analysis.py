# IMPORTS 
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml

from utils import (
    AnalysisResult,
    create_output_folders,
    load_yolo_dataset,
    create_diagnosis,
    write_report,
    get_plot_style,
    format_number,
    print_header,
)

# LOAD PATHS AND CONFIGURATIONS
def load_configuration():
    """
    Load all project paths and configuration required for the
    bounding box analysis.

    Returns
    -------
    dict
        Dictionary containing project paths, class names and
        plotting style.
    """

    project_root = Path(__file__).resolve().parent.parent

    dataset_root = project_root / "datasets" / "final_food_dataset"

    analysis_root = project_root / "analysis"

    plots_root, reports_root = create_output_folders(
        "bbox_analysis",
        analysis_root
    )

    with open(dataset_root / "data.yaml", "r") as file:
        data = yaml.safe_load(file)

    names = data["names"]

    if isinstance(names, dict):
        class_names = {
            int(key): value
            for key, value in names.items()
        }
    else:
        class_names = {
            index: name
            for index, name in enumerate(names)
        }

    return {
        "project_root": project_root,
        "dataset_root": dataset_root,
        "labels_root": dataset_root / "labels",
        "images_root": dataset_root / "images",
        "plots_root": plots_root,
        "reports_root": reports_root,
        "class_names": class_names,
        "plot_style": get_plot_style(),
    }


def load_dataset(config):
    """
    Load the YOLO dataset into memory.

    The dataset is organized into structures that can be reused by all
    subsequent analysis functions without repeatedly parsing the label files.

    Parameters
    ----------
    config : dict
        Configuration dictionary returned by load_configuration().

    Returns
    -------
    dict
        Dataset containing annotations and image-level groupings.
    """

    annotations = load_yolo_dataset(config["labels_root"])

    image_annotations = {}

    for annotation in annotations:

        image = annotation["image"]

        if image not in image_annotations:
            image_annotations[image] = []

        image_annotations[image].append(annotation)

    dataset = {
        "annotations": annotations,
        "image_annotations": image_annotations,
        "num_images": len(image_annotations),
        "num_boxes": len(annotations),
        "class_names": config["class_names"]
    }

    return dataset
