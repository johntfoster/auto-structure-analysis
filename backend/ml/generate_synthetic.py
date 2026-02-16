"""Generate synthetic truss structure images for training."""

import argparse
import random
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


TrussType = Literal["warren", "pratt", "howe", "k_truss", "a_frame"]


class SyntheticTrussGenerator:
    """Generate synthetic truss images with YOLO annotations."""
    
    def __init__(self, image_size: tuple[int, int] = (640, 480)):
        self.image_size = image_size
        self.width, self.height = image_size
        
    def generate_warren_truss(self, num_panels: int = 3) -> tuple[list, list, list, list]:
        """Generate Warren truss coordinates and annotations."""
        panel_width = self.width / (num_panels + 1)
        truss_height = self.height * 0.4
        baseline_y = self.height * 0.7
        
        joints = []
        members = []
        supports = []
        
        # Bottom chord joints
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y
            joints.append((x, y))
        
        # Top chord joints  
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y - truss_height
            joints.append((x, y))
        
        # Bottom chord members
        for i in range(num_panels):
            members.append((joints[i], joints[i + 1]))
        
        # Top chord members
        for i in range(num_panels):
            members.append((joints[num_panels + 1 + i], joints[num_panels + 2 + i]))
        
        # Diagonal members (alternating)
        for i in range(num_panels):
            if i % 2 == 0:
                members.append((joints[i], joints[num_panels + 2 + i]))
            else:
                members.append((joints[num_panels + 1 + i], joints[i + 1]))
        
        # Supports at ends
        supports.append((joints[0], "pin"))
        supports.append((joints[num_panels], "roller"))
        
        return joints, members, supports, []
    
    def generate_pratt_truss(self, num_panels: int = 4) -> tuple[list, list, list, list]:
        """Generate Pratt truss coordinates and annotations."""
        panel_width = self.width / (num_panels + 1)
        truss_height = self.height * 0.4
        baseline_y = self.height * 0.7
        
        joints = []
        members = []
        supports = []
        
        # Bottom chord joints
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y
            joints.append((x, y))
        
        # Top chord joints
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y - truss_height
            joints.append((x, y))
        
        # Bottom chord members
        for i in range(num_panels):
            members.append((joints[i], joints[i + 1]))
        
        # Top chord members
        for i in range(num_panels):
            members.append((joints[num_panels + 1 + i], joints[num_panels + 2 + i]))
        
        # Verticals
        for i in range(num_panels + 1):
            members.append((joints[i], joints[num_panels + 1 + i]))
        
        # Diagonals (all sloping same direction)
        for i in range(num_panels):
            members.append((joints[i], joints[num_panels + 2 + i]))
        
        # Supports
        supports.append((joints[0], "pin"))
        supports.append((joints[num_panels], "roller"))
        
        return joints, members, supports, []
    
    def generate_howe_truss(self, num_panels: int = 4) -> tuple[list, list, list, list]:
        """Generate Howe truss coordinates and annotations."""
        panel_width = self.width / (num_panels + 1)
        truss_height = self.height * 0.4
        baseline_y = self.height * 0.7
        
        joints = []
        members = []
        supports = []
        
        # Bottom chord joints
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y
            joints.append((x, y))
        
        # Top chord joints
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y - truss_height
            joints.append((x, y))
        
        # Bottom chord members
        for i in range(num_panels):
            members.append((joints[i], joints[i + 1]))
        
        # Top chord members
        for i in range(num_panels):
            members.append((joints[num_panels + 1 + i], joints[num_panels + 2 + i]))
        
        # Verticals
        for i in range(num_panels + 1):
            members.append((joints[i], joints[num_panels + 1 + i]))
        
        # Diagonals (opposite direction from Pratt)
        for i in range(num_panels):
            members.append((joints[i + 1], joints[num_panels + 1 + i]))
        
        # Supports
        supports.append((joints[0], "pin"))
        supports.append((joints[num_panels], "roller"))
        
        return joints, members, supports, []
    
    def generate_k_truss(self, num_panels: int = 3) -> tuple[list, list, list, list]:
        """Generate K-truss coordinates and annotations."""
        panel_width = self.width / (num_panels + 1)
        truss_height = self.height * 0.4
        baseline_y = self.height * 0.7
        
        joints = []
        members = []
        supports = []
        
        # Bottom chord joints
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y
            joints.append((x, y))
        
        # Top chord joints
        for i in range(num_panels + 1):
            x = (i + 0.5) * panel_width
            y = baseline_y - truss_height
            joints.append((x, y))
        
        # Mid-height joints for K pattern
        for i in range(num_panels):
            x = (i + 1) * panel_width
            y = baseline_y - truss_height / 2
            joints.append((x, y))
        
        # Bottom chord members
        for i in range(num_panels):
            members.append((joints[i], joints[i + 1]))
        
        # Top chord members
        for i in range(num_panels):
            members.append((joints[num_panels + 1 + i], joints[num_panels + 2 + i]))
        
        # K-pattern diagonals
        for i in range(num_panels):
            mid_joint = joints[2 * (num_panels + 1) + i]
            members.append((joints[i], mid_joint))
            members.append((joints[i + 1], mid_joint))
            members.append((joints[num_panels + 1 + i], mid_joint))
            members.append((joints[num_panels + 2 + i], mid_joint))
        
        # Supports
        supports.append((joints[0], "pin"))
        supports.append((joints[num_panels], "roller"))
        
        return joints, members, supports, []
    
    def generate_a_frame(self) -> tuple[list, list, list, list]:
        """Generate simple A-frame structure."""
        apex_x = self.width / 2
        apex_y = self.height * 0.25
        base_y = self.height * 0.75
        span = self.width * 0.6
        
        joints = [
            (apex_x - span / 2, base_y),  # Left base
            (apex_x, apex_y),              # Apex
            (apex_x + span / 2, base_y),  # Right base
        ]
        
        members = [
            (joints[0], joints[1]),  # Left rafter
            (joints[1], joints[2]),  # Right rafter
            (joints[0], joints[2]),  # Tie beam
        ]
        
        supports = [
            (joints[0], "pin"),
            (joints[2], "roller"),
        ]
        
        return joints, members, supports, []
    
    def generate_truss(self, truss_type: TrussType, member_count: int | None = None) -> tuple[list, list, list, list]:
        """Generate truss of specified type."""
        if member_count is None:
            member_count = random.randint(3, 6)
        
        if truss_type == "warren":
            return self.generate_warren_truss(member_count)
        elif truss_type == "pratt":
            return self.generate_pratt_truss(member_count)
        elif truss_type == "howe":
            return self.generate_howe_truss(member_count)
        elif truss_type == "k_truss":
            return self.generate_k_truss(member_count)
        elif truss_type == "a_frame":
            return self.generate_a_frame()
        else:
            raise ValueError(f"Unknown truss type: {truss_type}")
    
    def add_aruco_marker(self, draw: ImageDraw.Draw, marker_id: int = 0, size: int = 60) -> tuple[int, int, int, int]:
        """Add ArUco marker to image and return its bounding box."""
        # Generate ArUco marker
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size)
        
        # Place in corner
        x = random.randint(10, 50)
        y = random.randint(10, 50)
        
        # Convert to PIL and paste
        marker_pil = Image.fromarray(marker_img)
        return (x, y, x + size, y + size), marker_pil
    
    def draw_structure(self, joints: list, members: list, supports: list, 
                       add_marker: bool = False) -> tuple[Image.Image, list]:
        """Draw structure and return image with YOLO annotations."""
        # Create image with random background
        bg_color = random.randint(220, 255)
        img = Image.new('RGB', self.image_size, color=(bg_color, bg_color, bg_color))
        draw = ImageDraw.Draw(img)
        
        annotations = []
        
        # Add ArUco marker sometimes
        if add_marker:
            marker_bbox, marker_img = self.add_aruco_marker(draw)
            img.paste(marker_img, (marker_bbox[0], marker_bbox[1]))
        
        # Vary line thickness
        member_thickness = random.randint(2, 5)
        joint_radius = random.randint(4, 8)
        
        # Draw members first (behind joints)
        for member in members:
            p1, p2 = member
            # Add slight imperfection
            jitter = random.uniform(-1, 1)
            draw.line([p1, p2], fill=(0, 0, 0), width=member_thickness)
            
            # Calculate member bounding box
            x1, y1 = p1
            x2, y2 = p2
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            
            # Normalize coordinates
            norm_cx = cx / self.width
            norm_cy = cy / self.height
            norm_w = max(length / self.width, 0.02)
            norm_h = 0.02
            
            annotations.append((1, norm_cx, norm_cy, norm_w, norm_h))
        
        # Draw joints
        for joint in joints:
            x, y = joint
            bbox = [x - joint_radius, y - joint_radius, x + joint_radius, y + joint_radius]
            draw.ellipse(bbox, fill=(50, 50, 50), outline=(0, 0, 0))
            
            # Normalize coordinates
            norm_x = x / self.width
            norm_y = y / self.height
            norm_w = (2 * joint_radius) / self.width
            norm_h = (2 * joint_radius) / self.height
            
            annotations.append((0, norm_x, norm_y, norm_w, norm_h))
        
        # Draw supports
        for support_pos, support_type in supports:
            x, y = support_pos
            size = 15
            
            if support_type == "pin":
                # Triangle for pin
                points = [
                    (x, y),
                    (x - size, y + size),
                    (x + size, y + size),
                ]
                draw.polygon(points, fill=(100, 100, 200), outline=(0, 0, 0))
                class_id = 2
            else:  # roller
                # Circle for roller
                bbox = [x - size/2, y, x + size/2, y + size]
                draw.ellipse(bbox, fill=(100, 200, 100), outline=(0, 0, 0))
                class_id = 3
            
            # Normalize coordinates
            norm_x = x / self.width
            norm_y = (y + size/2) / self.height
            norm_w = size / self.width
            norm_h = size / self.height
            
            annotations.append((class_id, norm_x, norm_y, norm_w, norm_h))
        
        # Add slight blur for realism
        if random.random() < 0.3:
            img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return img, annotations
    
    def generate_dataset(self, output_dir: Path, num_images: int = 200, 
                        train_split: float = 0.8):
        """Generate complete synthetic dataset."""
        output_dir = Path(output_dir)
        images_dir = output_dir / "images"
        labels_dir = output_dir / "labels"
        
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        truss_types: list[TrussType] = ["warren", "pratt", "howe", "k_truss", "a_frame"]
        
        train_files = []
        val_files = []
        
        for i in range(num_images):
            # Random truss type
            truss_type = random.choice(truss_types)
            
            # Generate structure
            member_count = random.randint(3, 6) if truss_type != "a_frame" else None
            joints, members, supports, _ = self.generate_truss(truss_type, member_count)
            
            # Add ArUco marker 30% of the time
            add_marker = random.random() < 0.3
            
            # Draw and get annotations
            img, annotations = self.draw_structure(joints, members, supports, add_marker)
            
            # Save image
            img_filename = f"truss_{i:04d}.jpg"
            img_path = images_dir / img_filename
            img.save(img_path, quality=95)
            
            # Save annotations
            label_filename = f"truss_{i:04d}.txt"
            label_path = labels_dir / label_filename
            with open(label_path, 'w') as f:
                for ann in annotations:
                    class_id, cx, cy, w, h = ann
                    f.write(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
            
            # Add to train or val split
            rel_path = f"images/{img_filename}"
            if random.random() < train_split:
                train_files.append(rel_path)
            else:
                val_files.append(rel_path)
        
        # Write train.txt and val.txt
        with open(output_dir / "train.txt", 'w') as f:
            f.write('\n'.join(train_files))
        
        with open(output_dir / "val.txt", 'w') as f:
            f.write('\n'.join(val_files))
        
        print(f"Generated {num_images} images:")
        print(f"  Training: {len(train_files)} images")
        print(f"  Validation: {len(val_files)} images")
        print(f"  Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic truss training data")
    parser.add_argument("--count", type=int, default=200, help="Number of images to generate")
    parser.add_argument("--output", type=str, default="ml/dataset", help="Output directory")
    parser.add_argument("--width", type=int, default=640, help="Image width")
    parser.add_argument("--height", type=int, default=480, help="Image height")
    parser.add_argument("--train-split", type=float, default=0.8, help="Training split ratio")
    
    args = parser.parse_args()
    
    generator = SyntheticTrussGenerator(image_size=(args.width, args.height))
    generator.generate_dataset(
        output_dir=Path(args.output),
        num_images=args.count,
        train_split=args.train_split
    )


if __name__ == "__main__":
    main()
