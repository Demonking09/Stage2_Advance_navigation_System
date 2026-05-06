# Testing Guide for Advanced Navigation System

## Quick Start

### 1. Test Proximity Tracker (No Camera/Models Required)

```bash
python test_proximity_tracker.py
```

**What it tests:**
- Object tracking across frames
- Approach detection (getting closer)
- Distance categorization
- Alert generation and formatting
- Cooldown logic to prevent alert spam

**Expected output:**
```
============================================================
PROXIMITY TRACKER UNIT TESTS
============================================================

Test 1: Basic Tracking
✅ Frame 1: Detected person with ID 0
✅ Frame 2: Same person tracked (ID 0)
...
✅ ALL TESTS PASSED
```

---

### 2. Test Full Pipeline (Integration Test)

```bash
python test_combined_pipeline.py
```

**What it tests:**
- Model loading (YOLO + CNN)
- Synthetic frame generation
- Proximity tracking integration
- Alert generation with hazard severity
- Surface hazard mapping

**Expected output:**
```
============================================================
INTEGRATION TEST: Combined Pipeline
============================================================

[1] Loading YOLO and texture models...
✅ YOLOv8 loaded
✅ Texture CNN loaded

[2] Creating synthetic test image...
✅ Synthetic frame created

[5] Processing detections through tracker...
  • Object 0: person at center
    Distance: moderate, Approaching: True, Urgency: 0.45
    Alert: ⚠️ [WARNING] Warning: Person approaching from center.

✅ INTEGRATION TEST PASSED
```

---

### 3. Test on Real Image File

```bash
python test_combined_pipeline.py /path/to/image.jpg
```

**What it does:**
- Loads the image
- Runs YOLO detection on it
- Saves annotated result as `test_detection_result.jpg`

**Example:**
```bash
python test_combined_pipeline.py Sample_Image.jpg
```

---

### 4. Test with Live Camera Feed

```bash
python combined_pipeline_v2.py
```

**What it does:**
- Opens webcam (device 0)
- Runs real-time YOLO detection
- Classifies floor surface texture
- Tracks approaching objects
- Speaks alerts (if pyttsx3 installed)
- Logs everything to `navigation_log.txt`

**To stop:** Press `q`

**Requirements:**
- Webcam connected
- `texture_model.pth` in current directory
- `yolov8n.pt` in current directory (auto-downloads on first run)

---

## Testing Scenarios

### Scenario 1: Approach Detection
**How to test:**
1. Run `python combined_pipeline_v2.py` or `python test_combined_pipeline.py`
2. Move your hand/object closer to simulate approach
3. Watch distance change: `moderate` → `close` → `very_close`
4. See urgency alerts escalate: `info` → `caution` → `warning` → `critical`

### Scenario 2: Hazard Detection
**How to test:**
1. Review `surface_hazard` dictionary in `combined_pipeline_v2.py`
2. Current hazard mapping:
   - `unsafe`: aluminium_foil, sandpaper, styrofoam, water
   - `caution`: sponge, corduroy, cracker, orange_peel
   - `safe`: linen, cotton, brown_bread

3. If texture model is trained, point camera at these surfaces
4. Check alerts change based on hazard severity

### Scenario 3: Multiple Objects
**How to test:**
1. Have multiple people/objects in frame
2. Each should be tracked independently (different object IDs)
3. Alerts should be generated per-object
4. Cooldown prevents spam even with multiple objects

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'proximity_tracker'"
**Fix:** Ensure `proximity_tracker.py` is in the same directory as the test script.

### "FileNotFoundError: yolov8n.pt"
**Fix:** YOLO will auto-download on first run. Make sure you have internet and ~100MB disk space.

### "FileNotFoundError: texture_model.pth"
**Fix:** Train the model first using:
```bash
python train_with_validation_confusion.py
```

### "ModuleNotFoundError: No module named 'pyttsx3'"
**Fix:** Speaker alerts will fallback to `print()`. Install if needed:
```bash
pip install pyttsx3
```

### Webcam not opening
**Fix:** Check if another app is using the camera. Or specify different device index in `combined_pipeline_v2.py`:
```python
cap = cv2.VideoCapture(1)  # Try device 1 instead of 0
```

---

## Log Files

After running tests, check:

- **`navigation_log.txt`** - Full log of all detections, alerts, and surface classifications
- **`test_detection_result.jpg`** - Annotated image with bounding boxes (if you tested with an image)

---

## Performance Tips

1. **Reduce frame size** for faster processing (edit `combined_pipeline_v2.py`):
   ```python
   frame = cv2.resize(frame, (320, 240))  # Before YOLO
   ```

2. **Skip some frames**:
   ```python
   if frame_count % 2 == 0:  # Process every other frame
       results = yolo_model(frame)
   ```

3. **Use YOLOv8n** (lightweight) instead of larger models.

---

## What Each Component Tests

| Component | Unit Test | Integration Test | Live Test |
|-----------|-----------|------------------|-----------|
| Object Tracking | ✅ test_proximity_tracker.py | ✅ test_combined_pipeline.py | ✅ combined_pipeline_v2.py |
| Approach Detection | ✅ | ✅ | ✅ |
| Alert Generation | ✅ | ✅ | ✅ |
| YOLO Detection | — | ✅ (simulated) | ✅ (real) |
| Texture Classification | — | — | ✅ (if model exists) |
| Hazard Mapping | — | ✅ | ✅ |
| Speaker/Haptic | — | — | ✅ (fallback to print) |

---

## Next Steps After Testing

1. **Validate with real users** - Test with physically impaired users if possible
2. **Add more hazard classes** - Collect data for wet floor, stairs, etc.
3. **Optimize for embedded hardware** - Profile on target device
4. **Integrate actual hardware** - Connect real speaker and haptic motors
5. **Field test** - Test in real-world navigation scenarios

