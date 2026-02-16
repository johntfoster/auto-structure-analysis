"""Train YOLO model for truss structure detection."""

import argparse
from pathlib import Path

from ultralytics import YOLO


def train_model(
    config_path: str = "ml/config.yaml",
    epochs: int = 100,
    img_size: int = 640,
    batch_size: int = 16,
    model_name: str = "yolov8n.pt",
    output_dir: str = "ml/models",
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
    """
    print("="*60)
    print("Training YOLO model for truss structure detection")
    print("="*60)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
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
    
    # Get best model path
    best_model_path = Path(model.trainer.save_dir) / "weights" / "best.pt"
    
    print("\n" + "="*60)
    print("Training completed!")
    print(f"Best model saved to: {best_model_path}")
    print("="*60)
    
    # Export to different formats
    print("\nExporting model to different formats...")
    
    # Load best model
    best_model = YOLO(str(best_model_path))
    
    # Export to ONNX
    onnx_path = output_path / "best.onnx"
    print(f"Exporting to ONNX: {onnx_path}")
    best_model.export(format="onnx", simplify=True)
    
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
    print(f"  - TFLite: {tflite_path}")
    print("="*60)
    
    return results


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
