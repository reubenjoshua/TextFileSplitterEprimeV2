#!/usr/bin/env python3
"""
Test localhost backend connection
"""

import requests
import sys

def test_localhost():
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        print(f"✅ Backend is running on localhost!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Backend is NOT running on localhost:5000")
        print("Please start the backend with: cd PythonProject2 && py app_localhost.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing localhost backend connection...")
    print("=" * 40)
    
    if test_localhost():
        print("\n✅ Backend is ready!")
        print("Frontend should now connect successfully!")
    else:
        print("\n❌ Backend not running")
        print("\nTo start backend:")
        print("1. cd PythonProject2")
        print("2. py app_localhost.py")
        sys.exit(1)
