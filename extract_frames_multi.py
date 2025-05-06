#!/usr/bin/env python3
"""
Frame extraction script for the Video Annotation Tool (Multi-Video Version)

This script extracts frames from a video file at a specified rate and saves them
as JPEG images in the appropriate directory structure for the multi-video tool.

Usage:
  python extract_frames_multi.py --video-id VIDEO_ID [options]

Options:
  --video-id ID        ID of the video (required)
  --video-path PATH    Path to the video file (default: static/videos/VIDEO_ID/video.mp4)
  --output-dir PATH    Directory to save frames (default: static/videos/VIDEO_ID/frames)
  --fps RATE           Frames per second to extract (default: 1)
  --help               Show this help message
"""

import os
import sys
import cv2
import getopt

def print_help():
    """Print help message"""
    print(__doc__)

def extract_frames(video_id, video_path=None, output_dir=None, target_fps=1):
    """Extract frames from a video at the specified rate"""
    # Set default paths based on video_id if not provided
    if video_path is None:
        video_path = os.path.join("static", "videos", video_id, "video.mp4")
    
    if output_dir is None:
        output_dir = os.path.join("static", "videos", video_id, "frames")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Open the video
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"Error: Could not open video {video_path}")
        return False
    
    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"Video ID: {video_id}")
    print(f"Video path: {video_path}")
    print(f"Output directory: {output_dir}")
    print(f"FPS: {fps}")
    print(f"Total frames: {total_frames}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Extracting frames at {target_fps} fps")
    
    # Calculate frame interval
    if target_fps >= fps:
        # If target fps is higher than video fps, extract every frame
        frame_interval = 1
        print("Warning: Target FPS is higher than video FPS. Extracting every frame.")
    else:
        frame_interval = int(fps / target_fps)
    
    # Extract frames
    count = 0
    saved_count = 0
    
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        # Save frame at the specified interval
        if count % frame_interval == 0:
            output_path = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
            cv2.imwrite(output_path, frame)
            saved_count += 1
            
            # Print progress
            if saved_count % 10 == 0:
                print(f"Extracted {saved_count} frames...", end="\r")
        
        count += 1
    
    video.release()
    print(f"\nExtraction complete. Saved {saved_count} frames to {output_dir}")
    return True

def main():
    """Main function"""
    # Default parameters
    video_id = None
    video_path = None
    output_dir = None
    target_fps = 1
    
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:v:o:f:", ["help", "video-id=", "video-path=", "output-dir=", "fps="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-i", "--video-id"):
            video_id = arg
        elif opt in ("-v", "--video-path"):
            video_path = arg
        elif opt in ("-o", "--output-dir"):
            output_dir = arg
        elif opt in ("-f", "--fps"):
            try:
                target_fps = float(arg)
            except ValueError:
                print("Error: FPS must be a number")
                sys.exit(2)
    
    # Check if video_id is provided
    if not video_id:
        print("Error: video-id is required")
        print_help()
        sys.exit(2)
    
    # Extract frames
    success = extract_frames(video_id, video_path, output_dir, target_fps)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 