# Video Annotation Tool

A Flask-based web application for annotating videos by selecting start and end frames and adding metadata.

## Features

- Play MP4 video and view frame thumbnails in a scrollable timeline
- Select start and end frames for events
- Add event type and notes as metadata
- Save annotations to CSV
- Load annotations from CSV
- Simple, lightweight interface with no frontend frameworks

## Requirements

- Python 3.6+
- Flask
- OpenCV (optional, for frame extraction)
- FFmpeg (optional, recommended for frame extraction)

## Setup

1. Clone this repository or download the files

2. Set up a Python virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

   The `requirements.txt` already includes `opencv-python` for the optional
   frame extraction script.

4. Prepare your video:
   - Place your MP4 video in the `static/` directory
   - Name it `video.mp4` or update the `VIDEO_FILE` variable in `app.py`

5. Extract frames from your video:
   
   **Option 1: Using FFmpeg (recommended):**
   ```
   mkdir -p static/frames
   ffmpeg -i static/video.mp4 -r 1 static/frames/frame_%04d.jpg
   ```
   This extracts 1 frame per second. Adjust `-r 1` to change the extraction rate.
   
   **Option 2: Using the included Python script:**
   ```
   python extract_frames.py
   ```
   
   Use `python extract_frames.py --help` to see available options.

## Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```
   or
   ```
   flask run --host=0.0.0.0
   ```

2. Open a web browser and navigate to:
   - `http://localhost:5000` (local development)
   - Or use the VSCode Flask preview if running on a remote server

## Using the Annotation Tool

1. **Play Video**: Use the video player controls to play, pause, and navigate through the video

2. **Browse Frames**: Scroll through the frame strip below the video to see thumbnails of video frames
   - Click a thumbnail to jump to that point in the video

3. **Create Annotations**:
   - Navigate to the start of an event (either using the video player or by clicking a thumbnail)
   - Click "Set Start" to mark the current frame as the start
   - Navigate to the end of the event
   - Click "Set End" to mark the current frame as the end
   - Enter an Event Type (required) and Notes (optional)
   - Click "Add Annotation" to save this event

4. **Manage Annotations**:
   - View all annotations in the table
   - Click on a row to jump to that event in the video
   - Use the "✕" button to delete an annotation
   - Click "Save to CSV" to save all annotations to a CSV file
   - Use "Load CSV" to import annotations from a previously saved CSV file

## CSV Format

The CSV file uses the following format:
```
start_frame,end_frame,event_type,notes
150,300,Goal,Player scores off a corner kick
420,450,Penalty,Handball leads to penalty kick awarded
```

## Troubleshooting

- If you see an error about missing frames, make sure you've extracted frames from your video
- If the video doesn't play, ensure it's in a web-compatible format (H.264 MP4 is recommended)
- For any other issues, check the Flask server logs for error messages

## License

This project is open source and available under the MIT License. 