#!/usr/bin/env python3
"""
Test script for frame timestamp extraction

This script tests the new timestamp extraction functionality to verify
that frame-to-video alignment issues are resolved.
"""

import os
import sys
import yaml
import json
from iframe_video_processor import IFrameVideoProcessor


def test_timestamp_extraction():
    """Test timestamp extraction on a small subset"""
    print("🧪 Testing Frame Timestamp Extraction")
    print("=" * 50)
    
    # Load config
    config_file = "config.yaml"
    if not os.path.exists(config_file):
        print(f"❌ Config file {config_file} not found")
        return False
    
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
    # Find dashcam video config
    dashcam_config = None
    for video in config.get('videos', []):
        if video.get('id') == 'dashcam60fps':
            dashcam_config = video
            break
    
    if not dashcam_config:
        print("❌ dashcam60fps video not found in config")
        return False
    
    # Check if source video exists
    source_video = dashcam_config.get('source_video')
    if not os.path.exists(source_video):
        print(f"❌ Source video not found: {source_video}")
        return False
    
    print(f"✅ Found dashcam video: {source_video}")
    
    # Create test output directory
    test_output_dir = "test_timestamp_output"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Create processor
    processor = IFrameVideoProcessor(config)
    
    # Test with a very limited config for quick testing
    test_config = {
        'id': 'dashcam60fps_timestamp_test',
        'source_video': source_video,
        'fps_variants': [10],  # Test with just 1 variant
        'clips': []  # No clips for this test
    }
    
    print(f"\n🔄 Testing timestamp extraction with 10 FPS variant")
    
    try:
        # Process the video
        results = processor.process_video_with_iframe_preprocessing(test_config, test_output_dir)
        
        if results['success']:
            print(f"\n✅ Processing completed successfully!")
            
            # Check if timestamps were extracted
            variant_key = "full_10"
            frames_dir = os.path.join(test_output_dir, "frames", variant_key)
            timestamp_file = os.path.join(frames_dir, "frame_timestamps.json")
            
            if os.path.exists(timestamp_file):
                print(f"\n📁 Checking timestamp file: {timestamp_file}")
                
                with open(timestamp_file, 'r') as f:
                    timestamp_data = json.load(f)
                
                frame_mapping = timestamp_data.get('frame_mapping', {})
                total_frames = timestamp_data.get('total_frames', 0)
                
                print(f"   Total frames: {total_frames}")
                print(f"   Frame mappings: {len(frame_mapping)}")
                
                # Show first few frame mappings
                print(f"\n📊 Sample frame-to-timestamp mappings:")
                for i, (frame_file, data) in enumerate(list(frame_mapping.items())[:5]):
                    timestamp = data['timestamp']
                    frame_index = data['frame_index']
                    print(f"   {frame_file}: frame {frame_index} -> {timestamp:.6f}s")
                
                # Verify timestamps are increasing
                timestamps = [data['timestamp'] for data in frame_mapping.values()]
                timestamps.sort()
                
                if len(timestamps) > 1:
                    intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                    avg_interval = sum(intervals) / len(intervals)
                    expected_interval = 1.0 / 10  # 10 FPS = 0.1s intervals
                    
                    print(f"\n⏱️  Timestamp Analysis:")
                    print(f"   Expected interval (10 FPS): {expected_interval:.6f}s")
                    print(f"   Average actual interval: {avg_interval:.6f}s")
                    print(f"   Difference: {abs(avg_interval - expected_interval):.6f}s")
                    
                    if abs(avg_interval - expected_interval) < 0.01:  # 10ms tolerance
                        print(f"   ✅ Intervals are consistent with 10 FPS")
                    else:
                        print(f"   ⚠️  Intervals differ from expected 10 FPS")
                
                return True
            else:
                print(f"❌ Timestamp file not found: {timestamp_file}")
                return False
        else:
            print(f"\n❌ Processing failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return False


def test_direct_timestamp_extraction():
    """Test direct timestamp extraction from a video file"""
    print("\n" + "=" * 50)
    print("🧪 Testing Direct Timestamp Extraction")
    print("=" * 50)
    
    # Load config to get video path
    config_file = "config.yaml"
    if not os.path.exists(config_file):
        print(f"❌ Config file {config_file} not found")
        return False
    
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
    # Find dashcam video
    source_video = None
    for video in config.get('videos', []):
        if video.get('id') == 'dashcam60fps':
            source_video = video.get('source_video')
            break
    
    if not source_video or not os.path.exists(source_video):
        print(f"❌ Source video not found")
        return False
    
    # Create processor and test direct extraction
    processor = IFrameVideoProcessor(config)
    
    print(f"🔄 Extracting timestamps directly from: {source_video}")
    timestamps = processor.extract_frame_timestamps(source_video)
    
    if timestamps:
        print(f"✅ Extracted {len(timestamps)} timestamps")
        print(f"📊 First 10 timestamps:")
        for i, ts in enumerate(timestamps[:10]):
            print(f"   Frame {i}: {ts:.6f}s")
        
        if len(timestamps) > 1:
            # Calculate frame rate from timestamps
            duration = timestamps[-1] - timestamps[0]
            frame_count = len(timestamps) - 1
            calculated_fps = frame_count / duration if duration > 0 else 0
            
            print(f"\n📈 Analysis:")
            print(f"   Duration: {duration:.6f}s")
            print(f"   Frame count: {frame_count}")
            print(f"   Calculated FPS: {calculated_fps:.2f}")
        
        return True
    else:
        print(f"❌ No timestamps extracted")
        return False


def cleanup_test_output():
    """Clean up test output directory"""
    import shutil
    test_output_dir = "test_timestamp_output"
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir)
        print(f"🧹 Cleaned up {test_output_dir}")


def main():
    """Main function"""
    print("🚀 Frame Timestamp Extraction Test")
    
    # Run tests
    success1 = test_direct_timestamp_extraction()
    success2 = test_timestamp_extraction()
    
    if success1 and success2:
        print(f"\n🎉 All timestamp tests passed!")
        
        # Ask if user wants to clean up
        response = input("\nClean up test outputs? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            cleanup_test_output()
        else:
            print("📁 Test outputs preserved in test_timestamp_output/")
        
        return 0
    else:
        print(f"\n💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(main()) 