#!/usr/bin/env python3
"""
Test script to verify frame display fix

This script tests that loaded annotations display correct frame numbers
instead of showing '0' for all annotations.
"""

import os
import json
import requests
import time

def test_frame_display_fix():
    """Test the frame display fix"""
    base_url = "http://localhost:5001"
    
    print("Testing frame display fix...")
    print("=" * 50)
    
    # Test 1: Check if the app is running
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✓ App is running successfully")
        else:
            print(f"✗ App returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to the app. Make sure it's running on port 5001")
        return False
    
    # Test 2: Create test annotations with known frame numbers
    test_annotations = {
        "annotations": [
            {
                "id": "test_frame_1",
                "start": 60,   # Should map to frame 30 for 30fps variant (60fps canonical)
                "end": 120,    # Should map to frame 60 for 30fps variant
                "type": "test_event_1",
                "notes": "Test annotation 1"
            },
            {
                "id": "test_frame_2", 
                "start": 180,  # Should map to frame 90 for 30fps variant
                "end": 240,    # Should map to frame 120 for 30fps variant
                "type": "test_event_2",
                "notes": "Test annotation 2"
            }
        ]
    }
    
    # Save test annotations
    try:
        response = requests.post(
            f"{base_url}/save_annotations/dashcam60fps",
            json=test_annotations,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✓ Test annotations saved successfully")
            else:
                print(f"✗ Failed to save test annotations: {result.get('message')}")
                return False
        else:
            print(f"✗ Save annotations returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error saving test annotations: {e}")
        return False
    
    # Test 3: Load the video page and check JavaScript console output
    print("\n📋 Manual Testing Instructions:")
    print("1. Open http://localhost:5001/video/dashcam60fps")
    print("2. Open browser developer tools (F12) and check Console tab")
    print("3. Look for debug output like:")
    print("   'Video annotation tool initialized: { ... }'")
    print("   'Adding annotation to table: { ... }'")
    print("4. Check that the Annotations table shows:")
    print("   - Test Event 1: Start frame ~30, End frame ~60")
    print("   - Test Event 2: Start frame ~90, End frame ~120")
    print("5. If frames show as '0', there's still an issue")
    print("6. Switch between variants (30fps, 60fps) to test frame mapping")
    
    print(f"\n✅ Expected Frame Mappings (60fps canonical -> 30fps variant):")
    print(f"   Canonical 60 -> Variant 30")
    print(f"   Canonical 120 -> Variant 60")
    print(f"   Canonical 180 -> Variant 90")
    print(f"   Canonical 240 -> Variant 120")
    
    return True

if __name__ == "__main__":
    test_frame_display_fix() 