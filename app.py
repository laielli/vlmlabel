import os
import csv
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
VIDEO_FILE = 'video.mp4'  # The video file in static folder
FRAMES_DIR = 'frames'  # Directory within static containing frame images
CSV_PATH = os.path.join('data', 'annotations.csv')
FPS = 30  # Default FPS, can be overridden

@app.route('/')
def index():
    """Main page with video player and annotation interface"""
    # Get list of frame images from static/frames/
    frames_path = os.path.join(app.static_folder, FRAMES_DIR)
    
    # Check if frames directory exists
    if not os.path.exists(frames_path):
        return render_template('error.html', message="Frames directory not found. Please extract frames first.")
    
    # Get list of frames sorted by frame number
    frames = sorted([f for f in os.listdir(frames_path) if f.endswith(('.jpg', '.jpeg', '.png'))])
    
    # If no frames found, return error
    if not frames:
        return render_template('error.html', message="No frame images found. Please extract frames from the video first.")
    
    return render_template('index.html', video_file=VIDEO_FILE, frames=frames, fps=FPS)

@app.route('/save_annotations', methods=['POST'])
def save_annotations():
    """Save annotations to CSV file"""
    try:
        data = request.json
        annotations = data.get('annotations', [])
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        
        # Write annotations to CSV
        with open(CSV_PATH, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['start_frame', 'end_frame', 'event_type', 'notes'])  # Header
            
            for annotation in annotations:
                writer.writerow([
                    annotation['start'],
                    annotation['end'],
                    annotation['type'],
                    annotation['notes']
                ])
        
        return jsonify({'status': 'success', 'message': 'Annotations saved successfully'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/load_annotations', methods=['POST'])
def load_annotations():
    """Load annotations from uploaded CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
            
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'File must be a CSV'}), 400
        
        annotations = []
        csv_file = file.stream.read().decode('utf-8').splitlines()
        reader = csv.reader(csv_file)
        
        # Skip header if present
        first_row = next(reader)
        if not all(h.isdigit() for h in first_row[:2]):  # If first/second cols aren't numbers, it's a header
            pass  # Skip header
        else:
            # It's not a header, process this row
            annotations.append({
                'start': int(first_row[0]),
                'end': int(first_row[1]),
                'type': first_row[2] if len(first_row) > 2 else '',
                'notes': first_row[3] if len(first_row) > 3 else ''
            })
        
        # Process remaining rows
        for row in reader:
            if len(row) >= 4:
                annotations.append({
                    'start': int(row[0]),
                    'end': int(row[1]),
                    'type': row[2],
                    'notes': row[3]
                })
        
        return jsonify({'status': 'success', 'annotations': annotations})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download_csv')
def download_csv():
    """Allow user to download the CSV file"""
    if os.path.exists(CSV_PATH):
        return send_file(CSV_PATH, as_attachment=True, download_name="annotations.csv")
    else:
        return jsonify({'status': 'error', 'message': 'No annotations file found'}), 404

@app.route('/extract_frames')
def extract_frames_route():
    """Simple HTML page with instructions for extracting frames"""
    return render_template('extract_frames.html')

# Helper function for ffmpeg frame extraction
def extract_frames(video_path, output_dir, fps=1):
    """Extract frames from video using ffmpeg"""
    # This would be implemented if we want to add automatic extraction
    # But for now, we're assuming frames are extracted manually
    pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 