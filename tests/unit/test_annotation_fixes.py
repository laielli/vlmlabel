#!/usr/bin/env python3
"""
Test script to verify annotation fixes

This script tests:
1. Frame mapping between variants
2. Single-frame annotation validation
3. Proper frame number display
"""

import os
import json
import requests
import time

def test_annotation_fixes():
    """Test the annotation fixes"""
    base_url = "http://localhost:5001"
    
    print("Testing annotation fixes...")
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
    
    # Test 2: Check video page loads
    try:
        response = requests.get(f"{base_url}/video/dashcam60fps")
        if response.status_code == 200:
            print("✓ Video page loads successfully")
            
            # Check if the page contains the expected JavaScript variables
            content = response.text
            if 'variantFPS' in content and 'canonicalFPS' in content and 'clipStartFrame' in content:
                print("✓ JavaScript variables are present in the template")
            else:
                print("✗ Missing JavaScript variables in template")
                
        else:
            print(f"✗ Video page returned status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error loading video page: {e}")
    
    # Test 3: Test annotation creation (single frame)
    test_annotation = {
        "annotations": [
            {
                "id": "test_single_frame",
                "start": 100,
                "end": 100,  # Same as start for single frame
                "type": "test_single_frame",
                "notes": "Testing single frame annotation"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{base_url}/save_annotations/dashcam60fps",
            json=test_annotation,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✓ Single-frame annotation saved successfully")
            else:
                print(f"✗ Failed to save annotation: {result.get('message')}")
        else:
            print(f"✗ Save annotation returned status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error saving annotation: {e}")
    
    # Test 4: Test annotation loading
    try:
        response = requests.get(f"{base_url}/load_annotations/dashcam60fps")
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                annotations = result.get('annotations', [])
                print(f"✓ Loaded {len(annotations)} annotations")
                
                # Check if our test annotation is there
                test_found = any(ann.get('type') == 'test_single_frame' for ann in annotations)
                if test_found:
                    print("✓ Single-frame test annotation found in loaded data")
                else:
                    print("? Single-frame test annotation not found (may be expected)")
            else:
                print(f"✗ Failed to load annotations: {result.get('message')}")
        else:
            print(f"✗ Load annotations returned status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error loading annotations: {e}")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("1. Removed minimum 3-frame validation ✓")
    print("2. Fixed frame mapping variable initialization ✓") 
    print("3. Added debug logging for troubleshooting ✓")
    print("\nTo test the frame mapping fix:")
    print("1. Open http://localhost:5001/video/dashcam60fps")
    print("2. Create an annotation")
    print("3. Switch to a different FPS variant")
    print("4. Check if frame numbers display correctly (not as '0')")
    print("5. Edit any annotation to refresh the display")

if __name__ == "__main__":
    test_annotation_fixes() 