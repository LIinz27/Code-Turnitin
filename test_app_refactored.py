"""
Test script untuk menguji refactored Flask application
"""
import requests
import json


def test_endpoints():
    """Test various endpoints of the refactored application"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Refactored Flask Application Endpoints...")
    
    # Test health endpoint
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Health check: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test web routes
    print("\n2. Testing Web Routes...")
    web_routes = ['/', '/auto-search', '/classroom', '/test-repos']
    
    for route in web_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {route}: OK")
            else:
                print(f"   ❌ {route}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {route}: {e}")
    
    # Test API endpoints (that don't require authentication)
    print("\n3. Testing API Endpoints...")
    
    # Test file info
    try:
        response = requests.get(f"{base_url}/api/files/info/mahasiswa", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ File info endpoint: {response.json()}")
        else:
            print(f"   ❌ File info failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ File info error: {e}")
    
    # Test classroom list (might require token)
    try:
        response = requests.get(f"{base_url}/api/classroom/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Classroom list: {data.get('count', 0)} classrooms")
        else:
            print(f"   ⚠️ Classroom list: {response.status_code} (might need token)")
    except Exception as e:
        print(f"   ⚠️ Classroom list error: {e}")
    
    print("\n✅ Endpoint testing completed!")


if __name__ == "__main__":
    test_endpoints()
