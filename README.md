# Video Annotation Tool (Multi-Video Version)

A Flask-based web application for annotating videos by selecting start and end frames and adding metadata. This multi-video version supports annotating multiple videos within the same application.

## Features

- Support for multiple videos with organized file storage
- Video selection via dropdown menu
- **NEW: Multi-FPS variant support with lossless annotation remapping**
- **NEW: Configuration-based video and variant management**
- Automatic video FPS detection for accurate frame timing
- Play MP4 video and view frame thumbnails in a scrollable timeline
- Select start and end frames for events
- Add event type and notes as metadata
- Save annotations to CSV with automatic timestamping for versioning
- Load annotations from CSV
- Simple, lightweight interface with no frontend frameworks

## Requirements

- Python 3.6+
- Flask
- OpenCV (required for FPS detection and frame extraction)
- FFmpeg (required for variant generation and frame extraction)
- PyYAML (for configuration parsing)

## Directory Structure

The application organizes videos and annotations in the following structure:

```
project-root/
├── config.yaml          # Configuration file for videos and variants
├── static/
│   └── videos/
│       ├── video_id_1/
│       │   ├── video_id_1__full_30.mp4  # Canonical 30 FPS version
│       │   ├── video_id_1__full_10.mp4  # 10 FPS version
│       │   ├── video_id_1__full_5.mp4   # 5 FPS version
│       │   └── frames/
│       │       ├── full_30/             # 30 FPS frames
│       │       │   ├── frame_0000.jpg
│       │       │   └── ...
│       │       ├── full_10/             # 10 FPS frames
│       │       └── full_5/              # 5 FPS frames
│       ├── video_id_2/
│       │   ├── video_id_2__full_30.mp4
│       │   └── ...
├── data/
│   └── annotations/
│       ├── video_id_1/
│       │   ├── annotations_20230506T101530.csv
│       │   └── ...
│       ├── video_id_2/
│       │   └── ...
```

Each video has its own folder with variants, frames, and annotations organized separately.

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

   OpenCV is required for FPS detection and frame extraction:
   ```
   pip install opencv-python
   ```

4. Add videos to the application:
   - Create a directory for each video under `static/videos/` with a descriptive ID (e.g., `static/videos/soccer_match_1`)
   - Place MP4 video files named `video.mp4` in their respective directories
   - Extract frames for each video (see below)

5. (NEW) Configure videos and variants:
   
   Create a `config.yaml` file in the project root with your video configurations:
   ```yaml
   # Default canonical FPS for all videos
   default_canonical_fps: 30

   # Video definitions
   videos:
     - id: soccer_game
       source_video: input_videos/soccer_game.mp4
       canonical_variant: full_30
       fps_variants: [30, 10, 5]  # full-length, different FPS
   ```

6. (NEW) Process videos and create variants:
   
   Process videos according to the configuration and generate all FPS variants:
   ```
   python preprocess_variants.py
   ```
   
   You can also process a specific video:
   ```
   python preprocess_variants.py --video-id soccer_game
   ```

7. Extract frames from your videos (Legacy method, use preprocess_variants.py instead):
   
   **Option 1: Using FFmpeg (recommended):**
   ```
   mkdir -p static/videos/your_video_id/frames
   ffmpeg -i static/videos/your_video_id/video.mp4 -r 1 static/videos/your_video_id/frames/frame_%04d.jpg
   ```
   This extracts 1 frame per second. Adjust `-r 1` to change the extraction rate.
   
   **Option 2: Using the included Python script (with auto FPS detection):**
   ```
   python extract_frames_multi.py --video-id your_video_id
   ```
   
   This will automatically detect the video's FPS and extract frames accordingly. You can override with `--fps` option.
   
   Use `python extract_frames_multi.py --help` to see all available options.

8. (Optional) To set up sample placeholder directories for testing:
   ```
   python setup_test_videos.py
   ```
   This creates three sample video directories with placeholders for video files and frames.

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

1. **Select a Video**: Use the dropdown at the top of the page to choose which video to annotate.

2. **Select a Variant**: Use the variant dropdown to switch between different FPS versions of the same video.
   - All annotations automatically remap between variants to maintain precise timing.
   - The canonical variant (typically full_30) is used to store annotation data.

3. **Play Video**: Use the video player controls to play, pause, and navigate through the video.

4. **Browse Frames**: Scroll through the frame strip below the video to see thumbnails of video frames.
   - Click a thumbnail to jump to that point in the video.

5. **Create Annotations**:
   - Navigate to the start of an event (either using the video player or by clicking a thumbnail).
   - Click "Set Start" to mark the current frame as the start.
   - Navigate to the end of the event.
   - Click "Set End" to mark the current frame as the end.
   - Enter an Event Type (required) and Notes (optional).
   - Click "Add Annotation" to save this event.

6. **Manage Annotations**:
   - View all annotations in the table.
   - Click on a row to jump to that event in the video.
   - Use the "✕" button to delete an annotation.
   - Click "Save to CSV" to save all annotations to a timestamped CSV file.
   - Use "Load CSV" to import annotations from a previously saved CSV file.

## CSV Format

The CSV file uses the following format:
```
start_frame,end_frame,event_type,notes
150,300,Goal,Player scores off a corner kick
420,450,Penalty,Handball leads to penalty kick awarded
```

Each video's annotations are stored separately in its own directory under `data/annotations/<video_id>/`. Files are named with timestamps (e.g., `annotations_20230506T101530.csv`) for versioning.

## Adding a New Video

To add a new video to the annotation tool:

1. Add an entry to the `config.yaml` file:
   ```yaml
   videos:
     # Existing videos here...
     - id: your_new_video_id
       source_video: path/to/your/source_video.mp4
       canonical_variant: full_30
       fps_variants: [30, 10, 5]
   ```

2. Process the video and generate all variants:
   ```
   python preprocess_variants.py --video-id your_new_video_id
   ```

3. Refresh the application in your browser, and the new video will appear in the dropdown menu.

## Troubleshooting

- If you see an error about missing frames, make sure you've extracted frames from your video for the selected video ID.
- If the video doesn't play, ensure it's in a web-compatible format (H.264 MP4 is recommended).
- For any other issues, check the Flask server logs for error messages.