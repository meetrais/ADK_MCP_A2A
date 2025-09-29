#!/usr/bin/env python3
"""
Test script for AP2 integration in the payment processor
"""

import requests
import json
from datetime import datetime, timedelta, timezone

def test_ap2_integration():
    """Test the AP2 integration via HTTP endpoints"""
    
    # Start the payment processor server first
    print("🧪 Testing AP2 Integration")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"   AP2 Enabled: {health_data.get('ap2_enabled', 'Unknown')}")
            print(f"   Supported Protocols: {health_data.get('supported_protocols', [])}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        print("   Make sure the payment processor server is running on port 8080")
        return False
    
    print("\n2. Testing agent card endpoint...")
    try:
        response = requests.get(f"{base_url}/agent-card")
        if response.status_code == 200:
            card_data = response.json()
            print(f"✅ Agent card retrieved")
            print(f"   Version: {card_data.get('version', 'Unknown')}")
            print(f"   Capabilities: {len(card_data.get('capabilities', []))} capabilities")
            print(f"   AP2 Config: {'Available' if 'ap2_config' in card_data else 'Not available'}")
        else:
            print(f"❌ Agent card failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent card error: {e}")
    
    print("\n3. Testing AP2 test endpoint...")
    try:
        response = requests.post(f"{base_url}/ap2/test")
        if response.status_code == 200:
            test_data = response.json()
            print(f"✅ AP2 test endpoint passed")
            print(f"   Test Status: {test_data.get('test_status', 'Unknown')}")
            print(f"   AP2 Enabled: {test_data.get('ap2_enabled', 'Unknown')}")
            
            if 'test_result' in test_data:
                result = test_data['test_result']
                print(f"   Processing Mode: {result.get('processing_mode', 'Unknown')}")
                print(f"   Response Status: {result.get('status', 'Unknown')}")
        else:
            print(f"❌ AP2 test failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ AP2 test error: {e}")
    
    print("\n4. Testing AP2 message endpoint with intent mandate...")
    try:
        # Create test intent mandate
        test_intent = {
            "natural_language_description": "I want to buy red basketball shoes",
            "user_cart_confirmation_required": True,
            "intent_expiry": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "merchants": None,
            "requires_refundability": False
        }
        
        # Create test message with AP2 data
        test_message = {
            "message": "Process this shopping intent",
            "artifacts": {
                "ap2.mandates.IntentMandate": test_intent
            },
            "context_id": "test_context_123",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = requests.post(
            f"{base_url}/ap2/message",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ AP2 message processing passed")
            print(f"   Processing Mode: {result_data.get('processing_mode', 'Unknown')}")
            print(f"   Status: {result_data.get('status', 'Unknown')}")
            print(f"   Agent: {result_data.get('agent', 'Unknown')}")
        else:
            print(f"❌ AP2 message processing failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ AP2 message processing error: {e}")
    
    print("\n5. Testing legacy chat endpoint...")
    try:
        legacy_message = {
            "message": '{"items": [{"name": "Test Item", "price": 10.99}], "payment_method": "Credit Card"}'
        }
        
        response = requests.post(
            f"{base_url}/chat",
            json=legacy_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"✅ Legacy chat endpoint passed")
            print(f"   Processing Mode: {result_data.get('processing_mode', 'Unknown')}")
            print(f"   Status: {result_data.get('status', 'Unknown')}")
        else:
            print(f"❌ Legacy chat failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Legacy chat error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 AP2 Integration Test Complete")
    return True

if __name__ == "__main__":
    print("AP2 Integration Test Script")
    print("Make sure to start the payment processor server first:")
    print("  cd online_boutique/online_boutique_manager/sub_agents/payment_processor")
    print("  python agent.py")
    print()
    
    input("Press Enter when the server is running...")
    test_ap2_integration()
