"""Dataset export functionality"""
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# DatasetExporter exports captured frames as datasets.
class DatasetExporter:
    """Exports captured frames as datasets"""
    
    # Initialize the DatasetExporter
    def __init__(self):
        self.frames: List[Dict[str, Any]] = []
    
    # Add a frame to the dataset
    def add_frame(self, frame_data: bytes, frame_id: int, metadata: Dict[str, Any]):
        """Add a frame to the dataset"""
        self.frames.append({
            "frame_id": frame_id,
            "timestamp": datetime.now().isoformat(),
            "size_bytes": len(frame_data),
            "metadata": metadata
        })
    
    # Export dataset as JSON
    def export_json(self, output_path: Path):
        """Export as JSON"""
        with open(output_path, 'w') as f:
            json.dump(self.frames, f, indent=2)
    
    # Export dataset as JSONL (one frame per line)
    def export_jsonl(self, output_path: Path):
        """Export as JSONL (one frame per line)"""
        with open(output_path, 'w') as f:
            for frame in self.frames:
                f.write(json.dumps(frame) + '\n')
    
    # Export dataset as CSV
    def export_csv(self, output_path: Path):
        """Export metadata as CSV"""
        import csv
        
        if not self.frames:
            return
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.frames[0].keys())
            writer.writeheader()
            writer.writerows(self.frames)
    
    # Clear all frames from the dataset
    def clear(self):
        """Clear all frames"""
        self.frames = []