#!/usr/bin/env python3
"""
Test error handling edge cases
"""

import requests
import json

BASE_URL = "https://84fba3ec-51f2-495a-b130-c09fc152e76c.preview.emergentagent.com/api"

def test_error_cases():
    """Test various error scenarios"""
    
    print("=== ERROR HANDLING TESTS ===")
    
    # Test 1: Invalid barcode format
    print("\n1. Testing invalid barcode format...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-product",
            json={"barcode": "invalid123"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Empty barcode
    print("\n2. Testing empty barcode...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-product",
            json={"barcode": ""},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Non-existent but valid format barcode
    print("\n3. Testing non-existent barcode (valid format)...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-product",
            json={"barcode": "9999999999999"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 4: Missing barcode field
    print("\n4. Testing missing barcode field...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-product",
            json={},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 5: Test the third barcode that failed
    print("\n5. Testing third barcode (8712566451111)...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-product",
            json={"barcode": "8712566451111"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_error_cases()