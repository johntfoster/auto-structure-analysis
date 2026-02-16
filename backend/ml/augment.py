"""Data augmentation pipeline for YOLO dataset."""

import argparse
import random
import shutil
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image


class YOLOAugmenter:
    """Augment YOLO dataset with image transformations."""
    
    def __init__(self, preserve_aspect: bool = True):
        self.preserve_aspect = preserve_aspect
    
    def adjust_brightness_contrast(self, img: np.ndarray) -> np.ndarray:
        """Randomly adjust brightness and contrast."""
        # Brightness
        alpha = random.uniform(0.7, 1.3)  # Contrast
        beta = random.randint(-30, 30)    # Brightness
        
        img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        return img
    
    def add_blur(self, img: np.ndarray) -> np.ndarray:
        """Add random blur."""
        blur_type = random.choice(['gaussian', 'motion', 'none'])
        
        if blur_type == 'gaussian':
            ksize = random.choice([3, 5, 7])
            img = cv2.GaussianBlur(img, (ksize, ksize), 0)
        elif blur_type == 'motion':
            # Motion blur kernel
            size = random.choice([5, 7, 9])
            kernel = np.zeros((size, size))
            kernel[int((size-1)/2), :] = np.ones(size)
            kernel = kernel / size
            img = cv2.filter2D(img, -1, kernel)
        
        return img
    
    def add_noise(self, img: np.ndarray) -> np.ndarray:
        """Add Gaussian noise."""
        if random.random() < 0.5:
            noise = np.random.normal(0, random.randint(5, 15), img.shape)
            img = np.clip(img + noise, 0, 255).astype(np.uint8)
        return img
    
    def horizontal_flip(self, img: np.ndarray, boxes: list) -> Tuple[np.ndarray, list]:
        """Horizontal flip with bbox adjustment."""
        img = cv2.flip(img, 1)
        
        # Adjust bounding boxes (flip x-center)
        flipped_boxes = []
        for box in boxes:
            class_id, x_center, y_center, width, height = box
            # Flip x coordinate: new_x = 1 - old_x
            x_center = 1.0 - x_center
            flipped_boxes.append((class_id, x_center, y_center, width, height))
        
        return img, flipped_boxes
    
    def random_crop(self, img: np.ndarray, boxes: list, 
                   min_crop: float = 0.8) -> Tuple[np.ndarray, list]:
        """Random crop while preserving annotations."""
        h, w = img.shape[:2]
        
        # Random crop size (at least min_crop of original)
        crop_scale = random.uniform(min_crop, 1.0)
        crop_w = int(w * crop_scale)
        crop_h = int(h * crop_scale)
        
        # Random crop position
        x1 = random.randint(0, w - crop_w)
        y1 = random.randint(0, h - crop_h)
        x2 = x1 + crop_w
        y2 = y1 + crop_h
        
        # Crop image
        img_cropped = img[y1:y2, x1:x2]
        
        # Adjust bounding boxes
        adjusted_boxes = []
        crop_x1_norm = x1 / w
        crop_y1_norm = y1 / h
        crop_x2_norm = x2 / w
        crop_y2_norm = y2 / h
        
        for box in boxes:
            class_id, x_center, y_center, width, height = box
            
            # Check if box center is within crop
            if (crop_x1_norm <= x_center <= crop_x2_norm and
                crop_y1_norm <= y_center <= crop_y2_norm):
                
                # Adjust coordinates relative to crop
                new_x = (x_center - crop_x1_norm) / (crop_x2_norm - crop_x1_norm)
                new_y = (y_center - crop_y1_norm) / (crop_y2_norm - crop_y1_norm)
                new_w = width / (crop_x2_norm - crop_x1_norm)
                new_h = height / (crop_y2_norm - crop_y1_norm)
                
                # Clip to valid range
                new_w = min(new_w, 1.0)
                new_h = min(new_h, 1.0)
                
                if new_x >= 0 and new_x <= 1 and new_y >= 0 and new_y <= 1:
                    adjusted_boxes.append((class_id, new_x, new_y, new_w, new_h))
        
        # Only return crop if we kept some boxes
        if len(adjusted_boxes) > 0:
            return img_cropped, adjusted_boxes
        else:
            return img, boxes
    
    def augment_image(self, img_path: Path, label_path: Path, 
                     augmentation_type: str = 'full') -> Tuple[np.ndarray, list]:
        """Apply augmentation to a single image."""
        # Load image
        img = cv2.imread(str(img_path))
        if img is None:
            raise ValueError(f"Failed to load image: {img_path}")
        
        # Load annotations
        boxes = []
        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    class_id = int(parts[0])
                    x, y, w, h = map(float, parts[1:])
                    boxes.append((class_id, x, y, w, h))
        
        # Apply augmentations based on type
        if augmentation_type == 'brightness':
            img = self.adjust_brightness_contrast(img)
        elif augmentation_type == 'blur':
            img = self.add_blur(img)
        elif augmentation_type == 'noise':
            img = self.add_noise(img)
        elif augmentation_type == 'crop':
            img, boxes = self.random_crop(img, boxes)
        elif augmentation_type == 'flip':
            img, boxes = self.horizontal_flip(img, boxes)
        else:  # 'full' - random combination
            # Brightness/contrast
            if random.random() < 0.6:
                img = self.adjust_brightness_contrast(img)
            
            # Blur
            if random.random() < 0.3:
                img = self.add_blur(img)
            
            # Noise
            if random.random() < 0.4:
                img = self.add_noise(img)
            
            # Crop (less frequently as it can lose annotations)
            if random.random() < 0.2:
                img, boxes = self.random_crop(img, boxes)
            
            # Flip
            if random.random() < 0.5:
                img, boxes = self.horizontal_flip(img, boxes)
        
        return img, boxes
    
    def augment_dataset(self, dataset_dir: Path, output_dir: Path, 
                       multiplier: int = 3):
        """Augment entire dataset by a multiplier factor."""
        dataset_dir = Path(dataset_dir)
        output_dir = Path(output_dir)
        
        images_dir = dataset_dir / "images"
        labels_dir = dataset_dir / "labels"
        
        output_images_dir = output_dir / "images"
        output_labels_dir = output_dir / "labels"
        
        output_images_dir.mkdir(parents=True, exist_ok=True)
        output_labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all image files
        image_files = sorted(images_dir.glob("*.jpg"))
        
        train_files = []
        val_files = []
        
        # Load existing train/val splits
        train_txt = dataset_dir / "train.txt"
        val_txt = dataset_dir / "val.txt"
        
        train_set = set()
        val_set = set()
        
        if train_txt.exists():
            with open(train_txt, 'r') as f:
                for line in f:
                    fname = Path(line.strip()).name
                    train_set.add(fname)
        
        if val_txt.exists():
            with open(val_txt, 'r') as f:
                for line in f:
                    fname = Path(line.strip()).name
                    val_set.add(fname)
        
        total_generated = 0
        
        for img_path in image_files:
            label_path = labels_dir / f"{img_path.stem}.txt"
            
            if not label_path.exists():
                print(f"Warning: No label file for {img_path.name}")
                continue
            
            # Copy original
            orig_out_img = output_images_dir / img_path.name
            orig_out_label = output_labels_dir / label_path.name
            shutil.copy(img_path, orig_out_img)
            shutil.copy(label_path, orig_out_label)
            
            # Add to train or val
            if img_path.name in train_set:
                train_files.append(f"images/{img_path.name}")
            elif img_path.name in val_set:
                val_files.append(f"images/{img_path.name}")
            else:
                # Default to train if not in either
                train_files.append(f"images/{img_path.name}")
            
            # Generate augmented versions
            for aug_idx in range(multiplier - 1):
                aug_img, aug_boxes = self.augment_image(img_path, label_path, 'full')
                
                # Save augmented image
                aug_name = f"{img_path.stem}_aug{aug_idx}{img_path.suffix}"
                aug_img_path = output_images_dir / aug_name
                cv2.imwrite(str(aug_img_path), aug_img)
                
                # Save augmented labels
                aug_label_path = output_labels_dir / f"{img_path.stem}_aug{aug_idx}.txt"
                with open(aug_label_path, 'w') as f:
                    for box in aug_boxes:
                        class_id, x, y, w, h = box
                        f.write(f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
                
                # Add to same split as original
                if img_path.name in train_set or img_path.name not in val_set:
                    train_files.append(f"images/{aug_name}")
                else:
                    val_files.append(f"images/{aug_name}")
                
                total_generated += 1
        
        # Write train.txt and val.txt
        with open(output_dir / "train.txt", 'w') as f:
            f.write('\n'.join(train_files))
        
        with open(output_dir / "val.txt", 'w') as f:
            f.write('\n'.join(val_files))
        
        print(f"Augmentation complete:")
        print(f"  Original images: {len(image_files)}")
        print(f"  Augmented images: {total_generated}")
        print(f"  Total images: {len(image_files) + total_generated}")
        print(f"  Training: {len(train_files)} images")
        print(f"  Validation: {len(val_files)} images")
        print(f"  Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Augment YOLO dataset")
    parser.add_argument("--input", type=str, required=True, help="Input dataset directory")
    parser.add_argument("--output", type=str, required=True, help="Output dataset directory")
    parser.add_argument("--multiplier", type=int, default=3, help="Augmentation multiplier")
    
    args = parser.parse_args()
    
    augmenter = YOLOAugmenter()
    augmenter.augment_dataset(
        dataset_dir=Path(args.input),
        output_dir=Path(args.output),
        multiplier=args.multiplier
    )


if __name__ == "__main__":
    main()
