# Dataset Preparation for Truss Structure Detection

This directory contains the training and validation datasets for YOLO-based truss structure detection.

## Dataset Format

This dataset uses YOLO annotation format. Each image has a corresponding text file with the same name.

### Annotation Format

Each line in the annotation file represents one object:

```
<class_id> <x_center> <y_center> <width> <height>
```

Where:
- `class_id`: Integer class identifier (0-3)
- `x_center`: Normalized x-coordinate of bounding box center (0.0 - 1.0)
- `y_center`: Normalized y-coordinate of bounding box center (0.0 - 1.0)
- `width`: Normalized width of bounding box (0.0 - 1.0)
- `height`: Normalized height of bounding box (0.0 - 1.0)

### Classes

- `0`: **joint** - Connection point between members
- `1`: **member** - Structural beam/truss member
- `2`: **support_pin** - Pinned support (constrains x,y translation)
- `3`: **support_roller** - Roller support (constrains y translation only)

## Directory Structure

```
dataset/
├── README.md          # This file
├── images/            # All image files (.jpg, .png)
├── labels/            # YOLO annotation files (.txt)
├── train.txt          # List of training image paths (one per line)
└── val.txt            # List of validation image paths (one per line)
```

## Generating Synthetic Data

To generate synthetic training data:

```bash
cd /path/to/backend
uv run python ml/generate_synthetic.py --count 200 --output ml/dataset
```

This will:
1. Create 200 synthetic truss structure images
2. Generate corresponding YOLO annotation files
3. Split data into training (80%) and validation (20%) sets
4. Create `train.txt` and `val.txt` index files

## Adding Real Data

To add real images:

1. Place image files in `dataset/images/`
2. Create annotation files in `dataset/labels/` with matching names
3. Add image paths to `train.txt` or `val.txt`

Example:
```
# File: dataset/images/truss_001.jpg
# File: dataset/labels/truss_001.txt
0 0.5 0.3 0.05 0.05
1 0.3 0.3 0.2 0.02
1 0.7 0.3 0.2 0.02
2 0.1 0.9 0.03 0.03
3 0.9 0.9 0.03 0.03
```

## Training

After preparing the dataset, run training:

```bash
cd /path/to/backend
uv run python ml/train.py
```

This will:
- Load the dataset configuration from `ml/config.yaml`
- Fine-tune YOLOv8 nano model
- Save the best model to `ml/models/best.pt`
- Export to TFLite and ONNX formats

## Evaluation

To evaluate model performance:

```bash
uv run python ml/evaluate.py
```

This generates:
- mAP (mean Average Precision) metrics
- Per-class precision and recall
- Confusion matrix plot
