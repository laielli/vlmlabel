# Consistent Frame Extraction Test Script

This script tests the two frame extraction methods described in `consistent_frame_extraction.md` on the `input_videos/dashcam60fps.mp4` video.

## What It Tests

### Option 1: Re-encode to I-frame-only video
```bash
ffmpeg -i input.mp4 -g 1 -keyint_min 1 -sc_threshold 0 -x264opts "keyint=1:min-keyint=1:no-scenecut" -c:v libx264 -preset fast -crf 18 i_frames_only.mp4
```

This method:
1. Re-encodes the video so every frame is an I-frame (keyframe)
2. Extracts frames at different FPS rates from the I-frame-only video
3. Ensures deterministic and perfectly aligned frame extraction

### Option 2: Decode entire video and then extract
```bash
ffmpeg -i input.mp4 -vsync 0 frame_%05d.png
```

This method:
1. Decodes the entire video stream into individual PNG frames
2. Creates FPS variants by selecting frames at regular intervals
3. Preserves temporal accuracy through complete decoding

## Usage

### Basic Usage
```bash
python test_consistent_frame_extraction.py
```

This will:
- Test both methods on `input_videos/dashcam60fps.mp4`
- Extract the first 10 seconds
- Create frame sequences at 5, 10, 15, and 30 FPS
- Compare consistency between methods
- Save results to `test_outputs/` directory

### Advanced Usage
```bash
# Test with custom parameters
python test_consistent_frame_extraction.py \
    --input "path/to/your/video.mp4" \
    --duration 20 \
    --fps-rates 1 5 10 30 60 \
    --cleanup

# Test only first 5 seconds with specific FPS rates
python test_consistent_frame_extraction.py --duration 5 --fps-rates 10 30

# Clean up outputs after testing
python test_consistent_frame_extraction.py --cleanup
```

### Command Line Options
- `--input`: Input video file (default: `input_videos/dashcam60fps.mp4`)
- `--duration`: Test duration in seconds (default: 10)
- `--fps-rates`: List of FPS rates to test (default: 5 10 15 30)
- `--cleanup`: Remove output files after testing

## Output Structure

The script creates the following directory structure:

```
test_outputs/
├── dashcam_iframe_only.mp4          # I-frame-only re-encoded video
├── all_frames/                      # All decoded frames (Option 2)
│   ├── frame_00001.png
│   ├── frame_00002.png
│   └── ...
├── option1_fps5/                    # Option 1 results at 5 FPS
│   ├── frame_00001.png
│   └── ...
├── option1_fps10/                   # Option 1 results at 10 FPS
├── option1_fps15/                   # Option 1 results at 15 FPS
├── option1_fps30/                   # Option 1 results at 30 FPS
├── option2_fps5/                    # Option 2 results at 5 FPS
├── option2_fps10/                   # Option 2 results at 10 FPS
├── option2_fps15/                   # Option 2 results at 15 FPS
└── option2_fps30/                   # Option 2 results at 30 FPS
```

## What the Script Analyzes

1. **Performance**: Measures encoding/decoding times for each method
2. **Frame Counts**: Verifies expected number of frames at each FPS rate
3. **Consistency**: Compares file sizes between methods as a consistency check
4. **Video Info**: Displays original video properties (duration, FPS, resolution, codec)

## Expected Results

- **Option 1** should provide perfectly consistent frame extraction across all FPS rates
- **Option 2** should also be consistent but may take longer for the initial decode step
- Both methods should produce similar frame counts and file sizes for equivalent FPS rates
- The script will highlight any significant differences between methods

## Requirements

- `ffmpeg` and `ffprobe` must be installed and available in PATH
- Python 3.6+ with standard library modules
- Sufficient disk space for temporary frame files

## Example Output

```
🚀 Starting Consistent Frame Extraction Test
📹 Input video: input_videos/dashcam60fps.mp4
📁 Output directory: test_outputs
⏱️  Test duration: 10 seconds
🎯 Test FPS rates: [5, 10, 15, 30]

📊 Video Info:
   Duration: 30.53s
   FPS: 60.00
   Resolution: 1920x1080
   Codec: h264

============================================================
🎯 TESTING OPTION 1: Re-encode to I-frame-only video
============================================================

🔄 Creating I-frame-only video
✅ Completed in 8.45 seconds

🔄 Extracting frames at 5 FPS from I-frame-only video
✅ Completed in 1.23 seconds
   📊 Extracted 50 frames

...

============================================================
📋 TEST SUMMARY
============================================================
Option 1 (I-frame-only): ✅ Success
Option 2 (Decode all): ✅ Success

🎉 Both methods completed successfully!
📁 Check the test_outputs/ directory for extracted frames
```

## Troubleshooting

- **ffmpeg not found**: Install ffmpeg and ensure it's in your PATH
- **Permission errors**: Make sure you have write permissions in the current directory
- **Out of disk space**: The script can generate many frame files; ensure sufficient space
- **Video codec issues**: Some codecs may require additional ffmpeg libraries 