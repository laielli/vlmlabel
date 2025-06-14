import os
import csv
import glob
import yaml
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import cv2  # Import OpenCV for video FPS detection
from iframe_video_processor import IFrameVideoProcessor  # Import I-frame processor

app = Flask(__name__)

# Configuration
VIDEO_BASE_DIR = os.path.join(app.static_folder, "videos")
ANNOTATION_BASE_DIR = os.path.join("data", "annotations")
CONFIG_FILE = "config.yaml"
DEFAULT_FPS = 30  # Default FPS if detection fails
DEFAULT_CANONICAL_FPS = 30  # Default canonical FPS

@app.before_request
def ensure_directories():
    """Ensure required directories exist before processing requests"""
    os.makedirs(VIDEO_BASE_DIR, exist_ok=True)
    os.makedirs(ANNOTATION_BASE_DIR, exist_ok=True)

# Load configuration from YAML file
def load_config():
    """Load configuration from YAML file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return yaml.safe_load(file)
    return {"default_canonical_fps": DEFAULT_CANONICAL_FPS, "videos": []}

# Global config
config = load_config()

# Function to detect video FPS
def detect_video_fps(video_path):
    """Detect the FPS of a video file using OpenCV"""
    try:
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            return DEFAULT_FPS
        
        # Get FPS from the video
        fps = video.get(cv2.CAP_PROP_FPS)
        video.release()
        
        # If FPS is unreasonably low or high, use default
        if fps < 1 or fps > 120:
            return DEFAULT_FPS
            
        return round(fps)
    except Exception as e:
        print(f"Error detecting video FPS: {e}")
        return DEFAULT_FPS

# Function to parse time string to seconds
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

# Function to compute frame offset for clip variants
def get_clip_start_frame(video_id, clip_name):
    """Get the start frame (in canonical timeline) for a clip"""
    canonical_fps = get_canonical_fps(video_id)
    
    # Find clip in config
    for video in config.get('videos', []):
        if video.get('id') == video_id:
            for clip in video.get('clips', []):
                if clip.get('name') == clip_name:
                    start_time = clip.get('start')
                    if start_time:
                        start_seconds = time_to_seconds(start_time)
                        return round(start_seconds * canonical_fps)
    return 0  # Default to 0 for full video or if clip not found

@app.route('/')
def index():
    """Display a list of available videos for selection"""
    # Get list of available videos
    video_ids = get_available_video_ids()
    
    if not video_ids:
        return render_template('error.html', message="No videos found. Please add videos to the static/videos directory.")
    
    # Redirect to the first available video if exists
    if video_ids:
        return redirect(url_for('annotate_video', video_id=video_ids[0]))
    
    return render_template('video_select.html', video_ids=video_ids)

@app.route('/video/<video_id>')
def annotate_video(video_id):
    """Main page with video player and annotation interface for specific video"""
    # Get list of available videos for dropdown
    video_ids = get_available_video_ids()
    
    # Check if the video ID exists
    video_path = os.path.join(VIDEO_BASE_DIR, video_id)
    if not os.path.exists(video_path):
        return render_template('error.html', message=f"Video ID '{video_id}' not found. Please check the ID or add this video.")
    
    # Get available variants and default to canonical
    variants = get_variants_for_video(video_id)
    variant = request.args.get('variant', get_canonical_variant(video_id))
    
    # Check if video file exists for the selected variant
    variant_video_file = os.path.join(video_path, f"{video_id}__{variant}.mp4")
    if not os.path.exists(variant_video_file):
        # Try fallback to video.mp4 for backward compatibility
        variant_video_file = os.path.join(video_path, "video.mp4")
        if not os.path.exists(variant_video_file):
            return render_template('error.html', message=f"Video file not found for '{video_id}' variant '{variant}'. Please ensure video files exist.")
    
    # Get variant FPS
    variant_fps = get_variant_fps(video_id, variant)
    
    # Get list of frame images from frames directory for the variant
    frames_path = os.path.join(video_path, "frames", variant)
    
    # Check if frames directory exists
    if not os.path.exists(frames_path):
        # Try fallback to legacy path for backward compatibility
        legacy_frames_path = os.path.join(video_path, "frames")
        if os.path.exists(legacy_frames_path):
            frames_path = legacy_frames_path
        else:
            return render_template('error.html', 
                                message=f"Frames directory not found for '{video_id}' variant '{variant}'. Please extract frames first.",
                                video_id=video_id)
    
    # Get list of frames sorted by frame number
    frames = sorted([f for f in os.listdir(frames_path) if f.endswith(('.jpg', '.jpeg', '.png'))])
    
    # If no frames found, return error
    if not frames:
        return render_template('error.html', 
                              message=f"No frame images found for '{video_id}' variant '{variant}'. Please extract frames from the video first.",
                              video_id=video_id)
    
    # Get the latest annotations for this video
    annotations = load_latest_annotation(video_id)
    
    # Create relative paths for templates
    video_url = f"videos/{video_id}/{video_id}__{variant}.mp4"
    # Fall back to legacy path if needed
    if not os.path.exists(os.path.join(app.static_folder, video_url)):
        video_url = f"videos/{video_id}/video.mp4"
    
    frames_relative_path = f"videos/{video_id}/frames/{variant}/"
    # Fall back to legacy path if needed
    if not os.path.exists(os.path.join(app.static_folder, frames_relative_path.strip('/'))):
        frames_relative_path = f"videos/{video_id}/frames/"
    
    # Get canonical FPS for timeline mapping
    canonical_fps = get_canonical_fps(video_id)
    
    # Get clip start frame for proper mapping
    clip_start_frame = 0
    if '_' in variant:
        parts = variant.split('_')
        if len(parts) >= 2 and parts[0] != 'full':
            # This is a clip variant
            clip_name = parts[0]
            clip_start_frame = get_clip_start_frame(video_id, clip_name)
    
    # Get variant structure for grouped dropdown
    variant_groups = get_variant_groups(video_id)
    
    # Load frame timestamps if available
    frame_timestamps = load_frame_timestamps(video_id, variant)
    
    return render_template('index.html', 
                          video_ids=video_ids,
                          current_video_id=video_id,
                          video_file=video_url, 
                          frames=frames, 
                          frames_path=frames_relative_path,
                          fps=variant_fps,
                          canonical_fps=canonical_fps,
                          variants=variants,
                          variant_groups=variant_groups,
                          current_variant=variant,
                          clip_start_frame=clip_start_frame,
                          annotations=annotations,
                          frame_timestamps=frame_timestamps)

@app.route('/save_annotations/<video_id>', methods=['POST'])
def save_annotations(video_id):
    """Save annotations to timestamped CSV file for specific video"""
    try:
        data = request.json
        annotations = data.get('annotations', [])
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        
        # Ensure video directory exists
        video_ann_dir = os.path.join(ANNOTATION_BASE_DIR, video_id)
        os.makedirs(video_ann_dir, exist_ok=True)
        
        # Create filename with timestamp
        filename = f"annotations_{timestamp}.csv"
        csv_path = os.path.join(video_ann_dir, filename)
        
        # Write annotations to CSV
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'start_frame', 'end_frame', 'event_type', 'notes'])  # Header
            
            for annotation in annotations:
                writer.writerow([
                    annotation.get('id', ''),
                    annotation['start'],
                    annotation['end'],
                    annotation['type'],
                    annotation['notes']
                ])
        
        return jsonify({
            'status': 'success', 
            'message': 'Annotations saved successfully',
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/load_annotations/<video_id>', methods=['GET'])
def get_annotations(video_id):
    """API endpoint to get the latest annotations for a video"""
    annotations = load_latest_annotation(video_id)
    return jsonify({'status': 'success', 'annotations': annotations})

@app.route('/load_annotations/<video_id>', methods=['POST'])
def load_annotations(video_id):
    """Load annotations from uploaded CSV file for specific video"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
            
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'File must be a CSV'}), 400
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        
        # Ensure video annotation directory exists
        video_ann_dir = os.path.join(ANNOTATION_BASE_DIR, video_id)
        os.makedirs(video_ann_dir, exist_ok=True)
        
        # Save the uploaded file with a timestamp
        filename = f"annotations_{timestamp}.csv"
        file_path = os.path.join(video_ann_dir, filename)
        file.save(file_path)
        
        # Read the saved file to return its contents
        annotations = parse_annotation_file(file_path)
        
        return jsonify({'status': 'success', 'annotations': annotations, 'filename': filename})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download_annotations/<video_id>')
def download_annotations(video_id):
    """Download the latest annotations CSV for a specific video"""
    annotation_file = get_latest_annotation_file(video_id)
    
    if annotation_file:
        return send_file(annotation_file, as_attachment=True, 
                        download_name=f"{video_id}_annotations.csv")
    else:
        return jsonify({'status': 'error', 'message': 'No annotations file found'}), 404

@app.route('/extract_frames/<video_id>')
def extract_frames_route(video_id):
    """Show instructions for extracting frames for a specific video"""
    return render_template('extract_frames.html', video_id=video_id)

@app.route('/api/frame_timestamps/<video_id>/<variant>')
def get_frame_timestamps_api(video_id, variant):
    """API endpoint to get frame timestamps for a specific video variant"""
    try:
        frame_timestamps = load_frame_timestamps(video_id, variant)
        return jsonify({
            'success': True,
            'frame_timestamps': frame_timestamps,
            'has_timestamps': len(frame_timestamps) > 0
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'frame_timestamps': {},
            'has_timestamps': False
        }), 500

@app.route('/preprocess_video/<video_id>', methods=['POST'])
def preprocess_video_route(video_id):
    """Route to trigger I-frame preprocessing for a video"""
    try:
        # Find video config
        video_config = None
        for video in config.get('videos', []):
            if video.get('id') == video_id:
                video_config = video
                break
        
        if not video_config:
            return jsonify({
                "success": False, 
                "message": f"Video ID '{video_id}' not found in configuration"
            }), 404
        
        # Check if source video exists
        source_video = video_config.get('source_video')
        if not source_video or not os.path.exists(source_video):
            return jsonify({
                "success": False,
                "message": f"Source video not found: {source_video}"
            }), 404
        
        # Create processor and process video
        processor = IFrameVideoProcessor(config)
        output_dir = os.path.join("static", "videos", video_id)
        
        results = processor.process_video_with_iframe_preprocessing(video_config, output_dir)
        
        if results['success']:
            variant_count = len([v for v in results['variants'].values() if v['success']])
            clip_count = len([c for c in results['clips'].values() if c['success']])
            
            return jsonify({
                "success": True,
                "message": f"Successfully processed {video_id}",
                "variants_created": variant_count,
                "clips_processed": clip_count,
                "results": results
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Processing failed for {video_id}",
                "results": results
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing {video_id}: {str(e)}"
        }), 500

@app.route('/preprocess_all', methods=['POST'])
def preprocess_all_route():
    """Route to trigger I-frame preprocessing for all videos in config"""
    try:
        processor = IFrameVideoProcessor(config)
        results = {}
        successful = 0
        failed = 0
        
        for video_config in config.get('videos', []):
            video_id = video_config.get('id')
            
            try:
                output_dir = os.path.join("static", "videos", video_id)
                video_results = processor.process_video_with_iframe_preprocessing(video_config, output_dir)
                
                if video_results['success']:
                    successful += 1
                else:
                    failed += 1
                
                results[video_id] = video_results
                
            except Exception as e:
                failed += 1
                results[video_id] = {
                    'success': False,
                    'error': str(e),
                    'variants': {},
                    'clips': {}
                }
        
        return jsonify({
            "success": failed == 0,
            "message": f"Processed {successful + failed} videos. {successful} successful, {failed} failed.",
            "successful": successful,
            "failed": failed,
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error during batch processing: {str(e)}"
        }), 500

# Helper function to get available video IDs
def get_available_video_ids():
    """Return a list of available video IDs (directories in the videos folder)"""
    if not os.path.exists(VIDEO_BASE_DIR):
        return []
    
    # Get directories in the videos folder
    return sorted([d for d in os.listdir(VIDEO_BASE_DIR) 
                 if os.path.isdir(os.path.join(VIDEO_BASE_DIR, d))])

# Helper function to get the latest annotation file path
def get_latest_annotation_file(video_id):
    """Find the latest annotation file for a video based on filename timestamp"""
    video_ann_dir = os.path.join(ANNOTATION_BASE_DIR, video_id)
    
    if not os.path.exists(video_ann_dir):
        return None
    
    # Find all annotation files
    files = glob.glob(os.path.join(video_ann_dir, "annotations_*.csv"))
    
    if not files:
        return None
    
    # Return the most recent file (by modification time)
    return max(files, key=os.path.getmtime)

# Helper function to load the latest annotation
def load_latest_annotation(video_id):
    """Load and parse the latest annotation file for a video"""
    latest_file = get_latest_annotation_file(video_id)
    
    if not latest_file:
        return []
    
    return parse_annotation_file(latest_file)

# Helper function to parse an annotation file
def parse_annotation_file(file_path):
    """Parse a CSV annotation file with better error handling"""
    annotations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:  # Handle BOM
            reader = csv.DictReader(csvfile)
            
            # Validate headers
            required_fields = {'start_frame', 'end_frame', 'event_type', 'notes'}
            if reader.fieldnames and not required_fields.issubset(set(reader.fieldnames)):
                # Try legacy format
                csvfile.seek(0)
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip potential header
                
                for row in reader:
                    if len(row) >= 4 and row[0].isdigit() and row[1].isdigit():
                        annotations.append({
                            'id': str(uuid.uuid4()),
                            'start': int(row[0]),
                            'end': int(row[1]),
                            'type': row[2],
                            'notes': row[3] if len(row) > 3 else ''
                        })
            else:
                # Modern format with headers
                for row in reader:
                    annotations.append({
                        'id': row.get('id', str(uuid.uuid4())),
                        'start': int(row['start_frame']),
                        'end': int(row['end_frame']),
                        'type': row['event_type'],
                        'notes': row['notes']
                    })
    except Exception as e:
        print(f"Error parsing annotation file: {e}")
        
    return annotations

# Helper function to load frame timestamps
def load_frame_timestamps(video_id, variant):
    """Load frame timestamps from JSON file if available"""
    frames_dir = os.path.join(VIDEO_BASE_DIR, video_id, "frames", variant)
    timestamp_file = os.path.join(frames_dir, "frame_timestamps.json")
    
    if os.path.exists(timestamp_file):
        try:
            import json
            with open(timestamp_file, 'r') as f:
                data = json.load(f)
            return data.get('frame_mapping', {})
        except Exception as e:
            print(f"Error loading frame timestamps: {e}")
    
    return {}

# Helper function for ffmpeg frame extraction (unused but available for reference)
def extract_frames(video_id, fps=1):
    """Extract frames from video using ffmpeg (placeholder)"""
    # This would be implemented if we want to add automatic extraction
    # But for now, we're assuming frames are extracted manually
    pass

# Helper function to get variant information for a video
def get_variants_for_video(video_id):
    """Get available variants for a video from config"""
    variants = []
    
    # Check in config
    for video in config.get('videos', []):
        if video.get('id') == video_id:
            # Add full video variants
            for fps in video.get('fps_variants', []):
                variants.append(f"full_{fps}")
            
            # Add clip variants
            for clip in video.get('clips', []):
                clip_name = clip.get('name')
                for fps in clip.get('fps', []):
                    variants.append(f"{clip_name}_{fps}")
            
            return variants
    
    # Fallback: Look for variant files in the directory
    video_dir = os.path.join(VIDEO_BASE_DIR, video_id)
    if os.path.exists(video_dir):
        for file in os.listdir(video_dir):
            if file.startswith(f"{video_id}__") and file.endswith(".mp4"):
                variant = file[len(f"{video_id}__"):-4]  # Extract the variant part
                variants.append(variant)
    
    # If no variants found, create a default one
    if not variants and os.path.exists(os.path.join(video_dir, "video.mp4")):
        variants.append("full_30")  # Default legacy variant
    
    return variants

# Helper function to get the variant groups for the UI dropdown
def get_variant_groups(video_id):
    """Get variant groups for a video from config"""
    variant_groups = {}
    
    # Check in config
    for video in config.get('videos', []):
        if video.get('id') == video_id:
            # Add full video variants
            full_variants = []
            for fps in video.get('fps_variants', []):
                full_variants.append({
                    'key': f"full_{fps}",
                    'label': f"{fps} FPS"
                })
            
            if full_variants:
                variant_groups['Full Video'] = full_variants
            
            # Add clip variants
            for clip in video.get('clips', []):
                clip_name = clip.get('name')
                clip_label = clip.get('label', clip_name.replace('_', ' ').title())
                
                clip_variants = []
                for fps in clip.get('fps', []):
                    clip_variants.append({
                        'key': f"{clip_name}_{fps}",
                        'label': f"{fps} FPS"
                    })
                
                if clip_variants:
                    variant_groups[clip_label] = clip_variants
            
            return variant_groups
    
    # Fallback: Create a simple group from flat list
    variants = get_variants_for_video(video_id)
    if variants:
        variant_groups['Variants'] = [{'key': v, 'label': v} for v in variants]
    
    return variant_groups

# Helper function to get canonical variant for a video
def get_canonical_variant(video_id):
    """Get canonical variant for a video from config"""
    for video in config.get('videos', []):
        if video.get('id') == video_id:
            return video.get('canonical_variant', 'full_30')
    return 'full_30'  # Default

# Helper function to get canonical FPS for a video
def get_canonical_fps(video_id):
    """Get canonical FPS for a video from config"""
    for video in config.get('videos', []):
        if video.get('id') == video_id:
            canonical_variant = video.get('canonical_variant', 'full_30')
            if canonical_variant.startswith('full_'):
                try:
                    return int(canonical_variant.split('_')[1])
                except (IndexError, ValueError):
                    pass
    return config.get('default_canonical_fps', DEFAULT_CANONICAL_FPS)

# Helper function to get variant FPS
def get_variant_fps(video_id, variant):
    """Get FPS for a specific variant"""
    if variant and '_' in variant:
        try:
            return int(variant.split('_')[-1])  # Get FPS from last part of variant key
        except (IndexError, ValueError):
            pass
    
    # Fallback: detect from video file
    variant_video_file = os.path.join(VIDEO_BASE_DIR, video_id, f"{video_id}__{variant}.mp4")
    if os.path.exists(variant_video_file):
        return detect_video_fps(variant_video_file)
    
    # Legacy fallback
    legacy_video_file = os.path.join(VIDEO_BASE_DIR, video_id, "video.mp4")
    if os.path.exists(legacy_video_file):
        return detect_video_fps(legacy_video_file)
    
    return DEFAULT_FPS

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 