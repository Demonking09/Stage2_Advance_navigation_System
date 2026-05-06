#!/usr/bin/env python3
"""
Quick-start test to verify the system is working.
No external data files required.
"""

import sys
import time

print("\n" + "="*70)
print("ADVANCED NAVIGATION SYSTEM - QUICK START TEST")
print("="*70 + "\n")

# Test 1: Import check
print("[TEST 1] Checking imports...")
try:
    import cv2
    print("  ✅ OpenCV installed")
except ImportError:
    print("  ❌ OpenCV not found. Install: pip install opencv-python")
    sys.exit(1)

try:
    import torch
    print("  ✅ PyTorch installed")
except ImportError:
    print("  ❌ PyTorch not found. Install: pip install torch")
    sys.exit(1)

try:
    from ultralytics import YOLO
    print("  ✅ YOLOv8 installed")
except ImportError:
    print("  ❌ YOLOv8 not found. Install: pip install ultralytics")
    sys.exit(1)

try:
    from proximity_tracker import ObjectTracker, ProximityAlert
    print("  ✅ Proximity tracker module found")
except ImportError:
    print("  ❌ proximity_tracker.py not found in current directory")
    sys.exit(1)

# Test 2: Module functionality
print("\n[TEST 2] Running proximity tracker module tests...")
try:
    tracker = ObjectTracker(max_history=10, distance_threshold=100)
    print("  ✅ ObjectTracker initialized")
    
    alert_sys = ProximityAlert()
    print("  ✅ ProximityAlert initialized")
    
    severity, msg = alert_sys.generate_alert("person", "center", "very_close", True, 0.9)
    print(f"  ✅ Alert generated: [{severity}] {msg}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 3: Model loading
print("\n[TEST 3] Loading YOLO model (may take a moment)...")
try:
    model = YOLO("yolov8n.pt")
    print("  ✅ YOLOv8n model loaded")
except Exception as e:
    print(f"  ❌ Error loading YOLO: {e}")
    sys.exit(1)

# Test 4: Texture model
print("\n[TEST 4] Checking texture model...")
try:
    import os
    if os.path.exists("texture_model.pth"):
        import torch.nn as nn
        from torchvision import models
        cnn = models.resnet18(weights=None)
        cnn.fc = nn.Linear(cnn.fc.in_features, 10)
        cnn.load_state_dict(torch.load("texture_model.pth"))
        cnn.eval()
        print("  ✅ Texture model loaded (texture_model.pth)")
    else:
        print("  ⚠️  texture_model.pth not found (optional - train with train_with_validation_confusion.py)")
except Exception as e:
    print(f"  ⚠️  Could not load texture model: {e}")

# Test 5: Pipeline integration
print("\n[TEST 5] Testing full pipeline integration...")
try:
    import numpy as np
    from proximity_tracker import format_alert_message
    
    # Simulate a detection
    tracker = ObjectTracker()
    detection = (np.array([100, 100, 200, 250]), "person", 0.95)
    tracked = tracker.associate_detections([detection])
    
    obj_id = tracked[0][0]
    is_app, urgency, _ = tracker.estimate_approach(obj_id)
    distance = tracker.estimate_distance_category(obj_id)
    
    severity, msg = alert_sys.generate_alert("person", "center", distance, is_app, urgency)
    alert = format_alert_message(severity, msg)
    
    print(f"  ✅ Full pipeline working:")
    print(f"     {alert}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 6: Test files
print("\n[TEST 6] Checking test scripts...")
test_files = [
    "test_proximity_tracker.py",
    "test_combined_pipeline.py",
    "TESTING_GUIDE.md",
]
for fname in test_files:
    if os.path.exists(fname):
        print(f"  ✅ {fname}")
    else:
        print(f"  ❌ {fname} not found")

# Summary
print("\n" + "="*70)
print("✅ QUICK START TEST COMPLETED SUCCESSFULLY!")
print("="*70)

print("\n📚 NEXT STEPS:")
print("   1. Run unit tests:        python test_proximity_tracker.py")
print("   2. Run integration tests: python test_combined_pipeline.py")
print("   3. Test with webcam:      python combined_pipeline_v2.py")
print("   4. Read testing guide:    TESTING_GUIDE.md")

print("\n📖 For detailed testing instructions, see TESTING_GUIDE.md")
print("="*70 + "\n")
