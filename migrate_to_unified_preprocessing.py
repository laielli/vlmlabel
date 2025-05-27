#!/usr/bin/env python3
"""
Migration Script for Unified Preprocessing System

This script helps users migrate from the old preprocessing scripts
(preprocess_variants.py, preprocess_clips.py, extract_frames.py)
to the new unified preprocess_videos.py system.

Features:
- Validates existing processed files
- Identifies files that need reprocessing with new system
- Optionally cleans up old processing artifacts
- Provides migration recommendations

Usage:
  python migrate_to_unified_preprocessing.py [options]

Options:
  --analyze         Analyze current setup and provide recommendations
  --reprocess       Reprocess all videos with new unified system
  --cleanup         Remove old processing artifacts after validation
  --video-id ID     Process specific video only
  --help            Show this help message
"""

import os
import sys
import getopt
import yaml
import glob
import shutil
from datetime import datetime
from video_processor import VideoProcessor
from frame_extractor import FrameExtractor


def print_help():
    """Print help message"""
    print(__doc__)


def load_config():
    """Load configuration from YAML file"""
    config_file = "config.yaml"
    if not os.path.exists(config_file):
        print(f"Error: Configuration file {config_file} not found")
        return None
    
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)


def analyze_video_processing(video_config):
    """
    Analyze a video's current processing state
    
    Args:
        video_config: Video configuration dictionary
        
    Returns:
        dict: Analysis results
    """
    video_id = video_config.get('id')
    source_video = video_config.get('source_video')
    fps_variants = video_config.get('fps_variants', [])
    clips = video_config.get('clips', [])
    
    analysis = {
        'video_id': video_id,
        'source_exists': os.path.exists(source_video) if source_video else False,
        'output_dir': os.path.join("static", "videos", video_id),
        'has_processing_info': False,
        'full_variants': {},
        'clip_variants': {},
        'frame_directories': {},
        'issues': [],
        'recommendations': []
    }
    
    output_dir = analysis['output_dir']
    
    if not os.path.exists(output_dir):
        analysis['issues'].append("Output directory does not exist")
        analysis['recommendations'].append("Run preprocess_videos.py to create video variants")
        return analysis
    
    # Check for new processing info file
    info_file = os.path.join(output_dir, f"{video_id}_processing_info.yaml")
    analysis['has_processing_info'] = os.path.exists(info_file)
    
    if not analysis['has_processing_info']:
        analysis['recommendations'].append("Reprocess with unified system to generate processing metadata")
    
    # Check full video variants
    for fps in fps_variants:
        variant_key = f"full_{fps}"
        variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
        frames_dir = os.path.join(output_dir, "frames", variant_key)
        
        analysis['full_variants'][variant_key] = {
            'video_exists': os.path.exists(variant_path),
            'frames_exist': os.path.exists(frames_dir),
            'frame_count': len(glob.glob(os.path.join(frames_dir, "frame_*.jpg"))) if os.path.exists(frames_dir) else 0
        }
        
        if not os.path.exists(variant_path):
            analysis['issues'].append(f"Missing video variant: {variant_key}")
        
        if not os.path.exists(frames_dir):
            analysis['issues'].append(f"Missing frames directory: {variant_key}")
    
    # Check clip variants
    for clip in clips:
        clip_name = clip.get('name')
        fps_list = clip.get('fps', [])
        
        for fps in fps_list:
            variant_key = f"{clip_name}_{fps}"
            variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
            frames_dir = os.path.join(output_dir, "frames", variant_key)
            
            analysis['clip_variants'][variant_key] = {
                'video_exists': os.path.exists(variant_path),
                'frames_exist': os.path.exists(frames_dir),
                'frame_count': len(glob.glob(os.path.join(frames_dir, "frame_*.jpg"))) if os.path.exists(frames_dir) else 0
            }
            
            if not os.path.exists(variant_path):
                analysis['issues'].append(f"Missing clip variant: {variant_key}")
            
            if not os.path.exists(frames_dir):
                analysis['issues'].append(f"Missing frames directory: {variant_key}")
    
    # Check for legacy files
    legacy_files = []
    
    # Check for old fps_info.yaml (from preprocess_variants.py)
    old_fps_info = os.path.join(output_dir, "fps_info.yaml")
    if os.path.exists(old_fps_info):
        legacy_files.append(old_fps_info)
    
    # Check for any temporary files
    temp_files = glob.glob(os.path.join(output_dir, "*__tmp_*.mp4"))
    legacy_files.extend(temp_files)
    
    if legacy_files:
        analysis['legacy_files'] = legacy_files
        analysis['recommendations'].append("Clean up legacy files after migration")
    
    # Frame analysis recommendations
    processor = VideoProcessor()
    extractor = FrameExtractor()
    
    try:
        if analysis['source_exists']:
            source_duration = processor.get_video_duration(source_video)
            
            # Check frame counts for accuracy
            for variant_key, variant_info in analysis['full_variants'].items():
                if variant_info['frames_exist'] and variant_info['frame_count'] > 0:
                    target_fps = int(variant_key.split('_')[1])
                    expected_frames = int(source_duration * target_fps)
                    actual_frames = variant_info['frame_count']
                    
                    # Check for duplicate frame indicators (too many frames)
                    if actual_frames > expected_frames * 1.1:  # 10% tolerance
                        analysis['issues'].append(f"Possible duplicate frames in {variant_key}: {actual_frames} frames (expected ~{expected_frames})")
                        analysis['recommendations'].append(f"Reprocess {variant_key} to eliminate duplicate frames")
    
    except Exception as e:
        analysis['issues'].append(f"Error analyzing source video: {e}")
    
    return analysis


def print_analysis_report(analysis):
    """Print a formatted analysis report"""
    video_id = analysis['video_id']
    
    print(f"\n{'='*60}")
    print(f"Analysis Report: {video_id}")
    print(f"{'='*60}")
    
    # Source status
    if analysis['source_exists']:
        print("✓ Source video found")
    else:
        print("✗ Source video missing")
    
    # Processing info status
    if analysis['has_processing_info']:
        print("✓ New processing metadata found")
    else:
        print("⚠ No new processing metadata (needs migration)")
    
    # Variants status
    print(f"\nFull Video Variants:")
    for variant_key, info in analysis['full_variants'].items():
        status = "✓" if info['video_exists'] and info['frames_exist'] else "✗"
        frame_info = f"({info['frame_count']} frames)" if info['frames_exist'] else "(no frames)"
        print(f"  {status} {variant_key} {frame_info}")
    
    if analysis['clip_variants']:
        print(f"\nClip Variants:")
        for variant_key, info in analysis['clip_variants'].items():
            status = "✓" if info['video_exists'] and info['frames_exist'] else "✗"
            frame_info = f"({info['frame_count']} frames)" if info['frames_exist'] else "(no frames)"
            print(f"  {status} {variant_key} {frame_info}")
    
    # Issues
    if analysis['issues']:
        print(f"\n⚠ Issues Found:")
        for issue in analysis['issues']:
            print(f"  - {issue}")
    
    # Recommendations
    if analysis['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")
    
    # Legacy files
    if 'legacy_files' in analysis:
        print(f"\n🗂 Legacy Files Found:")
        for file in analysis['legacy_files']:
            print(f"  - {file}")


def cleanup_legacy_files(video_id, analysis, dry_run=True):
    """
    Clean up legacy files from old preprocessing
    
    Args:
        video_id: Video identifier
        analysis: Analysis results
        dry_run: If True, only show what would be deleted
    """
    if 'legacy_files' not in analysis:
        print(f"No legacy files found for {video_id}")
        return
    
    print(f"\n{'Cleaning up' if not dry_run else 'Would clean up'} legacy files for {video_id}:")
    
    for file_path in analysis['legacy_files']:
        if os.path.exists(file_path):
            print(f"  {'Removing' if not dry_run else 'Would remove'}: {file_path}")
            if not dry_run:
                os.remove(file_path)
        else:
            print(f"  Already removed: {file_path}")


def main():
    """Main function"""
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "harci:", 
                                   ["help", "analyze", "reprocess", "cleanup", "video-id="])
    except getopt.GetoptError as e:
        print(f"Error: {e}")
        print_help()
        sys.exit(2)
    
    # Default parameters
    target_video_id = None
    mode_analyze = False
    mode_reprocess = False
    mode_cleanup = False
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-a", "--analyze"):
            mode_analyze = True
        elif opt in ("-r", "--reprocess"):
            mode_reprocess = True
        elif opt in ("-c", "--cleanup"):
            mode_cleanup = True
        elif opt in ("-i", "--video-id"):
            target_video_id = arg
    
    # Default to analyze mode if no mode specified
    if not any([mode_analyze, mode_reprocess, mode_cleanup]):
        mode_analyze = True
    
    print("VLMLABEL Migration Tool")
    print("======================")
    print("Migrating to unified preprocessing system\n")
    
    # Load configuration
    config = load_config()
    if not config:
        sys.exit(1)
    
    videos = config.get('videos', [])
    if target_video_id:
        videos = [v for v in videos if v.get('id') == target_video_id]
        if not videos:
            print(f"Error: Video ID '{target_video_id}' not found in config")
            sys.exit(1)
    
    # Analyze current state
    analyses = []
    for video_config in videos:
        analysis = analyze_video_processing(video_config)
        analyses.append(analysis)
        
        if mode_analyze:
            print_analysis_report(analysis)
    
    # Summary
    total_videos = len(analyses)
    videos_with_issues = len([a for a in analyses if a['issues']])
    videos_needing_migration = len([a for a in analyses if not a['has_processing_info']])
    
    print(f"\n{'='*60}")
    print(f"MIGRATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total videos: {total_videos}")
    print(f"Videos with issues: {videos_with_issues}")
    print(f"Videos needing migration: {videos_needing_migration}")
    
    # Reprocessing
    if mode_reprocess:
        print(f"\nReprocessing videos with unified system...")
        import subprocess
        
        cmd = ["python", "preprocess_videos.py", "--force"]
        if target_video_id:
            cmd.extend(["--video-id", target_video_id])
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✓ Reprocessing completed successfully")
        else:
            print("✗ Reprocessing failed")
            sys.exit(1)
    
    # Cleanup
    if mode_cleanup:
        print(f"\nCleaning up legacy files...")
        for analysis in analyses:
            cleanup_legacy_files(analysis['video_id'], analysis, dry_run=False)
    
    # Final recommendations
    if mode_analyze and not mode_reprocess:
        print(f"\n💡 Next Steps:")
        if videos_needing_migration > 0:
            print(f"  1. Run: python migrate_to_unified_preprocessing.py --reprocess")
        if videos_with_issues > 0:
            print(f"  2. Address the issues listed above")
        print(f"  3. Test the new system: python test_preprocessing.py")
        print(f"  4. Clean up legacy files: python migrate_to_unified_preprocessing.py --cleanup")


if __name__ == "__main__":
    main() 