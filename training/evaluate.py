from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
def main():
    model = YOLO(ROOT/'runs'/'yolov8s_100e-3'/'weights'/'best.pt')

    metrics = model.val(source = ROOT/'datasets'/'final_food_dataset'/'data.yaml',
                        split = 'test',
                        project = ROOT/'runs',
                        name = 'evaluation',
                        plots = True)

    print(metrics)


if __name__ == '__main__':
    main()