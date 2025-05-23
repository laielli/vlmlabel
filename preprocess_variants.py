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
    
    # Create output directories
    video_dir = create_directory(os.path.join("static", "videos", video_id))
    
    # Process each FPS variant
    for fps in fps_variants:
        variant_key = f"full_{fps}"
        variant_video = os.path.join(video_dir, f"{video_id}__{variant_key}.mp4")
        frames_dir = create_directory(os.path.join(video_dir, "frames", variant_key))
        
        # Generate video at this FPS
        print(f"\nProcessing variant {variant_key} for {video_id}")
        ffmpeg_cmd = f"ffmpeg -i {source_video} -r {fps} {variant_video} -y"
        if not run_command(ffmpeg_cmd):
            print(f"Error generating {variant_key} variant")
            continue
        
        # Extract frames at this FPS
        print(f"\nExtracting frames for {variant_key} variant")
        ffmpeg_cmd = f"ffmpeg -i {variant_video} -start_number 0 {os.path.join(frames_dir, 'frame_%04d.jpg')} -y"
        if not run_command(ffmpeg_cmd):
            print(f"Error extracting frames for {variant_key} variant")
            continue
        
        print(f"Successfully processed {variant_key} variant for {video_id}")
    
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