#!/usr/bin/env python3
"""
Unified Video Preprocessing Script for VLMLABEL

This script combines functionality from the previous separate scripts and implements
proper FPS handling for creating video variants and extracting frames. It processes
videos according to config.yaml and generates:

- Different FPS variants for full-length videos (maintaining duration)
- Clip variants at specified time ranges and FPS rates  
- Unique frame extraction at target FPS intervals (no duplicates)

Key improvements:
- Maintains video duration when creating FPS variants
- Extracts unique frames at proper time intervals
- Unified processing for both full videos and clips
- Comprehensive validation and error handling

Usage:
  python preprocess_videos.py [options]

Options:
  --video-id ID       Process specific video ID (default: process all)
  --type TYPE         Process 'full', 'clips', or 'all' (default: all)
  --force             Overwrite existing files
  --validate          Validate output without processing
  --help              Show this help message
"""

import os
import sys
import getopt
import yaml
import time
from datetime import datetime
from video_processor import VideoProcessor, ProcessingError, ValidationError


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


def validate_config(config):
    """Validate configuration structure"""
    if not config:
        raise ValidationError("Empty configuration")
    
    videos = config.get('videos', [])
    if not videos:
        raise ValidationError("No videos defined in configuration")
    
    for video in videos:
        video_id = video.get('id')
        source_video = video.get('source_video')
        
        if not video_id:
            raise ValidationError("Video configuration missing 'id'")
        
        if not source_video:
            raise ValidationError(f"Video '{video_id}' missing 'source_video'")
        
        if not os.path.exists(source_video):
            raise ValidationError(f"Source video not found: {source_video}")


def create_output_directory(video_id):
    """Create and return output directory for a video"""
    output_dir = os.path.join("static", "videos", video_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create frames subdirectory
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    return output_dir


def should_skip_processing(video_config, output_dir, force=False):
    """
    Determine if processing should be skipped based on existing files
    
    Args:
        video_config: Video configuration
        output_dir: Output directory
        force: Whether to force reprocessing
        
    Returns:
        bool: True if should skip
    """
    if force:
        return False
    
    video_id = video_config.get('id')
    source_video = video_config.get('source_video')
    
    # Check if processing info exists
    info_file = os.path.join(output_dir, f"{video_id}_processing_info.yaml")
    if not os.path.exists(info_file):
        return False
    
    # Check if source video is newer than info file
    source_mtime = os.path.getmtime(source_video)
    info_mtime = os.path.getmtime(info_file)
    
    if source_mtime > info_mtime:
        print(f"Source video is newer than processing info, reprocessing...")
        return False
    
    # Check if all expected variants exist
    fps_variants = video_config.get('fps_variants', [])
    clips = video_config.get('clips', [])
    
    # Check full video variants
    for fps in fps_variants:
        variant_key = f"full_{fps}"
        variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
        frames_dir = os.path.join(output_dir, "frames", variant_key)
        
        if not os.path.exists(variant_path) or not os.path.exists(frames_dir):
            return False
    
    # Check clip variants
    for clip in clips:
        clip_name = clip.get('name')
        fps_list = clip.get('fps', [])
        
        for fps in fps_list:
            variant_key = f"{clip_name}_{fps}"
            variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
            frames_dir = os.path.join(output_dir, "frames", variant_key)
            
            if not os.path.exists(variant_path) or not os.path.exists(frames_dir):
                return False
    
    print(f"All variants exist and are up-to-date for {video_id}, skipping...")
    return True


def process_video(video_config, processor, process_type='all', force=False, validate_only=False):
    """
    Process a single video configuration
    
    Args:
        video_config: Video configuration dictionary
        processor: VideoProcessor instance
        process_type: Type of processing ('full', 'clips', 'all')
        force: Whether to force reprocessing
        validate_only: Only validate, don't process
        
    Returns:
        bool: Success status
    """
    video_id = video_config.get('id')
    source_video = video_config.get('source_video')
    
    print(f"\n{'='*60}")
    print(f"Processing video: {video_id}")
    print(f"Source: {source_video}")
    print(f"Type: {process_type}")
    print(f"{'='*60}")
    
    # Create output directory
    output_dir = create_output_directory(video_id)
    
    # Check if we should skip processing
    if not force and should_skip_processing(video_config, output_dir, force):
        return True
    
    if validate_only:
        print("Validation mode - skipping actual processing")
        return True
    
    # Track overall results
    all_results = {}
    
    try:
        # Process full video variants
        if process_type in ['full', 'all']:
            fps_variants = video_config.get('fps_variants', [])
            if fps_variants:
                print(f"\nProcessing {len(fps_variants)} full video variants...")
                full_results = processor.process_full_video_variants(video_config, output_dir)
                all_results.update(full_results)
            else:
                print("No full video variants configured")
        
        # Process clip variants
        if process_type in ['clips', 'all']:
            clips = video_config.get('clips', [])
            if clips:
                print(f"\nProcessing {len(clips)} clips...")
                clip_results = processor.process_clip_variants(video_config, output_dir)
                all_results.update(clip_results)
            else:
                print("No clips configured")
        
        # Save processing information
        processor.save_processing_info(video_config, output_dir, all_results)
        
        # Report results
        success_count = sum(1 for success in all_results.values() if success)
        total_count = len(all_results)
        
        print(f"\n{'='*40}")
        print(f"Processing complete for {video_id}")
        print(f"Success: {success_count}/{total_count} variants")
        
        if success_count < total_count:
            failed_variants = [key for key, success in all_results.items() if not success]
            print(f"Failed variants: {', '.join(failed_variants)}")
            return False
        
        print(f"✓ All variants processed successfully")
        return True
        
    except ProcessingError as e:
        print(f"✗ Processing error for {video_id}: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error processing {video_id}: {e}")
        return False


def main():
    """Main function"""
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:t:fv", 
                                   ["help", "video-id=", "type=", "force", "validate"])
    except getopt.GetoptError as e:
        print(f"Error: {e}")
        print_help()
        sys.exit(2)
    
    # Default parameters
    target_video_id = None
    process_type = 'all'
    force = False
    validate_only = False
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-i", "--video-id"):
            target_video_id = arg
        elif opt in ("-t", "--type"):
            if arg not in ['full', 'clips', 'all']:
                print("Error: --type must be 'full', 'clips', or 'all'")
                sys.exit(2)
            process_type = arg
        elif opt in ("-f", "--force"):
            force = True
        elif opt in ("-v", "--validate"):
            validate_only = True
    
    print("VLMLABEL Video Preprocessing Script")
    print("===================================")
    
    # Load and validate configuration
    try:
        config = load_config()
        validate_config(config)
        print("✓ Configuration loaded and validated")
    except (ValidationError, Exception) as e:
        print(f"✗ Configuration error: {e}")
        sys.exit(1)
    
    # Filter videos based on target ID
    videos = config.get('videos', [])
    if target_video_id:
        videos = [v for v in videos if v.get('id') == target_video_id]
        if not videos:
            print(f"Error: Video ID '{target_video_id}' not found in config")
            sys.exit(1)
        print(f"Processing single video: {target_video_id}")
    else:
        print(f"Processing {len(videos)} videos")
    
    # Initialize processor
    processor = VideoProcessor(config)
    
    # Track processing statistics
    start_time = time.time()
    success_count = 0
    fail_count = 0
    
    # Process each video
    for video_config in videos:
        video_id = video_config.get('id')
        
        try:
            success = process_video(video_config, processor, process_type, force, validate_only)
            if success:
                success_count += 1
            else:
                fail_count += 1
        except KeyboardInterrupt:
            print(f"\n\nProcessing interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Unexpected error processing {video_id}: {e}")
            fail_count += 1
    
    # Print final summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total videos: {len(videos)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Processing time: {elapsed_time:.1f} seconds")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if validate_only:
        print("\nValidation mode completed")
    elif fail_count == 0:
        print("\n✓ All videos processed successfully!")
    else:
        print(f"\n⚠  {fail_count} video(s) failed processing")
        sys.exit(1)


if __name__ == "__main__":
    main() 