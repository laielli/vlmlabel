#!/usr/bin/env python3
"""
Test script to verify FPS variants are working correctly

This script checks:
- Video duration preservation
- Correct frame rates
- Proper frame extraction counts
- Video playback timing
"""

import os
import subprocess
import cv2

def get_video_properties(video_path):
    """Get video properties using ffprobe and cv2"""
    # Use ffprobe for precise measurements
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,duration",
        "-of", "csv=p=0", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return None
    
    parts = result.stdout.strip().split(',')
    fps_parts = parts[0].split('/')
    fps = float(fps_parts[0]) / float(fps_parts[1])
    duration = float(parts[1])
    
    # Also get frame count using cv2
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    return {
        'fps': fps,
        'duration': duration,
        'frame_count': frame_count
    }

def count_extracted_frames(frames_dir):
    """Count extracted frame files"""
    if not os.path.exists(frames_dir):
        return 0
    return len([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])

def test_fps_variants():
    """Test all FPS variants"""
    video_id = "dashcam60fps"
    base_dir = f"static/videos/{video_id}"
    
    # Define expected variants
    variants = [
        ("full_60", 60),
        ("full_30", 30), 
        ("full_10", 10),
        ("full_5", 5),
        ("full_2", 2),
        ("full_1", 1)
    ]
    
    print(f"Testing FPS variants for {video_id}")
    print("=" * 60)
    
    # Get source video properties for comparison
    source_video = f"input_videos/{video_id}.mp4"
    source_props = get_video_properties(source_video)
    print(f"Source video: {source_props['fps']:.1f} FPS, {source_props['duration']:.2f}s, {source_props['frame_count']} frames")
    print()
    
    all_passed = True
    
    for variant_key, expected_fps in variants:
        variant_path = os.path.join(base_dir, f"{video_id}__{variant_key}.mp4")
        frames_dir = os.path.join(base_dir, "frames", variant_key)
        
        print(f"Testing {variant_key} (expected {expected_fps} FPS):")
        
        if not os.path.exists(variant_path):
            print(f"  ✗ Video file not found: {variant_path}")
            all_passed = False
            continue
        
        # Get video properties
        props = get_video_properties(variant_path)
        if not props:
            print(f"  ✗ Could not read video properties")
            all_passed = False
            continue
        
        # Test FPS
        fps_ok = abs(props['fps'] - expected_fps) < 0.1
        fps_status = "✓" if fps_ok else "✗"
        print(f"  {fps_status} FPS: {props['fps']:.1f} (expected {expected_fps})")
        
        # Test duration (should be close to source)
        duration_diff = abs(props['duration'] - source_props['duration'])
        duration_ok = duration_diff < 0.5  # Allow 0.5s tolerance
        duration_status = "✓" if duration_ok else "✗"
        print(f"  {duration_status} Duration: {props['duration']:.2f}s (source: {source_props['duration']:.2f}s, diff: {duration_diff:.2f}s)")
        
        # Test frame count in video
        expected_video_frames = int(props['duration'] * expected_fps)
        video_frame_diff = abs(props['frame_count'] - expected_video_frames)
        video_frames_ok = video_frame_diff <= 2  # Allow 2 frame tolerance for rounding
        video_frames_status = "✓" if video_frames_ok else "✗"
        print(f"  {video_frames_status} Video frames: {props['frame_count']} (expected ~{expected_video_frames})")
        
        # Test extracted frame count
        extracted_frames = count_extracted_frames(frames_dir)
        extracted_frames_ok = abs(extracted_frames - props['frame_count']) <= 1
        extracted_frames_status = "✓" if extracted_frames_ok else "✗"
        print(f"  {extracted_frames_status} Extracted frames: {extracted_frames} (video has {props['frame_count']})")
        
        # Overall status for this variant
        variant_ok = fps_ok and duration_ok and video_frames_ok and extracted_frames_ok
        if not variant_ok:
            all_passed = False
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("✓ All FPS variants passed tests!")
    else:
        print("✗ Some variants failed tests.")
    
    return all_passed

if __name__ == "__main__":
    test_fps_variants() 