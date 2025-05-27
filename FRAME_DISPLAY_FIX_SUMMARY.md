# Frame Display Bug Fix Summary

## Issue Fixed

**Problem**: When loading annotations from existing data, all start/stop frame numbers were displaying as '0' in the annotations table, even though the correct frame numbers were stored. However, when editing an annotation, the correct frame numbers would appear in the form, and after updating, they would display correctly in the table.

## Root Cause Analysis

The issue was caused by the timing of when annotations were being loaded and displayed:

1. **Initial Loading**: Annotations were being loaded and displayed in the table immediately when the page loaded
2. **Video Metadata**: The video's metadata (including duration) wasn't available yet when the frame mapping calculations were performed
3. **Frame Mapping Failure**: The `mapCanonicalToVariant` function would fail because:
   - `videoPlayer.duration` was `0` or `undefined`
   - This caused the max frame calculation to be `0`
   - Frame mapping would return `0` for all frame numbers

## Solution Implemented

### 1. **Delayed Annotation Loading**
- Moved annotation loading to happen after video metadata is loaded
- Added event listener for `loadedmetadata` event
- Included fallback timeout (1000ms) in case metadata loading fails

### 2. **Improved Frame Mapping Function**
- Added validation for FPS variables before calculation
- Used reasonable default video duration (3600s) when video duration is unavailable
- Enhanced debug logging to identify mapping issues
- Better error handling for edge cases

### 3. **Debug Logging**
- Added comprehensive logging in `addAnnotationToTable` function
- Logs original canonical frames and mapped variant frames
- Shows FPS variables and clip offset values
- Helps troubleshoot future frame mapping issues

## Code Changes

### `static/js/script.js`

#### Frame Mapping Function
```javascript
// Before (problematic):
function mapCanonicalToVariant(canonicalFrame) {
    const maxCanonicalFrame = Math.floor((videoPlayer.duration || 0) * canonicalFps);
    // ... rest of function
}

// After (fixed):
function mapCanonicalToVariant(canonicalFrame) {
    // Ensure we have valid values for FPS variables
    if (!fps || !canonicalFps) {
        console.warn('FPS variables not properly initialized:', { fps, canonicalFps });
        return 0;
    }
    
    // Use reasonable default if video duration not available
    const videoDuration = videoPlayer.duration || 3600;
    const maxCanonicalFrame = Math.floor(videoDuration * canonicalFps);
    // ... rest of function
}
```

#### Annotation Loading Timing
```javascript
// Before (immediate loading):
if (typeof initialAnnotations !== 'undefined' && initialAnnotations.length > 0) {
    // Load annotations immediately
}

// After (delayed loading):
videoPlayer.addEventListener('loadedmetadata', function() {
    if (!annotationsLoaded) {
        loadInitialAnnotations();
        annotationsLoaded = true;
    }
});

// Fallback timeout
setTimeout(() => {
    if (!annotationsLoaded) {
        loadInitialAnnotations();
        annotationsLoaded = true;
    }
}, 1000);
```

## Testing

### Automated Test
- Created `test_frame_display_fix.py` with known frame mappings
- Tests canonical frames 60→30, 120→60, 180→90, 240→120 for 60fps→30fps conversion
- Verifies annotations are saved and can be loaded

### Manual Testing Steps
1. Open http://localhost:5001/video/dashcam60fps
2. Check browser console for debug output
3. Verify annotations table shows correct frame numbers (not '0')
4. Switch between variants to test frame mapping
5. Edit annotations to verify they still work correctly

## Expected Results

### ✅ Frame Number Display
- Loaded annotations now display correct variant frame numbers
- No more '0' values in the annotations table
- Frame mapping works correctly for all FPS variants

### ✅ Debug Information
- Console shows initialization values for troubleshooting
- Frame mapping calculations are logged when issues occur
- Video duration and FPS values are visible in debug output

### ✅ Backward Compatibility
- Existing annotations continue to work
- Edit functionality remains unchanged
- No impact on annotation saving/loading workflow

## Browser Console Output

When working correctly, you should see:
```
Video annotation tool initialized: {
  videoId: "dashcam60fps",
  variant: "full_30",
  fps: 30,
  canonicalFps: 60,
  clipStartFrameOffset: 0
}

Adding annotation to table: {
  originalStart: 60,
  originalEnd: 120,
  variantStartFrame: 30,
  variantEndFrame: 60,
  fps: 30,
  canonicalFps: 60,
  clipStartFrameOffset: 0
}
```

## Impact

This fix ensures that users see the correct frame numbers immediately when loading a page with existing annotations, eliminating the confusing behavior where they had to edit and update annotations to see the proper frame numbers. 