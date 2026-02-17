"""Train YOLO model for truss structure detection."""

import argparse
import json
from pathlib import Path
from datetime import datetime

from ultralytics import YOLO


def train_model(
    config_path: str = "ml/config.yaml",
    epochs: int = 100,
    img_size: int = 640,
    batch_size: int = 16,
    model_name: str = "yolov8n.pt",
    output_dir: str = "ml/models",
    export_torchscript: bool = True,
):
    """
    Train YOLOv8 model for structure detection.
    
    Args:
        config_path: Path to dataset config YAML
        epochs: Number of training epochs
        img_size: Input image size
        batch_size: Training batch size
        model_name: Base model to fine-tune from
        output_dir: Directory to save trained models
        export_torchscript: Whether to export to TorchScript format
    """
    print("="*60)
    print("Training YOLO model for truss structure detection")
    print("="*60)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Training start timestamp
    training_start = datetime.now()
    
    # Load pretrained model
    print(f"\nLoading base model: {model_name}")
    model = YOLO(model_name)
    
    # Train the model
    print(f"\nStarting training:")
    print(f"  Config: {config_path}")
    print(f"  Epochs: {epochs}")
    print(f"  Image size: {img_size}")
    print(f"  Batch size: {batch_size}")
    print()
    
    results = model.train(
        data=config_path,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        name="truss_detector",
        patience=20,  # Early stopping patience
        save=True,
        plots=True,
        verbose=True,
    )
    
    training_end = datetime.now()
    training_duration = (training_end - training_start).total_seconds()
    
    # Get best model path
    best_model_path = Path(model.trainer.save_dir) / "weights" / "best.pt"
    
    # Load validation results
    validator = model.val()
    
    # Extract and log evaluation metrics
    metrics = {
        "training": {
            "start_time": training_start.isoformat(),
            "end_time": training_end.isoformat(),
            "duration_seconds": training_duration,
            "epochs_completed": len(results.box.maps) if hasattr(results, 'box') else epochs,
            "base_model": model_name,
            "config": {
                "epochs": epochs,
                "img_size": img_size,
                "batch_size": batch_size,
            }
        },
        "validation": {
            "mAP50": float(validator.box.map50),  # mAP at IoU=0.50
            "mAP50-95": float(validator.box.map),  # mAP at IoU=0.50:0.95
            "precision": float(validator.box.mp),  # Mean precision
            "recall": float(validator.box.mr),  # Mean recall
            "fitness": float(validator.fitness),  # Overall fitness score
        },
        "per_class_metrics": {}
    }
    
    # Per-class metrics if available
    if hasattr(validator.box, 'ap_class_index'):
        class_names = ["joint", "member", "support_pin", "support_roller"]
        for idx, class_idx in enumerate(validator.box.ap_class_index):
            if idx < len(class_names):
                metrics["per_class_metrics"][class_names[idx]] = {
                    "AP50": float(validator.box.ap50[idx]),
                    "AP": float(validator.box.ap[idx]),
                }
    
    # Save metrics to JSON
    metrics_path = output_path / "training_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to: {metrics_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("Training completed!")
    print(f"Best model saved to: {best_model_path}")
    print(f"Training duration: {training_duration:.1f} seconds")
    print("\nValidation Metrics:")
    print(f"  mAP@0.5: {metrics['validation']['mAP50']:.4f}")
    print(f"  mAP@0.5:0.95: {metrics['validation']['mAP50-95']:.4f}")
    print(f"  Precision: {metrics['validation']['precision']:.4f}")
    print(f"  Recall: {metrics['validation']['recall']:.4f}")
    print("="*60)
    
    # Export to different formats
    print("\nExporting model to different formats...")
    
    # Load best model
    best_model = YOLO(str(best_model_path))
    
    # Export to ONNX
    onnx_path = output_path / "best.onnx"
    print(f"Exporting to ONNX: {onnx_path}")
    best_model.export(format="onnx", simplify=True)
    
    # Export to TorchScript
    if export_torchscript:
        torchscript_path = output_path / "best.torchscript"
        print(f"Exporting to TorchScript: {torchscript_path}")
        best_model.export(format="torchscript")
    
    # Export to TFLite (for mobile deployment)
    tflite_path = output_path / "best.tflite"
    print(f"Exporting to TFLite: {tflite_path}")
    best_model.export(format="tflite")
    
    # Copy best.pt to models directory
    import shutil
    final_model_path = output_path / "best.pt"
    shutil.copy2(best_model_path, final_model_path)
    print(f"\nBest PyTorch model copied to: {final_model_path}")
    
    print("\n" + "="*60)
    print("Model export completed!")
    print(f"Available formats:")
    print(f"  - PyTorch: {final_model_path}")
    print(f"  - ONNX: {onnx_path}")
    if export_torchscript:
        print(f"  - TorchScript: {torchscript_path}")
    print(f"  - TFLite: {tflite_path}")
    print(f"  - Metrics: {metrics_path}")
    print("="*60)
    
    return results, metrics


def main():
    parser = argparse.ArgumentParser(description="Train YOLO model for truss detection")
    parser.add_argument("--config", type=str, default="ml/config.yaml", 
                       help="Path to dataset config YAML")
    parser.add_argument("--epochs", type=int, default=100,
                       help="Number of training epochs")
    parser.add_argument("--img-size", type=int, default=640,
                       help="Input image size")
    parser.add_argument("--batch-size", type=int, default=16,
                       help="Training batch size")
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                       help="Base model to fine-tune from")
    parser.add_argument("--output", type=str, default="ml/models",
                       help="Output directory for trained models")
    
    args = parser.parse_args()
    
    train_model(
        config_path=args.config,
        epochs=args.epochs,
        img_size=args.img_size,
        batch_size=args.batch_size,
        model_name=args.model,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
