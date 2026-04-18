import cv2
import torch
import torch.nn as nn
from torchvision import transforms, models
from ultralytics import YOLO
from PIL import Image
from collections import deque
import logging

# -----------------------------
# 0. Setup Logging
# -----------------------------
logging.basicConfig(filename="navigation_log.txt", level=logging.INFO,
                    format="%(asctime)s - %(message)s")

# -----------------------------
# 1. Load YOLOv8 for obstacle detection
# -----------------------------
yolo_model = YOLO("yolov8n.pt")

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

# -----------------------------
# 4. Feedback Simulation Module
# -----------------------------
def feedback_obstacle(label, direction):
    # Simulate haptic/audio feedback
    print(f"[FEEDBACK] Obstacle {label} → {direction} actuator vibration")

def feedback_surface(label):
    # Risk assessment: safe vs unsafe
    unsafe = ["aluminium_foil", "sandpaper", "styrofoam"]
    if label in unsafe:
        print(f"[FEEDBACK] Surface {label} → Warning: unsafe/slippery")
    else:
        print(f"[FEEDBACK] Surface {label} → Safe")

# -----------------------------
# 5. Fusion Module (YOLO + CNN)
# -----------------------------
def fuse_context(obstacle_label, surface_label):
    return f"Fusion: {obstacle_label} detected on {surface_label} surface"

# -----------------------------
# 6. Real-time Capture Loop
# -----------------------------
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # --- YOLO Detection ---
    results = yolo_model(frame)
    annotated_frame = results[0].plot()

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = yolo_model.names[cls_id]

        x_center = (box.xyxy[0][0] + box.xyxy[0][2]) / 2
        if x_center < frame.shape[1] // 3:
            direction = "left"
        elif x_center > 2 * frame.shape[1] // 3:
            direction = "right"
        else:
            direction = "center"

        print(f"Obstacle Detected: {label} ({conf:.2f}) → {direction}")
        feedback_obstacle(label, direction)
        logging.info(f"Obstacle: {label}, Conf: {conf:.2f}, Dir: {direction}")

    # --- CNN Texture Classification ---
    h, w, _ = frame.shape
    patch = frame[h-128:h, w//2-64:w//2+64]
    patch_rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
    patch_pil = Image.fromarray(patch_rgb)
    patch_tensor = transform(patch_pil).unsqueeze(0)

    with torch.no_grad():
        output = cnn_model(patch_tensor)
        probs = torch.softmax(output, dim=1)
        conf, predicted = torch.max(probs, 1)
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
    feedback_surface(stable_label)
    logging.info(f"Surface: {stable_label}")

    # --- Fusion Example ---
    if results[0].boxes:
        fused = fuse_context(yolo_model.names[int(results[0].boxes[0].cls[0])], stable_label)
        print(fused)
        logging.info(fused)

    # --- Display ---
    cv2.imshow("Stage2 Pipeline", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
