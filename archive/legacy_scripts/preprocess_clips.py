#!/usr/bin/env python3
"""
Clip Preprocessing Script for the Video Annotation Tool

This script processes the source videos to create clip variants at different FPS
as defined in the config.yaml file. It extracts clips at specified time ranges and
processes them at different frame rates.

Usage:
  python preprocess_clips.py [--video-id VIDEO_ID]

Options:
  --video-id ID     Process only the specified video ID (default: process all videos)
  --help            Show this help message
"""

import os
import sys
import yaml
import getopt
import subprocess
import shutil
from datetime import datetime

CONFIG_FILE = "config.yaml"
VIDEO_BASE_DIR = "static/videos"
DEFAULT_CANONICAL_FPS = 60

def print_help():
    """Print help message"""
    print(__doc__)

def load_config():
    """Load configuration from YAML file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return yaml.safe_load(file)
    return {"default_canonical_fps": DEFAULT_CANONICAL_FPS, "videos": []}

def time_to_seconds(time_str):
    """Convert time string (HH:MM:SS.S) to seconds"""
    try:
        # Split by : and .
        parts = time_str.split(':')
        seconds_parts = parts[-1].split('.')
        
        hours = int(parts[0]) if len(parts) > 2 else 0
        minutes = int(parts[-2] if len(parts) > 1 else parts[0])
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 10
        return total_seconds
    except Exception as e:
        print(f"Error parsing time string '{time_str}': {e}")
        return 0

def process_clip(video_id, source_path, clip_name, start_time, end_time, fps_list, output_base_dir):
    """Process a clip at different FPS values"""
    print(f"Processing clip '{clip_name}' from {start_time} to {end_time}")
    
    # Create temporary file for highest FPS extraction
    tmp_clip_path = os.path.join(output_base_dir, f"{video_id}__tmp_clip.mp4")
    
    # Get the highest FPS in the list for initial extraction
    max_fps = max(fps_list)
    
    # Extract clip once at highest fps in the list
    extract_cmd = [
        "ffmpeg", "-y",  # Overwrite output files without asking
        "-i", source_path,
        "-ss", start_time,
        "-to", end_time,
        "-r", str(max_fps),
        tmp_clip_path
    ]
    
    print(f"Extracting clip at {max_fps} FPS: {' '.join(extract_cmd)}")
    subprocess.run(extract_cmd)
    
    # Process for each FPS value
    for fps in fps_list:
        # Skip if it's already the max FPS (already processed)
        if fps == max_fps:
            # Just rename the temp file
            clip_path = os.path.join(output_base_dir, f"{video_id}__{clip_name}_{fps}.mp4")
            shutil.copy(tmp_clip_path, clip_path)
        else:
            # Down-sample for remaining FPS values
            clip_path = os.path.join(output_base_dir, f"{video_id}__{clip_name}_{fps}.mp4")
            downsample_cmd = [
                "ffmpeg", "-y",
                "-i", tmp_clip_path,
                "-r", str(fps),
                clip_path
            ]
            print(f"Downsampling to {fps} FPS: {' '.join(downsample_cmd)}")
            subprocess.run(downsample_cmd)
        
        # Create frames directory for this variant
        frames_dir = os.path.join(output_base_dir, "frames", f"{clip_name}_{fps}")
        os.makedirs(frames_dir, exist_ok=True)
        
        # Extract frames
        frames_cmd = [
            "ffmpeg", "-y",
            "-i", clip_path,
            "-start_number", "0",
            os.path.join(frames_dir, "frame_%04d.jpg")
        ]
        print(f"Extracting frames for {clip_name}_{fps}: {' '.join(frames_cmd)}")
        subprocess.run(frames_cmd)
    
    # Remove temporary clip
    if os.path.exists(tmp_clip_path):
        os.remove(tmp_clip_path)
        print(f"Removed temporary file {tmp_clip_path}")

def process_video(video_config):
    """Process a video's clip variants"""
    video_id = video_config.get('id')
    source_video = video_config.get('source_video')
    clips = video_config.get('clips', [])
    
    if not video_id or not source_video:
        print("Error: Missing video ID or source path")
        return False
    
    if not os.path.exists(source_video):
        print(f"Error: Source video not found: {source_video}")
        return False
    
    # Create output directory
    output_dir = os.path.join(VIDEO_BASE_DIR, video_id)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing video: {video_id}")
    print(f"Source: {source_video}")
    print(f"Output directory: {output_dir}")
    
    # Process each clip
    for clip in clips:
        clip_name = clip.get('name')
        start_time = clip.get('start')
        end_time = clip.get('end')
        fps_list = clip.get('fps', [])
        
        if not clip_name or not start_time or not end_time or not fps_list:
            print(f"Skipping clip with missing configuration: {clip}")
            continue
        
        process_clip(video_id, source_video, clip_name, start_time, end_time, fps_list, output_dir)
    
    return True

def main():
    """Main function"""
    # Parse command line arguments
    target_video_id = None
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:", ["help", "video-id="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-i", "--video-id"):
            target_video_id = arg
    
    # Load configuration
    config = load_config()
    
    # Get videos to process
    videos = config.get('videos', [])
    if target_video_id:
        videos = [v for v in videos if v.get('id') == target_video_id]
        if not videos:
            print(f"Error: Video ID '{target_video_id}' not found in config")
            sys.exit(1)
    
    # Process each video
    for video_config in videos:
        success = process_video(video_config)
        if not success:
            print(f"Error processing video: {video_config.get('id')}")
    
    print("Processing complete!")

if __name__ == "__main__":
    main() 