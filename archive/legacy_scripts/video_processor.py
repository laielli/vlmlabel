#!/usr/bin/env python3
"""
Video Processing Core Module

This module provides the core video processing logic for creating FPS variants
and extracting clips while maintaining proper duration and timing relationships.
"""

import os
import subprocess
import shutil
import yaml
import cv2
from frame_extractor import FrameExtractor


class ProcessingError(Exception):
    """Base exception for processing errors"""
    pass


class ValidationError(ProcessingError):
    """Exception for validation failures"""
    pass


class VideoProcessor:
    """Core video processing engine"""
    
    def __init__(self, config=None):
        """
        Initialize video processor
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        self.frame_extractor = FrameExtractor()
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        try:
            info = self.frame_extractor.get_video_info(video_path)
            return info['duration']
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0
    
    def get_video_fps(self, video_path):
        """Get video FPS"""
        try:
            info = self.frame_extractor.get_video_info(video_path)
            return info['fps']
        except Exception as e:
            print(f"Error getting video FPS: {e}")
            return 30.0  # Default fallback
    
    def time_to_seconds(self, time_str):
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
    
    def create_fps_variant(self, source_path, target_path, source_fps, target_fps):
        """
        Create FPS variant maintaining duration using proper frame selection
        
        Args:
            source_path: Path to source video
            target_path: Path for output video
            source_fps: Source video frame rate
            target_fps: Target frame rate
            
        Returns:
            bool: Success status
        """
        print(f"Creating FPS variant: {source_fps:.1f} -> {target_fps} FPS")
        
        # Create directory for target
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # If target FPS is same as source, just copy
        if abs(source_fps - target_fps) < 0.01:
            print("  Same FPS - copying file")
            shutil.copy2(source_path, target_path)
            return True
        
        # Always use the fps filter to maintain duration properly
        # The fps filter handles both upsampling (frame duplication) and downsampling (frame dropping)
        # while preserving the original video duration
        cmd = [
            "ffmpeg", "-i", source_path,
            "-vf", f"fps={target_fps}",  # This maintains duration by duplicating or dropping frames as needed
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",  # Copy audio unchanged
            "-y", target_path
        ]
        
        print(f"  Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating FPS variant: {result.stderr}")
            return False
        
        # Validate duration preservation
        source_duration = self.get_video_duration(source_path)
        target_duration = self.get_video_duration(target_path)
        duration_diff = abs(source_duration - target_duration)
        
        if duration_diff > 0.1:  # Allow 0.1s tolerance
            print(f"Warning: Duration changed by {duration_diff:.2f}s ({source_duration:.2f}s -> {target_duration:.2f}s)")
        else:
            print(f"✓ Duration preserved: {target_duration:.2f}s")
        
        return True
    
    def extract_clip(self, source_path, clip_path, start_time, end_time):
        """
        Extract clip from source video
        
        Args:
            source_path: Path to source video
            clip_path: Path for output clip
            start_time: Start time (string format)
            end_time: End time (string format)
            
        Returns:
            bool: Success status
        """
        print(f"Extracting clip: {start_time} to {end_time}")
        
        # Create directory for clip
        os.makedirs(os.path.dirname(clip_path), exist_ok=True)
        
        # Extract clip with precise timing
        cmd = [
            "ffmpeg", "-i", source_path,
            "-ss", start_time,
            "-to", end_time,
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",  # Copy audio unchanged
            "-avoid_negative_ts", "make_zero",  # Handle timing issues
            "-y", clip_path
        ]
        
        print(f"  Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error extracting clip: {result.stderr}")
            return False
        
        # Validate clip duration
        expected_duration = self.time_to_seconds(end_time) - self.time_to_seconds(start_time)
        actual_duration = self.get_video_duration(clip_path)
        duration_diff = abs(expected_duration - actual_duration)
        
        if duration_diff > 0.2:  # Allow 0.2s tolerance for clips
            print(f"Warning: Clip duration mismatch. Expected {expected_duration:.2f}s, got {actual_duration:.2f}s")
        else:
            print(f"✓ Clip extracted: {actual_duration:.2f}s")
        
        return True
    
    def process_full_video_variants(self, video_config, output_dir):
        """
        Process full video variants at different FPS rates
        
        Args:
            video_config: Video configuration dictionary
            output_dir: Base output directory
            
        Returns:
            dict: Mapping of variant names to success status
        """
        source_video = video_config.get('source_video')
        fps_variants = video_config.get('fps_variants', [])
        video_id = video_config.get('id')
        
        if not os.path.exists(source_video):
            raise ProcessingError(f"Source video not found: {source_video}")
        
        # Get source video FPS
        source_fps = self.get_video_fps(source_video)
        print(f"Source video FPS: {source_fps:.3f}")
        
        results = {}
        
        # Process each FPS variant
        for target_fps in fps_variants:
            variant_key = f"full_{target_fps}"
            variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
            
            print(f"\nProcessing variant: {variant_key}")
            
            # Create FPS variant
            success = self.create_fps_variant(source_video, variant_path, source_fps, target_fps)
            results[variant_key] = success
            
            if success:
                # Extract frames from the properly created FPS variant
                frames_dir = os.path.join(output_dir, "frames", variant_key)
                frame_success, frame_count = self.frame_extractor.extract_frames_at_intervals(
                    variant_path, frames_dir, target_fps)
                
                if frame_success:
                    print(f"✓ Variant {variant_key} completed successfully")
                else:
                    print(f"✗ Frame extraction failed for {variant_key}")
                    results[variant_key] = False
            else:
                print(f"✗ Variant {variant_key} failed")
        
        return results
    
    def process_clip_variants(self, video_config, output_dir):
        """
        Process clip variants at different FPS rates
        
        Args:
            video_config: Video configuration dictionary
            output_dir: Base output directory
            
        Returns:
            dict: Mapping of clip variant names to success status
        """
        source_video = video_config.get('source_video')
        clips = video_config.get('clips', [])
        video_id = video_config.get('id')
        
        if not os.path.exists(source_video):
            raise ProcessingError(f"Source video not found: {source_video}")
        
        results = {}
        
        # Process each clip
        for clip in clips:
            clip_name = clip.get('name')
            start_time = clip.get('start')
            end_time = clip.get('end')
            fps_list = clip.get('fps', [])
            
            if not all([clip_name, start_time, end_time, fps_list]):
                print(f"Skipping clip with missing configuration: {clip}")
                continue
            
            print(f"\nProcessing clip: {clip_name}")
            
            # First extract the clip at source quality
            temp_clip_path = os.path.join(output_dir, f"temp_{clip_name}.mp4")
            clip_success = self.extract_clip(source_video, temp_clip_path, start_time, end_time)
            
            if not clip_success:
                print(f"✗ Failed to extract base clip: {clip_name}")
                continue
            
            # Get clip FPS (should match source)
            clip_fps = self.get_video_fps(temp_clip_path)
            
            # Process each FPS variant of the clip
            for target_fps in fps_list:
                variant_key = f"{clip_name}_{target_fps}"
                variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
                
                print(f"  Creating {variant_key} variant")
                
                # Create FPS variant from the extracted clip
                success = self.create_fps_variant(temp_clip_path, variant_path, clip_fps, target_fps)
                results[variant_key] = success
                
                if success:
                    # Extract frames from the properly created FPS variant
                    frames_dir = os.path.join(output_dir, "frames", variant_key)
                    frame_success, frame_count = self.frame_extractor.extract_frames_at_intervals(
                        variant_path, frames_dir, target_fps)
                    
                    if frame_success:
                        print(f"  ✓ Clip variant {variant_key} completed successfully")
                    else:
                        print(f"  ✗ Frame extraction failed for {variant_key}")
                        results[variant_key] = False
                else:
                    print(f"  ✗ Clip variant {variant_key} failed")
            
            # Clean up temporary clip
            if os.path.exists(temp_clip_path):
                os.remove(temp_clip_path)
        
        return results
    
    def cleanup_partial_processing(self, video_id, variant_key, output_dir):
        """
        Clean up partial files if processing fails
        
        Args:
            video_id: Video identifier
            variant_key: Variant key (e.g., 'full_30', 'clip_001_5')
            output_dir: Output directory
        """
        variant_video = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
        frames_dir = os.path.join(output_dir, "frames", variant_key)
        
        # Remove partial files
        if os.path.exists(variant_video):
            os.remove(variant_video)
            print(f"Removed partial video: {variant_video}")
        
        if os.path.exists(frames_dir):
            shutil.rmtree(frames_dir)
            print(f"Removed partial frames: {frames_dir}")
    
    def save_processing_info(self, video_config, output_dir, processing_results):
        """
        Save processing information and FPS mappings
        
        Args:
            video_config: Video configuration
            output_dir: Output directory
            processing_results: Results from processing
        """
        video_id = video_config.get('id')
        source_fps = self.get_video_fps(video_config.get('source_video'))
        
        # Create processing info
        processing_info = {
            'video_id': video_id,
            'source_video': video_config.get('source_video'),
            'source_fps': source_fps,
            'processed_variants': {},
            'processing_results': processing_results
        }
        
        # Add variant information
        for variant_key, success in processing_results.items():
            if success:
                variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
                if os.path.exists(variant_path):
                    variant_fps = self.get_video_fps(variant_path)
                    variant_duration = self.get_video_duration(variant_path)
                    
                    processing_info['processed_variants'][variant_key] = {
                        'fps': variant_fps,
                        'duration': variant_duration,
                        'path': variant_path
                    }
        
        # Save to file
        info_file = os.path.join(output_dir, f"{video_id}_processing_info.yaml")
        with open(info_file, 'w') as f:
            yaml.dump(processing_info, f, default_flow_style=False)
        
        print(f"✓ Saved processing info to {info_file}")


def process_with_fallback(primary_method, fallback_method, *args, **kwargs):
    """
    Try primary method, fall back to alternative if it fails
    
    Args:
        primary_method: Primary processing method
        fallback_method: Fallback processing method
        *args: Arguments to pass to methods
        **kwargs: Keyword arguments to pass to methods
        
    Returns:
        Result from successful method
    """
    try:
        return primary_method(*args, **kwargs)
    except ProcessingError as e:
        print(f"Primary method failed: {e}, trying fallback")
        return fallback_method(*args, **kwargs) 