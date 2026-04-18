import cv2
from ultralytics import YOLO

# -----------------------------
# 1. Load YOLOv8 model
# -----------------------------
# Use the lightweight YOLOv8n model (fast for real-time)
model = YOLO("yolov8n.pt")

# -----------------------------
# 2. Open webcam (or replace with video file path)
# -----------------------------
cap = cv2.VideoCapture(0)  # 0 = default webcam

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # -----------------------------
    # 3. Run YOLOv8 detection
    # -----------------------------
    results = model(frame)

    # Annotated frame with bounding boxes
    annotated_frame = results[0].plot()

    # Print detections in console
    for box in results[0].boxes:
        cls_id = int(box.cls[0])          # class ID
        conf = float(box.conf[0])         # confidence score
        label = model.names[cls_id]       # class label
        print(f"Detected: {label} ({conf:.2f})")

    # -----------------------------
    # 4. Display results
    # -----------------------------
    cv2.imshow("Obstacle Detection", annotated_frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
