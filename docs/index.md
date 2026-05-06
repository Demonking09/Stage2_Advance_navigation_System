# Advanced Navigation Assistance System (ANAS)

Welcome to the official documentation for ANAS - an AI-powered navigation assistance system designed to help visually impaired users navigate safely through real-world environments.

## 🚀 Quick Start

Get started with ANAS in minutes:

1. [Installation Guide](installation.md)
2. [Basic Usage](usage.md)
3. [Hardware Setup](hardware.md)

## 📚 Documentation

### User Guides
- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Troubleshooting](troubleshooting.md)

### Developer Resources
- [API Reference](api-reference.md)
- [Contributing](contributing.md)
- [Architecture](architecture.md)

### Research & Testing
- [Field Testing Protocol](field-testing.md)
- [Performance Metrics](performance.md)
- [Lighting Robustness](lighting-tests.md)

## 🎯 Key Features

- **Real-time Obstacle Detection**: YOLOv8-powered object recognition
- **Surface Hazard Identification**: 67-class texture classification
- **Multi-modal Feedback**: Audio speech + haptic vibration
- **Cross-platform Support**: Windows, Linux, macOS, Raspberry Pi
- **Lighting Robustness**: Tested across 8 illumination conditions

## 📊 System Architecture

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

## 📈 Performance Metrics

| Metric | Target | Current Status |
|--------|--------|----------------|
| Obstacle Detection Rate | ≥95% | ✅ Achieved |
| False Positive Rate | ≤3% | ✅ Achieved |
| Detection Latency | <200ms | ✅ Achieved |
| Surface Classification | 67 classes | 🔄 Training (57.65% acc) |

## 🔬 Research Impact

ANAS represents a significant advancement in assistive navigation technology:

- **Accessibility**: Enhances independence for visually impaired users
- **AI Integration**: Combines computer vision with haptic feedback
- **Real-world Testing**: Comprehensive field testing protocols
- **Open Source**: Freely available for research and development

## 📞 Contact & Support

- **Repository**: [GitHub](https://github.com/Demonking09/Stage2_Advance_navigation_System)
- **Issues**: [Report Bugs](https://github.com/Demonking09/Stage2_Advance_navigation_System/issues)
- **Discussions**: [Community Forum](https://github.com/Demonking09/Stage2_Advance_navigation_System/discussions)

---

*This system is designed to assist visually impaired users but should not replace human judgment or professional mobility training.*