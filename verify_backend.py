import requests
import os
import time

BASE_URL = "http://localhost:8000"
ADMIN_KEY = "localdev123"

def test_api():
    print("🔍 Testing API endpoints...")
    
    # 1. Check healthy
    try:
        resp = requests.get(f"{BASE_URL}/api/docs")
        if resp.status_code == 200:
            print("✅ Backend is reachable at /api/docs")
        else:
            print(f"❌ Backend returned {resp.status_code} at /api/docs")
            return
    except Exception as e:
        print(f"❌ Backend unreachable: {str(e)}")
        return

    # 2. Check Static Pages
    for path in ["/", "/admin", "/about", "/services", "/contact"]:
        resp = requests.get(f"{BASE_URL}{path}")
        if resp.status_code == 200:
            print(f"✅ Page {path} is serving correctly")
        else:
            print(f"❌ Page {path} returned {resp.status_code}")

    print("\n🚀 API basic check complete.")


if __name__ == "__main__":
    test_api()
