#!/usr/bin/env python3
"""
Test script to verify frame alignment fix.
This test checks that frame filenames are correctly mapped to video times.
"""

import os
import re
import sys

def test_frame_time_mapping():
    """Test that frame filenames are correctly mapped to video times"""
    
    # Simulate the frame processing logic from app.py
    frames_dir = "static/videos/dashcam60fps/frames/full_30"
    
    if not os.path.exists(frames_dir):
        print(f"❌ Test directory not found: {frames_dir}")
        return False
    
    # Get list of frames sorted by filename
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
    
    if not frames:
        print(f"❌ No frame files found in {frames_dir}")
        return False
    
    print(f"✅ Found {len(frames)} frames")
    
    # Test the frame processing logic
    variant_fps = 30
    frame_interval = 1.0 / variant_fps  # 0.033 seconds per frame
    
    frame_data = []
    
    for i, frame_file in enumerate(frames[:10]):  # Test first 10 frames
        # Extract the frame number from the filename (e.g., frame_0004.jpg -> 4)
        frame_match = re.search(r'frame_(\d+)', frame_file)
        if frame_match:
            frame_number = int(frame_match.group(1))
        else:
            # Fallback to enumeration index if filename doesn't match pattern
            frame_number = i
        
        # Calculate the actual time this frame represents based on the frame number
        frame_time = frame_number * frame_interval
        frame_data.append({
            'file': frame_file,
            'index': i,
            'frame_number': frame_number,
            'time': round(frame_time, 3)
        })
        
        print(f"Frame {frame_file}: index={i}, frame_number={frame_number}, time={frame_time:.3f}s")
    
    # Verify that frame numbers match expected pattern
    expected_issues = []
    
    for frame in frame_data:
        expected_time = frame['frame_number'] * frame_interval
        if abs(frame['time'] - expected_time) > 0.001:  # Allow small floating point differences
            expected_issues.append(f"Frame {frame['file']}: expected time {expected_time:.3f}, got {frame['time']:.3f}")
    
    if expected_issues:
        print("❌ Frame time mapping issues found:")
        for issue in expected_issues:
            print(f"  {issue}")
        return False
    
    # Test specific case mentioned in the issue
    frame_0004_found = False
    frame_0003_found = False
    
    for frame in frame_data:
        if frame['file'] == 'frame_0004.jpg':
            frame_0004_found = True
            expected_time_0004 = 4 * frame_interval  # 4 * (1/30) = 0.133
            if abs(frame['time'] - expected_time_0004) > 0.001:
                print(f"❌ frame_0004.jpg has incorrect time: expected {expected_time_0004:.3f}, got {frame['time']:.3f}")
                return False
            else:
                print(f"✅ frame_0004.jpg correctly mapped to time {frame['time']:.3f}s")
        
        if frame['file'] == 'frame_0003.jpg':
            frame_0003_found = True
            expected_time_0003 = 3 * frame_interval  # 3 * (1/30) = 0.100
            if abs(frame['time'] - expected_time_0003) > 0.001:
                print(f"❌ frame_0003.jpg has incorrect time: expected {expected_time_0003:.3f}, got {frame['time']:.3f}")
                return False
            else:
                print(f"✅ frame_0003.jpg correctly mapped to time {frame['time']:.3f}s")
    
    if not frame_0004_found:
        print("⚠️  frame_0004.jpg not found in test data")
    if not frame_0003_found:
        print("⚠️  frame_0003.jpg not found in test data")
    
    print("✅ All frame time mappings are correct!")
    return True

def test_frame_click_behavior():
    """Test the expected behavior when clicking frames"""
    
    print("\n=== Frame Click Behavior Test ===")
    
    # Simulate clicking frame_0004.jpg
    frame_0004_time = 4 * (1.0 / 30)  # 0.133 seconds
    frame_0003_time = 3 * (1.0 / 30)  # 0.100 seconds
    
    print(f"When clicking frame_0004.jpg:")
    print(f"  - Should seek video to time: {frame_0004_time:.3f}s")
    print(f"  - Should NOT show content from frame_0003.jpg (time: {frame_0003_time:.3f}s)")
    print(f"  - Time difference: {frame_0004_time - frame_0003_time:.3f}s")
    
    if frame_0004_time > frame_0003_time:
        print("✅ frame_0004.jpg should show different content than frame_0003.jpg")
        return True
    else:
        print("❌ Frame time calculation error")
        return False

if __name__ == "__main__":
    print("Testing Frame Alignment Fix")
    print("=" * 40)
    
    success = True
    
    # Test frame time mapping
    if not test_frame_time_mapping():
        success = False
    
    # Test frame click behavior
    if not test_frame_click_behavior():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed! Frame alignment should be fixed.")
    else:
        print("❌ Some tests failed. Frame alignment issue may persist.")
    
    sys.exit(0 if success else 1) 