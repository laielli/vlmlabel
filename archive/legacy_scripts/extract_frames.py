#!/usr/bin/env python3
"""
Frame extraction script for the Video Annotation Tool

This script extracts frames from a video file at a specified rate and saves them
as JPEG images in the static/frames directory.

Usage:
  python extract_frames.py [options]

Options:
  --video-path PATH   Path to the video file (default: static/video.mp4)
  --output-dir PATH   Directory to save frames (default: static/frames)
  --fps RATE          Frames per second to extract (default: 1)
  --help              Show this help message
"""

import os
import sys
import cv2
import getopt

def print_help():
    """Print help message"""
    print(__doc__)

def extract_frames(video_path, output_dir, target_fps=1):
    """Extract frames from a video at the specified rate"""
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
    
    print(f"Video: {video_path}")
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
    video_path = "static/video.mp4"
    output_dir = "static/frames"
    target_fps = 1
    
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:o:f:", ["help", "video-path=", "output-dir=", "fps="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
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
    
    # Extract frames
    success = extract_frames(video_path, output_dir, target_fps)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 