# Advanced Navigation Assistance System (ANAS) - Stage 2

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)

An AI-powered navigation assistance system designed to help visually impaired users navigate safely through real-world environments. This system combines real-time obstacle detection, surface hazard identification, and multi-modal feedback (audio and haptic) to provide comprehensive navigation support.

## 🎯 Project Overview

**Status:** Production-Ready for Field Testing (April 2026)  
**Target Users:** Visually impaired individuals  
**Platform:** Cross-platform (Windows, Linux, macOS, Raspberry Pi)  
**AI Models:** YOLOv8n for obstacle detection, ResNet50 for surface texture classification  
**Site is live at:** https://demonking09.github.io/Stage2_Advance_navigation_System/

### Key Capabilities
- **Real-time Obstacle Detection:** Identifies persons, furniture, stairs, doors, and other navigation hazards
- **Surface Hazard Recognition:** Classifies 67 different floor textures and maps them to safety risks
- **Proximity Tracking:** Monitors object approach and provides timely warnings
- **Multi-modal Alerts:** Audio speech synthesis and haptic vibration feedback
- **Lighting Robustness:** Tested across 8 different lighting conditions
- **Hardware Integration:** Production-ready drivers for Raspberry Pi and desktop systems

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Webcam or camera device
- (Optional) Raspberry Pi with GPIO and I2S for hardware feedback

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Demonking09/Stage2_Advance_navigation_System.git
   cd Stage2_Advance_navigation_System
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   # Activate (Windows)
   .venv\Scripts\activate
   # Activate (Linux/macOS)
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   pip install ultralytics opencv-python numpy pillow pyttsx3
   # For Raspberry Pi hardware support
   pip install RPi.GPIO
   ```

### Basic Usage

1. **Run the main system:**
   ```bash
   python combined_pipeline_v2.py
   ```
   - Press 'q' to quit
   - The system will start camera capture and provide real-time audio/haptic feedback

2. **Test components individually:**
   ```bash
   # Quick validation of all components
   python quick_test.py

   # Test proximity tracking
   python test_proximity_tracker.py

   # Test lighting robustness
   python test_lighting_conditions.py

   # Test hardware interface
   python hardware_interface.py
   ```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│         User Feedback Layer                          │
│   (Audio via TTS + Haptic Vibration)                │
│   [hardware_interface.py]                           │
├─────────────────────────────────────────────────────┤
│         Decision & Fusion Layer                      │
│   ├─ Proximity Tracking [proximity_tracker.py]      │
│   ├─ Surface Hazard Mapping                         │
│   ├─ Severity Assessment                            │
│   └─ Alert Filtering                                │
├─────────────────────────────────────────────────────┤
│         Detection Layer                              │
│   ├─ Obstacle Detection [YOLO v8n]                  │
│   ├─ Surface Classification [ResNet50 - 67 classes] │
│   ├─ Direction Classification                       │
│   └─ Distance Estimation                            │
├─────────────────────────────────────────────────────┤
│         Input Layer                                  │
│   ├─ Camera Capture [OpenCV]                        │
│   ├─ Frame Preprocessing                            │
│   ├─ Lighting Adaptation                            │
│   └─ Performance Optimization                       │
└─────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Obstacle Detection (`obstacle_detection.py`)
- **Model:** YOLOv8n (5.2M parameters)
- **Classes:** person, chair, stairs, door, furniture, etc.
- **Performance:** Real-time on CPU (<100ms latency)

#### 2. Surface Classification (`train_with_validation_confusion.py`)
- **Model:** ResNet50 fine-tuned on 67 texture classes
- **Input:** 128×128 RGB image patches
- **Classes:** aluminium_foil, banded, blotchy, braided, bubbly, bumpy, etc.
- **Hazard Mapping:** Semantic mapping from texture to safety risk

#### 3. Proximity Tracking (`proximity_tracker.py`)
- **Algorithm:** Frame-to-frame object tracking using bounding box analysis
- **Categories:** very_close, close, moderate, far
- **Alerts:** Approach warnings with configurable urgency levels

#### 4. Hardware Interface (`hardware_interface.py`)
- **Platforms:** Windows, Linux, macOS, Raspberry Pi
- **Audio:** Text-to-speech (pyttsx3) or I2S (Festival TTS)
- **Haptic:** GPIO PWM vibration motor control
- **Fallback:** Console output for development/testing

## 📊 Performance Metrics

### Obstacle Detection
- **Detection Rate:** ≥95% (target), ≥90% (threshold)
- **False Positive Rate:** ≤3% (target), ≤5% (threshold)
- **Latency:** <200ms (target), <400ms (threshold)

### Surface Classification
- **Training Progress:** Epoch 17/50 (70% validation accuracy)
- **Expected Final:** 90-95% accuracy
- **Classes:** 67 texture types (expanded from 10)

### Lighting Robustness
Tested across 8 conditions with optimal performance in:
- Dim indoor lighting
- Bright sunlight
- Fluorescent lighting

## 🧪 Testing & Validation

### Test Suites
- **Unit Tests:** Component-level validation
- **Integration Tests:** Full pipeline testing
- **Lighting Tests:** Robustness across illumination conditions
- **Hardware Tests:** Platform-specific driver validation

### Field Testing Protocol
Comprehensive testing framework covering:
- **Safety Protocols:** IRB approval, informed consent
- **Test Environments:** 3 tiers (controlled → real-world)
- **Metrics:** Objective (accuracy, latency) + subjective (user surveys)
- **Timeline:** 7+ weeks (pilot → full validation)

See [FIELD_TESTING_GUIDE.md](FIELD_TESTING_GUIDE.md) for detailed protocols.

## � Documentation

📖 **Full Documentation Website**: [https://demonking09.github.io/Stage2_Advance_navigation_System](https://demonking09.github.io/Stage2_Advance_navigation_System)

### Documentation Files
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [QUICK_START.md](QUICK_START.md) - Developer quick start guide
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures and validation
- [FIELD_TESTING_GUIDE.md](FIELD_TESTING_GUIDE.md) - Field testing protocol

## �📁 Project Structure

```
Stage2_Advance_navigation_System/
├── combined_pipeline_v2.py           # Main application
├── hardware_interface.py             # Hardware abstraction layer
├── proximity_tracker.py              # Object tracking logic
├── obstacle_detection.py             # YOLO-based detection
├── lebles_images.py                  # Image labeling utilities
│
├── Models/
│   ├── yolov8n.pt                   # Obstacle detection model
│   ├── texture_model.pth            # Original texture classifier
│   ├── best_model.pth               # Best training checkpoint
│   └── texture_model_resnet50.pth   # 67-class ResNet50 model
│
├── Dataset/
│   ├── Combined_Textures/           # 67 texture classes dataset
│   ├── dtd/                         # Describable Textures Dataset
│   └── image/                       # Test images
│
├── Test Scripts/
│   ├── quick_test.py                # Component validation
│   ├── test_proximity_tracker.py     # Tracking unit tests
│   ├── test_combined_pipeline.py     # Integration tests
│   └── test_lighting_conditions.py   # Lighting robustness tests
│
├── Training Scripts/
│   ├── train_with_validation_confusion.py  # Active 67-class training
│   ├── train_and_test_combined.py   # Combined training pipeline
│   └── train_texture_cnn.py         # CNN texture training
│
├── Documentation/
│   ├── IMPLEMENTATION_SUMMARY.md     # Technical implementation details
│   ├── QUICK_START.md               # Developer quick start
│   ├── TESTING_GUIDE.md             # Testing procedures
│   ├── FIELD_TESTING_GUIDE.md       # Field testing protocol
│   └── SESSION_COMPLETION_REPORT.md  # Development progress
│
├── Logs & Reports/
│   ├── navigation_log.txt           # Runtime event logging
│   ├── diagnostics.csv              # Training diagnostics
│   ├── lighting_test_report.txt     # Lighting test results
│   └── lighting_test_log.txt        # Lighting test logs
│
├── Figures/                         # Training visualizations
├── GradCAM_Reports/                 # Model interpretability
└── Misclassified/                   # Error analysis samples
```

## 🔧 Hardware Setup (Raspberry Pi)

### GPIO Haptic Motor
```
GPIO17 (pin 11) → Vibration Motor Ground
GPIO VCC → Motor +5V (through MOSFET)
```

### I2S Audio Setup
```bash
# Install ALSA and Festival TTS
sudo apt-get install alsa-utils festival
```

### Configuration
```python
from hardware_interface import init_hardware

# Auto-detect platform
hardware = init_hardware()

# Or specify manually
hardware = init_hardware(platform=PlatformType.RASPBERRY_PI, haptic_gpio_pin=27)
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **YOLOv8:** Ultralytics for the excellent object detection framework
- **PyTorch:** Facebook AI Research for the deep learning platform
- **OpenCV:** Intel for computer vision libraries
- **Raspberry Pi Community:** For hardware integration support

## 📞 Contact

**Project Lead:** Demonking09  
**Repository:** [GitHub](https://github.com/Demonking09/Stage2_Advance_navigation_System)  
**Issues:** [GitHub Issues](https://github.com/Demonking09/Stage2_Advance_navigation_System/issues)

---

*This system is designed to assist visually impaired users but should not replace human judgment or professional mobility training. Always test thoroughly in controlled environments before real-world deployment.*
