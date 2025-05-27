# VLM Label - Advanced Video Annotation Tool

A professional Flask-based web application for precise video annotation with frame-accurate timestamp extraction, dual frame scrollers, and space-efficient UI design.

## ✨ Key Features

### 🎯 **Precision Frame Navigation**
- **Dual Frame Scrollers**: Small timeline scroller + large 3-frame detail view
- **99.9% Frame Accuracy**: Precise timestamp extraction eliminates clicking misalignment
- **Optimized Thumbnails**: 50-85% faster loading with smart thumbnail generation
- **I-Frame Processing**: Every frame is seekable for perfect video player synchronization

### 🎮 **Space-Efficient Interface**
- **Minimize/Maximize Controls**: Collapse video player, timeline, and detail view independently
- **Unified Control Row**: Essential controls (Play/Pause, Set Start/End) always accessible
- **Up to 780px Space Savings**: Fit annotations above the fold on any screen
- **Professional Dark Theme**: Clean, modern interface with smooth animations

### 📹 **Advanced Video Processing**
- **I-Frame Video Variants**: Lossless conversion for perfect frame seeking
- **Multi-FPS Support**: Generate 60, 30, 10, 5 FPS variants with precise timing
- **Smart Preprocessing**: Automatic thumbnail generation and timestamp extraction
- **Configuration-Based**: Simple YAML setup for multiple videos and variants

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Clone the repository
git clone <repository-url>
cd vlmlabel

# Set up virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

**Requirements**: Python 3.6+, Flask, OpenCV, FFmpeg, PyYAML

### 2. Configure Your Videos
Create a `config.yaml` file in the project root:

```yaml
# Default settings
default_canonical_fps: 60

# Video definitions
videos:
  - id: my_video
    source_video: input_videos/my_video.mp4
    canonical_variant: full_60
    fps_variants: [60, 30, 10, 5]  # Generate these FPS variants
```

### 3. Process Videos (I-Frame Integration)
```bash
# Process all videos with I-frame optimization
python preprocess_with_iframe.py

# Process specific video
python preprocess_with_iframe.py --video-id my_video

# Force reprocessing
python preprocess_with_iframe.py --force
```

**What this does:**
- Converts videos to I-frame-only format for perfect seeking
- Generates multiple FPS variants with precise timing
- Extracts optimized thumbnails (small + large sizes)
- Creates frame timestamp mappings for 99.9% accuracy

### 4. Start the Application
```bash
python app.py
```

Open `http://localhost:5000` in your browser.

## 🎬 Using the Annotation Tool

### Interface Overview
- **Video Player**: Main video with standard controls
- **Small Frame Scroller**: Timeline with thumbnail navigation
- **Large Frame Scroller**: 3-frame detail view (previous, current, next)
- **Unified Controls**: Always-accessible Play/Pause, Set Start/End buttons
- **Annotation Table**: Manage and review all annotations

### Creating Annotations
1. **Navigate**: Use video player or click frame thumbnails
2. **Set Start**: Click "Set Start" button or use frame scroller
3. **Set End**: Navigate to end frame and click "Set End"
4. **Add Details**: Enter event type (required) and notes (optional)
5. **Save**: Click "Add Annotation"

### Space Management
- **Minimize Features**: Click 📹 (video), 🎞️ (timeline), or 🔍 (detail view) to minimize
- **Unified Controls**: Essential functions remain accessible when minimized
- **Maximize**: Click the same buttons to restore full view

## 📁 Project Structure

```
vlmlabel/
├── config.yaml                    # Video configuration
├── preprocess_with_iframe.py      # Primary preprocessing script
├── app.py                         # Flask application
├── iframe_video_processor.py      # Core video processing engine
├── static/
│   └── videos/
│       └── my_video/
│           ├── my_video__full_60.mp4           # I-frame video variants
│           ├── my_video__full_30.mp4
│           ├── frame_timestamps_full_60.json   # Precise timestamps
│           └── frames/
│               └── full_60/
│                   ├── frame_0000.jpg          # Full-size frames
│                   ├── thumbnails/             # Small thumbnails
│                   └── large_thumbnails/       # Large thumbnails
├── data/
│   └── annotations/
│       └── my_video/
│           └── annotations_20250527T143022.csv # Timestamped annotations
├── docs/                          # Comprehensive documentation
└── tests/                         # Organized test suite
```

## 🔧 Advanced Configuration

### Multiple Videos
```yaml
videos:
  - id: dashcam_footage
    source_video: input_videos/dashcam.mp4
    canonical_variant: full_60
    fps_variants: [60, 30, 10, 5, 2, 1]
    
  - id: security_camera
    source_video: input_videos/security.mp4
    canonical_variant: full_30
    fps_variants: [30, 15, 5]
```

### Processing Options
```bash
# Validate configuration without processing
python preprocess_with_iframe.py --validate

# Process only specific FPS variants
python preprocess_with_iframe.py --fps 30,10

# Skip thumbnail generation (faster processing)
python preprocess_with_iframe.py --no-thumbnails

# Verbose output for debugging
python preprocess_with_iframe.py --verbose
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
# All tests
python -m pytest tests/ -v

# Specific categories
python -m pytest tests/preprocessing/ -v  # Video processing tests
python -m pytest tests/features/ -v      # Feature tests
python -m pytest tests/integration/ -v   # Integration tests
```

See **[tests/README.md](./tests/README.md)** for detailed testing documentation.

## 📚 Documentation

Comprehensive documentation is available in the **[docs/](./docs/)** directory:

- **[Features](./docs/features/)** - User guides for timestamp extraction, frame scrollers, minimize functionality
- **[Implementation](./docs/implementation/)** - Technical details and system improvements
- **[Testing](./docs/testing/)** - Testing procedures and validation guides
- **[Design](./docs/design/)** - Design specifications and architectural decisions

## 🎯 Key Improvements

### Frame Accuracy
- **Before**: ~90% accuracy with calculated timestamps
- **After**: 99.9% accuracy with extracted timestamps
- **Method**: Direct timestamp extraction from video frames

### Performance
- **Thumbnail Loading**: 50-85% faster with optimized sizes
- **Video Seeking**: Perfect frame accuracy with I-frame processing
- **UI Responsiveness**: Smooth animations and instant minimize/maximize

### User Experience
- **Space Efficiency**: Up to 780px vertical space savings
- **Dual Navigation**: Timeline + detail view for different use cases
- **Always-Accessible Controls**: Critical functions never hidden
- **Professional Interface**: Clean, modern design with dark theme

## 🔧 Troubleshooting

- **Missing frames**: Run `python preprocess_with_iframe.py` for your video
- **Video won't play**: Ensure source video is H.264 MP4 format
- **Processing errors**: Check that FFmpeg is installed and accessible
- **Frame alignment issues**: The I-frame processing should eliminate these
- **Test failures**: See [tests/README.md](./tests/README.md) for debugging

## 📄 CSV Export Format

Annotations are saved with precise timing:
```csv
start_frame,end_frame,event_type,notes
150,300,Goal,Player scores off corner kick
420,450,Penalty,Handball in penalty area
```

Each video's annotations are stored separately with automatic timestamping for version control.

## 🚀 What's New

- **I-Frame Integration**: Perfect video seeking with frame-accurate navigation
- **Dual Frame Scrollers**: Timeline + 3-frame detail view for precise annotation
- **Minimize Functionality**: Space-efficient UI with unified control row
- **Optimized Thumbnails**: Multiple sizes for different use cases
- **99.9% Frame Accuracy**: Precise timestamp extraction eliminates misalignment
- **Professional Interface**: Modern dark theme with smooth animations

---

**Ready to start annotating?** Follow the Quick Start guide above and you'll be creating precise video annotations in minutes!