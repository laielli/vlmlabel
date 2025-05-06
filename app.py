import os
import csv
import glob
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
VIDEO_BASE_DIR = os.path.join(app.static_folder, "videos")
ANNOTATION_BASE_DIR = os.path.join("data", "annotations")
FPS = 30  # Default FPS, can be overridden

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
    
    # Check if video file exists
    video_file = os.path.join(video_path, "video.mp4")
    if not os.path.exists(video_file):
        return render_template('error.html', message=f"Video file not found for '{video_id}'. Please ensure video.mp4 exists in the directory.")
    
    # Get list of frame images from frames directory
    frames_path = os.path.join(video_path, "frames")
    
    # Check if frames directory exists
    if not os.path.exists(frames_path):
        return render_template('error.html', 
                              message=f"Frames directory not found for '{video_id}'. Please extract frames first.",
                              video_id=video_id)
    
    # Get list of frames sorted by frame number
    frames = sorted([f for f in os.listdir(frames_path) if f.endswith(('.jpg', '.jpeg', '.png'))])
    
    # If no frames found, return error
    if not frames:
        return render_template('error.html', 
                              message=f"No frame images found for '{video_id}'. Please extract frames from the video first.",
                              video_id=video_id)
    
    # Get the latest annotations for this video
    annotations = load_latest_annotation(video_id)
    
    # Create relative paths for templates
    video_url = f"videos/{video_id}/video.mp4"
    frames_relative_path = f"videos/{video_id}/frames/"
    
    return render_template('index.html', 
                          video_ids=video_ids,
                          current_video_id=video_id,
                          video_file=video_url, 
                          frames=frames, 
                          frames_path=frames_relative_path,
                          fps=FPS,
                          annotations=annotations)

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
            writer.writerow(['start_frame', 'end_frame', 'event_type', 'notes'])  # Header
            
            for annotation in annotations:
                writer.writerow([
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
    """Parse a CSV annotation file into a list of annotation objects"""
    annotations = []
    
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        
        # Skip header row if present
        header = next(reader, None)
        if not header or not all(col in ['start_frame', 'end_frame', 'event_type', 'notes'] for col in header):
            # If not a proper header with expected columns, reopen and read all rows
            csvfile.seek(0)
            reader = csv.reader(csvfile)
        
        for row in reader:
            if len(row) >= 4 and row[0].isdigit() and row[1].isdigit():
                annotations.append({
                    'start': int(row[0]),
                    'end': int(row[1]),
                    'type': row[2],
                    'notes': row[3]
                })
    
    return annotations

# Helper function for ffmpeg frame extraction (unused but available for reference)
def extract_frames(video_id, fps=1):
    """Extract frames from video using ffmpeg (placeholder)"""
    # This would be implemented if we want to add automatic extraction
    # But for now, we're assuming frames are extracted manually
    pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 