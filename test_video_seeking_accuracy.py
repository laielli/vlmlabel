#!/usr/bin/env python3
"""
Test script to verify video seeking accuracy by comparing expected vs actual video times.
This will help identify if the video player is actually seeking to the correct times.
"""

import os
import sys
import re

def analyze_frame_timing():
    """Analyze the frame timing calculations used in the app"""
    
    frames_dir = "static/videos/dashcam60fps/frames/full_30"
    
    if not os.path.exists(frames_dir):
        print(f"❌ Frames directory not found: {frames_dir}")
        return False
    
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])[:10]
    
    print("🔍 FRAME TIMING ANALYSIS")
    print("=" * 60)
    print("Analyzing the frame timing calculations used in app.py")
    print()
    
    # Simulate the frame processing logic from app.py
    fps = 30  # This is the FPS used for the full_30 variant
    frame_interval = 1.0 / fps
    
    print(f"Video FPS: {fps}")
    print(f"Frame interval: {frame_interval:.6f} seconds")
    print()
    
    print("Frame timing calculations:")
    for i, frame_file in enumerate(frame_files):
        # Extract frame number from filename (like app.py does)
        match = re.search(r'frame_(\d+)', frame_file)
        if match:
            frame_number = int(match.group(1))
            calculated_time = frame_number * frame_interval
            
            print(f"{frame_file}:")
            print(f"  Frame number: {frame_number}")
            print(f"  Calculated time: {calculated_time:.6f}s")
            print(f"  Expected in video: {calculated_time:.3f}s")
            print()
    
    # Focus on frames 3 and 4
    print("🎯 SPECIFIC ANALYSIS: Frames 3 and 4")
    print("=" * 60)
    
    frame_3_time = 3 * frame_interval
    frame_4_time = 4 * frame_interval
    time_difference = frame_4_time - frame_3_time
    
    print(f"Frame 3 expected time: {frame_3_time:.6f}s ({frame_3_time:.3f}s)")
    print(f"Frame 4 expected time: {frame_4_time:.6f}s ({frame_4_time:.3f}s)")
    print(f"Time difference: {time_difference:.6f}s ({time_difference:.3f}s)")
    print()
    
    print("🔧 DEBUGGING RECOMMENDATIONS")
    print("=" * 60)
    print("To verify video seeking accuracy:")
    print("1. Open browser developer tools")
    print("2. Click on frame_0003.jpg")
    print("3. Check console for 'Target time' and 'Actual time after seek'")
    print("4. Click on frame_0004.jpg")
    print("5. Verify the actual times match the expected times above")
    print()
    print("Expected behavior:")
    print(f"- Clicking frame_0003.jpg should seek to {frame_3_time:.3f}s")
    print(f"- Clicking frame_0004.jpg should seek to {frame_4_time:.3f}s")
    print(f"- Time difference should be {time_difference:.3f}s")
    print()
    print("If the video player shows the same visual content for both frames,")
    print("but the console shows correct times, then the issue is:")
    print("- Video seeking precision (browser limitation)")
    print("- Video encoding keyframe spacing")
    print("- Video player implementation")
    
    return True

def check_video_properties():
    """Check video file properties that might affect seeking"""
    
    video_path = "static/videos/dashcam60fps/dashcam60fps__full_30.mp4"
    
    print("\n🎬 VIDEO FILE ANALYSIS")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    file_size = os.path.getsize(video_path)
    print(f"Video file: {video_path}")
    print(f"File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")
    
    # Try to get video info using ffprobe if available
    try:
        import subprocess
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                print(f"Video codec: {video_stream.get('codec_name', 'unknown')}")
                print(f"Video duration: {video_stream.get('duration', 'unknown')}s")
                print(f"Video FPS: {video_stream.get('r_frame_rate', 'unknown')}")
                print(f"Keyframe interval: {video_stream.get('gop_size', 'unknown')}")
                
                # Check if this is a variable bitrate video
                if 'bit_rate' in video_stream:
                    print(f"Bitrate: {video_stream['bit_rate']} bps")
                
        else:
            print("⚠️  Could not analyze video with ffprobe")
            
    except (ImportError, FileNotFoundError):
        print("⚠️  ffprobe not available for detailed video analysis")
    
    return True

def create_manual_test_instructions():
    """Create instructions for manual testing"""
    
    print("\n📋 MANUAL TESTING INSTRUCTIONS")
    print("=" * 60)
    print("Follow these steps to verify the video seeking issue:")
    print()
    print("1. Start the Flask app:")
    print("   python app.py")
    print()
    print("2. Open browser and go to the video annotation page")
    print()
    print("3. Open browser Developer Tools (F12)")
    print("   - Go to Console tab")
    print()
    print("4. Click on frame_0003.jpg thumbnail")
    print("   - Look for console output showing:")
    print("     * Target time: 0.100s")
    print("     * Actual time after seek: [should be 0.100s]")
    print()
    print("5. Click on frame_0004.jpg thumbnail")
    print("   - Look for console output showing:")
    print("     * Target time: 0.133s")
    print("     * Actual time after seek: [should be 0.133s]")
    print()
    print("6. Compare the visual content:")
    print("   - If times are correct but visual content is identical:")
    print("     → Video seeking precision issue")
    print("   - If times are incorrect:")
    print("     → Frame timing calculation issue")
    print("   - If visual content changes but very subtly:")
    print("     → Normal behavior for dashcam footage")
    print()
    print("7. Test with larger frame gaps:")
    print("   - Click frame_0000.jpg, then frame_0010.jpg")
    print("   - Should see more obvious visual difference")
    print()
    print("Expected console output format:")
    print("=== FRAME CLICK DEBUG ===")
    print("Frame clicked: frame_0003.jpg")
    print("Frame number: 3")
    print("Target time (calculated): 0.100000")
    print("Current video time (before seek): [previous time]")
    print("Target time: 0.100000")
    print("Actual time after seek: 0.100000")
    print("Time difference: 0.000000")
    print("✅ Frame alignment correct")

if __name__ == "__main__":
    print("Video Seeking Accuracy Test")
    print("=" * 60)
    
    success = True
    
    # Analyze frame timing
    if not analyze_frame_timing():
        success = False
    
    # Check video properties
    if not check_video_properties():
        success = False
    
    # Create manual test instructions
    create_manual_test_instructions()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Video seeking accuracy test setup completed")
        print("\nNext step: Follow the manual testing instructions above")
        print("to verify if the video player is seeking to correct times.")
    else:
        print("❌ Video seeking accuracy test setup failed")
    
    sys.exit(0 if success else 1) 