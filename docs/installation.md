# Installation Guide

## Prerequisites

Before installing ANAS, ensure your system meets these requirements:

### System Requirements
- **Operating System**: Windows 10+, Ubuntu 18.04+, macOS 10.14+, or Raspberry Pi OS
- **Python Version**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Camera**: Webcam or USB camera (required for real-time operation)

### Hardware Requirements (Optional)
- **Raspberry Pi**: Model 3B+ or newer for embedded deployment
- **GPIO Access**: For haptic feedback motor
- **Audio Output**: Speakers or audio jack for voice feedback

## Quick Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Demonking09/Stage2_Advance_navigation_System.git
cd Stage2_Advance_navigation_System
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Pre-trained Models
The system requires pre-trained models. Download them from the releases page or train your own.

## Platform-Specific Setup

### Windows Setup
```bash
# Install PyTorch (CPU version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

### Linux Setup
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-dev python3-pip

# Install PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

### macOS Setup
```bash
# Install PyTorch
pip install torch torchvision torchaudio

# Install remaining dependencies
pip install -r requirements.txt
```

### Raspberry Pi Setup
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade

# Install system dependencies
sudo apt-get install python3-dev python3-pip libatlas-base-dev

# Install PyTorch (ARM version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install GPIO support
pip install RPi.GPIO

# Install remaining dependencies
pip install -r requirements.txt
```

## Model Setup

### Download Pre-trained Models
1. Go to [Releases](https://github.com/Demonking09/Stage2_Advance_navigation_System/releases)
2. Download the latest model files:
   - `yolov8n.pt` - Obstacle detection model
   - `texture_model.pth` - Surface classification model
3. Place them in the project root directory

### Training Your Own Models (Optional)
```bash
# Train surface texture classifier
python train_with_validation_confusion.py

# Train with custom dataset
python train_texture_cnn.py
```

## Hardware Configuration

### GPIO Setup (Raspberry Pi)
```python
# Edit hardware_interface.py
HAPTIC_GPIO_PIN = 17  # Change to your GPIO pin
SPEAKER_DEVICE = "alsa"  # or "pulseaudio"
```

### Audio Setup
```bash
# Test audio output
python hardware_interface.py
```

## Verification

### Run Quick Tests
```bash
# Test all components
python quick_test.py

# Test proximity tracking
python test_proximity_tracker.py

# Test hardware interface
python hardware_interface.py
```

### Expected Output
```
============================================================
QUICK TEST: All Components
============================================================
✅ YOLO Model: Loaded successfully
✅ Texture Model: Loaded successfully
✅ Hardware Interface: Initialized
✅ Proximity Tracker: Ready
✅ Camera: Accessible

All tests passed! System ready for operation.
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Reinstall dependencies
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

#### Camera Not Found
```bash
# Check camera access
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

#### GPIO Permission Denied (Raspberry Pi)
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
# Reboot required
sudo reboot
```

#### Audio Issues
```bash
# Install audio dependencies
sudo apt-get install alsa-utils pulseaudio
```

## Next Steps

Once installation is complete:
1. [Run the main system](usage.md)
2. [Configure hardware](hardware.md)
3. [Start field testing](field-testing.md)

For detailed usage instructions, see the [Usage Guide](usage.md).