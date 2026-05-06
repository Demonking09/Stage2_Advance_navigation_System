"""
Lighting Condition Testing Module
Tests navigation system robustness under various illumination conditions.
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(filename="lighting_test_log.txt", level=logging.INFO,
                    format="%(asctime)s - [%(levelname)s] %(message)s")

print("=" * 70)
print("LIGHTING CONDITION TESTING MODULE")
print("=" * 70)

# ============================================================================
# 1. Image Processing Utilities for Lighting Simulation
# ============================================================================

def apply_brightness(frame, factor=1.0):
    """Adjust image brightness (1.0 = normal, 0.5 = dark, 1.5 = bright)."""
    return np.clip(frame.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def apply_color_cast(frame, color_channel='blue'):
    """Apply color cast (simulates lighting from different colored light sources)."""
    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    if color_channel == 'warm':  # Warm light (yellowish)
        frame_hsv[:,:,0] = np.clip(frame_hsv[:,:,0].astype(np.float32) - 20, 0, 255).astype(np.uint8)
    elif color_channel == 'cool':  # Cool light (bluish)
        frame_hsv[:,:,0] = np.clip(frame_hsv[:,:,0].astype(np.float32) + 20, 0, 255).astype(np.uint8)
    return cv2.cvtColor(frame_hsv, cv2.COLOR_HSV2BGR)


def apply_shadows(frame, shadow_intensity=0.5):
    """Apply shadow effects (simulates uneven lighting)."""
    height, width = frame.shape[:2]
    shadow_mask = np.ones((height, width), dtype=np.float32)
    
    # Create gradient shadows from left to right
    for i in range(width):
        shadow_mask[:, i] = 1.0 - (shadow_intensity * (1.0 - (i / width)))
    
    for c in range(3):
        frame[:,:,c] = np.clip(frame[:,:,c].astype(np.float32) * shadow_mask, 0, 255).astype(np.uint8)
    return frame


def apply_glare(frame, glare_intensity=0.3):
    """Apply lens glare (simulates bright light reflections)."""
    height, width = frame.shape[:2]
    glare = np.zeros_like(frame, dtype=np.float32)
    
    # Create bright spot in center
    center_y, center_x = height // 2, width // 2
    for y in range(height):
        for x in range(width):
            dist = np.sqrt((y - center_y)**2 + (x - center_x)**2)
            radius = min(height, width) // 4
            if dist < radius:
                intensity = (1.0 - (dist / radius)) * glare_intensity
                glare[y, x] = np.array([255, 255, 200]) * intensity  # Yellowish glare
    
    frame_float = frame.astype(np.float32)
    frame_float += glare
    return np.clip(frame_float, 0, 255).astype(np.uint8)


def apply_noise(frame, noise_type='gaussian', intensity=10):
    """Add noise to simulate poor lighting conditions."""
    frame_float = frame.astype(np.float32)
    
    if noise_type == 'gaussian':
        noise = np.random.normal(0, intensity, frame.shape)
    elif noise_type == 'salt_pepper':
        noise = np.random.random(frame.shape)
        noise = np.where(noise < 0.01, 255, 0)
        noise = noise - np.where(noise < 0.01, 0, 128)
    else:
        noise = 0
    
    frame_float += noise
    return np.clip(frame_float, 0, 255).astype(np.uint8)


def apply_low_contrast(frame, contrast_factor=0.5):
    """Reduce contrast (simulates hazy or overcast conditions)."""
    mean_val = frame.mean()
    frame = frame.astype(np.float32)
    frame = (frame - mean_val) * contrast_factor + mean_val
    return np.clip(frame, 0, 255).astype(np.uint8)


# ============================================================================
# 2. Lighting Conditions Definition
# ============================================================================

LIGHTING_CONDITIONS = {
    "bright_sunlight": {
        "description": "Direct bright sunlight",
        "factor": 1.5,
        "color_cast": None,
        "shadows": 0.0,
        "glare": 0.3,
        "noise": 0,
        "contrast": 1.0
    },
    "dim_indoor": {
        "description": "Dim indoor lighting (poor light)",
        "factor": 0.4,
        "color_cast": None,
        "shadows": 0.0,
        "glare": 0.0,
        "noise": 20,
        "contrast": 0.7
    },
    "fluorescent": {
        "description": "Fluorescent lights (cool white)",
        "factor": 1.0,
        "color_cast": 'cool',
        "shadows": 0.2,
        "glare": 0.1,
        "noise": 8,
        "contrast": 0.9
    },
    "incandescent": {
        "description": "Incandescent lights (warm yellow)",
        "factor": 0.8,
        "color_cast": 'warm',
        "shadows": 0.3,
        "glare": 0.15,
        "noise": 5,
        "contrast": 0.8
    },
    "sunset": {
        "description": "Low-angle sunset light (long shadows)",
        "factor": 0.6,
        "color_cast": 'warm',
        "shadows": 0.8,
        "glare": 0.2,
        "noise": 10,
        "contrast": 0.6
    },
    "shadow": {
        "description": "Heavy shadows (building/tree shade)",
        "factor": 0.3,
        "color_cast": 'cool',
        "shadows": 0.9,
        "glare": 0.0,
        "noise": 25,
        "contrast": 0.5
    },
    "hazy": {
        "description": "Hazy/overcast conditions",
        "factor": 0.7,
        "color_cast": None,
        "shadows": 0.0,
        "glare": 0.05,
        "noise": 15,
        "contrast": 0.4
    },
    "mixed_lighting": {
        "description": "Mixed indoor/outdoor lighting",
        "factor": 0.9,
        "color_cast": None,
        "shadows": 0.5,
        "glare": 0.2,
        "noise": 12,
        "contrast": 0.7
    }
}

# ============================================================================
# 3. Synthetic Test Frame Generation
# ============================================================================

def generate_synthetic_frame(width=640, height=480):
    """Generate a synthetic test frame with simulated objects."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create background (floor pattern)
    for y in range(height):
        for x in range(width):
            if (y // 20 + x // 20) % 2 == 0:
                frame[y, x] = [100, 100, 100]
            else:
                frame[y, x] = [150, 150, 150]
    
    # Add person simulation (vertical rectangle)
    person_x, person_y = width // 2 - 40, height // 2 - 100
    cv2.rectangle(frame, (person_x, person_y), (person_x + 80, person_y + 200), (200, 150, 100), -1)
    cv2.circle(frame, (person_x + 40, person_y - 20), 20, (200, 170, 140), -1)  # Head
    
    # Add chair simulation
    chair_x, chair_y = width // 3, height - 100
    cv2.rectangle(frame, (chair_x, chair_y), (chair_x + 80, chair_y + 80), (139, 69, 19), -1)
    
    # Add texture pattern to simulate floor surface
    for y in range(height // 2, height):
        for x in range(width):
            if (y // 5 + x // 5) % 3 == 0:
                frame[y, x] = np.clip(frame[y, x].astype(np.float32) * 0.8, 0, 255).astype(np.uint8)
    
    return frame


# ============================================================================
# 4. Lighting Test Framework
# ============================================================================

class LightingTestSuite:
    """Test navigation system under various lighting conditions."""
    
    def __init__(self):
        self.results = {}
        self.test_start_time = datetime.now()
        logging.info(f"Lighting Test Suite started at {self.test_start_time}")
    
    def apply_lighting_condition(self, frame, condition_name):
        """Apply a specific lighting condition to a frame."""
        params = LIGHTING_CONDITIONS[condition_name]
        
        # Apply transformations in sequence
        frame = apply_brightness(frame, params["factor"])
        
        if params["color_cast"]:
            frame = apply_color_cast(frame, params["color_cast"])
        
        frame = apply_shadows(frame, params["shadows"])
        frame = apply_glare(frame, params["glare"])
        frame = apply_noise(frame, 'gaussian', params["noise"])
        frame = apply_low_contrast(frame, params["contrast"])
        
        return frame
    
    def test_frame_processing(self, frame, condition_name):
        """Test how frame looks under lighting condition."""
        test_frame = frame.copy()
        test_frame = self.apply_lighting_condition(test_frame, condition_name)
        return test_frame
    
    def measure_frame_quality(self, frame):
        """Measure frame quality metrics."""
        # Calculate histogram
        hist_b = cv2.calcHist([frame], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([frame], [1], None, [256], [0, 256])
        hist_r = cv2.calcHist([frame], [2], None, [256], [0, 256])
        
        # Calculate contrast (standard deviation of intensity)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        contrast = gray.std()
        
        # Calculate brightness (mean intensity)
        brightness = gray.mean()
        
        # Calculate focus quality (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        focus = laplacian.var()
        
        return {
            "brightness": brightness,
            "contrast": contrast,
            "focus": focus
        }
    
    def run_tests(self, num_test_frames=3):
        """Run lighting tests on synthetic frames."""
        print("\n" + "=" * 70)
        print("RUNNING LIGHTING CONDITION TESTS")
        print("=" * 70 + "\n")
        
        for condition_name, condition_info in LIGHTING_CONDITIONS.items():
            print(f"\n🔦 Testing: {condition_info['description']}")
            print("-" * 70)
            
            condition_results = {
                "description": condition_info['description'],
                "frames": []
            }
            
            # Generate and test multiple frames
            for frame_idx in range(num_test_frames):
                # Generate synthetic frame
                test_frame = generate_synthetic_frame()
                
                # Apply lighting condition
                lit_frame = self.test_frame_processing(test_frame, condition_name)
                
                # Measure quality
                quality = self.measure_frame_quality(lit_frame)
                
                condition_results["frames"].append({
                    "index": frame_idx,
                    "quality": quality
                })
                
                print(f"  Frame {frame_idx + 1}: Brightness={quality['brightness']:.1f}, "
                      f"Contrast={quality['contrast']:.1f}, Focus={quality['focus']:.1f}")
            
            # Calculate averages
            avg_brightness = np.mean([f["quality"]["brightness"] for f in condition_results["frames"]])
            avg_contrast = np.mean([f["quality"]["contrast"] for f in condition_results["frames"]])
            avg_focus = np.mean([f["quality"]["focus"] for f in condition_results["frames"]])
            
            condition_results["avg_brightness"] = avg_brightness
            condition_results["avg_contrast"] = avg_contrast
            condition_results["avg_focus"] = avg_focus
            
            self.results[condition_name] = condition_results
            
            print(f"  ✓ Average Metrics: Brightness={avg_brightness:.1f}, "
                  f"Contrast={avg_contrast:.1f}, Focus={avg_focus:.1f}")
            
            logging.info(f"Condition: {condition_name}, "
                        f"Brightness={avg_brightness:.1f}, "
                        f"Contrast={avg_contrast:.1f}, "
                        f"Focus={avg_focus:.1f}")
    
    def generate_report(self):
        """Generate testing report."""
        print("\n" + "=" * 70)
        print("LIGHTING TEST REPORT")
        print("=" * 70 + "\n")
        
        # Summary statistics
        all_brightness = [r["avg_brightness"] for r in self.results.values()]
        all_contrast = [r["avg_contrast"] for r in self.results.values()]
        all_focus = [r["avg_focus"] for r in self.results.values()]
        
        print("SUMMARY STATISTICS:")
        print(f"  Brightness Range: {min(all_brightness):.1f} - {max(all_brightness):.1f}")
        print(f"  Contrast Range: {min(all_contrast):.1f} - {max(all_contrast):.1f}")
        print(f"  Focus Quality Range: {min(all_focus):.1f} - {max(all_focus):.1f}")
        
        # Ranking
        print("\nCONDITIONS RANKED BY QUALITY (Best to Worst):")
        ranked = sorted(self.results.items(), 
                       key=lambda x: (x[1]["avg_focus"], x[1]["avg_contrast"]), 
                       reverse=True)
        
        for idx, (condition_name, result) in enumerate(ranked, 1):
            status = "✓ OPTIMAL" if idx <= 3 else "⚠ CHALLENGING" if idx <= 6 else "❌ DIFFICULT"
            print(f"  {idx}. {condition_name:20s} {status:15s} "
                  f"(Focus={result['avg_focus']:.1f}, Contrast={result['avg_contrast']:.1f})")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        worst_conditions = ranked[-3:]
        print(f"  ⚠️  Most challenging conditions:")
        for condition_name, _ in worst_conditions:
            print(f"      - {LIGHTING_CONDITIONS[condition_name]['description']}")
        
        print(f"\n  💡 Recommendations:")
        print(f"      - Use infrared lighting for low-light scenarios")
        print(f"      - Implement adaptive gain control for dim conditions")
        print(f"      - Apply histogram equalization for contrast enhancement")
        print(f"      - Consider multi-spectral camera for shadow/glare handling")
        
        # Save report
        report_filename = "lighting_test_report.txt"
        with open(report_filename, 'w') as f:
            f.write("LIGHTING CONDITION TEST REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now()}\n\n")
            
            for condition_name, result in ranked:
                f.write(f"\n{condition_name}:\n")
                f.write(f"  Description: {result['description']}\n")
                f.write(f"  Avg Brightness: {result['avg_brightness']:.1f}\n")
                f.write(f"  Avg Contrast: {result['avg_contrast']:.1f}\n")
                f.write(f"  Avg Focus: {result['avg_focus']:.1f}\n")
        
        print(f"\n✓ Report saved to {report_filename}")
        logging.info(f"Test report generated and saved to {report_filename}")


# ============================================================================
# 5. Main Test Execution
# ============================================================================

if __name__ == "__main__":
    # Run test suite
    suite = LightingTestSuite()
    suite.run_tests(num_test_frames=2)
    suite.generate_report()
    
    print("\n" + "=" * 70)
    print("✓ LIGHTING TEST COMPLETE")
    print("=" * 70)
