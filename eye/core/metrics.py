"""Metrics collection for Eye"""
from typing import Dict, Any
from datetime import datetime
import time

# MetricsCollector collects and tracks metrics
class MetricsCollector:
    """Collects and tracks metrics"""

    # Initialize the metrics collector
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "captures_total": 0,
            "captures_success": 0,
            "captures_failed": 0,
            "bytes_uploaded": 0,
            "start_time": time.time()
        }
    
    # Record a capture attempt
    def record_capture(self, success: bool = True, size_bytes: int = 0):
        """Record a capture attempt"""
        self.metrics["captures_total"] += 1
        if success:
            self.metrics["captures_success"] += 1
            self.metrics["bytes_uploaded"] += size_bytes
        else:
            self.metrics["captures_failed"] += 1
    
    # Get current metrics
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = time.time() - self.metrics["start_time"]
        
        return {
            **self.metrics,
            "uptime_seconds": uptime,
            "success_rate": self.metrics["captures_success"] / max(self.metrics["captures_total"], 1),
            "avg_upload_rate": self.metrics["captures_success"] / max(uptime, 1)
        }
    
    # Reset all metrics
    def reset(self):
        """Reset all metrics"""
        self.metrics = {
            "captures_total": 0,
            "captures_success": 0,
            "captures_failed": 0,
            "bytes_uploaded": 0,
            "start_time": time.time()
        }