#!/usr/bin/env python3
"""
I-Frame Video Processor for VLM Label

This module implements consistent frame extraction by re-encoding videos to I-frame-only
format first, then performing all clipping and FPS reduction operations on the I-frame video.

This ensures deterministic and perfectly aligned frame extraction across all FPS variants.
"""

import os
import subprocess
import shutil
import yaml
import cv2
import time
from pathlib import Path
from frame_extractor import FrameExtractor


class IFrameVideoProcessor:
    """Video processor that uses I-frame-only re-encoding for consistent frame extraction"""
    
    def __init__(self, config=None):
        """
        Initialize I-frame video processor
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        self.frame_extractor = FrameExtractor()
    
    def get_video_info(self, video_path):
        """Get video information using ffprobe"""
        command = [
            "ffprobe", "-v", "quiet", "-print_format", "json", 
            "-show_format", "-show_streams", video_path
        ]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            import json
            info = json.loads(result.stdout)
            
            video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
            duration = float(info['format']['duration'])
            fps = eval(video_stream['r_frame_rate'])  # e.g., "60/1" -> 60.0
            
            return {
                'duration': duration,
                'fps': fps,
                'width': video_stream['width'],
                'height': video_stream['height'],
                'codec': video_stream['codec_name']
            }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def extract_frame_timestamps(self, video_path):
        """
        Extract exact timestamps for all frames from video
        
        Uses ffmpeg to get precise frame timestamps to avoid precision errors
        when calculating timestamps from frame indices.
        
        Args:
            video_path: Path to video file
            
        Returns:
            list: List of timestamps in seconds for each frame
        """
        print(f"🔄 Extracting frame timestamps from {video_path}")
        
        # Use ffmpeg to extract frame timestamps
        # This gets the exact presentation timestamp for each frame
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", "showinfo",
            "-an", "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            # Parse timestamps from stderr (where showinfo outputs)
            timestamps = []
            lines = result.stderr.split('\n')
            
            for line in lines:
                if 'showinfo' in line and 'pts_time:' in line:
                    # Extract pts_time value
                    # Format: [Parsed_showinfo_0 @ 0x...] n:0 pts:0 pts_time:0.000000 ...
                    try:
                        pts_time_start = line.find('pts_time:') + 9
                        pts_time_end = line.find(' ', pts_time_start)
                        if pts_time_end == -1:
                            pts_time_end = len(line)
                        
                        timestamp = float(line[pts_time_start:pts_time_end])
                        timestamps.append(timestamp)
                    except (ValueError, IndexError):
                        continue
            
            print(f"✅ Extracted {len(timestamps)} frame timestamps")
            return timestamps
            
        except Exception as e:
            print(f"❌ Error extracting frame timestamps: {e}")
            return []
    
    def save_frame_timestamps(self, timestamps, frames_dir, variant_key):
        """
        Save frame timestamps to JSON file alongside frames
        
        Args:
            timestamps: List of timestamps in seconds
            frames_dir: Directory where frames are stored
            variant_key: Variant identifier (e.g., 'full_30', 'clip_001_10')
        """
        import json
        
        # Create frame-to-timestamp mapping
        frame_mapping = {}
        for i, timestamp in enumerate(timestamps):
            frame_filename = f"frame_{i:04d}.jpg"  # Match frame extractor naming
            frame_mapping[frame_filename] = {
                'frame_index': i,
                'timestamp': timestamp,
                'frame_number': i + 1  # 1-based frame numbering for UI
            }
        
        # Save to JSON file
        timestamp_file = os.path.join(frames_dir, "frame_timestamps.json")
        
        try:
            with open(timestamp_file, 'w') as f:
                json.dump({
                    'variant': variant_key,
                    'total_frames': len(timestamps),
                    'frame_mapping': frame_mapping
                }, f, indent=2)
            
            print(f"✅ Saved frame timestamps to {timestamp_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving frame timestamps: {e}")
            return False
    
    def create_iframe_only_video(self, source_path, iframe_path):
        """
        Re-encode video to I-frame-only format for consistent frame extraction
        
        Uses the exact command from consistent_frame_extraction.md:
        ffmpeg -i input.mp4 -g 1 -keyint_min 1 -sc_threshold 0 
               -x264opts "keyint=1:min-keyint=1:no-scenecut" 
               -c:v libx264 -preset fast -crf 18 i_frames_only.mp4
        
        Args:
            source_path: Path to source video
            iframe_path: Path for I-frame-only output video
            
        Returns:
            bool: Success status
        """
        print(f"🔄 Creating I-frame-only video: {source_path} -> {iframe_path}")
        
        # Create directory for output
        os.makedirs(os.path.dirname(iframe_path), exist_ok=True)
        
        # I-frame-only re-encoding command
        cmd = [
            "ffmpeg", "-y", "-i", source_path,
            "-g", "1",
            "-keyint_min", "1", 
            "-sc_threshold", "0",
            "-x264opts", "keyint=1:min-keyint=1:no-scenecut",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            iframe_path
        ]
        
        print(f"  Command: {' '.join(cmd)}")
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            end_time = time.time()
            print(f"✅ I-frame-only video created in {end_time - start_time:.2f} seconds")
            
            # Validate the output
            if os.path.exists(iframe_path):
                iframe_info = self.get_video_info(iframe_path)
                source_info = self.get_video_info(source_path)
                
                if iframe_info and source_info:
                    duration_diff = abs(iframe_info['duration'] - source_info['duration'])
                    if duration_diff > 0.1:  # Allow 0.1s tolerance
                        print(f"⚠️  Duration changed by {duration_diff:.2f}s")
                    else:
                        print(f"✅ Duration preserved: {iframe_info['duration']:.2f}s")
                
                return True
            else:
                print("❌ I-frame-only video file not created")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating I-frame-only video: {e}")
            print(f"stderr: {e.stderr}")
            return False
    
    def create_fps_variant_from_iframe(self, iframe_path, target_path, target_fps):
        """
        Create FPS variant from I-frame-only video
        
        Args:
            iframe_path: Path to I-frame-only video
            target_path: Path for output video
            target_fps: Target frame rate
            
        Returns:
            bool: Success status
        """
        print(f"🔄 Creating {target_fps} FPS variant from I-frame video")
        
        # Create directory for target
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Extract frames at target FPS from I-frame-only video
        cmd = [
            "ffmpeg", "-y", "-i", iframe_path,
            "-vf", f"fps={target_fps}",
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",  # Copy audio unchanged
            target_path
        ]
        
        print(f"  Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error creating FPS variant: {result.stderr}")
            return False
        
        # Validate duration preservation
        iframe_info = self.get_video_info(iframe_path)
        target_info = self.get_video_info(target_path)
        
        if iframe_info and target_info:
            duration_diff = abs(iframe_info['duration'] - target_info['duration'])
            if duration_diff > 0.1:  # Allow 0.1s tolerance
                print(f"⚠️  Duration changed by {duration_diff:.2f}s")
            else:
                print(f"✅ Duration preserved: {target_info['duration']:.2f}s")
        
        print(f"✅ {target_fps} FPS variant created successfully")
        return True
    
    def extract_clip_from_iframe(self, iframe_path, clip_path, start_time, end_time):
        """
        Extract clip from I-frame-only video
        
        Args:
            iframe_path: Path to I-frame-only video
            clip_path: Path for output clip
            start_time: Start time (string format)
            end_time: End time (string format)
            
        Returns:
            bool: Success status
        """
        print(f"🔄 Extracting clip: {start_time} to {end_time} from I-frame video")
        
        # Create directory for clip
        os.makedirs(os.path.dirname(clip_path), exist_ok=True)
        
        # Extract clip with precise timing from I-frame-only video
        cmd = [
            "ffmpeg", "-y", "-i", iframe_path,
            "-ss", start_time,
            "-to", end_time,
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",  # Copy audio unchanged
            "-avoid_negative_ts", "make_zero",  # Handle timing issues
            clip_path
        ]
        
        print(f"  Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Error extracting clip: {result.stderr}")
            return False
        
        print(f"✅ Clip extracted successfully")
        return True
    
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
    
    def process_video_with_iframe_preprocessing(self, video_config, output_dir):
        """
        Process video with I-frame-only preprocessing
        
        This is the main processing function that:
        1. Creates I-frame-only version of source video
        2. Processes all variants and clips from the I-frame-only video
        3. Extracts frames from each variant
        
        Args:
            video_config: Video configuration dictionary
            output_dir: Base output directory
            
        Returns:
            dict: Processing results
        """
        source_video = video_config.get('source_video')
        video_id = video_config.get('id')
        fps_variants = video_config.get('fps_variants', [])
        clips = video_config.get('clips', [])
        
        if not os.path.exists(source_video):
            raise Exception(f"Source video not found: {source_video}")
        
        print(f"\n{'='*60}")
        print(f"🎯 PROCESSING VIDEO: {video_id}")
        print(f"📹 Source: {source_video}")
        print(f"{'='*60}")
        
        # Get source video info
        source_info = self.get_video_info(source_video)
        if source_info:
            print(f"📊 Source Video Info:")
            print(f"   Duration: {source_info['duration']:.2f}s")
            print(f"   FPS: {source_info['fps']:.2f}")
            print(f"   Resolution: {source_info['width']}x{source_info['height']}")
            print(f"   Codec: {source_info['codec']}")
        
        results = {'success': True, 'variants': {}, 'clips': {}}
        
        # Step 1: Create I-frame-only version
        iframe_video_path = os.path.join(output_dir, f"{video_id}__iframe_only.mp4")
        iframe_success = self.create_iframe_only_video(source_video, iframe_video_path)
        
        if not iframe_success:
            print("❌ Failed to create I-frame-only video. Aborting processing.")
            results['success'] = False
            return results
        
        # Step 2: Process full video variants from I-frame-only video
        print(f"\n🔄 Processing {len(fps_variants)} FPS variants...")
        
        for target_fps in fps_variants:
            variant_key = f"full_{target_fps}"
            variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
            
            print(f"\n📹 Processing variant: {variant_key}")
            
            # Create FPS variant from I-frame-only video
            variant_success = self.create_fps_variant_from_iframe(
                iframe_video_path, variant_path, target_fps
            )
            
            if variant_success:
                # Extract frames from the variant
                frames_dir = os.path.join(output_dir, "frames", variant_key)
                frame_success, frame_count = self.frame_extractor.extract_frames_at_intervals(
                    variant_path, frames_dir, target_fps
                )
                
                if frame_success:
                    # Generate thumbnails for faster loading
                    print(f"🔄 Generating thumbnails for {variant_key}")
                    self.generate_thumbnails(frames_dir, thumbnail_size=(200, 150))
                    self.generate_large_thumbnails(frames_dir, thumbnail_size=(400, 300))
                    
                    # Extract and save precise timestamps for this variant
                    print(f"🔄 Extracting timestamps for {variant_key}")
                    timestamps = self.extract_frame_timestamps(variant_path)
                    
                    if timestamps and len(timestamps) >= frame_count:
                        # Use only the timestamps that correspond to extracted frames
                        frame_timestamps = timestamps[:frame_count]
                        self.save_frame_timestamps(frame_timestamps, frames_dir, variant_key)
                        print(f"✅ Variant {variant_key} completed successfully ({frame_count} frames with timestamps)")
                        results['variants'][variant_key] = {
                            'success': True, 
                            'frame_count': frame_count,
                            'has_timestamps': True
                        }
                    else:
                        print(f"⚠️  Timestamp extraction failed for {variant_key}, using frame indices")
                        results['variants'][variant_key] = {
                            'success': True, 
                            'frame_count': frame_count,
                            'has_timestamps': False
                        }
                else:
                    print(f"❌ Frame extraction failed for {variant_key}")
                    results['variants'][variant_key] = {'success': False, 'frame_count': 0}
            else:
                print(f"❌ Variant {variant_key} failed")
                results['variants'][variant_key] = {'success': False, 'frame_count': 0}
        
        # Step 3: Process clip variants from I-frame-only video
        if clips:
            print(f"\n🔄 Processing {len(clips)} clips...")
            
            for clip in clips:
                clip_name = clip.get('name')
                start_time = clip.get('start')
                end_time = clip.get('end')
                clip_fps_list = clip.get('fps', [])
                
                if not all([clip_name, start_time, end_time, clip_fps_list]):
                    print(f"⚠️  Skipping clip with missing configuration: {clip}")
                    continue
                
                print(f"\n🎬 Processing clip: {clip_name}")
                
                # Extract clip from I-frame-only video
                temp_clip_path = os.path.join(output_dir, f"temp_{clip_name}.mp4")
                clip_success = self.extract_clip_from_iframe(
                    iframe_video_path, temp_clip_path, start_time, end_time
                )
                
                if not clip_success:
                    print(f"❌ Failed to extract base clip: {clip_name}")
                    results['clips'][clip_name] = {'success': False, 'variants': {}}
                    continue
                
                clip_results = {'success': True, 'variants': {}}
                
                # Process each FPS variant of the clip
                for target_fps in clip_fps_list:
                    variant_key = f"{clip_name}_{target_fps}"
                    variant_path = os.path.join(output_dir, f"{video_id}__{variant_key}.mp4")
                    
                    print(f"  🔄 Creating {variant_key} variant")
                    
                    # Create FPS variant from the extracted clip
                    variant_success = self.create_fps_variant_from_iframe(
                        temp_clip_path, variant_path, target_fps
                    )
                    
                    if variant_success:
                        # Extract frames from the clip variant
                        frames_dir = os.path.join(output_dir, "frames", variant_key)
                        frame_success, frame_count = self.frame_extractor.extract_frames_at_intervals(
                            variant_path, frames_dir, target_fps
                        )
                        
                        if frame_success:
                            # Generate thumbnails for faster loading
                            print(f"  🔄 Generating thumbnails for {variant_key}")
                            self.generate_thumbnails(frames_dir, thumbnail_size=(200, 150))
                            self.generate_large_thumbnails(frames_dir, thumbnail_size=(400, 300))
                            
                            # Extract and save precise timestamps for this clip variant
                            print(f"  🔄 Extracting timestamps for {variant_key}")
                            timestamps = self.extract_frame_timestamps(variant_path)
                            
                            if timestamps and len(timestamps) >= frame_count:
                                # Use only the timestamps that correspond to extracted frames
                                frame_timestamps = timestamps[:frame_count]
                                self.save_frame_timestamps(frame_timestamps, frames_dir, variant_key)
                                print(f"  ✅ Clip variant {variant_key} completed ({frame_count} frames with timestamps)")
                                clip_results['variants'][variant_key] = {
                                    'success': True, 
                                    'frame_count': frame_count,
                                    'has_timestamps': True
                                }
                            else:
                                print(f"  ⚠️  Timestamp extraction failed for {variant_key}, using frame indices")
                                clip_results['variants'][variant_key] = {
                                    'success': True, 
                                    'frame_count': frame_count,
                                    'has_timestamps': False
                                }
                        else:
                            print(f"  ❌ Frame extraction failed for {variant_key}")
                            clip_results['variants'][variant_key] = {'success': False, 'frame_count': 0}
                    else:
                        print(f"  ❌ Clip variant {variant_key} failed")
                        clip_results['variants'][variant_key] = {'success': False, 'frame_count': 0}
                
                results['clips'][clip_name] = clip_results
                
                # Clean up temporary clip
                if os.path.exists(temp_clip_path):
                    os.remove(temp_clip_path)
        
        # Step 4: Clean up I-frame-only video (optional - keep for debugging)
        # if os.path.exists(iframe_video_path):
        #     os.remove(iframe_video_path)
        #     print(f"🧹 Cleaned up I-frame-only video: {iframe_video_path}")
        
        print(f"\n{'='*60}")
        print(f"📋 PROCESSING SUMMARY FOR {video_id}")
        print(f"{'='*60}")
        
        # Summary
        successful_variants = sum(1 for v in results['variants'].values() if v['success'])
        total_variants = len(results['variants'])
        print(f"Full video variants: {successful_variants}/{total_variants} successful")
        
        successful_clips = sum(1 for c in results['clips'].values() if c['success'])
        total_clips = len(results['clips'])
        if total_clips > 0:
            print(f"Clips: {successful_clips}/{total_clips} successful")
        
        if results['success'] and successful_variants == total_variants and successful_clips == total_clips:
            print("🎉 All processing completed successfully!")
        else:
            print("⚠️  Some processing steps failed. Check logs above.")
        
        return results

    def generate_thumbnails(self, frames_dir, thumbnail_size=(200, 150)):
        """
        Generate optimized thumbnails from full-size frames
        
        Creates smaller thumbnail versions of frames for faster loading in the UI.
        Thumbnails are saved in a 'thumbnails' subdirectory.
        
        Args:
            frames_dir: Directory containing full-size frame images
            thumbnail_size: Tuple of (width, height) for thumbnails
            
        Returns:
            bool: Success status
        """
        import cv2
        import glob
        
        print(f"🔄 Generating thumbnails in {frames_dir}")
        
        # Create thumbnails directory
        thumbnails_dir = os.path.join(frames_dir, "thumbnails")
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Find all frame files
        frame_files = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
        
        if not frame_files:
            print("❌ No frame files found for thumbnail generation")
            return False
        
        success_count = 0
        
        for frame_file in frame_files:
            try:
                # Read the full-size frame
                img = cv2.imread(frame_file)
                if img is None:
                    print(f"⚠️  Could not read frame: {frame_file}")
                    continue
                
                # Resize to thumbnail size while maintaining aspect ratio
                height, width = img.shape[:2]
                target_width, target_height = thumbnail_size
                
                # Calculate scaling to fit within target size while maintaining aspect ratio
                scale_w = target_width / width
                scale_h = target_height / height
                scale = min(scale_w, scale_h)
                
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # Resize the image
                thumbnail = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                
                # Save thumbnail with same filename in thumbnails directory
                thumbnail_file = os.path.join(thumbnails_dir, os.path.basename(frame_file))
                
                # Use higher compression for thumbnails to reduce file size
                cv2.imwrite(thumbnail_file, thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                success_count += 1
                
            except Exception as e:
                print(f"⚠️  Error creating thumbnail for {frame_file}: {e}")
                continue
        
        print(f"✅ Generated {success_count}/{len(frame_files)} thumbnails")
        return success_count > 0

    def generate_large_thumbnails(self, frames_dir, thumbnail_size=(400, 300)):
        """
        Generate larger thumbnails for the detailed frame scroller
        
        Creates medium-sized thumbnail versions for the 3-frame detailed view.
        Thumbnails are saved in a 'large_thumbnails' subdirectory.
        
        Args:
            frames_dir: Directory containing full-size frame images
            thumbnail_size: Tuple of (width, height) for large thumbnails
            
        Returns:
            bool: Success status
        """
        import cv2
        import glob
        
        print(f"🔄 Generating large thumbnails in {frames_dir}")
        
        # Create large thumbnails directory
        large_thumbnails_dir = os.path.join(frames_dir, "large_thumbnails")
        os.makedirs(large_thumbnails_dir, exist_ok=True)
        
        # Find all frame files
        frame_files = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))
        
        if not frame_files:
            print("❌ No frame files found for large thumbnail generation")
            return False
        
        success_count = 0
        
        for frame_file in frame_files:
            try:
                # Read the full-size frame
                img = cv2.imread(frame_file)
                if img is None:
                    print(f"⚠️  Could not read frame: {frame_file}")
                    continue
                
                # Resize to large thumbnail size while maintaining aspect ratio
                height, width = img.shape[:2]
                target_width, target_height = thumbnail_size
                
                # Calculate scaling to fit within target size while maintaining aspect ratio
                scale_w = target_width / width
                scale_h = target_height / height
                scale = min(scale_w, scale_h)
                
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # Resize the image
                large_thumbnail = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                
                # Save large thumbnail with same filename in large_thumbnails directory
                large_thumbnail_file = os.path.join(large_thumbnails_dir, os.path.basename(frame_file))
                
                # Use good quality for large thumbnails but still compressed
                cv2.imwrite(large_thumbnail_file, large_thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 90])
                
                success_count += 1
                
            except Exception as e:
                print(f"⚠️  Error creating large thumbnail for {frame_file}: {e}")
                continue
        
        print(f"✅ Generated {success_count}/{len(frame_files)} large thumbnails")
        return success_count > 0


def main():
    """Test the I-frame video processor"""
    # Load config
    config_file = "config.yaml"
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    else:
        print(f"Config file {config_file} not found")
        return 1
    
    # Create processor
    processor = IFrameVideoProcessor(config)
    
    # Process each video in config
    for video_config in config.get('videos', []):
        video_id = video_config.get('id')
        output_dir = os.path.join("static", "videos", video_id)
        
        try:
            results = processor.process_video_with_iframe_preprocessing(video_config, output_dir)
            print(f"\n✅ Processing completed for {video_id}")
        except Exception as e:
            print(f"\n❌ Processing failed for {video_id}: {e}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 