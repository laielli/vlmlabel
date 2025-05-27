#!/usr/bin/env python3
"""
Frame Extraction Utilities for Video Preprocessing

This module provides utilities for extracting unique frames from videos at
specific FPS intervals, avoiding duplicate frames and maintaining proper timing.
"""

import os
import subprocess
import cv2
import glob
import math


class FrameExtractor:
    """Handles frame extraction with proper FPS timing"""
    
    def __init__(self):
        pass
    
    def get_video_info(self, video_path):
        """Get video information including FPS and duration"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration
        }
    
    def extract_frames_at_intervals(self, video_path, output_dir, target_fps):
        """
        Extract frames at specific time intervals to avoid duplicates
        
        Args:
            video_path: Path to source video
            output_dir: Directory to save frames
            target_fps: Target frames per second for extraction
            
        Returns:
            Tuple of (success: bool, frame_count: int)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Get video info
        video_info = self.get_video_info(video_path)
        source_fps = video_info['fps']
        duration = video_info['duration']
        
        print(f"  Source FPS: {source_fps:.3f}")
        print(f"  Target FPS: {target_fps}")
        print(f"  Duration: {duration:.3f}s")
        
        # Calculate frame extraction strategy
        if target_fps >= source_fps:
            # Extract all frames if target is higher than source
            print("  Strategy: Extract all frames (target >= source)")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-start_number", "0",
                "-y",
                os.path.join(output_dir, "frame_%04d.jpg")
            ]
        else:
            # Use time-based selection for proper interval extraction
            frame_interval = 1.0 / target_fps
            print(f"  Strategy: Time-based selection every {frame_interval:.3f}s")
            
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vf", f"select='eq(n\\,0)+gte(t-prev_selected_t\\,{frame_interval})'",
                "-vsync", "0",
                "-start_number", "0",
                "-y",
                os.path.join(output_dir, "frame_%04d.jpg")
            ]
        
        # Execute frame extraction
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error extracting frames: {result.stderr}")
            return False, 0
        
        # Count extracted frames
        frame_files = glob.glob(os.path.join(output_dir, "frame_*.jpg"))
        actual_frame_count = len(frame_files)
        
        # Validate frame count
        expected_frame_count = int(duration * target_fps)
        tolerance = max(1, expected_frame_count * 0.02)  # 2% tolerance
        
        if abs(actual_frame_count - expected_frame_count) > tolerance:
            print(f"Warning: Frame count mismatch. Expected ~{expected_frame_count}, got {actual_frame_count}")
        else:
            print(f"✓ Extracted {actual_frame_count} frames (expected ~{expected_frame_count})")
        
        return True, actual_frame_count
    
    def extract_clip_frames_at_intervals(self, video_path, output_dir, start_time, end_time, target_fps):
        """
        Extract frames from a specific time range at target FPS intervals
        
        Args:
            video_path: Path to source video
            output_dir: Directory to save frames
            start_time: Start time (HH:MM:SS.S format)
            end_time: End time (HH:MM:SS.S format)
            target_fps: Target frames per second for extraction
            
        Returns:
            Tuple of (success: bool, frame_count: int)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert time strings to seconds for calculation
        def time_to_seconds(time_str):
            parts = time_str.split(':')
            seconds_parts = parts[-1].split('.')
            
            hours = int(parts[0]) if len(parts) > 2 else 0
            minutes = int(parts[-2] if len(parts) > 1 else parts[0])
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 10
        
        start_seconds = time_to_seconds(start_time)
        end_seconds = time_to_seconds(end_time)
        clip_duration = end_seconds - start_seconds
        
        print(f"  Clip duration: {clip_duration:.3f}s")
        print(f"  Target FPS: {target_fps}")
        
        # Use time-based selection for proper interval extraction within the clip
        frame_interval = 1.0 / target_fps
        print(f"  Strategy: Time-based selection every {frame_interval:.3f}s from clip")
        
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", start_time,
            "-to", end_time,
            "-vf", f"select='eq(n\\,0)+gte(t-prev_selected_t\\,{frame_interval})'",
            "-vsync", "0",
            "-start_number", "0",
            "-y",
            os.path.join(output_dir, "frame_%04d.jpg")
        ]
        
        # Execute frame extraction
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error extracting clip frames: {result.stderr}")
            return False, 0
        
        # Count extracted frames
        frame_files = glob.glob(os.path.join(output_dir, "frame_*.jpg"))
        actual_frame_count = len(frame_files)
        
        # Validate frame count
        expected_frame_count = int(clip_duration * target_fps)
        tolerance = max(1, expected_frame_count * 0.02)  # 2% tolerance
        
        if abs(actual_frame_count - expected_frame_count) > tolerance:
            print(f"Warning: Clip frame count mismatch. Expected ~{expected_frame_count}, got {actual_frame_count}")
        else:
            print(f"✓ Extracted {actual_frame_count} clip frames (expected ~{expected_frame_count})")
        
        return True, actual_frame_count
    
    def validate_frame_extraction(self, video_path, frames_dir, expected_fps):
        """
        Validate that extracted frames match expected count and timing
        
        Args:
            video_path: Path to source video
            frames_dir: Directory containing extracted frames
            expected_fps: Expected frames per second
            
        Returns:
            bool: True if validation passes
        """
        try:
            # Get video duration
            video_info = self.get_video_info(video_path)
            duration = video_info['duration']
            
            # Count extracted frames
            frame_files = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
            actual_frame_count = len(frame_files)
            
            # Calculate expected frame count
            expected_frame_count = int(duration * expected_fps)
            
            # Validate within tolerance
            tolerance = max(1, expected_frame_count * 0.02)  # 2% tolerance
            
            if abs(actual_frame_count - expected_frame_count) > tolerance:
                raise Exception(f"Frame count mismatch: expected ~{expected_frame_count}, got {actual_frame_count}")
            
            print(f"✓ Frame validation passed: {actual_frame_count} frames for {duration:.2f}s at {expected_fps} FPS")
            return True
            
        except Exception as e:
            print(f"✗ Frame validation failed: {e}")
            return False


if __name__ == "__main__":
    # Simple test functionality
    extractor = FrameExtractor()
    
    # Example usage
    video_path = "test_video.mp4"
    output_dir = "test_frames"
    target_fps = 30
    
    if os.path.exists(video_path):
        success, count = extractor.extract_frames_at_intervals(video_path, output_dir, target_fps)
        if success:
            extractor.validate_frame_extraction(video_path, output_dir, target_fps)
    else:
        print("No test video found. Create a test_video.mp4 file to test frame extraction.") 