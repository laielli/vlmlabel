# Annotation Bugs Fixes Summary

## Issues Fixed

### 1. Frame Numbers Displaying as '0' After Variant Switch

**Problem**: When switching between FPS variants, the start/stop frame numbers in the annotations list would display as '0' instead of the correct mapped frame numbers.

**Root Cause**: The JavaScript frame mapping functions were not properly initialized with the correct FPS and clip offset values from the template variables.

**Solution**: 
- Fixed the initialization of `fps`, `canonicalFps`, and `clipStartFrameOffset` variables to prioritize template variables over data attributes
- Added proper fallback chain: `variantFPS || data-attribute || default`
- Added debug logging to help troubleshoot frame mapping issues

**Code Changes**:
```javascript
// Before (problematic):
let fps = parseInt(videoPlayer.getAttribute('data-fps')) || 30;
let canonicalFps = parseInt(videoPlayer.getAttribute('data-canonical-fps')) || 30;

// After (fixed):
let fps = variantFPS || parseInt(videoPlayer.getAttribute('data-fps')) || 30;
let canonicalFps = canonicalFPS || parseInt(videoPlayer.getAttribute('data-canonical-fps')) || 30;
let clipStartFrameOffset = clipStartFrame || 0;
```

### 2. Minimum Frame Length Validation Too Strict

**Problem**: The annotation validator required a minimum of 3 frames between start and end, preventing single-frame annotations.

**Root Cause**: Overly strict validation logic that assumed all annotations needed to span multiple frames.

**Solution**: 
- Removed the minimum 3-frame validation check
- Changed validation from `start >= end` to `start > end` to allow single-frame annotations (where start == end)

**Code Changes**:
```javascript
// Before (too strict):
if (start >= end) {
    errors.push("End frame must be after start frame");
}
if (end - start < 3) {  // Minimum 3 frames
    errors.push("Annotation must be at least 3 frames long");
}

// After (allows single frames):
if (start > end) {
    errors.push("End frame must be at or after start frame");
}
// Removed minimum length check
```

## Technical Details

### Frame Mapping Logic
The frame mapping between variants works as follows:

1. **Canonical to Variant**: `((canonicalFrame - clipStartOffset) / canonicalFps) * variantFps`
2. **Variant to Canonical**: `(variantFrame / variantFps) * canonicalFps + clipStartOffset`

### Variable Initialization Order
The fix ensures proper initialization order:
1. Template variables (most reliable)
2. Video element data attributes (fallback)
3. Default values (last resort)

### Debug Logging
Added comprehensive logging to help troubleshoot frame mapping issues:
- Initialization values logging
- Frame mapping calculation logging when results are unexpected
- Console output for debugging variant switches

## Files Modified

1. **`static/js/script.js`**:
   - Fixed FPS variable initialization
   - Removed minimum frame length validation
   - Added debug logging
   - Improved frame mapping reliability

2. **`app.py`**:
   - Changed default port to 5001 to avoid conflicts

3. **`test_annotation_fixes.py`** (new):
   - Comprehensive test suite for the fixes
   - Validates single-frame annotation support
   - Tests frame mapping functionality

## Testing

### Automated Tests
- ✅ App startup and connectivity
- ✅ Video page loading with correct variables
- ✅ Single-frame annotation creation and saving
- ✅ Annotation loading and retrieval

### Manual Testing Steps
1. Open http://localhost:5001/video/dashcam60fps
2. Create an annotation with start and end frames
3. Switch to a different FPS variant (e.g., from 60fps to 30fps)
4. Verify frame numbers display correctly (not as '0')
5. Test single-frame annotations (start == end)
6. Edit any annotation to verify frame mapping works correctly

## Results

### ✅ Frame Number Display
- Frame numbers now display correctly after variant switches
- Proper mapping between canonical and variant frame numbers
- Debug logging helps identify any remaining issues

### ✅ Single-Frame Annotations
- Can now create annotations where start frame equals end frame
- Validation allows start == end (single frame)
- No more "must be at least 3 frames long" error

### ✅ Improved Reliability
- Better variable initialization prevents undefined values
- Fallback mechanisms ensure functionality even with missing data
- Debug logging aids in troubleshooting

## Browser Console Output
When working correctly, you should see initialization logging like:
```
Video annotation tool initialized: {
  videoId: "dashcam60fps",
  variant: "full_30", 
  fps: 30,
  canonicalFps: 60,
  clipStartFrameOffset: 0,
  ...
}
```

Any frame mapping issues will be logged with detailed calculation information for debugging. 