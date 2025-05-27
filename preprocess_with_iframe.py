#!/usr/bin/env python3
"""
VLM Label Preprocessing with I-Frame Consistency

This script processes videos using I-frame-only re-encoding for consistent frame extraction.
It replaces the existing preprocessing scripts with a more reliable approach.

Usage:
  python preprocess_with_iframe.py [--video-id VIDEO_ID] [--force]

Options:
  --video-id ID   Process only this video ID (otherwise process all in config)
  --force         Force re-processing even if outputs already exist
  --help          Show this help message
"""

import os
import sys
import argparse
import yaml
from iframe_video_processor import IFrameVideoProcessor


def print_help():
    """Print help message"""
    print(__doc__)


def check_prerequisites():
    """Check if required tools are available"""
    import subprocess
    
    # Check for ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: ffmpeg not found. Please install ffmpeg and ensure it's in your PATH.")
        return False
    
    # Check for ffprobe
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: ffprobe not found. Please install ffmpeg (includes ffprobe).")
        return False
    
    print("✅ Prerequisites check passed")
    return True


def load_config(config_file="config.yaml"):
    """Load configuration from YAML file"""
    if not os.path.exists(config_file):
        print(f"❌ Error: Config file '{config_file}' not found")
        return None
    
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        print(f"✅ Loaded configuration from {config_file}")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None


def validate_video_config(video_config):
    """Validate a video configuration"""
    required_fields = ['id', 'source_video']
    
    for field in required_fields:
        if field not in video_config:
            print(f"❌ Error: Video config missing required field '{field}'")
            return False
    
    # Check if source video exists
    source_video = video_config['source_video']
    if not os.path.exists(source_video):
        print(f"❌ Error: Source video not found: {source_video}")
        return False
    
    return True


def check_existing_outputs(video_id, output_dir, force=False):
    """Check if outputs already exist and whether to skip processing"""
    if force:
        return False  # Don't skip if force is enabled
    
    # Check if any variant files exist
    if os.path.exists(output_dir):
        variant_files = [f for f in os.listdir(output_dir) 
                        if f.startswith(f"{video_id}__") and f.endswith(".mp4")]
        
        if variant_files:
            print(f"⚠️  Output files already exist for {video_id}:")
            for file in variant_files[:5]:  # Show first 5
                print(f"   - {file}")
            if len(variant_files) > 5:
                print(f"   ... and {len(variant_files) - 5} more")
            
            return True  # Skip processing
    
    return False  # Proceed with processing


def process_single_video(processor, video_config, force=False):
    """Process a single video configuration"""
    video_id = video_config.get('id')
    
    print(f"\n{'='*60}")
    print(f"🎯 PROCESSING VIDEO: {video_id}")
    print(f"{'='*60}")
    
    # Validate configuration
    if not validate_video_config(video_config):
        return False
    
    # Set up output directory
    output_dir = os.path.join("static", "videos", video_id)
    
    # Check if outputs already exist
    if check_existing_outputs(video_id, output_dir, force):
        response = input(f"Skip processing {video_id}? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            print(f"⏭️  Skipping {video_id}")
            return True
    
    # Process the video
    try:
        results = processor.process_video_with_iframe_preprocessing(video_config, output_dir)
        
        if results['success']:
            print(f"\n✅ Successfully processed {video_id}")
            
            # Print summary
            variant_count = len([v for v in results['variants'].values() if v['success']])
            clip_count = len([c for c in results['clips'].values() if c['success']])
            
            print(f"   📹 {variant_count} video variants created")
            if clip_count > 0:
                print(f"   🎬 {clip_count} clips processed")
            
            return True
        else:
            print(f"\n❌ Processing failed for {video_id}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error processing {video_id}: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="VLM Label Preprocessing with I-Frame Consistency",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--video-id", help="Process only this video ID")
    parser.add_argument("--force", action="store_true", 
                       help="Force re-processing even if outputs exist")
    parser.add_argument("--config", default="config.yaml",
                       help="Configuration file path (default: config.yaml)")
    
    args = parser.parse_args()
    
    print("🚀 VLM Label Preprocessing with I-Frame Consistency")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        return 1
    
    # Create processor
    processor = IFrameVideoProcessor(config)
    
    # Get videos to process
    videos_to_process = []
    
    if args.video_id:
        # Process specific video
        video_found = False
        for video_config in config.get('videos', []):
            if video_config.get('id') == args.video_id:
                videos_to_process.append(video_config)
                video_found = True
                break
        
        if not video_found:
            print(f"❌ Error: Video ID '{args.video_id}' not found in configuration")
            return 1
    else:
        # Process all videos
        videos_to_process = config.get('videos', [])
    
    if not videos_to_process:
        print("❌ Error: No videos to process")
        return 1
    
    print(f"📋 Found {len(videos_to_process)} video(s) to process")
    
    # Process videos
    successful = 0
    failed = 0
    
    for video_config in videos_to_process:
        if process_single_video(processor, video_config, args.force):
            successful += 1
        else:
            failed += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📊 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Total: {successful + failed}")
    
    if failed == 0:
        print("\n🎉 All videos processed successfully!")
        print("📁 Check the static/videos/ directory for outputs")
        return 0
    else:
        print(f"\n⚠️  {failed} video(s) failed processing")
        return 1


if __name__ == "__main__":
    exit(main()) 