#!/usr/bin/env python3
"""
Test script for Nashville Zoning AI Assistant
Demonstrates the key functionality for commercial real estate developers
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_developer_analysis():
    """Test comprehensive developer analysis for a Nashville property"""
    print("🏢 Testing Comprehensive Developer Analysis")
    print("=" * 50)
    
    payload = {
        "address": "100 Broadway, Nashville, TN",
        "proposed_use": "mixed-use hotel and retail",
        "include_variance_analysis": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/zoning/developer-analysis", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Address: {data['address']}")
            print(f"📍 Coordinates: {data['coordinates']}")
            print(f"🏘️  Zoning District: {data['zoning_district']}")
            print(f"📊 Facts Extracted: {len(data['facts'])} items")
            print(f"📄 Sources: {len(data['sources'])} documents")
            print("\n📋 Detailed Analysis Preview:")
            print(data['detailed_analysis'][:500] + "...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_use_specific_analysis():
    """Test use-specific analysis for a restaurant development"""
    print("\n🍽️  Testing Use-Specific Analysis")
    print("=" * 50)
    
    payload = {
        "address": "456 Music Row, Nashville, TN",
        "use_type": "restaurant with outdoor seating and live music"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/zoning/use-analysis", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Address: {data['address']}")
            print(f"🏘️  Zoning District: {data['zoning_district']}")
            print(f"🎯 Use Type: {data['use_type']}")
            print(f"📄 Sources: {len(data['sources'])} documents")
            print("\n📋 Analysis Preview:")
            print(data['analysis'][:400] + "...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_variance_analysis():
    """Test variance analysis for a development project"""
    print("\n⚖️  Testing Variance Analysis")
    print("=" * 50)
    
    payload = {
        "address": "789 Hillsboro Pike, Nashville, TN",
        "zoning_district": "CS",
        "proposed_use": "multi-family residential with ground floor retail",
        "variance_types": ["height", "parking", "setback"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/zoning/variance-analysis", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Address: {data['address']}")
            print(f"🏘️  Zoning District: {data['zoning_district']}")
            print(f"🎯 Proposed Use: {data['proposed_use']}")
            print(f"📏 Variance Types: {', '.join(data['variance_types'])}")
            print(f"📄 Sources: {len(data['sources'])} documents")
            print("\n📋 Variance Analysis Preview:")
            print(data['analysis'][:400] + "...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_quick_snapshot():
    """Test quick zoning snapshot"""
    print("\n⚡ Testing Quick Zoning Snapshot")
    print("=" * 50)
    
    payload = {
        "address": "321 Demonbreun St, Nashville, TN",
        "focus": ["height", "setbacks", "parking", "permitted_uses"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/zoning/snapshot", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Address: {payload['address']}")
            print(f"📊 Facts: {len(data['facts'])} items")
            print("\n📋 Key Facts:")
            for key, value in data['facts'].items():
                print(f"  • {key}: {value}")
            print(f"\n📄 Sources: {len(data['sources'])} documents")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_geocoding():
    """Test address geocoding functionality"""
    print("\n🗺️  Testing Address Geocoding")
    print("=" * 50)
    
    from app.tools import geocode_address, get_zoning_district
    
    test_addresses = [
        "100 Broadway, Nashville, TN",
        "456 Music Row, Nashville, TN", 
        "789 Hillsboro Pike, Nashville, TN"
    ]
    
    for address in test_addresses:
        try:
            coords = geocode_address(address)
            if coords:
                zoning = get_zoning_district(coords)
                print(f"✅ {address}")
                print(f"   📍 Coordinates: {coords[0]:.4f}, {coords[1]:.4f}")
                print(f"   🏘️  Zoning District: {zoning}")
            else:
                print(f"❌ Could not geocode: {address}")
        except Exception as e:
            print(f"❌ Error geocoding {address}: {e}")

def main():
    """Run all tests"""
    print("🚀 Nashville Zoning AI Assistant - Test Suite")
    print("=" * 60)
    print("Make sure the API server is running: uvicorn app.api:app --reload")
    print("=" * 60)
    
    # Test geocoding first (doesn't require API)
    test_geocoding()
    
    # Test API endpoints
    test_quick_snapshot()
    test_use_specific_analysis()
    test_variance_analysis()
    test_developer_analysis()
    
    print("\n🎉 Test suite completed!")
    print("\n💡 Next steps:")
    print("1. Ensure Nashville Zoning Code 2025 PDF is in data/zoning_pdfs/")
    print("2. Run: uvicorn app.api:app --reload")
    print("3. Visit: http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    main()
