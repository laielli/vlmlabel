#!/usr/bin/env python3
"""
Test script for I-frame video processing

This script tests the new I-frame video processor on the dashcam video
to verify it works correctly before full integration.
"""

import os
import sys
import yaml
from iframe_video_processor import IFrameVideoProcessor


def test_iframe_processing():
    """Test I-frame processing on the dashcam video"""
    print("🧪 Testing I-Frame Video Processing")
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
    test_output_dir = "test_iframe_output"
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Create processor
    processor = IFrameVideoProcessor(config)
    
    # Test just a subset for quick testing
    test_config = {
        'id': 'dashcam60fps_test',
        'source_video': source_video,
        'fps_variants': [30, 10],  # Test with just 2 variants
        'clips': [
            {
                'name': 'test_clip',
                'start': '00:00:03.0',
                'end': '00:00:05.0',
                'fps': [10, 5]
            }
        ]
    }
    
    print(f"\n🔄 Testing with limited config:")
    print(f"   FPS variants: {test_config['fps_variants']}")
    print(f"   Test clip: {test_config['clips'][0]['start']} to {test_config['clips'][0]['end']}")
    
    try:
        # Process the video
        results = processor.process_video_with_iframe_preprocessing(test_config, test_output_dir)
        
        if results['success']:
            print(f"\n✅ Test completed successfully!")
            
            # Check outputs
            print(f"\n📁 Checking outputs in {test_output_dir}:")
            
            if os.path.exists(test_output_dir):
                files = os.listdir(test_output_dir)
                video_files = [f for f in files if f.endswith('.mp4')]
                
                print(f"   Video files created: {len(video_files)}")
                for vf in video_files:
                    print(f"   - {vf}")
                
                # Check frames directories
                frames_dir = os.path.join(test_output_dir, "frames")
                if os.path.exists(frames_dir):
                    frame_dirs = os.listdir(frames_dir)
                    print(f"   Frame directories: {len(frame_dirs)}")
                    for fd in frame_dirs:
                        frame_count = len([f for f in os.listdir(os.path.join(frames_dir, fd)) 
                                         if f.endswith(('.jpg', '.png'))])
                        print(f"   - {fd}: {frame_count} frames")
            
            return True
        else:
            print(f"\n❌ Test failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return False


def cleanup_test_output():
    """Clean up test output directory"""
    import shutil
    test_output_dir = "test_iframe_output"
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir)
        print(f"🧹 Cleaned up {test_output_dir}")


def main():
    """Main function"""
    print("🚀 I-Frame Processing Test")
    
    # Run test
    success = test_iframe_processing()
    
    if success:
        print(f"\n🎉 All tests passed!")
        
        # Ask if user wants to clean up
        response = input("\nClean up test outputs? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            cleanup_test_output()
        else:
            print("📁 Test outputs preserved in test_iframe_output/")
        
        return 0
    else:
        print(f"\n💥 Tests failed!")
        return 1


if __name__ == "__main__":
    exit(main()) 