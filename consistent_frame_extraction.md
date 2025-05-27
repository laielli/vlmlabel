Great question — understanding how MP4 video encoding works is crucial when you’re using ffmpeg to extract frames, especially at different FPS rates. The core issue here is that MP4 is not just a collection of frames — it’s a compressed video format that uses inter-frame compression, meaning not every frame is fully self-contained. Here’s a breakdown of what’s happening under the hood and what it means for frame extraction:

⸻

🧠 MP4 Encoding: The Basics

MP4 is a container format — it can hold video, audio, subtitles, and metadata. For video, it typically uses a codec like H.264 (AVC) to encode the video stream.

1. Compression Strategy

H.264 compresses video by breaking it into Groups of Pictures (GOPs) made up of three types of frames:

Frame Type	Name	Description
I-frame	Intra-coded	Full image (keyframe)
P-frame	Predicted	Encodes changes from a previous I- or P-frame
B-frame	Bi-directional	Encodes changes from both past and future frames

✅ Only I-frames are fully self-contained. P- and B-frames depend on other frames to be decoded correctly.

⸻

🔍 Why This Matters for Frame Extraction

When you extract frames from an MP4 using ffmpeg, the tool has to decode frames in sequence, especially when it needs to extract non-I-frames. This introduces two key implications:

A. Seeking Can Be Imprecise

If you try to jump to timestamp t=10s and extract a frame, ffmpeg might actually seek to the nearest previous I-frame, then decode forward from there to get the exact frame you requested.
	•	This is why frame-accurate extraction can be slow or off by a few frames unless you decode sequentially or re-encode with all I-frames (see below).

B. Extracting at Different FPS Rates May Not Align

If you extract:
	•	One version at 5 FPS, and
	•	Another version at 10 FPS,

They might not align exactly frame-to-frame, unless you:
	1.	Decode from the same I-frame boundaries,
	2.	Use deterministic decoding, or
	3.	Re-encode to an I-frame-only version.

⸻

🛠️ How to Get Consistent Frame Extraction with ffmpeg

✅ Option 1: Re-encode to I-frame-only video

ffmpeg -i input.mp4 -g 1 -keyint_min 1 -sc_threshold 0 -x264opts "keyint=1:min-keyint=1:no-scenecut" -c:v libx264 -preset fast -crf 18 i_frames_only.mp4

	•	This forces every frame to be an I-frame.
	•	Frame extraction will now be deterministic and perfectly aligned across FPS variants.

✅ Option 2: Decode Entire Video and Then Extract

If you can afford the storage and time:

ffmpeg -i input.mp4 -vsync 0 frame_%05d.png

	•	This decodes the full stream into raw frames (preserving temporal accuracy).

Then, to extract specific FPS variants, you can do a second pass on the extracted images.

⸻

🧪 Example Use Case

Say you have a dashcam video and want to extract:
	•	30 FPS full video
	•	5 FPS clip focusing on an event

To keep annotations consistent:
	•	Re-encode to all I-frames first
	•	Or decode the full stream and post-process downsampled frame sequences

This ensures that frame X at 5 FPS and frame 6*X at 30 FPS are actually the same visual moment, and not off due to B/P-frame interpolation artifacts.

⸻

📝 Summary

Concept	Explanation
MP4 is compressed	Not all frames are full images; uses inter-frame compression
I-frames are key	Only I-frames are fully decodable without context
Random access = complex	Seeking requires decoding from the last I-frame
Frame alignment needs care	Different FPS extraction rates can desync without preprocessing
Solution	Re-encode to I-frame-only or decode the full video first


⸻

If you’d like, I can generate example ffmpeg commands tailored to your FPS variants and naming convention needs. Just let me know your target FPS presets.