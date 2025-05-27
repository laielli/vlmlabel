#!/usr/bin/env python3
"""
Test script to demonstrate how different frame spacing affects visual differences.
"""

import os
import sys
from PIL import Image

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

def test_frame_spacing_solutions():
    """Test different frame spacing to find optimal visual differences"""
    
    frames_dir = "static/videos/dashcam60fps/frames/full_30"
    
    if not os.path.exists(frames_dir):
        print(f"❌ Frames directory not found: {frames_dir}")
        return False
    
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    
    print("🔍 FRAME SPACING ANALYSIS")
    print("=" * 60)
    print("Testing different frame intervals to find optimal visual differences")
    print()
    
    # Test different spacing intervals
    spacings = [1, 2, 3, 5, 10, 15, 30]  # frames apart
    
    for spacing in spacings:
        if spacing >= len(frame_files):
            continue
            
        print(f"📏 SPACING: {spacing} frames apart")
        print(f"   Time interval: {spacing * (1/30):.3f} seconds")
        
        # Test first few frame pairs with this spacing
        differences = []
        for i in range(min(5, len(frame_files) - spacing)):
            frame1 = frame_files[i]
            frame2 = frame_files[i + spacing]
            
            frame1_path = os.path.join(frames_dir, frame1)
            frame2_path = os.path.join(frames_dir, frame2)
            
            diff = calculate_image_difference(frame1_path, frame2_path)
            if diff is not None:
                differences.append(diff)
                print(f"   {frame1} vs {frame2}: {diff:.2f}%")
        
        if differences:
            avg_diff = sum(differences) / len(differences)
            print(f"   Average difference: {avg_diff:.2f}%")
            
            if avg_diff < 1.0:
                print(f"   ❌ TOO SIMILAR (<1%)")
            elif avg_diff < 5.0:
                print(f"   ⚠️  SOMEWHAT SIMILAR (<5%)")
            else:
                print(f"   ✅ GOOD VISUAL DIFFERENCE (≥5%)")
        print()
    
    # Recommend optimal spacing
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    print("Based on the analysis above:")
    print()
    print("For dashcam footage with slow movement:")
    print("• Use 5-10 frame spacing (5-10fps extraction from 30fps)")
    print("• This provides 0.167-0.333 second intervals")
    print("• Should give 2-10% visual difference between frames")
    print()
    print("Implementation options:")
    print("1. Extract frames at 5fps instead of 30fps")
    print("2. Extract every 6th frame from current 30fps extraction")
    print("3. Use adaptive spacing based on motion detection")
    
    return True

if __name__ == "__main__":
    print("Frame Spacing Solution Analysis")
    print("=" * 60)
    
    success = test_frame_spacing_solutions()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Frame spacing analysis completed")
        print("\nNext steps:")
        print("1. Re-extract frames at 5-10fps for better visual differences")
        print("2. Or modify the UI to skip frames for better navigation")
    else:
        print("❌ Frame spacing analysis failed")
    
    sys.exit(0 if success else 1) 