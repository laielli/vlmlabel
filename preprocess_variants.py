#!/usr/bin/env python3
"""
Preprocessing script for VLMLABEL to generate multi-FPS variants

This script processes videos according to config.yaml and generates:
- Different FPS variants for full-length videos
- Extracted frames for each variant

Usage:
  python preprocess_variants.py [--video-id VIDEO_ID]

Options:
  --video-id ID   Process only this video ID (otherwise process all in config)
  --help          Show this help message
"""

import os
import sys
import getopt
import yaml
import subprocess
import shutil
import cv2
import math
import glob

def get_exact_fps(video_path):
    """Get exact frame rate using multiple detection methods"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return 30.0  # Default fallback
    
    # Method 1: Get FPS from video properties
    fps_prop = cap.get(cv2.CAP_PROP_FPS)
    
    # Method 2: Calculate from frame count and duration
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Get duration by seeking to end
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count - 1)
    duration_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
    
    if duration_ms > 0:
        fps_calculated = (frame_count * 1000.0) / duration_ms
    else:
        fps_calculated = fps_prop
    
    cap.release()
    
    # Use the more precise value (if difference is small, use calculated)
    if abs(fps_calculated - fps_prop) < 0.1:
        return fps_calculated
    else:
        return fps_prop

def calculate_adjusted_fps(native_fps, target_fps):
    """Calculate adjusted FPS for perfect frame alignment"""
    # Common fractional frame rates
    common_rates = {
        29.97: 30000/1001,
        59.94: 60000/1001,
        23.976: 24000/1001,
        119.88: 120000/1001
    }
    
    # Check if native FPS is a common fractional rate
    for approx, exact in common_rates.items():
        if abs(native_fps - approx) < 0.01:
            native_fps = exact
            break
    
    # Calculate the exact divisor for perfect alignment
    divisor = round(native_fps / target_fps)
    if divisor == 0:
        divisor = 1
    adjusted_fps = native_fps / divisor
    
    return adjusted_fps, divisor

def get_video_duration(video_path):
    """Get video duration in seconds"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps if fps > 0 else 0
    
    cap.release()
    return duration

def extract_frames_aligned(video_path, output_dir, native_fps, target_fps):
    """Extract frames with perfect alignment to native FPS"""
    adjusted_fps, divisor = calculate_adjusted_fps(native_fps, target_fps)
    
    print(f"  Native FPS: {native_fps:.3f}")
    print(f"  Target FPS: {target_fps}")
    print(f"  Adjusted FPS: {adjusted_fps:.3f}")
    print(f"  Frame divisor: {divisor}")
    
    # Use ffmpeg with exact frame selection
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"select='not(mod(n\\,{divisor}))',setpts=N/FRAME_RATE/TB",
        "-r", str(adjusted_fps),
        "-start_number", "0",
        os.path.join(output_dir, "frame_%04d.jpg"),
        "-y"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error extracting frames: {result.stderr}")
        return False
    
    # Verify frame count
    expected_frames = math.ceil(get_video_duration(video_path) * adjusted_fps)
    actual_frames = len(glob.glob(os.path.join(output_dir, "frame_*.jpg")))
    
    if abs(actual_frames - expected_frames) > 1:
        print(f"Warning: Frame count mismatch. Expected ~{expected_frames}, got {actual_frames}")
    else:
        print(f"✓ Extracted {actual_frames} frames")
    
    return adjusted_fps

def print_help():
    """Print help message"""
    print(__doc__)

def load_config():
    """Load configuration from YAML file"""
    config_file = "config.yaml"
    if not os.path.exists(config_file):
        print(f"Error: Configuration file {config_file} not found")
        sys.exit(1)
    
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

def create_directory(path):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)
    return path

def run_command(command):
    """Run a shell command and display its output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error executing command: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def process_video(video_config, config):
    """Process a single video from the configuration"""
    video_id = video_config.get('id')
    source_video = video_config.get('source_video')
    canonical_variant = video_config.get('canonical_variant', 'full_30')
    fps_variants = video_config.get('fps_variants', [30])
    
    if not video_id or not source_video:
        print("Error: Video configuration must include 'id' and 'source_video'")
        return False
    
    if not os.path.exists(source_video):
        print(f"Error: Source video not found: {source_video}")
        return False
    
    # Detect exact native FPS
    print(f"Detecting native FPS for {source_video}")
    native_fps = get_exact_fps(source_video)
    print(f"Detected native FPS: {native_fps:.3f}")
    
    # Update config with detected native FPS if not already specified
    if 'native_fps' not in video_config:
        video_config['native_fps'] = native_fps
    
    # Create output directories
    video_dir = create_directory(os.path.join("static", "videos", video_id))
    
    # Store actual FPS values for each variant
    actual_fps_map = {}
    
    # Process each FPS variant
    for fps in fps_variants:
        variant_key = f"full_{fps}"
        variant_video = os.path.join(video_dir, f"{video_id}__{variant_key}.mp4")
        frames_dir = create_directory(os.path.join(video_dir, "frames", variant_key))
        
        print(f"\nProcessing variant {variant_key} for {video_id}")
        
        # Calculate adjusted FPS for perfect alignment
        adjusted_fps, divisor = calculate_adjusted_fps(native_fps, fps)
        actual_fps_map[fps] = adjusted_fps
        
        # Generate video at adjusted FPS using frame selection for precise alignment
        print(f"Generating {variant_key} variant with precise frame alignment")
        cmd = [
            "ffmpeg", "-i", source_video,
            "-vf", f"select='not(mod(n\\,{divisor}))',setpts=N/FRAME_RATE/TB",
            "-r", str(adjusted_fps),
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            variant_video, "-y"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error generating {variant_key} variant: {result.stderr}")
            continue
        
        # Extract frames using the new aligned method
        print(f"Extracting frames for {variant_key} variant")
        actual_fps = extract_frames_aligned(variant_video, frames_dir, adjusted_fps, adjusted_fps)
        if actual_fps is False:
            print(f"Error extracting frames for {variant_key} variant")
            continue
        
        print(f"✓ Successfully processed {variant_key} variant for {video_id}")
    
    # Save FPS mapping information
    fps_info_file = os.path.join(video_dir, "fps_info.yaml")
    fps_info = {
        'native_fps': native_fps,
        'variants': {}
    }
    
    for target_fps in fps_variants:
        adjusted_fps = actual_fps_map.get(target_fps, target_fps)
        fps_info['variants'][f'full_{target_fps}'] = {
            'target_fps': target_fps,
            'actual_fps': adjusted_fps
        }
    
    with open(fps_info_file, 'w') as f:
        yaml.dump(fps_info, f, default_flow_style=False)
    
    print(f"✓ Saved FPS information to {fps_info_file}")
    
    return True

def main():
    """Main function"""
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:", ["help", "video-id="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    target_video_id = None
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-i", "--video-id"):
            target_video_id = arg
    
    # Load configuration
    config = load_config()
    
    # Check if configuration is valid
    if not config:
        print("Error: Invalid configuration")
        sys.exit(1)
    
    videos = config.get('videos', [])
    if not videos:
        print("Warning: No videos defined in configuration")
        sys.exit(0)
    
    # Process videos
    success_count = 0
    fail_count = 0
    
    for video_config in videos:
        video_id = video_config.get('id')
        
        # Skip if not the target video (if specified)
        if target_video_id and video_id != target_video_id:
            continue
        
        print(f"\n=== Processing video: {video_id} ===")
        if process_video(video_config, config):
            success_count += 1
        else:
            fail_count += 1
    
    # Print summary
    print(f"\n=== Processing complete ===")
    print(f"Successfully processed {success_count} videos")
    if fail_count > 0:
        print(f"Failed to process {fail_count} videos")
        sys.exit(1)

if __name__ == "__main__":
    main() 