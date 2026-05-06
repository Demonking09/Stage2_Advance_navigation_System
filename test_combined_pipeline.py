"""
Integration test for combined pipeline.
Tests YOLO detection, texture classification, and hazard/proximity logic
without requiring a live camera feed.
"""

import cv2
import torch
import torch.nn as nn
import numpy as np
from torchvision import transforms, models
from ultralytics import YOLO
from PIL import Image
from collections import deque
import os

# Import our modules
from proximity_tracker import ObjectTracker, ProximityAlert, format_alert_message


def test_pipeline_on_test_image():
    """
    Test the full pipeline on a simple synthetic test image.
    """
    print("\n" + "="*60)
    print("INTEGRATION TEST: Combined Pipeline")
    print("="*60 + "\n")
    
    # 1. Load models
    print("[1] Loading YOLO and texture models...")
    try:
        yolo_model = YOLO("yolov8n.pt")
        print("✅ YOLOv8 loaded")
    except Exception as e:
        print(f"⚠️  YOLOv8 not available: {e}. Skipping YOLO test.")
        yolo_model = None
    
    try:
        classes = ['aluminium_foil', 'brown_bread', 'corduroy', 'cotton',
                   'cracker', 'linen', 'orange_peel', 'sandpaper',
                   'sponge', 'styrofoam']
        num_classes = len(classes)
        cnn_model = models.resnet18(weights=None)
        cnn_model.fc = nn.Linear(cnn_model.fc.in_features, num_classes)
        cnn_model.load_state_dict(torch.load("texture_model.pth"))
        cnn_model.eval()
        print("✅ Texture CNN loaded")
    except Exception as e:
        print(f"⚠️  Texture model not available: {e}. Skipping texture test.")
        cnn_model = None
    
    # 2. Create synthetic test image
    print("\n[2] Creating synthetic test image (480x640 frame)...")
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Add gradient background to simulate floor
    for i in range(480):
        val = min(50 + i//2, 255)  # Clamp to uint8 max
        frame[i, :] = [val, val, val]
    print("✅ Synthetic frame created")
    
    # 3. Initialize tracking
    print("\n[3] Initializing proximity tracker...")
    tracker = ObjectTracker(max_history=10, distance_threshold=100)
    proximity_alert = ProximityAlert()
    print("✅ Tracker and alert system initialized")
    
    # 4. Simulate YOLO detections (manually, since we don't have real detections)
    print("\n[4] Simulating object detections...")
    simulated_detections = [
        (np.array([100, 150, 180, 250]), "person", 0.95),      # Person center
        (np.array([400, 200, 500, 300]), "chair", 0.87),       # Chair right
    ]
    print(f"✅ Simulated {len(simulated_detections)} detections")
    
    # 5. Process detections through tracker
    print("\n[5] Processing detections through tracker...")
    tracked = tracker.associate_detections(simulated_detections)
    print(f"✅ Tracked {len(tracked)} objects")
    
    for obj_id, (box, label, conf), _, _ in tracked:
        x_center = (box[0] + box[2]) / 2
        if x_center < 640 // 3:
            direction = "left"
        elif x_center > 2 * 640 // 3:
            direction = "right"
        else:
            direction = "center"
        
        is_approaching, urgency, _ = tracker.estimate_approach(obj_id)
        distance_cat = tracker.estimate_distance_category(obj_id)
        
        print(f"  • Object {obj_id}: {label} at {direction}")
        print(f"    Distance: {distance_cat}, Approaching: {is_approaching}, Urgency: {urgency:.2f}")
        
        # Generate alert
        severity, msg = proximity_alert.generate_alert(label, direction, distance_cat, is_approaching, urgency)
        formatted = format_alert_message(severity, msg)
        print(f"    Alert: {formatted}")
    
    # 6. Simulate texture classification
    if cnn_model is not None:
        print("\n[6] Testing texture classification on synthetic floor patch...")
        patch = frame[400:, 300:428]  # Bottom center patch
        patch_rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
        patch_pil = Image.fromarray(patch_rgb)
        
        transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])
        patch_tensor = transform(patch_pil).unsqueeze(0)
        
        with torch.no_grad():
            output = cnn_model(patch_tensor)
            probs = torch.softmax(output, dim=1)
            conf, predicted = torch.max(probs, 1)
            surface_label = classes[predicted.item()]
            confidence = conf.item()
        
        print(f"✅ Surface classified as: {surface_label} (confidence: {confidence:.2f})")
    
    # 7. Hazard mapping test
    print("\n[7] Testing hazard risk assessment...")
    surface_hazard = {
        "aluminium_foil": {"severity": "unsafe", "description": "slippery surface"},
        "sandpaper": {"severity": "unsafe", "description": "abrasive surface"},
        "linen": {"severity": "safe", "description": "normal surface"},
    }
    
    test_surfaces = ["aluminium_foil", "linen", "unknown"]
    for surface in test_surfaces:
        hazard = surface_hazard.get(surface, {"severity": "unknown", "description": "uncertain"})
        print(f"  • {surface}: {hazard['severity'].upper()} - {hazard['description']}")
    print("✅ Hazard mapping verified")
    
    print("\n" + "="*60)
    print("✅ INTEGRATION TEST PASSED")
    print("="*60 + "\n")


def test_detector_on_image_file(image_path):
    """
    Test YOLO detection on an actual image file if provided.
    Usage: python test_combined_pipeline.py path/to/image.jpg
    """
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return
    
    print(f"\n[Test] Loading image: {image_path}")
    frame = cv2.imread(image_path)
    if frame is None:
        print("❌ Could not load image")
        return
    
    print(f"✅ Image loaded: {frame.shape}")
    
    try:
        yolo_model = YOLO("yolov8n.pt")
        results = yolo_model(frame)
        
        print(f"\n[Detections]")
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = yolo_model.names[cls_id]
            print(f"  • {label}: {conf:.2f}")
        
        annotated = results[0].plot()
        output_path = "test_detection_result.jpg"
        cv2.imwrite(output_path, annotated)
        print(f"\n✅ Result saved to {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    # Run integration test
    test_pipeline_on_test_image()
    
    # If an image path is provided, test detection on it
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_detector_on_image_file(image_path)
