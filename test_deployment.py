#!/usr/bin/env python3
"""
Test deployed Building Defect Detector AI Training System
"""
import requests
import json

def test_deployment():
    """Test the deployed application with AI training features"""
    
    base_url = "https://defect-production.up.railway.app"
    
    print("🚀 Testing REDEPLOYED Building Defect Detector...")
    print(f"🌐 Base URL: {base_url}")
    
    try:
        # Test main page
        print("\n1️⃣ Testing main page...")
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Main page accessible")
            if "Building Defect Detector" in response.text:
                print("   ✅ Application title found")
            else:
                print("   ⚠️ Application title not found")
        else:
            print(f"   ❌ Main page error: {response.status_code}")
            
        # Test analytics page (where AI Training metrics are)
        print("\n2️⃣ Testing analytics page...")
        analytics_url = f"{base_url}/analytics"
        response = requests.get(analytics_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Analytics page accessible")
            if "AI Training" in response.text:
                print("   ✅ AI Training section found")
            if "User Feedback" in response.text:
                print("   ✅ User Feedback metrics found")
            if "Accuracy Rate" in response.text:
                print("   ✅ Accuracy Rate metrics found")
        else:
            print(f"   ❌ Analytics page error: {response.status_code}")
            
        # Test if the AI training data is reflected
        print("\n3️⃣ Checking for populated training metrics...")
        if "User Feedback" in response.text and "0%" not in response.text:
            print("   ✅ Training metrics appear to be populated (not all zeros)")
        else:
            print("   ⚠️ Training metrics might still be zero")
            
        print("\n📊 DEPLOYMENT VERIFICATION COMPLETE!")
        print("🎯 Visit the analytics page to see AI Training metrics:")
        print(f"   {analytics_url}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == '__main__':
    test_deployment()
