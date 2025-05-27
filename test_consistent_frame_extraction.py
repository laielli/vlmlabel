#!/usr/bin/env python3
"""
Test script for consistent frame extraction methods.

This script tests the two options described in consistent_frame_extraction.md:
1. Re-encode to I-frame-only video
2. Decode entire video and then extract

Tests are performed on input_videos/dashcam60fps.mp4
"""

import os
import subprocess
import time
import shutil
from pathlib import Path
import argparse


class ConsistentFrameExtractionTester:
    def __init__(self, input_video="input_videos/dashcam60fps.mp4"):
        self.input_video = input_video
        self.output_dir = Path("test_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        # Test parameters
        self.test_fps_rates = [5, 10, 15, 30]  # Different FPS rates to test consistency
        self.test_duration = 10  # Extract first 10 seconds for testing
        
    def run_ffmpeg_command(self, command, description):
        """Run an ffmpeg command and measure execution time."""
        print(f"\n🔄 {description}")
        print(f"Command: {' '.join(command)}")
        
        start_time = time.time()
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            end_time = time.time()
            print(f"✅ Completed in {end_time - start_time:.2f} seconds")
            return True, end_time - start_time
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            print(f"stderr: {e.stderr}")
            return False, 0
    
    def get_video_info(self, video_path):
        """Get basic video information using ffprobe."""
        command = [
            "ffprobe", "-v", "quiet", "-print_format", "json", 
            "-show_format", "-show_streams", video_path
        ]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            import json
            info = json.loads(result.stdout)
            
            video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
            duration = float(info['format']['duration'])
            fps = eval(video_stream['r_frame_rate'])  # e.g., "60/1" -> 60.0
            
            return {
                'duration': duration,
                'fps': fps,
                'width': video_stream['width'],
                'height': video_stream['height'],
                'codec': video_stream['codec_name']
            }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def test_option1_iframe_only(self):
        """
        Option 1: Re-encode to I-frame-only video
        
        ffmpeg -i input.mp4 -g 1 -keyint_min 1 -sc_threshold 0 
               -x264opts "keyint=1:min-keyint=1:no-scenecut" 
               -c:v libx264 -preset fast -crf 18 i_frames_only.mp4
        """
        print("\n" + "="*60)
        print("🎯 TESTING OPTION 1: Re-encode to I-frame-only video")
        print("="*60)
        
        # Step 1: Create I-frame-only version
        iframe_video = self.output_dir / "dashcam_iframe_only.mp4"
        
        command = [
            "ffmpeg", "-y", "-i", self.input_video,
            "-t", str(self.test_duration),  # Limit to test duration
            "-g", "1",
            "-keyint_min", "1", 
            "-sc_threshold", "0",
            "-x264opts", "keyint=1:min-keyint=1:no-scenecut",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            str(iframe_video)
        ]
        
        success, encode_time = self.run_ffmpeg_command(
            command, "Creating I-frame-only video"
        )
        
        if not success:
            return False
        
        # Step 2: Extract frames at different FPS rates from I-frame-only video
        option1_results = {}
        
        for fps in self.test_fps_rates:
            output_pattern = self.output_dir / f"option1_fps{fps}" / "frame_%05d.png"
            output_pattern.parent.mkdir(exist_ok=True)
            
            command = [
                "ffmpeg", "-y", "-i", str(iframe_video),
                "-vf", f"fps={fps}",
                "-vsync", "0",
                str(output_pattern)
            ]
            
            success, extract_time = self.run_ffmpeg_command(
                command, f"Extracting frames at {fps} FPS from I-frame-only video"
            )
            
            if success:
                frame_count = len(list(output_pattern.parent.glob("*.png")))
                option1_results[fps] = {
                    'frame_count': frame_count,
                    'extract_time': extract_time
                }
                print(f"   📊 Extracted {frame_count} frames")
        
        # Step 3: Analyze results
        print(f"\n📈 Option 1 Results:")
        print(f"   Encoding time: {encode_time:.2f}s")
        for fps, data in option1_results.items():
            print(f"   {fps} FPS: {data['frame_count']} frames in {data['extract_time']:.2f}s")
        
        return True
    
    def test_option2_decode_all(self):
        """
        Option 2: Decode entire video and then extract
        
        ffmpeg -i input.mp4 -vsync 0 frame_%05d.png
        """
        print("\n" + "="*60)
        print("🎯 TESTING OPTION 2: Decode entire video and then extract")
        print("="*60)
        
        # Step 1: Decode all frames to PNG
        all_frames_dir = self.output_dir / "all_frames"
        all_frames_dir.mkdir(exist_ok=True)
        
        frame_pattern = all_frames_dir / "frame_%05d.png"
        
        command = [
            "ffmpeg", "-y", "-i", self.input_video,
            "-t", str(self.test_duration),  # Limit to test duration
            "-vsync", "0",
            str(frame_pattern)
        ]
        
        success, decode_time = self.run_ffmpeg_command(
            command, "Decoding entire video to individual frames"
        )
        
        if not success:
            return False
        
        total_frames = len(list(all_frames_dir.glob("*.png")))
        print(f"   📊 Decoded {total_frames} total frames")
        
        # Step 2: Create FPS variants by selecting frames
        option2_results = {}
        
        for fps in self.test_fps_rates:
            output_dir = self.output_dir / f"option2_fps{fps}"
            output_dir.mkdir(exist_ok=True)
            
            # Calculate frame interval for this FPS
            original_fps = total_frames / self.test_duration
            frame_interval = int(original_fps / fps)
            
            print(f"\n🔄 Creating {fps} FPS variant (every {frame_interval} frames)")
            
            selected_frames = 0
            for i, frame_file in enumerate(sorted(all_frames_dir.glob("*.png"))):
                if i % frame_interval == 0:
                    target_file = output_dir / f"frame_{selected_frames:05d}.png"
                    shutil.copy2(frame_file, target_file)
                    selected_frames += 1
            
            option2_results[fps] = {
                'frame_count': selected_frames,
                'frame_interval': frame_interval
            }
            print(f"   📊 Selected {selected_frames} frames")
        
        # Step 3: Analyze results
        print(f"\n📈 Option 2 Results:")
        print(f"   Decoding time: {decode_time:.2f}s")
        print(f"   Total frames decoded: {total_frames}")
        for fps, data in option2_results.items():
            print(f"   {fps} FPS: {data['frame_count']} frames (interval: {data['frame_interval']})")
        
        return True
    
    def compare_frame_consistency(self):
        """Compare frames between the two methods to verify consistency."""
        print("\n" + "="*60)
        print("🔍 COMPARING FRAME CONSISTENCY BETWEEN METHODS")
        print("="*60)
        
        for fps in self.test_fps_rates:
            option1_dir = self.output_dir / f"option1_fps{fps}"
            option2_dir = self.output_dir / f"option2_fps{fps}"
            
            if not (option1_dir.exists() and option2_dir.exists()):
                print(f"⚠️  Skipping {fps} FPS comparison - missing directories")
                continue
            
            option1_frames = sorted(option1_dir.glob("*.png"))
            option2_frames = sorted(option2_dir.glob("*.png"))
            
            print(f"\n📊 {fps} FPS Comparison:")
            print(f"   Option 1: {len(option1_frames)} frames")
            print(f"   Option 2: {len(option2_frames)} frames")
            
            # Compare file sizes as a rough consistency check
            if len(option1_frames) > 0 and len(option2_frames) > 0:
                min_frames = min(len(option1_frames), len(option2_frames))
                size_diffs = []
                
                for i in range(min(5, min_frames)):  # Compare first 5 frames
                    size1 = option1_frames[i].stat().st_size
                    size2 = option2_frames[i].stat().st_size
                    diff_pct = abs(size1 - size2) / max(size1, size2) * 100
                    size_diffs.append(diff_pct)
                
                avg_diff = sum(size_diffs) / len(size_diffs)
                print(f"   Average file size difference: {avg_diff:.2f}%")
                
                if avg_diff < 5:
                    print(f"   ✅ Frames appear consistent (< 5% size difference)")
                else:
                    print(f"   ⚠️  Significant differences detected (> 5% size difference)")
    
    def cleanup(self):
        """Clean up test output files."""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            print(f"\n🧹 Cleaned up test outputs in {self.output_dir}")
    
    def run_full_test(self, cleanup_after=False):
        """Run the complete test suite."""
        print("🚀 Starting Consistent Frame Extraction Test")
        print(f"📹 Input video: {self.input_video}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⏱️  Test duration: {self.test_duration} seconds")
        print(f"🎯 Test FPS rates: {self.test_fps_rates}")
        
        # Get video info
        video_info = self.get_video_info(self.input_video)
        if video_info:
            print(f"\n📊 Video Info:")
            print(f"   Duration: {video_info['duration']:.2f}s")
            print(f"   FPS: {video_info['fps']:.2f}")
            print(f"   Resolution: {video_info['width']}x{video_info['height']}")
            print(f"   Codec: {video_info['codec']}")
        
        # Run tests
        success1 = self.test_option1_iframe_only()
        success2 = self.test_option2_decode_all()
        
        if success1 and success2:
            self.compare_frame_consistency()
        
        # Summary
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        print(f"Option 1 (I-frame-only): {'✅ Success' if success1 else '❌ Failed'}")
        print(f"Option 2 (Decode all): {'✅ Success' if success2 else '❌ Failed'}")
        
        if success1 and success2:
            print("\n🎉 Both methods completed successfully!")
            print("📁 Check the test_outputs/ directory for extracted frames")
        
        if cleanup_after:
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Test consistent frame extraction methods")
    parser.add_argument("--input", default="input_videos/dashcam60fps.mp4", 
                       help="Input video file")
    parser.add_argument("--duration", type=int, default=10,
                       help="Test duration in seconds")
    parser.add_argument("--fps-rates", nargs="+", type=int, default=[5, 10, 15, 30],
                       help="FPS rates to test")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up output files after testing")
    
    args = parser.parse_args()
    
    # Check if input video exists
    if not os.path.exists(args.input):
        print(f"❌ Error: Input video '{args.input}' not found")
        return 1
    
    # Create tester and run
    tester = ConsistentFrameExtractionTester(args.input)
    tester.test_duration = args.duration
    tester.test_fps_rates = args.fps_rates
    
    tester.run_full_test(cleanup_after=args.cleanup)
    
    return 0


if __name__ == "__main__":
    exit(main()) 