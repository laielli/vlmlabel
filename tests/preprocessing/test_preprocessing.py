#!/usr/bin/env python3
"""
Test script for the new preprocessing system

This script provides basic tests to validate:
- FPS variant generation maintains duration
- Frame extraction produces unique frames
- Processing pipeline works correctly

Usage:
  python test_preprocessing.py
"""

import os
import sys
import tempfile
import shutil
import subprocess
from video_processor import VideoProcessor
from frame_extractor import FrameExtractor


def create_test_video(output_path, duration=5, fps=30):
    """Create a test video using ffmpeg"""
    cmd = [
        "ffmpeg", "-f", "lavfi", "-i", 
        f"testsrc=duration={duration}:size=320x240:rate={fps}",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-y", output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def test_fps_variant_duration():
    """Test that FPS variants maintain source duration"""
    print("Testing FPS variant duration preservation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test video
        source_video = os.path.join(temp_dir, "test_60fps.mp4")
        if not create_test_video(source_video, duration=5, fps=60):
            print("✗ Failed to create test video")
            return False
        
        # Create processor
        processor = VideoProcessor()
        
        # Create 30 FPS variant
        variant_video = os.path.join(temp_dir, "test_30fps.mp4")
        success = processor.create_fps_variant(source_video, variant_video, 60, 30)
        
        if not success:
            print("✗ Failed to create FPS variant")
            return False
        
        # Check durations
        source_duration = processor.get_video_duration(source_video)
        variant_duration = processor.get_video_duration(variant_video)
        duration_diff = abs(source_duration - variant_duration)
        
        if duration_diff > 0.1:  # Allow 0.1s tolerance
            print(f"✗ Duration mismatch: {source_duration:.2f}s -> {variant_duration:.2f}s")
            return False
        
        print(f"✓ Duration preserved: {source_duration:.2f}s -> {variant_duration:.2f}s")
        return True


def test_unique_frame_extraction():
    """Test that frame extraction produces unique frames at target intervals"""
    print("Testing unique frame extraction...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test video
        source_video = os.path.join(temp_dir, "test_30fps.mp4")
        if not create_test_video(source_video, duration=3, fps=30):
            print("✗ Failed to create test video")
            return False
        
        # Extract frames
        extractor = FrameExtractor()
        frames_dir = os.path.join(temp_dir, "frames")
        success, frame_count = extractor.extract_frames_at_intervals(source_video, frames_dir, 10)
        
        if not success:
            print("✗ Frame extraction failed")
            return False
        
        # For 3-second video at 10 FPS, expect ~30 frames
        expected_count = 30
        if abs(frame_count - expected_count) > 2:  # Allow some tolerance
            print(f"✗ Unexpected frame count: expected ~{expected_count}, got {frame_count}")
            return False
        
        print(f"✓ Frame extraction successful: {frame_count} frames")
        return True


def test_clip_extraction():
    """Test clip extraction functionality"""
    print("Testing clip extraction...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test video
        source_video = os.path.join(temp_dir, "test_source.mp4")
        if not create_test_video(source_video, duration=10, fps=30):
            print("✗ Failed to create test video")
            return False
        
        # Extract clip
        processor = VideoProcessor()
        clip_video = os.path.join(temp_dir, "test_clip.mp4")
        success = processor.extract_clip(source_video, clip_video, "00:00:02.0", "00:00:05.0")
        
        if not success:
            print("✗ Clip extraction failed")
            return False
        
        # Check clip duration (should be ~3 seconds)
        clip_duration = processor.get_video_duration(clip_video)
        expected_duration = 3.0
        
        if abs(clip_duration - expected_duration) > 0.2:
            print(f"✗ Clip duration mismatch: expected {expected_duration}s, got {clip_duration:.2f}s")
            return False
        
        print(f"✓ Clip extraction successful: {clip_duration:.2f}s")
        return True


def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def main():
    """Run all tests"""
    print("Video Preprocessing Test Suite")
    print("==============================")
    
    # Check prerequisites
    if not check_ffmpeg():
        print("✗ ffmpeg not found. Please install ffmpeg to run tests.")
        sys.exit(1)
    
    print("✓ ffmpeg found")
    
    # Run tests
    tests = [
        test_fps_variant_duration,
        test_unique_frame_extraction,
        test_clip_extraction
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    # Print summary
    print("="*40)
    print(f"Test Summary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 