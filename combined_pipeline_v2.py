"""
Advanced Navigation Assistance System (ANAS) - Stage 2
Main Pipeline for Real-time Obstacle Detection and Surface Hazard Identification

This module integrates YOLOv8 object detection, ResNet18 texture classification,
proximity tracking, and hardware feedback (audio/haptic) to assist visually impaired users.

Features:
- Real-time obstacle detection with proximity tracking
- Surface texture classification (10 classes)
- Multi-modal alerts (speech + vibration)
- Cross-platform hardware support
- Logging and diagnostics

Author: Demonking09
Date: April 2026
"""

import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from ultralytics import YOLO
from PIL import Image
from collections import deque
import logging
import time
from proximity_tracker import ObjectTracker, ProximityAlert, format_alert_message
from hardware_interface import init_hardware, get_hardware, close_hardware

# -----------------------------
# 0. Setup Logging
# -----------------------------
logging.basicConfig(filename="navigation_log.txt", level=logging.INFO,
                    format="%(asctime)s - %(message)s")

# Initialize hardware interface (speaker + haptic)
hardware = init_hardware()

# -----------------------------
# 1. Load YOLOv8 for obstacle detection
# -----------------------------
yolo_model = YOLO("yolov8s.pt")  # Upgraded to yolov8s for better accuracy

# -----------------------------
# 2. Load CNN for texture classification
# -----------------------------
classes = ['aluminium_foil', 'brown_bread', 'corduroy', 'cotton',
           'cracker', 'linen', 'orange_peel', 'sandpaper',
           'sponge', 'styrofoam']

num_classes = len(classes)
cnn_model = models.resnet18(weights=None)
cnn_model.fc = nn.Linear(cnn_model.fc.in_features, num_classes)
cnn_model.load_state_dict(torch.load("texture_model.pth"))
cnn_model.eval()

transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# -----------------------------
# 3. Prediction Buffer (for smoothing)
# -----------------------------
prediction_buffer = deque(maxlen=10)

# ============================================================================
# 4. Hardware-Integrated Alert Functions
# ============================================================================

def speak_alert(message):
    """
    Generate audio alert using the hardware interface.

    Args:
        message (str): The text message to speak
    """
    hardware.speak(message)


def vibrate_alert(duration=0.15):
    """
    Trigger haptic vibration feedback using the hardware interface.

    Args:
        duration (float): Vibration duration in seconds (default: 0.15)
    """
    duration_ms = int(duration * 1000)
    hardware.vibrate(duration_ms)


# Proximity/Approach Tracking
tracker = ObjectTracker(max_history=15, distance_threshold=80)
proximity_alert = ProximityAlert()

surface_hazard = {
    "water": {"severity": "unsafe", "description": "wet floor"},
    "aluminium_foil": {"severity": "unsafe", "description": "slippery surface"},
    "sandpaper": {"severity": "unsafe", "description": "rough or unsafe surface"},
    "styrofoam": {"severity": "unsafe", "description": "unstable surface"},
    "sponge": {"severity": "caution", "description": "wet or soft area"},
    "corduroy": {"severity": "caution", "description": "uneven surface"},
    "cracker": {"severity": "caution", "description": "fragile or bumpy surface"},
    "orange_peel": {"severity": "caution", "description": "textured surface"},
    "linen": {"severity": "safe", "description": "normal surface"},
    "cotton": {"severity": "safe", "description": "normal surface"},
    "brown_bread": {"severity": "safe", "description": "normal surface"},
}


def classify_surface_hazard(label):
    """
    Classify surface texture into hazard severity categories.

    Args:
        label (str): Predicted texture class label

    Returns:
        dict: Hazard metadata with 'severity' and 'description' keys
    """
    if label == "Unknown":
        return {"severity": "unknown", "description": "uncertain surface"}
    return surface_hazard.get(label, {"severity": "caution", "description": "unknown surface"})


def feedback_obstacle(label, direction, surface_severity="safe"):
    """
    Generate obstacle detection alert with surface hazard consideration.

    Args:
        label (str): Detected object class (e.g., 'person', 'chair')
        direction (str): Spatial direction ('left', 'center', 'right')
        surface_severity (str): Surface hazard level ('safe', 'caution', 'unsafe')
    """
    # Basic audio/haptic alert for obstacle direction.
    if label == "person":
        if surface_severity == "unsafe":
            message = f"Danger: person detected {direction} ahead on a hazardous surface."
        else:
            message = f"Person detected {direction} ahead. Please be careful."
    else:
        if surface_severity == "unsafe":
            message = f"Danger: {label} detected {direction} on a hazardous surface."
        else:
            message = f"Obstacle {label} detected {direction}."
    
    # Use hardware interface with appropriate severity mapping
    alert_severity = "critical" if surface_severity == "unsafe" else "warning"
    hardware.alert(message, severity=alert_severity)


def feedback_approach(severity, message):
    """
    Generate proximity-based approach alert with severity-appropriate feedback.

    Args:
        severity (str): Alert severity level ('critical', 'warning', 'caution', 'info')
        message (str): Alert message text
    """
    # Use hardware interface alert with severity
    hardware.alert(message, severity=severity)


def feedback_surface(label):
    """
    Generate surface hazard alert based on texture classification.

    Args:
        label (str): Predicted surface texture class

    Returns:
        dict: Hazard metadata with severity and description
    """
    meta = classify_surface_hazard(label)
    if meta["severity"] == "unknown":
        message = "Surface unknown. Please proceed with caution."
        alert_severity = "info"
    elif meta["severity"] == "unsafe":
        message = f"Warning: {meta['description']} detected ({label})."
        alert_severity = "warning"
    elif meta["severity"] == "caution":
        message = f"Caution: {meta['description']} detected." 
        alert_severity = "caution"
    else:
        message = f"{meta['description'].capitalize()} detected."
        alert_severity = "info"
    
    hardware.alert(message, severity=alert_severity)
    return meta


# -----------------------------
# 5. Fusion Module (YOLO + CNN)
# -----------------------------
def fuse_context(obstacle_label, surface_label, hazard_description):
    """
    Fuse obstacle and surface information into a comprehensive context message.

    Args:
        obstacle_label (str): Detected obstacle class
        surface_label (str): Predicted surface texture
        hazard_description (str): Surface hazard description

    Returns:
        str: Fused context message
    """
    if surface_label == "Unknown":
        return f"Fusion: {obstacle_label} detected on unknown surface"
    return f"Fusion: {obstacle_label} detected on {hazard_description} ({surface_label})"


def get_floor_patches(frame, patch_size=128):
    """
    Extract floor texture patches from the bottom portion of the frame.

    Args:
        frame (numpy.ndarray): Input video frame (BGR format)
        patch_size (int): Size of square patches to extract (default: 128)

    Returns:
        list: List of extracted image patches
    """
    h, w, _ = frame.shape
    y1 = max(0, h - patch_size)
    centers = [w // 4, w // 2, 3 * w // 4]
    patches = []
    for cx in centers:
        x1 = max(0, cx - patch_size // 2)
        x2 = min(w, x1 + patch_size)
        patches.append(frame[y1:h, x1:x2])
    return patches

# -----------------------------
# 6. Real-time Capture Loop
# -----------------------------
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # --- YOLO Detection with Proximity Tracking ---
    results = yolo_model(frame)
    annotated_frame = results[0].plot()

    # Prepare detections for tracking
    detections = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        if conf < 0.5:  # Filter low-confidence detections to improve precision
            continue
        label = yolo_model.names[cls_id]
        detections.append((box.xyxy[0].cpu().numpy(), label, conf))
    
    # Track and analyze proximity
    tracked = tracker.associate_detections(detections)
    
    for obj_id, (box, label, conf), _, _ in tracked:
        x_center = (box[0] + box[2]) / 2
        if x_center < frame.shape[1] // 3:
            direction = "left"
        elif x_center > 2 * frame.shape[1] // 3:
            direction = "right"
        else:
            direction = "center"
        
        # Analyze approach
        is_approaching, urgency, _ = tracker.estimate_approach(obj_id)
        distance_cat = tracker.estimate_distance_category(obj_id)
        
        print(f"Obstacle Detected: {label} ({conf:.2f}) → {direction} [{distance_cat}] (approaching={is_approaching})")
        
        # Generate proximity-aware alert
        severity, prox_message = proximity_alert.generate_alert(label, direction, distance_cat, is_approaching, urgency)
        
        if proximity_alert.should_alert(obj_id, severity):
            formatted_msg = format_alert_message(severity, prox_message)
            print(formatted_msg)
            feedback_approach(severity, prox_message)
            logging.info(f"Approach Alert [{severity}]: {prox_message}")
        
        logging.info(f"Obstacle: {label}, Conf: {conf:.2f}, Dir: {direction}, Dist: {distance_cat}")

    # --- CNN Texture Classification ---
    patches = get_floor_patches(frame, patch_size=128)
    patch_tensors = []
    for patch in patches:
        patch_rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
        patch_pil = Image.fromarray(patch_rgb)
        patch_tensors.append(transform(patch_pil).unsqueeze(0))

    patch_batch = torch.cat(patch_tensors, dim=0)
    with torch.no_grad():
        output = cnn_model(patch_batch)
        probs = torch.softmax(output, dim=1)
        avg_probs = probs.mean(dim=0)
        conf, predicted = torch.max(avg_probs, 0)
        confidence = conf.item()

        if confidence < 0.5:
            surface_label = "Unknown"
        else:
            surface_label = classes[predicted.item()]

    prediction_buffer.append((surface_label, confidence))

    confidence_sum = {}
    for label, conf in prediction_buffer:
        confidence_sum[label] = confidence_sum.get(label, 0) + conf
    stable_label = max(confidence_sum, key=confidence_sum.get)

    print(f"Surface Texture (smoothed): {stable_label}")
    surface_meta = feedback_surface(stable_label)
    logging.info(f"Surface: {stable_label}, Risk: {surface_meta['severity']}")

    # If we detected an obstacle and a risky surface, update obstacle warning.
    if results[0].boxes:
        first_label = yolo_model.names[int(results[0].boxes[0].cls[0])]
        first_direction = "center"
        first_box = results[0].boxes[0].xyxy[0]
        x_center = (first_box[0] + first_box[2]) / 2
        if x_center < frame.shape[1] // 3:
            first_direction = "left"
        elif x_center > 2 * frame.shape[1] // 3:
            first_direction = "right"
        print(f"Updating obstacle feedback for surface hazard {surface_meta['severity']}")
        feedback_obstacle(first_label, first_direction, surface_meta['severity'])

        fused = fuse_context(first_label, stable_label, surface_meta['description'])
        print(fused)
        logging.info(fused)

    # --- Display ---
    cv2.imshow("Stage2 Pipeline", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

# Cleanup hardware resources
close_hardware()
print("✓ Pipeline closed and hardware cleaned up.")

