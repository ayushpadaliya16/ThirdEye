import requests
import json
import os
import time

BASE_URL = "http://127.0.0.1:8001"
TEST_IMG_PATH = "sample_test_portrait.jpg"
# Using Lena as a standard, universally accessible OpenCV test image
TEST_IMG_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"

def print_result(endpoint, passed, response=None):
    """Prints clean, color-coded terminal output."""
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    status = "PASS" if passed else "FAIL"
    
    print(f"\n[{color}{status}{reset}] Endpoint: {endpoint}")
    if response:
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)
    print("-" * 60)

def download_sample_image():
    """Downloads a sample image if it doesn't exist."""
    if not os.path.exists(TEST_IMG_PATH):
        print(f"Downloading sample image to {TEST_IMG_PATH}...")
        r = requests.get(TEST_IMG_URL)
        if r.status_code == 200:
            with open(TEST_IMG_PATH, 'wb') as f:
                f.write(r.content)
            print("Download complete.")
        else:
            print("Failed to download sample image.")

def run_tests():
    print("Starting Automated API Test Suite...")
    download_sample_image()
    
    # Allow the server a moment to boot if it was just started
    time.sleep(1)
    
    # 1. Health Check
    try:
        r = requests.get(f"{BASE_URL}/health")
        print_result("GET /health", r.status_code == 200, r)
    except requests.exceptions.ConnectionError:
        print(f"\n[\033[91mFAIL\033[0m] Cannot connect to server at {BASE_URL}. Is Uvicorn running?")
        return
        
    # 2. Profile API
    try:
        r = requests.post(f"{BASE_URL}/api/v1/analyze/profile", json={"username": "target_suspect", "connections": []})
        print_result("POST /api/v1/analyze/profile", r.status_code == 200, r)
    except Exception as e:
        print_result("POST /api/v1/analyze/profile", False)
        
    # 3. Media API
    if os.path.exists(TEST_IMG_PATH):
        try:
            with open(TEST_IMG_PATH, 'rb') as f:
                files = {'file': (TEST_IMG_PATH, f, 'image/jpeg')}
                r = requests.post(f"{BASE_URL}/api/v1/analyze/media", files=files)
                print_result("POST /api/v1/analyze/media", r.status_code == 200, r)
        except Exception as e:
            print_result("POST /api/v1/analyze/media", False)
    else:
        print("\n[\033[93mSKIP\033[0m] Skipping media tests (image not found).")
        
    # 4. Comprehensive API
    if os.path.exists(TEST_IMG_PATH):
        try:
            with open(TEST_IMG_PATH, 'rb') as f:
                files = {'file': (TEST_IMG_PATH, f, 'image/jpeg')}
                data = {'username': 'target_suspect'}
                r = requests.post(f"{BASE_URL}/api/v1/analyze/comprehensive", files=files, data=data)
                print_result("POST /api/v1/analyze/comprehensive", r.status_code == 200, r)
        except Exception as e:
            print_result("POST /api/v1/analyze/comprehensive", False)

if __name__ == "__main__":
    run_tests()
