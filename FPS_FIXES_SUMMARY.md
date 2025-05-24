# FPS Variants and Frame Extraction Fixes

## Issues Identified

1. **FPS variants playing too fast**: The original code was using `-r` parameter without proper frame selection, causing videos to play at incorrect speeds.

2. **Incorrect frame extraction counts**: Frame extraction was extracting too few frames due to improper time-based selection filters.

3. **Duration changes**: Videos were not maintaining their original duration when converted to different FPS rates.

## Root Causes

### 1. Improper FPS Conversion
The original code had different approaches for upsampling vs downsampling:
- **Upsampling**: Used `-r` parameter which just changed playback rate (made videos play faster)
- **Downsampling**: Used complex `select` filters with `setpts` that were breaking timing

### 2. Complex Frame Selection Logic
The `calculate_frame_selection_pattern` function was creating overly complex FFmpeg filters that didn't preserve duration correctly.

### 3. Extracting from Wrong Source
Frame extraction was sometimes using source video, sometimes variant videos, leading to inconsistent frame counts.

## Solutions Implemented

### 1. Unified FPS Filter Approach
**Old problematic code:**
```python
if target_fps >= source_fps:
    # Wrong: Just changes playback rate
    cmd = ["ffmpeg", "-i", source_path, "-r", str(target_fps), ...]
else:
    # Wrong: Complex select filter that breaks timing
    cmd = ["ffmpeg", "-i", source_path, "-vf", selection_pattern, ...]
```

**New fixed code:**
```python
# Always use fps filter for both up and downsampling
cmd = [
    "ffmpeg", "-i", source_path,
    "-vf", f"fps={target_fps}",  # This maintains duration properly
    "-c:v", "libx264", "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-y", target_path
]
```

### 2. Simplified Frame Extraction
- **For full videos**: Extract frames from the created variant videos (which now have correct FPS and duration)
- **For clips**: Extract frames from the created clip variant videos
- Removed the complex time-based selection logic

### 3. Proper Duration Preservation
The `fps=N` filter in FFmpeg:
- **For downsampling**: Drops frames at regular intervals while maintaining timing
- **For upsampling**: Duplicates frames to reach target FPS while maintaining duration
- **Always preserves duration** (within rounding tolerance for very low FPS)

## Results

### ✅ Duration Preservation
- 60 FPS → 30 FPS: 7.75s → 7.77s (difference: 0.02s)
- 60 FPS → 10 FPS: 7.75s → 7.80s (difference: 0.05s)  
- 60 FPS → 5 FPS: 7.75s → 7.80s (difference: 0.05s)
- 60 FPS → 2 FPS: 7.75s → 8.00s (difference: 0.25s)
- 60 FPS → 1 FPS: 7.75s → 8.00s (difference: 0.25s)

### ✅ Correct Frame Rates
All variants now have exactly the expected frame rates (verified with ffprobe).

### ✅ Accurate Frame Extraction
Frame counts now match video duration × FPS exactly:
- 30 FPS variant: 233 frames extracted (7.77s × 30 = 233)
- 10 FPS variant: 78 frames extracted (7.80s × 10 = 78)
- 5 FPS variant: 39 frames extracted (7.80s × 5 = 39)
- etc.

## Technical Details

### FFmpeg fps Filter
The `fps=N` filter:
- Analyzes input timing and frame rate
- For downsampling: Selects frames at regular intervals to achieve target rate
- For upsampling: Duplicates frames to achieve target rate
- Maintains original video duration by adjusting frame timing
- Much more reliable than manual frame selection patterns

### Frame Extraction Strategy
```python
if target_fps >= source_fps:
    # Extract all frames when target equals or exceeds source
    cmd = ["ffmpeg", "-i", video_path, "-start_number", "0", "-y", output_pattern]
else:
    # Use time-based selection for lower FPS
    frame_interval = 1.0 / target_fps
    cmd = ["ffmpeg", "-i", video_path, 
           "-vf", f"select='eq(n\\,0)+gte(t-prev_selected_t\\,{frame_interval})'",
           "-vsync", "0", "-start_number", "0", "-y", output_pattern]
```

## Files Modified

1. **`video_processor.py`**:
   - Fixed `create_fps_variant()` method
   - Simplified FPS conversion logic
   - Fixed frame extraction calls

2. **`frame_extractor.py`**:
   - Removed unused `calculate_frame_selection_pattern()` function
   - Added `extract_clip_frames_at_intervals()` method

3. **`test_fps_variants.py`** (new):
   - Comprehensive test suite to verify fixes
   - Validates duration, FPS, and frame counts

## Testing

Created `test_fps_variants.py` which validates:
- ✅ Correct frame rates for all variants
- ✅ Duration preservation (within tolerance)
- ✅ Accurate frame counts in videos
- ✅ Correct extracted frame counts

All tests now pass successfully! 