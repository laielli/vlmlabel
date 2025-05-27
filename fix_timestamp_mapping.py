#!/usr/bin/env python3
"""
Fix the timestamp mapping by sorting frames by their actual timestamps.
This creates a proper sequential frame mapping for video seeking.
"""

import json
import os

def fix_timestamp_mapping():
    """Fix the timestamp mapping to be in chronological order"""
    
    timestamp_file = "static/videos/dashcam60fps__full_30/full_30_exact_timestamps.json"
    
    if not os.path.exists(timestamp_file):
        print(f"❌ Timestamp file not found: {timestamp_file}")
        return False
    
    # Load the original timestamps
    with open(timestamp_file, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Original data: {data['frame_count']} frames")
    
    # Extract and sort frames by timestamp
    frames = data['frames']
    sorted_frames = sorted(frames, key=lambda x: x['timestamp'])
    
    print(f"🔄 Sorting frames by timestamp...")
    
    # Create new sequential mapping
    fixed_frames = []
    for i, frame in enumerate(sorted_frames):
        fixed_frame = {
            'frame_number': i,  # Sequential frame number
            'timestamp': frame['timestamp'],  # Original timestamp
            'filename': f'frame_{i:04d}.jpg',  # Sequential filename
            'original_frame_number': frame['frame_number']  # Keep track of original
        }
        fixed_frames.append(fixed_frame)
    
    # Create fixed data
    fixed_data = {
        'frame_count': len(fixed_frames),
        'frames': fixed_frames,
        'note': 'Frames sorted by timestamp for sequential access'
    }
    
    # Save fixed mapping
    fixed_file = "static/videos/dashcam60fps__full_30/full_30_exact_timestamps_fixed.json"
    with open(fixed_file, 'w') as f:
        json.dump(fixed_data, f, indent=2)
    
    print(f"✅ Fixed timestamp mapping saved to: {fixed_file}")
    
    # Show comparison
    print(f"\n📋 COMPARISON:")
    print(f"Original frame order vs Fixed frame order:")
    print(f"{'Frame':<8} {'Original TS':<12} {'Fixed TS':<12} {'Difference':<12}")
    print("-" * 50)
    
    for i in range(min(10, len(fixed_frames))):
        original_ts = data['frames'][i]['timestamp']
        fixed_ts = fixed_frames[i]['timestamp']
        diff = abs(original_ts - fixed_ts)
        print(f"{i:<8} {original_ts:<12.6f} {fixed_ts:<12.6f} {diff:<12.6f}")
    
    # Show the critical frames 3 and 4
    print(f"\n🎯 CRITICAL FRAMES (3 and 4):")
    print(f"Frame 3: {fixed_frames[3]['timestamp']:.6f}s")
    print(f"Frame 4: {fixed_frames[4]['timestamp']:.6f}s")
    print(f"Difference: {fixed_frames[4]['timestamp'] - fixed_frames[3]['timestamp']:.6f}s")
    
    return True

def create_app_update():
    """Create the app.py update to use fixed timestamps"""
    
    print(f"\n📝 APP.PY UPDATE CODE:")
    print("=" * 60)
    print("""
# Add this function to app.py:

def load_frame_timestamps(video_id, variant):
    \"\"\"Load exact frame timestamps from JSON file\"\"\"
    timestamp_file = f"static/videos/{video_id}/{variant}_timestamps_fixed.json"
    
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as f:
            data = json.load(f)
        
        # Create lookup dict: frame_number -> timestamp
        timestamp_lookup = {}
        for frame_info in data['frames']:
            timestamp_lookup[frame_info['frame_number']] = frame_info['timestamp']
        
        return timestamp_lookup
    
    return None

# In the video route, replace the frame processing section:

# Find the timestamp lookup for this variant
timestamp_lookup = load_frame_timestamps(video_id, variant)

for i, frame_file in enumerate(frame_files):
    match = re.search(r'frame_(\\d+)', frame_file)
    if match:
        frame_number = int(match.group(1))
        
        # Use exact timestamp if available, otherwise calculate
        if timestamp_lookup and frame_number in timestamp_lookup:
            frame_time = timestamp_lookup[frame_number]
        else:
            frame_time = frame_number * frame_interval  # fallback
        
        frames.append({
            'file': frame_file,
            'time': frame_time,
            'frame_number': frame_number
        })
""")

if __name__ == "__main__":
    print("Timestamp Mapping Fix")
    print("=" * 60)
    
    success = fix_timestamp_mapping()
    
    if success:
        create_app_update()
        print(f"\n🎯 NEXT STEPS:")
        print("1. Update app.py with the code above")
        print("2. Test with the fixed timestamps")
        print("3. Compare frame alignment accuracy")
    else:
        print(f"\n❌ Failed to fix timestamp mapping") 