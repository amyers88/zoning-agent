#!/usr/bin/env python3
import requests
import json

def test_api():
    try:
        # Test the API
        response = requests.get("http://localhost:8000/")
        print(f"UI Status: {response.status_code}")
        
        # Test developer analysis
        payload = {
            "address": "100 Broadway, Nashville, TN",
            "proposed_use": "mixed-use retail and office",
            "include_variance_analysis": True
        }
        
        response = requests.post("http://localhost:8000/zoning/developer-analysis", json=payload)
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Zoning District: {data.get('zoning_district', 'Unknown')}")
            print(f"Analysis length: {len(data.get('detailed_analysis', ''))}")
            print("✅ API is working!")
            return True
        else:
            print(f"❌ API error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    test_api()



