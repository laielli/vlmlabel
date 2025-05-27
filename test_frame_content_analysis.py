#!/usr/bin/env python3
"""
Test script to analyze frame image content for visual differences.
This helps determine if the frame alignment issue is due to identical visual content.
"""

import os
import sys
from PIL import Image
import hashlib

def calculate_image_hash(image_path):
    """Calculate a simple hash of an image for comparison"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to a standard size for comparison
            img = img.resize((64, 64))
            
            # Get pixel data
            pixels = list(img.getdata())
            
            # Create a simple hash
            pixel_string = ''.join([f"{r}{g}{b}" for r, g, b in pixels])
            return hashlib.md5(pixel_string.encode()).hexdigest()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def calculate_image_difference(image1_path, image2_path):
    """Calculate the visual difference between two images"""
    try:
        with Image.open(image1_path) as img1, Image.open(image2_path) as img2:
            # Convert to RGB and resize
            img1 = img1.convert('RGB').resize((64, 64))
            img2 = img2.convert('RGB').resize((64, 64))
            
            # Get pixel data
            pixels1 = list(img1.getdata())
            pixels2 = list(img2.getdata())
            
            # Calculate difference
            total_diff = 0
            for (r1, g1, b1), (r2, g2, b2) in zip(pixels1, pixels2):
                total_diff += abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
            
            # Normalize to percentage
            max_possible_diff = len(pixels1) * 3 * 255  # 3 channels, max value 255
            percentage_diff = (total_diff / max_possible_diff) * 100
            
            return percentage_diff
    except Exception as e:
        print(f"Error comparing {image1_path} and {image2_path}: {e}")
        return None

def analyze_frame_content():
    """Analyze frame content for visual differences"""
    
    frames_dir = "static/videos/dashcam60fps/frames/full_30"
    
    if not os.path.exists(frames_dir):
        print(f"❌ Frames directory not found: {frames_dir}")
        return False
    
    # Get the first 10 frames for analysis
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])[:10]
    
    if len(frame_files) < 5:
        print(f"❌ Not enough frames found. Need at least 5, found {len(frame_files)}")
        return False
    
    print("🔍 FRAME CONTENT ANALYSIS")
    print("=" * 50)
    
    # Calculate hashes for each frame
    frame_hashes = {}
    for frame_file in frame_files:
        frame_path = os.path.join(frames_dir, frame_file)
        frame_hash = calculate_image_hash(frame_path)
        frame_hashes[frame_file] = frame_hash
        print(f"Frame {frame_file}: hash={frame_hash[:8]}...")
    
    print("\n📊 FRAME COMPARISON ANALYSIS")
    print("=" * 50)
    
    # Compare consecutive frames
    for i in range(len(frame_files) - 1):
        frame1 = frame_files[i]
        frame2 = frame_files[i + 1]
        
        frame1_path = os.path.join(frames_dir, frame1)
        frame2_path = os.path.join(frames_dir, frame2)
        
        # Calculate visual difference
        diff_percentage = calculate_image_difference(frame1_path, frame2_path)
        
        # Check hash similarity
        hash1 = frame_hashes[frame1]
        hash2 = frame_hashes[frame2]
        hashes_identical = hash1 == hash2
        
        print(f"{frame1} vs {frame2}:")
        print(f"  Visual difference: {diff_percentage:.2f}%")
        print(f"  Hashes identical: {hashes_identical}")
        
        if diff_percentage is not None and diff_percentage < 1.0:
            print(f"  ⚠️  VERY SIMILAR CONTENT (<1% difference)")
        elif diff_percentage is not None and diff_percentage < 5.0:
            print(f"  ⚠️  SIMILAR CONTENT (<5% difference)")
        else:
            print(f"  ✅ DISTINCT CONTENT")
        print()
    
    # Specific test for frames 3 and 4 (the problematic case)
    frame_0003 = "frame_0003.jpg"
    frame_0004 = "frame_0004.jpg"
    
    if frame_0003 in frame_files and frame_0004 in frame_files:
        print("🎯 SPECIFIC TEST: frame_0003.jpg vs frame_0004.jpg")
        print("=" * 50)
        
        frame3_path = os.path.join(frames_dir, frame_0003)
        frame4_path = os.path.join(frames_dir, frame_0004)
        
        diff_percentage = calculate_image_difference(frame3_path, frame4_path)
        hash3 = frame_hashes[frame_0003]
        hash4 = frame_hashes[frame_0004]
        
        print(f"Visual difference: {diff_percentage:.2f}%")
        print(f"Hash 3: {hash3}")
        print(f"Hash 4: {hash4}")
        print(f"Hashes identical: {hash3 == hash4}")
        
        if diff_percentage is not None and diff_percentage < 1.0:
            print("❌ PROBLEM IDENTIFIED: Frames 3 and 4 have nearly identical visual content!")
            print("   This explains why clicking between them doesn't appear to change the video.")
            print("   The frame alignment is working correctly, but the visual content is too similar to notice.")
        else:
            print("✅ Frames 3 and 4 have distinct visual content")
    
    return True

def check_frame_extraction_quality():
    """Check if frame extraction was done correctly"""
    
    print("\n🔧 FRAME EXTRACTION QUALITY CHECK")
    print("=" * 50)
    
    frames_dir = "static/videos/dashcam60fps/frames/full_30"
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    
    print(f"Total frames found: {len(frame_files)}")
    print(f"First frame: {frame_files[0] if frame_files else 'None'}")
    print(f"Last frame: {frame_files[-1] if frame_files else 'None'}")
    
    # Check for sequential numbering
    expected_sequence = True
    for i, frame_file in enumerate(frame_files[:20]):  # Check first 20
        expected_name = f"frame_{i:04d}.jpg"
        if frame_file != expected_name:
            expected_sequence = False
            print(f"⚠️  Sequence break: expected {expected_name}, found {frame_file}")
    
    if expected_sequence:
        print("✅ Frame numbering is sequential")
    else:
        print("❌ Frame numbering has gaps or irregularities")
    
    # Check frame file sizes
    frame_sizes = []
    for frame_file in frame_files[:10]:
        frame_path = os.path.join(frames_dir, frame_file)
        size = os.path.getsize(frame_path)
        frame_sizes.append(size)
        print(f"{frame_file}: {size:,} bytes")
    
    # Check for suspiciously similar file sizes (might indicate duplicate frames)
    avg_size = sum(frame_sizes) / len(frame_sizes)
    size_variance = sum((size - avg_size) ** 2 for size in frame_sizes) / len(frame_sizes)
    size_std_dev = size_variance ** 0.5
    
    print(f"\nFile size statistics:")
    print(f"Average size: {avg_size:,.0f} bytes")
    print(f"Standard deviation: {size_std_dev:,.0f} bytes")
    print(f"Coefficient of variation: {(size_std_dev / avg_size) * 100:.1f}%")
    
    if size_std_dev / avg_size < 0.1:  # Less than 10% variation
        print("⚠️  Very similar file sizes - might indicate duplicate or very similar frames")
    else:
        print("✅ File sizes show normal variation")

if __name__ == "__main__":
    print("Frame Content Analysis Tool")
    print("=" * 50)
    
    success = True
    
    # Analyze frame content
    if not analyze_frame_content():
        success = False
    
    # Check extraction quality
    check_frame_extraction_quality()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Frame content analysis completed")
    else:
        print("❌ Frame content analysis failed")
    
    sys.exit(0 if success else 1) 