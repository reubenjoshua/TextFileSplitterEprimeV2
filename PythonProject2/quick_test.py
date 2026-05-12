#!/usr/bin/env python3
"""
Quick test to check if backend is running
"""

import requests
import json

def test_backend():
    try:
        # Test health endpoint
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Available payment modes: {data.get('available_payment_modes', [])}")
            return True
        else:
            print(f"Health check failed: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running!")
        print("Please start the backend with: cd PythonProject2 && python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_backend()


















