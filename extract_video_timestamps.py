#!/usr/bin/env python3
"""
Extract actual frame timestamps from video files using ffprobe.
This ensures we use the exact same timestamps that the video player uses.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path

def extract_frame_timestamps(video_path, output_fps=None):
    """
    Extract actual frame timestamps from a video file.
    
    Args:
        video_path: Path to the video file
        output_fps: If specified, extract frames at this FPS rate
    
    Returns:
        List of (frame_number, timestamp) tuples
    """
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
    
    print(f"🎬 Extracting timestamps from: {video_path}")
    
    try:
        # First, get video info
        info_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', '-show_streams', video_path
        ]
        
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to get video info: {result.stderr}")
            return None
        
        info = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            print("❌ No video stream found")
            return None
        
        # Get video properties
        duration = float(video_stream.get('duration', 0))
        fps_str = video_stream.get('r_frame_rate', '30/1')
        fps_parts = fps_str.split('/')
        native_fps = float(fps_parts[0]) / float(fps_parts[1])
        
        print(f"Video duration: {duration:.3f}s")
        print(f"Native FPS: {native_fps:.3f}")
        
        # Determine extraction FPS
        extraction_fps = output_fps if output_fps else native_fps
        print(f"Extraction FPS: {extraction_fps:.3f}")
        
        # Extract frame timestamps using ffprobe
        # This gets the actual presentation timestamps (PTS) of frames
        timestamp_cmd = [
            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
            '-show_entries', 'packet=pts_time',
            '-of', 'csv=p=0', video_path
        ]
        
        result = subprocess.run(timestamp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to extract timestamps: {result.stderr}")
            return None
        
        # Parse timestamps
        all_timestamps = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    timestamp = float(line.strip())
                    all_timestamps.append(timestamp)
                except ValueError:
                    continue
        
        print(f"Found {len(all_timestamps)} total frames in video")
        
        # If we want a specific FPS, subsample the timestamps
        if output_fps and output_fps != native_fps:
            frame_interval = 1.0 / extraction_fps
            selected_timestamps = []
            
            for i, target_time in enumerate([i * frame_interval for i in range(int(duration * extraction_fps))]):
                if target_time > duration:
                    break
                
                # Find closest actual timestamp
                closest_timestamp = min(all_timestamps, key=lambda x: abs(x - target_time))
                selected_timestamps.append((i, closest_timestamp))
            
            print(f"Selected {len(selected_timestamps)} frames at {extraction_fps} FPS")
            return selected_timestamps
        else:
            # Use all frames
            return [(i, ts) for i, ts in enumerate(all_timestamps)]
    
    except Exception as e:
        print(f"❌ Error extracting timestamps: {e}")
        return None

def save_timestamp_mapping(timestamps, output_file):
    """Save timestamp mapping to a JSON file"""
    
    timestamp_data = {
        'frame_count': len(timestamps),
        'frames': [
            {
                'frame_number': frame_num,
                'timestamp': timestamp,
                'filename': f'frame_{frame_num:04d}.jpg'
            }
            for frame_num, timestamp in timestamps
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(timestamp_data, f, indent=2)
    
    print(f"✅ Saved timestamp mapping to: {output_file}")
    return timestamp_data

def extract_frames_with_timestamps(video_path, output_dir, timestamps):
    """Extract frames at the exact timestamps"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🎞️ Extracting {len(timestamps)} frames to: {output_dir}")
    
    for frame_num, timestamp in timestamps:
        output_file = os.path.join(output_dir, f'frame_{frame_num:04d}.jpg')
        
        # Extract frame at exact timestamp
        cmd = [
            'ffmpeg', '-y', '-v', 'quiet',
            '-ss', str(timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',  # High quality
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(f"⚠️ Failed to extract frame {frame_num} at {timestamp}s")
        
        # Progress indicator
        if (frame_num + 1) % 50 == 0:
            print(f"Extracted {frame_num + 1}/{len(timestamps)} frames...")
    
    print(f"✅ Frame extraction completed")

def process_video_with_exact_timestamps(video_path, variant_name, fps):
    """Process a video to extract frames with exact timestamps"""
    
    print(f"\n🚀 Processing video with exact timestamps")
    print(f"Video: {video_path}")
    print(f"Variant: {variant_name}")
    print(f"Target FPS: {fps}")
    print("=" * 60)
    
    # Extract timestamps
    timestamps = extract_frame_timestamps(video_path, fps)
    if not timestamps:
        return False
    
    # Create output directories
    video_name = Path(video_path).stem
    base_dir = f"static/videos/{video_name}"
    frames_dir = f"{base_dir}/frames/{variant_name}"
    
    # Ensure base directory exists
    os.makedirs(base_dir, exist_ok=True)
    
    # Save timestamp mapping
    timestamp_file = f"{base_dir}/{variant_name}_timestamps.json"
    timestamp_data = save_timestamp_mapping(timestamps, timestamp_file)
    
    # Extract frames
    extract_frames_with_timestamps(video_path, frames_dir, timestamps)
    
    print(f"\n✅ Processing completed!")
    print(f"Frames: {frames_dir}")
    print(f"Timestamps: {timestamp_file}")
    
    # Show first few timestamps for verification
    print(f"\nFirst 10 frame timestamps:")
    for i, (frame_num, timestamp) in enumerate(timestamps[:10]):
        print(f"  frame_{frame_num:04d}.jpg: {timestamp:.6f}s")
    
    return True

def update_app_to_use_timestamps():
    """Generate code to update app.py to use the timestamp files"""
    
    print(f"\n📝 CODE UPDATE NEEDED")
    print("=" * 60)
    print("To use exact timestamps in app.py, add this function:")
    print()
    print("""
def load_frame_timestamps(video_id, variant):
    \"\"\"Load exact frame timestamps from JSON file\"\"\"
    timestamp_file = f"static/videos/{video_id}/{variant}_timestamps.json"
    
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as f:
            data = json.load(f)
        
        # Create lookup dict: frame_number -> timestamp
        timestamp_lookup = {}
        for frame_info in data['frames']:
            timestamp_lookup[frame_info['frame_number']] = frame_info['timestamp']
        
        return timestamp_lookup
    
    return None

# In the video route, replace frame time calculation:
# OLD: frame_time = frame_number * frame_interval
# NEW: 
timestamp_lookup = load_frame_timestamps(video_id, variant)
if timestamp_lookup and frame_number in timestamp_lookup:
    frame_time = timestamp_lookup[frame_number]
else:
    frame_time = frame_number * frame_interval  # fallback
""")

if __name__ == "__main__":
    # Process the dashcam video
    video_path = "static/videos/dashcam60fps/dashcam60fps__full_30.mp4"
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        print("Usage: python extract_video_timestamps.py [video_path]")
        sys.exit(1)
    
    # Extract at 30 FPS with exact timestamps
    success = process_video_with_exact_timestamps(video_path, "full_30_exact", 30)
    
    if success:
        update_app_to_use_timestamps()
        print(f"\n🎯 NEXT STEPS:")
        print("1. Update app.py to use the timestamp lookup")
        print("2. Test frame alignment with exact timestamps")
        print("3. Compare with previous mathematical calculation")
    else:
        print(f"\n❌ Failed to process video")
        sys.exit(1) 