from ultralytics import YOLO
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

def main():
    model = YOLO('yolov8s.pt')
    model.train(data = str(ROOT / "datasets" / "final_food_dataset" / "data.yaml"),
                #Training
                epochs = 100,
                batch = 8,
                imgsz = 640,
                
                lr0 = 0.001,
                val=True,
                patience = 20,
                optimizer = 'AdamW',
                
                #Save results
                project = str(ROOT/'runs'),
                name = 'yolov8s_100e', # Iteration 1 -> 100 epochs
                save=True,
                save_period = 1,
                plots=True, #visualization
                seed=42,
                workers=2)
    

if __name__ == "__main__":
    main()