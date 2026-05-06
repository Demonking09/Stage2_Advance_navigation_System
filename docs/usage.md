# Usage Guide

## Basic Operation

### Starting the System
```bash
cd Stage2_Advance_navigation_System
python combined_pipeline_v2.py
```

### Controls
- **Camera Feed**: Real-time video with object detection overlays
- **Audio Alerts**: Voice announcements of detected obstacles
- **Haptic Feedback**: Vibration patterns for different alert levels
- **Exit**: Press `q` to quit the application

## Alert System

### Alert Types

| Severity | Vibration | Audio Example | Use Case |
|----------|-----------|----------------|----------|
| **Critical** | 300ms | "Danger: person directly ahead!" | Immediate threat |
| **Warning** | 200ms | "Warning: obstacle ahead" | Close obstacle |
| **Caution** | 150ms | "Caution: uneven surface" | Surface hazard |
| **Info** | 100ms | "Person detected to the left" | General information |

### Surface Hazard Alerts
- **Safe**: "Normal surface detected"
- **Caution**: "Caution: soft surface detected"
- **Unsafe**: "Warning: slippery surface detected (aluminium_foil)"

## Advanced Usage

### Command Line Options
```bash
# Run with specific camera
python combined_pipeline_v2.py --camera 1

# Disable audio alerts
python combined_pipeline_v2.py --no-audio

# Enable debug logging
python combined_pipeline_v2.py --debug
```

### Configuration Files
Edit `config.json` for custom settings:
```json
{
  "camera": {
    "device_id": 0,
    "resolution": [640, 480]
  },
  "detection": {
    "confidence_threshold": 0.5,
    "max_objects": 10
  },
  "alerts": {
    "audio_enabled": true,
    "haptic_enabled": true,
    "cooldown_seconds": 2.0
  }
}
```

## Testing Modes

### Component Testing
```bash
# Test proximity tracking only
python test_proximity_tracker.py

# Test lighting robustness
python test_lighting_conditions.py

# Test integrated pipeline
python test_combined_pipeline.py
```

### Hardware Testing
```bash
# Test audio output
python hardware_interface.py --test-audio

# Test haptic feedback
python hardware_interface.py --test-haptic

# Test combined alerts
python hardware_interface.py --test-all
```

## Real-world Usage Scenarios

### Indoor Navigation
1. Start system in well-lit indoor environment
2. Walk at normal pace
3. System provides alerts for furniture, doors, and people
4. Surface alerts help identify floor changes

### Outdoor Navigation
1. Ensure good lighting conditions
2. System adapts to changing light levels
3. Enhanced alerts for vehicles and street obstacles
4. Surface detection helps identify crosswalks vs roads

### Public Transport
1. Use in stations and on platforms
2. Alerts for moving people and vehicles
3. Surface detection identifies platform edges
4. Proximity tracking prevents collisions

## Safety Guidelines

### Important Safety Notes
- **Always maintain situational awareness**
- **Do not rely solely on the system**
- **Test in controlled environments first**
- **Keep emergency contacts accessible**
- **Report any system failures immediately**

### Emergency Procedures
1. **System Failure**: Stop movement immediately
2. **False Alerts**: Continue with caution, verify visually
3. **Hardware Issues**: Switch to backup navigation method
4. **Medical Emergency**: Call emergency services

## Performance Monitoring

### Log Files
- `navigation_log.txt`: Real-time event logging
- `diagnostics.csv`: Performance metrics
- `lighting_test_report.txt`: Lighting condition analysis

### Monitoring Commands
```bash
# View recent alerts
tail -f navigation_log.txt

# Check system performance
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, RAM: {psutil.virtual_memory().percent}%')"

# Test detection latency
python test_combined_pipeline.py --benchmark
```

## Customization

### Alert Customization
Modify `hardware_interface.py` to change:
- Alert messages and languages
- Vibration patterns and durations
- Audio voice settings

### Model Customization
- Train custom object detection models
- Add new surface texture classes
- Adjust detection thresholds

### Hardware Integration
- Add new sensor types
- Integrate with smart canes
- Connect to wearable devices

## Troubleshooting

### Common Issues

#### No Camera Feed
```
Error: Camera not accessible
```
**Solution**: Check camera permissions and connections

#### Audio Not Working
```
Error: Audio device not found
```
**Solution**: Install audio drivers and test speakers

#### Slow Performance
```
Warning: Detection latency > 500ms
```
**Solution**: Close other applications, use GPU if available

#### False Positives
```
Alert: Person detected (confidence: 0.3)
```
**Solution**: Adjust confidence threshold in configuration

## Support

### Getting Help
1. Check the [troubleshooting guide](troubleshooting.md)
2. Review [field testing protocols](field-testing.md)
3. Open an [issue](https://github.com/Demonking09/Stage2_Advance_navigation_System/issues) on GitHub
4. Join the [community discussions](https://github.com/Demonking09/Stage2_Advance_navigation_System/discussions)

### System Information
When reporting issues, include:
- Operating system and version
- Python version
- Hardware specifications
- Error messages and logs
- Steps to reproduce the issue