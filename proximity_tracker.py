"""
Proximity and Movement Tracker for Assistive Navigation
========================================================
Detects approaching obstacles/people and estimates distance/urgency.
Provides enhanced warning logic for physically impaired users.
"""

import numpy as np
from collections import deque, defaultdict
import time


class ObjectTracker:
    """Track objects across frames to detect movement and proximity."""
    
    def __init__(self, max_history=15, distance_threshold=50):
        """
        Args:
            max_history: Number of frames to keep for motion analysis
            distance_threshold: Min pixel distance to consider as same object
        """
        self.max_history = max_history
        self.distance_threshold = distance_threshold
        self.tracked_objects = {}  # object_id -> history deque
        self.next_id = 0
        self.frame_count = 0
    
    def get_box_center(self, box):
        """Extract center point from YOLO bounding box [x1, y1, x2, y2]."""
        return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    
    def get_box_area(self, box):
        """Calculate bounding box area as proxy for distance."""
        return (box[2] - box[0]) * (box[3] - box[1])
    
    def associate_detections(self, detections):
        """
        Match current detections to tracked objects.
        Returns: list of (object_id, detection, label, confidence)
        """
        self.frame_count += 1
        matched = []
        unmatched_detections = list(range(len(detections)))
        
        # Try to match existing tracked objects
        for obj_id, history in list(self.tracked_objects.items()):
            if not history:
                continue
            
            last_center = history[-1][0]
            best_dist = float('inf')
            best_idx = -1
            
            for det_idx, (box, label, conf) in enumerate(detections):
                if det_idx not in unmatched_detections:
                    continue
                
                center = self.get_box_center(box)
                dist = np.sqrt((center[0] - last_center[0])**2 + 
                              (center[1] - last_center[1])**2)
                
                if dist < best_dist:
                    best_dist = dist
                    best_idx = det_idx
            
            # Match if within threshold
            if best_idx >= 0 and best_dist < self.distance_threshold:
                box, label, conf = detections[best_idx]
                history.append((self.get_box_center(box), self.get_box_area(box), label, conf))
                matched.append((obj_id, (box, label, conf), label, conf))
                unmatched_detections.remove(best_idx)
        
        # Create new trackers for unmatched detections
        for det_idx in unmatched_detections:
            box, label, conf = detections[det_idx]
            obj_id = self.next_id
            self.next_id += 1
            history = deque(maxlen=self.max_history)
            history.append((self.get_box_center(box), self.get_box_area(box), label, conf))
            self.tracked_objects[obj_id] = history
            matched.append((obj_id, (box, label, conf), label, conf))
        
        return matched
    
    def estimate_approach(self, obj_id):
        """
        Estimate if object is approaching (getting larger/closer).
        Returns: (is_approaching, urgency_score, direction_change)
            urgency_score: 0.0 (stationary) to 1.0 (fast approach)
            direction_change: -1 (moving away), 0 (static), +1 (approaching)
        """
        if obj_id not in self.tracked_objects or len(self.tracked_objects[obj_id]) < 3:
            return False, 0.0, 0
        
        history = self.tracked_objects[obj_id]
        areas = [h[1] for h in history]
        
        # Recent area trend
        recent_areas = areas[-5:]
        if len(recent_areas) < 2:
            return False, 0.0, 0
        
        area_growth = (recent_areas[-1] - recent_areas[0]) / (recent_areas[0] + 1e-6)
        
        # Categorize movement
        if area_growth > 0.15:  # Growing significantly
            direction = 1
            urgency = min(area_growth, 1.0)
        elif area_growth < -0.15:  # Shrinking
            direction = -1
            urgency = 0.0
        else:  # Relatively static
            direction = 0
            urgency = 0.0
        
        is_approaching = direction > 0 and urgency > 0.1
        
        return is_approaching, urgency, direction
    
    def estimate_distance_category(self, obj_id):
        """
        Estimate relative distance based on bounding box size.
        Returns: 'very_close' (0-0.3m est), 'close' (0.3-1m), 'moderate' (1-3m), 'far'
        """
        if obj_id not in self.tracked_objects or len(self.tracked_objects[obj_id]) == 0:
            return "unknown"
        
        history = self.tracked_objects[obj_id]
        current_area = history[-1][1]
        
        # Heuristic: assume person bounding box grows from ~500 pixels at 3m to ~5000 at 0.3m
        if current_area > 4000:
            return "very_close"
        elif current_area > 1500:
            return "close"
        elif current_area > 400:
            return "moderate"
        else:
            return "far"


class ProximityAlert:
    """Generate urgency-based alerts based on approach detection."""
    
    def __init__(self, cooldown_by_severity=None):
        if cooldown_by_severity is None:
            cooldown_by_severity = {
                "critical": 0.5,    # Very close, approaching
                "warning": 1.5,     # Close, approaching
                "caution": 3.0,     # Moderate distance
            }
        self.cooldown_by_severity = cooldown_by_severity
        self.last_alert_time = defaultdict(lambda: {})
    
    def should_alert(self, obj_id, severity):
        """Check if enough time has passed since last alert of this severity."""
        now = time.time()
        if severity not in self.last_alert_time[obj_id]:
            self.last_alert_time[obj_id][severity] = 0
        
        cooldown = self.cooldown_by_severity.get(severity, 2.0)
        elapsed = now - self.last_alert_time[obj_id][severity]
        
        if elapsed >= cooldown:
            self.last_alert_time[obj_id][severity] = now
            return True
        return False
    
    def generate_alert(self, label, direction, distance_cat, is_approaching, urgency):
        """
        Generate spoken alert text based on approach state.
        Returns: (severity, message)
        """
        if label == "person":
            if is_approaching and distance_cat == "very_close":
                return ("critical", 
                       f"Danger: Person very close ahead at {direction}. Stop or step back immediately.")
            elif is_approaching and distance_cat == "close":
                return ("warning", 
                       f"Warning: Person approaching from {direction}.")
            elif is_approaching and distance_cat == "moderate":
                return ("caution", 
                       f"Person detected {direction}, getting closer.")
            elif distance_cat == "very_close":
                return ("critical", 
                       f"Danger: Person directly ahead at {direction}. Move carefully.")
            elif distance_cat == "close":
                return ("warning", 
                       f"Person nearby at {direction}.")
            else:
                return ("info", f"Person detected {direction}.")
        else:
            # Non-person obstacle
            if is_approaching and distance_cat == "very_close":
                return ("critical", 
                       f"Danger: {label} very close ahead at {direction}. Caution.")
            elif is_approaching and distance_cat == "close":
                return ("warning", 
                       f"Warning: {label} at {direction}, getting closer.")
            elif distance_cat == "very_close":
                return ("critical", 
                       f"Danger: {label} directly ahead at {direction}.")
            elif distance_cat == "close":
                return ("warning", 
                       f"Obstacle {label} detected {direction}.")
            else:
                return ("info", f"Object {label} detected {direction}.")


def format_alert_message(severity, message):
    """Format alert with severity indicator."""
    prefix_map = {
        "critical": "\u26a0\ufe0f [CRITICAL]",
        "warning": "\u26d4 [WARNING]",
        "caution": "\u26a0 [CAUTION]",
        "info": "ℹ [INFO]",
    }
    prefix = prefix_map.get(severity, "[ALERT]")
    return f"{prefix} {message}"
