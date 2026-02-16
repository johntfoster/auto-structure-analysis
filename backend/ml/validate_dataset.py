"""Validate YOLO dataset format and quality."""

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Tuple

from PIL import Image


class YOLODatasetValidator:
    """Validate YOLO format dataset."""
    
    def __init__(self, num_classes: int = 4):
        self.num_classes = num_classes
        self.errors = []
        self.warnings = []
        self.class_distribution = defaultdict(int)
        
    def validate_annotation_format(self, label_path: Path) -> Tuple[bool, list]:
        """Validate single annotation file format."""
        issues = []
        
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()
                
            if len(lines) == 0:
                issues.append(f"Empty label file: {label_path.name}")
                return False, issues
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split()
                
                if len(parts) != 5:
                    issues.append(
                        f"{label_path.name}:{line_num} - "
                        f"Invalid format (expected 5 values, got {len(parts)})"
                    )
                    continue
                
                try:
                    class_id = int(parts[0])
                    x_center, y_center, width, height = map(float, parts[1:])
                except ValueError as e:
                    issues.append(
                        f"{label_path.name}:{line_num} - "
                        f"Invalid number format: {e}"
                    )
                    continue
                
                # Validate class ID
                if class_id < 0 or class_id >= self.num_classes:
                    issues.append(
                        f"{label_path.name}:{line_num} - "
                        f"Invalid class ID {class_id} (valid: 0-{self.num_classes-1})"
                    )
                
                # Validate normalized coordinates (0-1 range)
                if not (0 <= x_center <= 1):
                    issues.append(
                        f"{label_path.name}:{line_num} - "
                        f"x_center out of range: {x_center}"
                    )
                
                if not (0 <= y_center <= 1):
                    issues.append(
                        f"{label_path.name}:{line_num} - "
                        f"y_center out of range: {y_center}"
                    )
                
                if not (0 < width <= 1):
                    issues.append(
                        f"{label_path.name}:{line_num} - "
                        f"width out of range: {width}"
                    )
                
                if not (0 < height <= 1):
                    issues.append(
                        f"{label_path.name}:{line_num} - "
                        f"height out of range: {height}"
                    )
                
                # Track class distribution
                if 0 <= class_id < self.num_classes:
                    self.class_distribution[class_id] += 1
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Error reading {label_path.name}: {e}")
            return False, issues
    
    def validate_image(self, img_path: Path) -> Tuple[bool, list]:
        """Validate image file."""
        issues = []
        
        try:
            img = Image.open(img_path)
            img.verify()
            return True, issues
        except Exception as e:
            issues.append(f"Invalid image {img_path.name}: {e}")
            return False, issues
    
    def validate_dataset(self, dataset_dir: Path, verbose: bool = False) -> bool:
        """Validate entire dataset."""
        dataset_dir = Path(dataset_dir)
        
        images_dir = dataset_dir / "images"
        labels_dir = dataset_dir / "labels"
        
        if not images_dir.exists():
            self.errors.append(f"Images directory not found: {images_dir}")
            return False
        
        if not labels_dir.exists():
            self.errors.append(f"Labels directory not found: {labels_dir}")
            return False
        
        # Get all images
        image_files = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png"))
        
        if len(image_files) == 0:
            self.errors.append("No images found in dataset")
            return False
        
        print(f"Validating {len(image_files)} images...")
        
        valid_count = 0
        invalid_count = 0
        
        for img_path in image_files:
            # Check for corresponding label
            label_path = labels_dir / f"{img_path.stem}.txt"
            
            if not label_path.exists():
                self.errors.append(f"Missing label file for: {img_path.name}")
                invalid_count += 1
                continue
            
            # Validate image
            img_valid, img_issues = self.validate_image(img_path)
            if not img_valid:
                self.errors.extend(img_issues)
                invalid_count += 1
                continue
            
            # Validate annotation
            ann_valid, ann_issues = self.validate_annotation_format(label_path)
            
            if ann_valid:
                valid_count += 1
                if verbose and valid_count % 100 == 0:
                    print(f"  Validated {valid_count} images...")
            else:
                self.errors.extend(ann_issues)
                invalid_count += 1
        
        # Check train/val splits
        train_txt = dataset_dir / "train.txt"
        val_txt = dataset_dir / "val.txt"
        
        if not train_txt.exists():
            self.warnings.append("train.txt not found")
        else:
            with open(train_txt, 'r') as f:
                train_count = len(f.readlines())
            print(f"\nTrain split: {train_count} images")
        
        if not val_txt.exists():
            self.warnings.append("val.txt not found")
        else:
            with open(val_txt, 'r') as f:
                val_count = len(f.readlines())
            print(f"Validation split: {val_count} images")
        
        return invalid_count == 0
    
    def print_report(self, class_names: dict = None):
        """Print validation report."""
        print("\n" + "="*60)
        print("DATASET VALIDATION REPORT")
        print("="*60)
        
        # Class distribution
        print("\nClass Distribution:")
        if class_names is None:
            class_names = {
                0: "joint",
                1: "member",
                2: "support_pin",
                3: "support_roller"
            }
        
        total_annotations = sum(self.class_distribution.values())
        
        for class_id in sorted(self.class_distribution.keys()):
            count = self.class_distribution[class_id]
            percentage = (count / total_annotations * 100) if total_annotations > 0 else 0
            name = class_names.get(class_id, f"class_{class_id}")
            print(f"  {name:20s} (ID {class_id}): {count:6d} ({percentage:5.1f}%)")
        
        print(f"\n  Total annotations: {total_annotations}")
        
        # Warnings
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")
        
        # Errors
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:20]:  # Show first 20
                print(f"  - {error}")
            if len(self.errors) > 20:
                print(f"  ... and {len(self.errors) - 20} more")
            print("\n❌ VALIDATION FAILED")
        else:
            print("\n✅ VALIDATION PASSED")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Validate YOLO dataset")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset directory")
    parser.add_argument("--num-classes", type=int, default=4, help="Number of classes")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    validator = YOLODatasetValidator(num_classes=args.num_classes)
    is_valid = validator.validate_dataset(Path(args.dataset), verbose=args.verbose)
    validator.print_report()
    
    exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
