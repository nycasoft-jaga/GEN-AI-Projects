import requests
import sys
import json
import base64
import io
from PIL import Image
import numpy as np
from datetime import datetime
import time
import websocket
import threading

class HealthScanAPITester:
    def __init__(self, base_url="https://mind-body-health.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.ws_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=10)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def create_test_image(self):
        """Create a simple test image with a face-like pattern"""
        # Create a 200x200 RGB image
        img = Image.new('RGB', (200, 200), color='white')
        pixels = img.load()
        
        # Draw a simple face pattern
        for i in range(200):
            for j in range(200):
                # Face outline (circle)
                if 50 <= i <= 150 and 50 <= j <= 150:
                    dist = ((i-100)**2 + (j-100)**2)**0.5
                    if 40 <= dist <= 50:
                        pixels[i, j] = (200, 180, 160)  # Skin color
                    elif dist < 40:
                        pixels[i, j] = (220, 200, 180)  # Face
                
                # Eyes
                if 70 <= i <= 80 and 80 <= j <= 90:
                    pixels[i, j] = (0, 0, 0)  # Left eye
                if 70 <= i <= 80 and 110 <= j <= 120:
                    pixels[i, j] = (0, 0, 0)  # Right eye
                
                # Mouth
                if 120 <= i <= 130 and 90 <= j <= 110:
                    pixels[i, j] = (100, 50, 50)  # Mouth
        
        return img

    def test_health_check(self):
        """Test health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success and response.get('status') == 'healthy'

    def test_health_history(self):
        """Test health history endpoint"""
        success, response = self.run_test(
            "Health History",
            "GET",
            "api/health/history",
            200
        )
        return success and 'readings' in response

    def test_image_analysis(self):
        """Test image analysis endpoint"""
        # Create test image
        test_image = self.create_test_image()
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        files = {'file': ('test_face.jpg', img_byte_arr, 'image/jpeg')}
        
        success, response = self.run_test(
            "Image Analysis",
            "POST",
            "api/analyze/image",
            200,
            files=files
        )
        
        if success:
            print(f"   Faces detected: {response.get('faces_detected', 0)}")
            if response.get('results'):
                result = response['results'][0]
                print(f"   Emotion: {result.get('emotion')}")
                print(f"   Stress: {result.get('stress_level')}")
                print(f"   Anxiety: {result.get('anxiety_score')}")
                print(f"   Depression: {result.get('depression_score')}")
                print(f"   Glucose: {result.get('glucose_simulation')}")
        
        return success and response.get('success') == True

    def test_websocket_connection(self):
        """Test WebSocket connection"""
        print(f"\n🔍 Testing WebSocket Connection...")
        
        ws_url = self.base_url.replace('https://', 'wss://') + '/api/ws/scan'
        print(f"   WebSocket URL: {ws_url}")
        
        try:
            def on_message(ws, message):
                print(f"   📨 WebSocket message received: {message[:100]}...")
                try:
                    data = json.loads(message)
                    self.ws_results.append(data)
                    if data.get('type') == 'analysis_result':
                        print(f"   ✅ Analysis result received with {data.get('faces_detected', 0)} faces")
                except:
                    pass

            def on_error(ws, error):
                print(f"   ❌ WebSocket error: {error}")

            def on_close(ws, close_status_code, close_msg):
                print(f"   🔌 WebSocket closed: {close_status_code}")

            def on_open(ws):
                print(f"   ✅ WebSocket connected successfully")
                
                # Send test frame after connection
                def send_test_frame():
                    time.sleep(1)  # Wait a bit after connection
                    
                    # Create test image and convert to base64
                    test_image = self.create_test_image()
                    img_byte_arr = io.BytesIO()
                    test_image.save(img_byte_arr, format='JPEG')
                    img_byte_arr.seek(0)
                    
                    # Convert to base64
                    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                    data_url = f"data:image/jpeg;base64,{img_base64}"
                    
                    frame_data = {
                        "frame": data_url,
                        "timestamp": int(time.time() * 1000),
                        "scanMode": "face"
                    }
                    
                    print(f"   📤 Sending test frame...")
                    ws.send(json.dumps(frame_data))
                    
                    # Close after sending
                    time.sleep(3)
                    ws.close()

                thread = threading.Thread(target=send_test_frame)
                thread.start()

            ws = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run with timeout
            ws.run_forever(ping_timeout=10)
            
            # Check if we got results
            if self.ws_results:
                self.tests_passed += 1
                print(f"   ✅ WebSocket test passed - received {len(self.ws_results)} messages")
                return True
            else:
                print(f"   ❌ WebSocket test failed - no messages received")
                return False
                
        except Exception as e:
            print(f"   ❌ WebSocket test failed - Error: {str(e)}")
            return False
        finally:
            self.tests_run += 1

def main():
    print("🏥 HealthScan API Testing Suite")
    print("=" * 50)
    
    # Setup
    tester = HealthScanAPITester()
    
    # Run tests
    print("\n📋 Running Backend API Tests...")
    
    # Test 1: Health Check
    health_ok = tester.test_health_check()
    if not health_ok:
        print("❌ Health check failed - API may be down")
        print(f"\n📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
        return 1
    
    # Test 2: Health History
    history_ok = tester.test_health_history()
    
    # Test 3: Image Analysis
    analysis_ok = tester.test_image_analysis()
    
    # Test 4: WebSocket Connection
    websocket_ok = tester.test_websocket_connection()
    
    # Print final results
    print(f"\n📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    print("\n🔍 Test Summary:")
    print(f"   ✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"   ✅ Health History: {'PASS' if history_ok else 'FAIL'}")
    print(f"   ✅ Image Analysis: {'PASS' if analysis_ok else 'FAIL'}")
    print(f"   ✅ WebSocket: {'PASS' if websocket_ok else 'FAIL'}")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All backend tests passed!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())