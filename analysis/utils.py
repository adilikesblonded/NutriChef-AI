

#utils.py
#Reusable utilities for the NutriChef AI analysis framework.

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import json


# ANALYSIS RESULT DATACLASS

@dataclass
class AnalysisResult:
    """
    Standard output format for every analysis module.

    Every analysis function should return one AnalysisResult.
    """

    title: str

    statistics: dict[str, Any] = field(default_factory=dict)

    description: str = ""

    model_impact: str = ""

    confidence: str = "MEDIUM"

    priority: str = "MEDIUM"

    recommendations: list[str] = field(default_factory=list)


# CONSOLE UTILITIES

def print_header(title: str) -> None:
    line = "=" * 70
    print("\n" + line)
    print(title.upper())
    print(line)


def format_number(value: Any) -> str:

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        return f"{value:,.4f}"

    return str(value)

# OUTPUT FOLDER UTILITIES

def create_output_folders(
    analysis_name: str,
    analysis_root: Path,
) -> tuple[Path, Path]:
    """
    Creates

    analysis/
        plots/<analysis_name>/
        reports/<analysis_name>/

    Returns
    -------
    plot_dir, report_dir
    """

    plots = analysis_root / "plots" / analysis_name
    reports = analysis_root / "reports" / analysis_name

    plots.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    return plots, reports


# DATASET LOADER


def load_yolo_dataset(labels_root: Path) -> list[dict]:
    """
    Loads every YOLO annotation into memory.

    Returns
    -------
    List of dictionaries.

    Example

    {
        "image": "...",
        "split": "train",
        "class_id": 5,
        "x": 0.53,
        "y": 0.42,
        "width": 0.18,
        "height": 0.22,
        "area": 0.0396,
        "aspect_ratio": 0.818
    }
    """

    annotations = []

    for split in ("train", "val", "test"):

        split_dir = labels_root / split

        if not split_dir.exists():
            continue

        for label_file in split_dir.glob("*.txt"):

            image_name = label_file.stem

            with open(label_file, "r") as f:

                for line in f:

                    values = line.strip().split()

                    if len(values) != 5:
                        continue

                    cls, x, y, w, h = values

                    w = float(w)
                    h = float(h)

                    annotations.append({

                        "image": image_name,

                        "split": split,

                        "class_id": int(cls),

                        "x": float(x),

                        "y": float(y),

                        "width": w,

                        "height": h,

                        "area": w * h,

                        "aspect_ratio":
                            w / h if h != 0 else 0

                    })

    return annotations



# DIAGNOSIS CREATOR


def create_diagnosis(
    *,
    title: str,
    statistics: dict,
    description: str,
    impact: str,
    confidence: str,
    priority: str,
    recommendations: list[str],
) -> AnalysisResult:
    """
    Creates a standardized AnalysisResult object.
    """

    return AnalysisResult(

        title=title,

        statistics=statistics,

        description=description,

        model_impact=impact,

        confidence=confidence,

        priority=priority,

        recommendations=recommendations,

    )



# REPORT WRITER

def write_report(
    results: list[AnalysisResult],
    report_directory: Path,
    report_name: str,
) -> None:
    """
    Saves both

    report.txt
    report.json
    """

    report_directory.mkdir(parents=True, exist_ok=True)

    txt_file = report_directory / f"{report_name}.txt"
    json_file = report_directory / f"{report_name}.json"

    with open(txt_file, "w", encoding="utf-8") as report:

        report.write("=" * 70 + "\n")
        report.write(report_name.upper() + "\n")
        report.write("=" * 70 + "\n\n")

        for section in results:

            report.write("=" * 70 + "\n")
            report.write(section.title.upper() + "\n")
            report.write("=" * 70 + "\n\n")

            report.write("STATISTICS\n")
            report.write("-" * 70 + "\n")

            for key, value in section.statistics.items():

                report.write(
                    f"{key:<30}: {format_number(value)}\n"
                )

            report.write("\n")

            report.write("DESCRIPTION\n")
            report.write("-" * 70 + "\n")
            report.write(section.description + "\n\n")

            report.write("MODEL IMPACT\n")
            report.write("-" * 70 + "\n")
            report.write(section.model_impact + "\n\n")

            report.write("CONFIDENCE\n")
            report.write("-" * 70 + "\n")
            report.write(section.confidence + "\n\n")

            report.write("PRIORITY\n")
            report.write("-" * 70 + "\n")
            report.write(section.priority + "\n\n")

            report.write("RECOMMENDATIONS\n")
            report.write("-" * 70 + "\n")

            for recommendation in section.recommendations:
                report.write(f"• {recommendation}\n")

            report.write("\n\n")

    with open(json_file, "w", encoding="utf-8") as f:

        json.dump(
            [asdict(result) for result in results],
            f,
            indent=4,
        )


# PLOTTING STYLE


def get_plot_style() -> dict:
    """
    Consistent plotting colors for every analysis script.
    """

    return {

        "primary": "#2563EB",
        "secondary": "#14B8A6",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",

        "purple": "#7C3AED",

        "background": "#F8FAFC",

        "grid": "#D1D5DB"

    }
