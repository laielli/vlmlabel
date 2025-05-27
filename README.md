# Video Annotation Tool (Multi-Video Version)

A Flask-based web application for annotating videos by selecting start and end frames and adding metadata. This multi-video version supports annotating multiple videos within the same application.

## Features

- Support for multiple videos with organized file storage
- Video selection via dropdown menu
- **NEW: Multi-FPS variant support with lossless annotation remapping**
- **NEW: Configuration-based video and variant management**
- **NEW: Unified preprocessing with proper FPS handling**
- **NEW: Clip variant support alongside full video variants**
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
├── preprocess_videos.py # New unified preprocessing script
├── static/
│   └── videos/
│       ├── video_id_1/
│       │   ├── video_id_1__full_30.mp4     # Full video, 30 FPS
│       │   ├── video_id_1__full_10.mp4     # Full video, 10 FPS
│       │   ├── video_id_1__clip_001_30.mp4 # Clip variant, 30 FPS
│       │   ├── video_id_1__clip_001_5.mp4  # Clip variant, 5 FPS
│       │   ├── video_id_1_processing_info.yaml # Processing metadata
│       │   └── frames/
│       │       ├── full_30/                # 30 FPS frames (unique)
│       │       │   ├── frame_0000.jpg
│       │       │   └── ...
│       │       ├── full_10/                # 10 FPS frames (unique)
│       │       ├── clip_001_30/            # Clip frames
│       │       └── clip_001_5/
│       ├── video_id_2/
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

## Key Improvements in Version 2.0

### Unified Preprocessing System
- **Single Script**: `preprocess_videos.py` replaces multiple separate scripts
- **Proper FPS Handling**: Maintains video duration when creating FPS variants
- **Unique Frame Extraction**: Extracts frames at precise intervals, no duplicates
- **Clip Support**: Process both full videos and time-based clips
- **Smart Caching**: Skip processing if files are up-to-date

### Technical Improvements
- **Duration Preservation**: 30 FPS variant of 7-second 60 FPS video remains 7 seconds
- **Frame Accuracy**: Uses mathematical frame selection instead of playback speed changes
- **Validation**: Comprehensive error checking and output validation
- **Incremental Processing**: Only reprocess when source files change

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

4. Configure videos and variants:
   
   Create a `config.yaml` file in the project root with your video configurations:
   ```yaml
   # Default canonical FPS for all videos
   default_canonical_fps: 60

   # Video definitions
   videos:
     - id: dashcam60fps
       source_video: input_videos/dashcam60fps.mp4
       canonical_variant: full_60
       fps_variants: [60, 30, 10, 5, 2, 1]  # Full video variants
       clips:
         - name: clip_001
           label: "001"
           start: "00:00:02.0"
           end: "00:00:08.0"
           fps: [30, 5]                      # Clip variants
         - name: clip_002
           label: "002" 
           start: "00:00:01.0"
           end: "00:00:09.0"
           fps: [2, 1]
   ```

5. **Process videos using the new unified script:**
   
   Process all videos according to the configuration:
   ```
   python preprocess_videos.py
   ```
   
   **Processing Options:**
   ```bash
   # Process specific video only
   python preprocess_videos.py --video-id dashcam60fps
   
   # Process only full video variants (skip clips)
   python preprocess_videos.py --type full
   
   # Process only clips (skip full videos)  
   python preprocess_videos.py --type clips
   
   # Force reprocessing (overwrite existing files)
   python preprocess_videos.py --force
   
   # Validate configuration without processing
   python preprocess_videos.py --validate
   ```

6. **Test the preprocessing system (optional):**
   ```
   python test_preprocessing.py
   ```
   This runs basic tests to validate FPS variant generation and frame extraction.

7. (Optional) To set up sample placeholder directories for testing:
   ```
   python setup_test_videos.py
   ```

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
   - The canonical variant (typically the highest FPS) is used to store annotation data.

3. **Play Video**: Use the video player controls to play, pause, and navigate through the video.

4. **Browse Frames**: Scroll through the frame strip below the video to see thumbnails of video frames.
   - Click a thumbnail to jump to that point in the video.
   - Frames are extracted at proper intervals - no duplicates or temporal inconsistencies.

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
       clips:  # Optional
         - name: clip_001
           start: "00:00:10.0"
           end: "00:00:20.0"
           fps: [30, 5]
   ```

2. Process the video and generate all variants:
   ```
   python preprocess_videos.py --video-id your_new_video_id
   ```

3. Refresh the application in your browser, and the new video will appear in the dropdown menu.

## Legacy Scripts (Deprecated)

The following scripts have been replaced by `preprocess_videos.py`:
- `preprocess_variants.py` (replaced)
- `preprocess_clips.py` (replaced)  
- `extract_frames.py` (replaced)

These scripts are kept for reference but should not be used for new processing.

## Technical Details

### FPS Variant Generation
The new system uses proper frame selection to maintain video duration:

**Old Approach (Incorrect):**
```bash
ffmpeg -i source.mp4 -r 30 output_30.mp4  # Changes duration
```

**New Approach (Correct):**
```bash
# Maintain duration using frame selection
ffmpeg -i source.mp4 -vf "select='not(mod(n,2))'" -r 30 output_30.mp4
```

### Frame Extraction
Frames are extracted at precise time intervals to avoid duplicates:

```bash
# Extract frames every 1/30 second for 30 FPS
ffmpeg -i video.mp4 -vf "select='eq(n\,0)+gte(t-prev_selected_t\,0.033)'" frames/frame_%04d.jpg
```

## Troubleshooting

- **Missing frames error**: Ensure you've run `preprocess_videos.py` for the selected video
- **Video won't play**: Ensure source video is in web-compatible format (H.264 MP4 recommended)
- **Duration mismatch**: Run tests with `python test_preprocessing.py` to validate processing
- **Processing errors**: Check that FFmpeg is installed and accessible
- **Frame count issues**: The new system should eliminate duplicate frames - contact support if issues persist

For any other issues, check the Flask server logs for error messages.