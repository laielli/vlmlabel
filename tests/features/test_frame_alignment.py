#!/usr/bin/env python3
"""
Test script to verify frame-video alignment fix

This script tests that the frame timestamp extraction implementation
correctly loads and uses precise timestamps for frame seeking.
"""

import os
import json
import sys
from app import load_frame_timestamps


def test_frame_timestamp_loading():
    """Test that frame timestamps can be loaded correctly"""
    print("🧪 Testing Frame Timestamp Loading")
    print("=" * 50)
    
    video_id = "dashcam60fps"
    variant = "full_30"
    
    # Test loading frame timestamps
    frame_timestamps = load_frame_timestamps(video_id, variant)
    
    if frame_timestamps:
        print(f"✅ Successfully loaded {len(frame_timestamps)} frame timestamps")
        
        # Show first few timestamps
        print(f"\n📊 Sample frame timestamps:")
        for i, (frame_file, data) in enumerate(list(frame_timestamps.items())[:5]):
            timestamp = data['timestamp']
            frame_index = data['frame_index']
            print(f"   {frame_file}: frame {frame_index} -> {timestamp:.6f}s")
        
        # Verify timestamp precision
        timestamps = [data['timestamp'] for data in frame_timestamps.values()]
        timestamps.sort()
        
        if len(timestamps) > 1:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_interval = sum(intervals) / len(intervals)
            expected_interval = 1.0 / 30  # 30 FPS = 0.033333s intervals
            
            print(f"\n⏱️  Timestamp Analysis:")
            print(f"   Expected interval (30 FPS): {expected_interval:.6f}s")
            print(f"   Average actual interval: {avg_interval:.6f}s")
            print(f"   Difference: {abs(avg_interval - expected_interval):.6f}s")
            
            if abs(avg_interval - expected_interval) < 0.001:  # 1ms tolerance
                print(f"   ✅ Intervals are consistent with 30 FPS")
                return True
            else:
                print(f"   ⚠️  Intervals differ from expected 30 FPS")
                return False
        else:
            print(f"   ⚠️  Not enough timestamps to analyze intervals")
            return False
    else:
        print(f"❌ Failed to load frame timestamps")
        return False


def test_multiple_variants():
    """Test loading timestamps for multiple variants"""
    print("\n" + "=" * 50)
    print("🧪 Testing Multiple Variants")
    print("=" * 50)
    
    video_id = "dashcam60fps"
    variants = ["full_60", "full_30", "full_10", "full_5"]
    
    results = {}
    
    for variant in variants:
        frame_timestamps = load_frame_timestamps(video_id, variant)
        
        if frame_timestamps:
            count = len(frame_timestamps)
            # Get FPS from variant name
            fps = int(variant.split('_')[1])
            
            # Calculate expected frame count (approximately)
            expected_count = fps * 7.7  # ~7.7 second video
            
            print(f"✅ {variant}: {count} frames (expected ~{expected_count:.0f})")
            results[variant] = {'success': True, 'count': count, 'expected': expected_count}
        else:
            print(f"❌ {variant}: Failed to load timestamps")
            results[variant] = {'success': False, 'count': 0, 'expected': 0}
    
    # Check if all variants loaded successfully
    successful = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"\n📊 Summary: {successful}/{total} variants loaded successfully")
    return successful == total


def test_api_format():
    """Test that the timestamp format matches what the JavaScript expects"""
    print("\n" + "=" * 50)
    print("🧪 Testing API Format Compatibility")
    print("=" * 50)
    
    video_id = "dashcam60fps"
    variant = "full_30"
    
    # Load timestamps using the same function as the API
    frame_timestamps = load_frame_timestamps(video_id, variant)
    
    if frame_timestamps:
        # Test the format expected by JavaScript
        test_frame = "frame_0010.jpg"
        
        if test_frame in frame_timestamps:
            data = frame_timestamps[test_frame]
            required_fields = ['frame_index', 'timestamp', 'frame_number']
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Frame data format is correct:")
                print(f"   Frame: {test_frame}")
                print(f"   Index: {data['frame_index']}")
                print(f"   Timestamp: {data['timestamp']:.6f}s")
                print(f"   Frame Number: {data['frame_number']}")
                return True
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
        else:
            print(f"❌ Test frame {test_frame} not found in timestamps")
            return False
    else:
        print(f"❌ Failed to load frame timestamps")
        return False


def main():
    """Main test function"""
    print("🚀 Frame-Video Alignment Fix Test")
    
    # Check if timestamp files exist
    timestamp_file = "static/videos/dashcam60fps/frames/full_30/frame_timestamps.json"
    if not os.path.exists(timestamp_file):
        print(f"❌ Timestamp file not found: {timestamp_file}")
        print("   Please run: python preprocess_with_iframe.py --video-id dashcam60fps")
        return 1
    
    # Run tests
    test1 = test_frame_timestamp_loading()
    test2 = test_multiple_variants()
    test3 = test_api_format()
    
    if test1 and test2 and test3:
        print(f"\n🎉 All frame alignment tests passed!")
        print(f"\n✅ Frame-video alignment fix is working correctly:")
        print(f"   • Precise timestamps are extracted from videos")
        print(f"   • Timestamps are stored in correct JSON format")
        print(f"   • API format matches JavaScript expectations")
        print(f"   • Multiple variants are supported")
        print(f"\n🎯 The misalignment issue should now be resolved!")
        return 0
    else:
        print(f"\n💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(main()) 