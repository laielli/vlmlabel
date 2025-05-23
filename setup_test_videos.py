#!/usr/bin/env python3
"""
A utility script to set up test video directories for the multi-video annotation tool.
This script creates demo directories with sample .txt files in place of actual videos and frames.

Usage:
  python setup_test_videos.py

This will create directories for three sample videos:
- static/videos/sample_video_1/
- static/videos/sample_video_2/
- static/videos/sample_video_3/

With placeholder files for videos and frames.
"""

import os
import shutil
from datetime import datetime

# Define base directories
VIDEO_BASE_DIR = os.path.join("static", "videos")
ANNOTATION_BASE_DIR = os.path.join("data", "annotations")

# Sample video IDs
SAMPLE_VIDEOS = [
    "sample_video_1",
    "sample_video_2", 
    "sample_video_3"
]

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def create_text_file(path, content):
    """Create a text file with given content"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created file: {path}")

def setup_test_video(video_id):
    """Set up directory structure and placeholder files for a test video"""
    # Create video directory
    video_dir = os.path.join(VIDEO_BASE_DIR, video_id)
    create_directory(video_dir)
    
    # Create frames directory
    frames_dir = os.path.join(video_dir, "frames")
    create_directory(frames_dir)
    
    # Create annotations directory
    ann_dir = os.path.join(ANNOTATION_BASE_DIR, video_id)
    create_directory(ann_dir)
    
    # Create placeholder files
    
    # 1. Placeholder video file
    video_placeholder = os.path.join(video_dir, "video.txt")  # Using .txt instead of .mp4
    create_text_file(video_placeholder, f"This is a placeholder for {video_id}'s video file.\n"
                                        f"In a real setup, this would be video.mp4")
    
    # 2. Create some placeholder frame files
    for i in range(1, 6):  # Create 5 frame placeholders
        frame_placeholder = os.path.join(frames_dir, f"frame_{i:04d}.txt")  # Using .txt instead of .jpg
        create_text_file(frame_placeholder, f"This is a placeholder for frame #{i} of {video_id}")
    
    # 3. Create a sample annotation file
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    annotation_file = os.path.join(ann_dir, f"annotations_{timestamp}.csv")
    create_text_file(annotation_file, "start_frame,end_frame,event_type,notes\n"
                                     f"10,20,Sample Event,This is a sample event for {video_id}\n"
                                     f"30,40,Another Event,This is another sample event for {video_id}")
    
    print(f"Test setup complete for {video_id}")

def main():
    """Main function to set up all test videos"""
    # Create base directories
    create_directory(VIDEO_BASE_DIR)
    create_directory(ANNOTATION_BASE_DIR)
    
    # Set up each test video
    for video_id in SAMPLE_VIDEOS:
        setup_test_video(video_id)
    
    print("\nSetup complete!")
    print(f"Created {len(SAMPLE_VIDEOS)} sample video directories in {VIDEO_BASE_DIR}")
    print("Note: These are just placeholders with .txt files. In a real setup, you would have:")
    print("- video.mp4 files for the actual videos")
    print("- frame_XXXX.jpg files for the extracted frames")
    print("\nTo see the app with real videos, follow these steps:")
    print("1. Place MP4 video files in each video directory (e.g., static/videos/sample_video_1/video.mp4)")
    print("2. Extract frames using FFmpeg or the provided extract_frames.py script")
    print("3. Run the Flask app with 'python app.py' and open http://localhost:5000 in your browser")

if __name__ == "__main__":
    main() 