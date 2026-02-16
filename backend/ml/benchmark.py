"""Performance benchmarking for YOLO model inference."""

import argparse
import time
from pathlib import Path
from typing import List

import cv2
import numpy as np
import psutil
from ultralytics import YOLO


class ModelBenchmark:
    """Benchmark YOLO model performance."""
    
    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self.model = None
        self.latencies: List[float] = []
        
    def load_model(self):
        """Load YOLO model."""
        print(f"Loading model from {self.model_path}...")
        start = time.time()
        self.model = YOLO(str(self.model_path))
        load_time = time.time() - start
        print(f"Model loaded in {load_time:.3f}s")
        return load_time
    
    def benchmark_inference(self, image_dir: Path, num_images: int = 50,
                          conf_threshold: float = 0.25) -> dict:
        """
        Benchmark inference on multiple images.
        
        Args:
            image_dir: Directory containing test images
            num_images: Number of images to test
            conf_threshold: Confidence threshold
            
        Returns:
            Benchmark results
        """
        image_dir = Path(image_dir)
        
        # Get image files
        image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        
        if len(image_files) == 0:
            raise ValueError(f"No images found in {image_dir}")
        
        # Limit to num_images
        image_files = image_files[:num_images]
        actual_count = len(image_files)
        
        print(f"\nBenchmarking on {actual_count} images...")
        
        # Warm-up run
        print("Warming up...")
        img = cv2.imread(str(image_files[0]))
        _ = self.model.predict(img, conf=conf_threshold, verbose=False)
        
        # Benchmark runs
        print("Running benchmark...")
        self.latencies = []
        detections_count = []
        
        # Get initial memory
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_total = time.time()
        
        for i, img_path in enumerate(image_files):
            # Load image
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            
            # Time inference
            start = time.time()
            results = self.model.predict(img, conf=conf_threshold, verbose=False)
            latency = time.time() - start
            
            self.latencies.append(latency)
            
            # Count detections
            num_detections = len(results[0].boxes) if results else 0
            detections_count.append(num_detections)
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{actual_count} images...")
        
        total_time = time.time() - start_total
        
        # Get final memory
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_usage = mem_after - mem_before
        
        # Calculate statistics
        latencies_sorted = sorted(self.latencies)
        n = len(latencies_sorted)
        
        avg_latency = np.mean(latencies_sorted)
        min_latency = np.min(latencies_sorted)
        max_latency = np.max(latencies_sorted)
        p50 = latencies_sorted[int(n * 0.5)]
        p95 = latencies_sorted[int(n * 0.95)]
        p99 = latencies_sorted[int(n * 0.99)] if n >= 100 else latencies_sorted[-1]
        
        throughput = actual_count / total_time
        avg_detections = np.mean(detections_count)
        
        results = {
            "num_images": actual_count,
            "total_time": total_time,
            "avg_latency_ms": avg_latency * 1000,
            "min_latency_ms": min_latency * 1000,
            "max_latency_ms": max_latency * 1000,
            "p50_latency_ms": p50 * 1000,
            "p95_latency_ms": p95 * 1000,
            "p99_latency_ms": p99 * 1000,
            "throughput_img_per_sec": throughput,
            "memory_usage_mb": mem_usage,
            "avg_detections_per_image": avg_detections,
        }
        
        return results
    
    def print_results(self, results: dict):
        """Print benchmark results."""
        print("\n" + "="*60)
        print("BENCHMARK RESULTS")
        print("="*60)
        print(f"\nImages processed: {results['num_images']}")
        print(f"Total time: {results['total_time']:.2f}s")
        print(f"\nLatency (ms):")
        print(f"  Average:  {results['avg_latency_ms']:8.2f}")
        print(f"  Min:      {results['min_latency_ms']:8.2f}")
        print(f"  Max:      {results['max_latency_ms']:8.2f}")
        print(f"  P50:      {results['p50_latency_ms']:8.2f}")
        print(f"  P95:      {results['p95_latency_ms']:8.2f}")
        print(f"  P99:      {results['p99_latency_ms']:8.2f}")
        print(f"\nThroughput: {results['throughput_img_per_sec']:.2f} images/sec")
        print(f"Memory usage: {results['memory_usage_mb']:.2f} MB")
        print(f"Avg detections: {results['avg_detections_per_image']:.1f} per image")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Benchmark YOLO model performance")
    parser.add_argument("--model", type=str, required=True, help="Path to YOLO model")
    parser.add_argument("--images", type=str, required=True, help="Directory containing test images")
    parser.add_argument("--count", type=int, default=50, help="Number of images to test")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    
    args = parser.parse_args()
    
    # Check if model exists
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        exit(1)
    
    # Check if image directory exists
    image_dir = Path(args.images)
    if not image_dir.exists():
        print(f"Error: Image directory not found at {image_dir}")
        exit(1)
    
    # Run benchmark
    benchmark = ModelBenchmark(model_path)
    
    try:
        load_time = benchmark.load_model()
        results = benchmark.benchmark_inference(image_dir, args.count, args.conf)
        results['model_load_time'] = load_time
        benchmark.print_results(results)
        
    except Exception as e:
        print(f"Benchmark failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
