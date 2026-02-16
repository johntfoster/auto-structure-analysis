"""Evaluate trained YOLO model on validation set."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from ultralytics import YOLO


def evaluate_model(
    model_path: str = "ml/models/best.pt",
    config_path: str = "ml/config.yaml",
    img_size: int = 640,
    save_dir: str = "ml/evaluation",
):
    """
    Evaluate YOLO model on validation set.
    
    Args:
        model_path: Path to trained model
        config_path: Path to dataset config
        img_size: Input image size
        save_dir: Directory to save evaluation results
    """
    print("="*60)
    print("Evaluating YOLO model")
    print("="*60)
    
    # Check if model exists
    model_file = Path(model_path)
    if not model_file.exists():
        print(f"\nError: Model file not found at {model_path}")
        print("Please train the model first using: uv run python ml/train.py")
        return
    
    # Create output directory
    output_path = Path(save_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load trained model
    print(f"\nLoading model from: {model_path}")
    model = YOLO(str(model_path))
    
    # Run validation
    print(f"\nRunning validation on dataset: {config_path}")
    results = model.val(
        data=config_path,
        imgsz=img_size,
        plots=True,
        save_json=True,
        verbose=True,
    )
    
    print("\n" + "="*60)
    print("Validation Results")
    print("="*60)
    
    # Overall metrics
    print(f"\nOverall Metrics:")
    print(f"  mAP@0.5: {results.box.map50:.4f}")
    print(f"  mAP@0.5:0.95: {results.box.map:.4f}")
    print(f"  Precision: {results.box.mp:.4f}")
    print(f"  Recall: {results.box.mr:.4f}")
    
    # Per-class metrics
    print(f"\nPer-Class Metrics:")
    class_names = ["joint", "member", "support_pin", "support_roller"]
    
    if hasattr(results.box, 'ap_class_index') and results.box.ap_class_index is not None:
        for i, class_name in enumerate(class_names):
            if i < len(results.box.ap):
                ap = results.box.ap[i]
                print(f"  {class_name}:")
                print(f"    AP@0.5: {ap[0]:.4f}")
                print(f"    AP@0.5:0.95: {ap.mean():.4f}")
    
    # Print confusion matrix info
    if hasattr(results, 'confusion_matrix') and results.confusion_matrix is not None:
        print(f"\nConfusion matrix saved to validation results")
    
    print("\n" + "="*60)
    print(f"Evaluation completed!")
    print(f"Results saved to: {results.save_dir}")
    print("="*60)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate YOLO model")
    parser.add_argument("--model", type=str, default="ml/models/best.pt",
                       help="Path to trained model")
    parser.add_argument("--config", type=str, default="ml/config.yaml",
                       help="Path to dataset config")
    parser.add_argument("--img-size", type=int, default=640,
                       help="Input image size")
    parser.add_argument("--save-dir", type=str, default="ml/evaluation",
                       help="Directory to save evaluation results")
    
    args = parser.parse_args()
    
    evaluate_model(
        model_path=args.model,
        config_path=args.config,
        img_size=args.img_size,
        save_dir=args.save_dir,
    )


if __name__ == "__main__":
    main()
