# Phase 2: Multi-Clip Variant Support

This phase adds support for temporal clips, allowing users to define and view specific segments of videos at different frame rates.

## Features Implemented

1. **Clip Definition in Config**: Define clips with time ranges and FPS options in config.yaml
2. **Two-Level Variant Selector**: UI now shows clips grouped by name with FPS options
3. **Timeline Mapping with Offsets**: Annotations correctly map between canonical timeline and clip variants
4. **Preprocessing Tool**: New script to generate clip variants from source videos

## How to Use

### Step 1: Define Clips in Config

Edit `config.yaml` to define clip segments:

```yaml
videos:
  - id: soccer_game
    source_video: input_videos/soccer_game.mp4
    canonical_variant: full_30
    fps_variants: [30, 10, 5]
    clips:
      - name: kick_off
        label: "Kick-off"
        start: "00:00:00.0"
        end:   "00:01:00.0"
        fps: [30, 5]
      - name: penalty
        label: "Penalty"
        start: "00:45:10.0"
        end:   "00:45:40.0"
        fps: [30]
```

### Step 2: Process Clips

Run the preprocessing script to generate clip variants:

```bash
python preprocess_clips.py
```

To process a specific video:

```bash
python preprocess_clips.py --video-id soccer_game
```

### Step 3: Use the Application

- Launch the application with `python app.py`
- Navigate to a video
- The variant dropdown now has clip sections with FPS options
- Select any clip or full-video variant to view it
- Annotations will automatically map to the correct position

## Directory Structure

After preprocessing, your directory will look like:

```
static/
 └─ videos/soccer_game/
      soccer_game__full_30.mp4
      soccer_game__full_10.mp4
      soccer_game__full_5.mp4
      soccer_game__kick_off_30.mp4
      soccer_game__kick_off_5.mp4
      soccer_game__penalty_30.mp4
 └─ frames/soccer_game/
      full_30/frame_0000.jpg
      full_10/frame_0000.jpg
      full_5/frame_0000.jpg
      kick_off_30/frame_0000.jpg
      kick_off_5/frame_0000.jpg
      penalty_30/frame_0000.jpg
```

## Technical Details

### Mapping Formulas

- **Canonical to Variant**: `variant_frame = round(((canon - clipStartCanon) / C_FPS) * V_FPS)`
- **Variant to Canonical**: `canon = round((variant_frame / V_FPS) * C_FPS) + clipStartCanon`

Where `clipStartCanon = 0` for full-video variants.

## Next Steps

Phase 3 will add support for on-the-fly variant generation with user-defined time ranges and FPS settings. 