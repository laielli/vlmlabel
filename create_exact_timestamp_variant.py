#!/usr/bin/env python3
"""
Create a new variant that uses exact timestamps by copying existing frames
and creating the proper timestamp mapping.
"""

import os
import shutil
import json

def create_exact_timestamp_variant():
    """Create the full_30_exact variant by copying existing frames"""
    
    # Source and destination paths
    source_frames = "static/videos/dashcam60fps/frames/full_30"
    dest_frames = "static/videos/dashcam60fps/frames/full_30_exact"
    timestamp_file = "static/videos/dashcam60fps__full_30/full_30_exact_timestamps_fixed.json"
    dest_timestamp_file = "static/videos/dashcam60fps/full_30_exact_timestamps_fixed.json"
    
    print("🔄 Creating exact timestamp variant...")
    
    # Check if source exists
    if not os.path.exists(source_frames):
        print(f"❌ Source frames not found: {source_frames}")
        return False
    
    if not os.path.exists(timestamp_file):
        print(f"❌ Timestamp file not found: {timestamp_file}")
        return False
    
    # Create destination directory
    os.makedirs(dest_frames, exist_ok=True)
    
    # Copy all frame files
    print(f"📁 Copying frames from {source_frames} to {dest_frames}")
    
    frame_files = [f for f in os.listdir(source_frames) if f.endswith('.jpg')]
    for frame_file in frame_files:
        src_path = os.path.join(source_frames, frame_file)
        dest_path = os.path.join(dest_frames, frame_file)
        shutil.copy2(src_path, dest_path)
    
    print(f"✅ Copied {len(frame_files)} frame files")
    
    # Copy timestamp file to the correct location
    print(f"📄 Copying timestamp file...")
    shutil.copy2(timestamp_file, dest_timestamp_file)
    
    print(f"✅ Created exact timestamp variant: full_30_exact")
    print(f"Frames: {dest_frames}")
    print(f"Timestamps: {dest_timestamp_file}")
    
    return True

def add_variant_to_config():
    """Add the new variant to the video configuration"""
    
    print("⚙️ Adding variant to configuration...")
    
    # This would normally update config.yaml, but for now just show what needs to be done
    print("""
To use the exact timestamp variant, you can:

1. Access it via URL: http://localhost:5001/video/dashcam60fps?variant=full_30_exact

2. Or add it to config.yaml:
   videos:
     - id: dashcam60fps
       variants:
         - name: full_30_exact
           fps: 30
           description: "Full video at 30fps with exact timestamps"
""")

if __name__ == "__main__":
    print("Exact Timestamp Variant Creator")
    print("=" * 60)
    
    success = create_exact_timestamp_variant()
    
    if success:
        add_variant_to_config()
        print(f"\n🎯 TESTING:")
        print("1. Start the Flask app: python app.py")
        print("2. Go to: http://localhost:5001/video/dashcam60fps?variant=full_30_exact")
        print("3. Test frame alignment with exact timestamps")
        print("4. Compare with the original full_30 variant")
    else:
        print(f"\n❌ Failed to create exact timestamp variant") 