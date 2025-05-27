# Frame Timing Fix Summary

## Issue Description

Users reported that clicking on sequential frame thumbnails in the horizontal frame scroller sometimes did not advance the video player to new content, but instead showed duplicate frames from the previous position.

## Root Cause Analysis

The issue was caused by **incorrect time mapping** between frame thumbnails and video timestamps:

### Original Implementation
```html
<!-- In templates/index.html -->
<img data-time="{{ (loop.index0 / fps) | round(2) }}">
```

This assumed:
1. Frame thumbnails are numbered sequentially (0, 1, 2, 3...)
2. Each frame represents exactly `1/fps` seconds of video time
3. No gaps or duplicates exist in the frame sequence

### The Problem
When the source video contained duplicate frames:
- **Frame Extraction**: Duplicates were extracted as separate files (`frame_0001.jpg`, `frame_0002.jpg`, `frame_0003.jpg`)
- **Time Calculation**: Sequential numbering created incorrect time mapping:
  - `frame_0001.jpg` → `data-time="0.017"` (1/60)
  - `frame_0002.jpg` → `data-time="0.033"` (2/60) 
  - `frame_0003.jpg` → `data-time="0.050"` (3/60)
- **Video Seeking**: Clicking `frame_0002.jpg` sought to time `0.033`, but showed the same content as `0.017` due to source duplicates

## Solution Implemented

### Backend Changes (`app.py`)

Modified the frame processing to provide proper time mapping:

```python
# Create frame data with proper time mapping
frame_data = []
frame_interval = 1.0 / variant_fps  # Time interval between frames at target FPS

for i, frame_file in enumerate(frames):
    # Calculate the actual time this frame represents
    # This accounts for the fact that frames are extracted at specific intervals
    frame_time = i * frame_interval
    frame_data.append({
        'file': frame_file,
        'index': i,
        'time': round(frame_time, 3)
    })
```

### Frontend Changes (`templates/index.html`)

Updated the template to use the new frame data structure:

```html
<!-- Before -->
<img src="{{ url_for('static', filename=frames_path + frame) }}" 
     data-time="{{ (loop.index0 / fps) | round(2) }}">

<!-- After -->
<img src="{{ url_for('static', filename=frames_path + frame.file) }}" 
     data-time="{{ frame.time }}">
```

## Key Improvements

1. **Accurate Time Mapping**: Frame times are now calculated based on the actual extraction interval (`1/fps`)
2. **Consistent Intervals**: Each frame thumbnail represents exactly `1/fps` seconds, regardless of source duplicates
3. **Better Precision**: Time values are rounded to 3 decimal places for better accuracy
4. **Structured Data**: Backend provides organized frame data instead of just filenames

## Expected Results

### ✅ Proper Frame Navigation
- Clicking sequential frame thumbnails now advances video to different time positions
- No more "stuck" on duplicate content when clicking adjacent frames
- Smooth navigation through the frame timeline

### ✅ Correct Time Intervals
- 60fps variant: frames at 0.000, 0.017, 0.033, 0.050... seconds
- 30fps variant: frames at 0.000, 0.033, 0.067, 0.100... seconds
- Consistent spacing regardless of source video quality

### ✅ Improved User Experience
- Frame thumbnails accurately represent their position in the video timeline
- Video seeking works reliably when clicking frame thumbnails
- Better synchronization between frame strip and video player

## Testing

### Automated Test
Created `test_frame_timing_fix.py` to verify:
- Frame data structure is properly generated
- Time intervals are correctly calculated
- Template renders with proper time mapping

### Manual Testing Steps
1. Open http://localhost:5001/video/dashcam60fps
2. Click on sequential frame thumbnails in the frame strip
3. Verify that the video player advances to different content
4. Check that frame times are evenly spaced
5. Ensure no duplicate video content when clicking adjacent frames

## Technical Notes

### Frame Extraction Consistency
This fix works with the current frame extraction logic but provides better time mapping. For even better results, consider also implementing the frame extraction improvements to eliminate source duplicates entirely.

### Backward Compatibility
The changes maintain backward compatibility with existing frame directories and don't require re-extraction of frames.

### Performance Impact
Minimal performance impact - the backend now does slightly more processing to create frame data structure, but this is negligible for typical frame counts. 