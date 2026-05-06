"""
Unit tests for proximity tracker module.
Tests object tracking, approach detection, and alert generation.
"""

import numpy as np
from proximity_tracker import ObjectTracker, ProximityAlert, format_alert_message


def test_tracker_basic():
    """Test basic object tracking across frames."""
    tracker = ObjectTracker(max_history=10, distance_threshold=100)
    
    # Frame 1: Person at center
    detections_1 = [
        (np.array([100, 100, 200, 300]), "person", 0.9),
    ]
    tracked_1 = tracker.associate_detections(detections_1)
    assert len(tracked_1) == 1
    obj_id_1, _, label_1, _ = tracked_1[0]
    print(f"✅ Frame 1: Detected person with ID {obj_id_1}")
    
    # Frame 2: Same person moved right (center to x=150)
    detections_2 = [
        (np.array([150, 100, 250, 300]), "person", 0.92),
    ]
    tracked_2 = tracker.associate_detections(detections_2)
    assert len(tracked_2) == 1
    obj_id_2, _, label_2, _ = tracked_2[0]
    assert obj_id_2 == obj_id_1  # Should be same object
    print(f"✅ Frame 2: Same person tracked (ID {obj_id_2})")
    
    # Estimate approach
    is_approaching, urgency, direction = tracker.estimate_approach(obj_id_1)
    distance_cat = tracker.estimate_distance_category(obj_id_1)
    print(f"✅ Approach analysis: is_approaching={is_approaching}, urgency={urgency:.2f}, distance={distance_cat}")


def test_proximity_growing():
    """Test detecting a person getting closer (larger bounding box)."""
    tracker = ObjectTracker(max_history=10, distance_threshold=150)
    
    # Simulate person getting progressively closer
    box_sizes = [
        (np.array([200, 150, 300, 350]), 0.85),  # Far
        (np.array([180, 130, 320, 370]), 0.88),  # Getting closer
        (np.array([150, 100, 350, 400]), 0.91),  # Very close
    ]
    
    for i, (box, conf) in enumerate(box_sizes):
        detections = [(box, "person", conf)]
        tracked = tracker.associate_detections(detections)
        
        if i > 0:
            obj_id = tracked[0][0]
            is_approaching, urgency, _ = tracker.estimate_approach(obj_id)
            distance_cat = tracker.estimate_distance_category(obj_id)
            print(f"Frame {i+1}: distance={distance_cat}, approaching={is_approaching}, urgency={urgency:.2f}")
            
            if i == len(box_sizes) - 1:
                assert is_approaching, "Person should be detected as approaching"
                assert distance_cat == "very_close", "Person should be very close"
                print("✅ Approach detection works correctly")


def test_alert_generation():
    """Test alert message generation."""
    proximity_alert = ProximityAlert()
    
    # Test critical alert
    severity, msg = proximity_alert.generate_alert("person", "center", "very_close", True, 0.9)
    assert severity == "critical"
    print(f"✅ Critical alert: {msg}")
    
    # Test warning alert
    severity, msg = proximity_alert.generate_alert("person", "left", "close", True, 0.6)
    assert severity == "warning"
    print(f"✅ Warning alert: {msg}")
    
    # Test caution alert
    severity, msg = proximity_alert.generate_alert("chair", "right", "moderate", False, 0.0)
    assert severity == "info"
    print(f"✅ Info alert: {msg}")


def test_alert_cooldown():
    """Test that alerts respect cooldown periods."""
    proximity_alert = ProximityAlert(cooldown_by_severity={"critical": 0.1, "warning": 0.2})
    
    obj_id = 1
    
    # First alert should be emitted
    assert proximity_alert.should_alert(obj_id, "critical")
    print("✅ First critical alert allowed")
    
    # Immediate second alert should be blocked
    assert not proximity_alert.should_alert(obj_id, "critical")
    print("✅ Second immediate critical alert blocked (cooldown active)")
    
    # Different severity should be allowed
    assert proximity_alert.should_alert(obj_id, "warning")
    print("✅ Different severity alert allowed")


def test_format_alert():
    """Test alert formatting."""
    msg = format_alert_message("critical", "Person very close ahead")
    assert "\u26a0" in msg or "[CRITICAL]" in msg
    print(f"✅ Formatted critical: {msg}")
    
    msg = format_alert_message("warning", "Obstacle approaching")
    assert "[WARNING]" in msg
    print(f"✅ Formatted warning: {msg}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PROXIMITY TRACKER UNIT TESTS")
    print("="*60 + "\n")
    
    print("Test 1: Basic Tracking")
    test_tracker_basic()
    
    print("\nTest 2: Proximity Growing (Approach Detection)")
    test_proximity_growing()
    
    print("\nTest 3: Alert Generation")
    test_alert_generation()
    
    print("\nTest 4: Alert Cooldown")
    test_alert_cooldown()
    
    print("\nTest 5: Alert Formatting")
    test_format_alert()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")
