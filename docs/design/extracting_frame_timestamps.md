Yes — you absolutely can extract the exact timestamps of all I-frames using ffmpeg. This is a common technique for aligning annotations, identifying scene cuts, or optimizing frame extraction workflows.

⸻

✅ Extracting I-frame Timestamps with ffmpeg

Here’s a reliable command:

ffmpeg -i input.mp4 -vf "select='eq(pict_type\,I)'" -vsync vfr -an -f null - 2>&1 | grep 'pts_time'

🔍 What it does:
	•	-vf "select='eq(pict_type\,I)'": Only selects I-frames.
	•	-vsync vfr: Ensures timestamps reflect the actual frame times.
	•	-an: Ignores audio.
	•	-f null -: Discards actual frame output; we’re only interested in the logs.
	•	grep 'pts_time': Filters the log output to only show presentation timestamps.

⸻

🧪 Sample Output:

[Parsed_select_0 @ 0x...] n:0 pts:9000 pts_time:0.300
[Parsed_select_0 @ 0x...] n:25 pts:225000 pts_time:7.500
[Parsed_select_0 @ 0x...] n:50 pts:450000 pts_time:15.000
...

	•	pts_time is the timestamp in seconds.
	•	These timestamps are your I-frame positions.

⸻

🛠️ Optional: Write I-frame Timestamps to a File

ffmpeg -i input.mp4 -vf "select='eq(pict_type\,I)'" -vsync vfr -an -f csv - | grep -oP 'pts_time:\K[0-9.]+' > i_frame_timestamps.txt

This writes just the numeric timestamps to a plain text file, one per line, e.g.:

0.300
7.500
15.000
...


⸻

🔁 Bonus: Extract I-frames as Images with Timestamps

If you also want to save the I-frames themselves:

ffmpeg -i input.mp4 -vf "select='eq(pict_type\,I)',showinfo" -vsync vfr i_frame_%04d.png 2>&1 | grep showinfo

This will give you both the frames and the pts_time for each one via showinfo.

⸻

🧭 When to Use This

This technique is extremely useful for:
	•	Frame-to-frame annotation mapping
	•	Scene boundary detection
	•	Understanding GOP structure
	•	Debugging why certain extractions don’t align between FPS variants

⸻

Let me know if you’d like to convert these timestamps into frame indices at a specific FPS or map them to annotation frames — I can help with that too.