#!/usr/bin/env python3
"""
Generate a metadata index file by scanning the outputs directory.
This is used by the frontend to display a list of available documents.
"""

import json
import os
from pathlib import Path

def generate_metadata_index():
    """
    Generate a metadata index file by scanning the outputs directory.
    """
    output_dir = Path("../outputs")
    metadata_files = list(output_dir.glob("*_metadata.json"))
    
    metadata_list = []
    
    for metadata_file in metadata_files:
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                metadata_list.append(metadata)
        except Exception as e:
            print(f"Error reading {metadata_file}: {e}")
    
    # Sort by filename
    metadata_list.sort(key=lambda x: x.get("filename", ""))
    
    # Write index file
    index_path = output_dir / "metadata_index.json"
    with open(index_path, "w") as f:
        json.dump(metadata_list, f, indent=2)
    
    print(f"Generated metadata index with {len(metadata_list)} entries.")

if __name__ == "__main__":
    generate_metadata_index() 