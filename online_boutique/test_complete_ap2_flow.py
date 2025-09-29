#!/usr/bin/env python3
"""
Complete AP2 Autonomous Commerce Flow Test
Tests the full 6-step A2A + AP2 flow implementation
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
SHOPPING_AGENT_URL = os.environ.get('SHOPPING_AGENT_URL', 'http://localhost:8090')
PAYMENT_PROCESSOR_URL = os.environ.get('PAYMENT_PROCESSOR_URL', 'http://localhost:8092')
CATALOG_SERVICE_URL = os.environ.get('CATALOG_SERVICE_URL', 'http://localhost:8095')

def test_service_health(service_name, url):
    """Test if a service is running and healthy"""
    print(f"🔍 Testing {service_name} health...")
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {service_name} is healthy")
            if 'ap2_enabled' in data:
                print(f"   AP2 Enabled: {data['ap2_enabled']}")
            return True
        else:
            print(f"❌ {service_name} health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} connection failed: {e}")
        return False

def test_ap2_autonomous_commerce_flow():
    """Test the complete 6-step AP2 autonomous commerce flow"""
    print("\\n🛍️ Testing Complete AP2 Autonomous Commerce Flow...")
    print("=" * 60)
    
    # Test message that should trigger the full flow
    test_request = "I want to buy red shoes for $99"
    
    print(f"👤 User Request: '{test_request}'")
    print("\\n🔄 Starting 6-Step A2A + AP2 Flow:")
    print("   Step 1: User Request → Shopping Agent")
    print("   Step 2: Shopping Agent → Merchant Agents (IntentMandate)")
    print("   Step 3: Merchant Agent → Shopping Agent (CartMandate)")
    print("   Step 4: Shopping Agent → Merchant Agent (ContactAddress)")
    print("   Step 5: Shopping Agent → Payment Processor (PaymentMandate)")
    print("   Step 6: Payment Processor → Shopping Agent → User (Payment Result)")
    
    try:
        # Send request to shopping agent to trigger AP2 flow
        response = requests.post(
            f"{SHOPPING_AGENT_URL}/chat",
            json={
                "message": test_request,
                "context_id": f"test_flow_{int(time.time())}"
            },
            timeout=60,  # Longer timeout for multi-step flow
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\\n✅ AP2 Flow Response:")
            print(json.dumps(result, indent=2))
            
            # Analyze the response
            ap2_used = result.get('ap2_used', False)
            flow_completed = result.get('flow_completed', False)
            steps_completed = result.get('steps_completed', 0)
            processing_mode = result.get('processing_mode', 'unknown')
            
            print(f"\\n📊 Flow Analysis:")
            print(f"   AP2 Used: {'✅' if ap2_used else '❌'}")
            print(f"   Flow Completed: {'✅' if flow_completed else '❌'}")
            print(f"   Steps Completed: {steps_completed}/6")
            print(f"   Processing Mode: {processing_mode}")
            
            if ap2_used and flow_completed and steps_completed == 6:
                print("\\n🎉 SUCCESS: Complete AP2 autonomous commerce flow executed!")
                return True
            else:
                print("\\n⚠️ WARNING: AP2 flow partially completed or used fallback")
                return False
        else:
            print(f"❌ AP2 flow test failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ AP2 flow test error: {e}")
        return False

def test_session_management():
    """Test session management capabilities"""
    print("\\n🔄 Testing Session Management...")
    
    try:
        # Check active sessions
        response = requests.get(f"{SHOPPING_AGENT_URL}/sessions", timeout=10)
        
        if response.status_code == 200:
            sessions = response.json()
            print(f"✅ Session Management Working")
            print(f"   Active Sessions: {sessions.get('session_count', 0)}")
            
            if sessions.get('session_count', 0) > 0:
                print("   Recent Sessions:")
                for session_id in sessions.get('active_sessions', []):
                    print(f"     - {session_id}")
            
            return True
        else:
            print(f"❌ Session management test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Session management test error: {e}")
        return False

def test_ap2_message_format():
    """Test AP2 message format handling"""
    print("\\n📨 Testing AP2 Message Format...")
    
    # Test with AP2-formatted message
    ap2_message = {
        "parts": [
            {
                "type": "text",
                "content": "I want to buy a dress for $120"
            }
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "context_id": f"ap2_test_{int(time.time())}",
        "artifacts": {
            "ap2.mandates.IntentMandate": {
                "natural_language_description": "I want to buy a dress for $120",
                "user_cart_confirmation_required": True,
                "intent_expiry": (datetime.utcnow()).isoformat(),
                "merchants": None,
                "requires_refundability": False
            }
        }
    }
    
    try:
        response = requests.post(
            f"{SHOPPING_AGENT_URL}/ap2/message",
            json=ap2_message,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AP2 Message Format Handling Working")
            
            ap2_used = result.get('ap2_used', False)
            if ap2_used:
                print("   AP2 mandates properly processed")
                return True
            else:
                print("   ⚠️ AP2 mandates not recognized")
                return False
        else:
            print(f"❌ AP2 message format test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AP2 message format test error: {e}")
        return False

def test_payment_integration():
    """Test payment processor integration"""
    print("\\n💳 Testing Payment Processor Integration...")
    
    try:
        # Test direct payment processor
        payment_data = {
            "message": "Process payment for red shoes $99",
            "context_id": f"payment_test_{int(time.time())}"
        }
        
        response = requests.post(
            f"{PAYMENT_PROCESSOR_URL}/chat",
            json=payment_data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Payment Processor Integration Working")
            
            ap2_used = result.get('ap2_used', False)
            if ap2_used:
                print("   Payment processor supports AP2")
                return True
            else:
                print("   ⚠️ Payment processor using legacy mode")
                return True  # Still working, just not AP2
        else:
            print(f"❌ Payment processor test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Payment processor test error: {e}")
        return False

def main():
    """Run all AP2 flow tests"""
    print("🚀 Starting Complete AP2 Autonomous Commerce Flow Tests")
    print("=" * 70)
    
    test_results = []
    
    # Test service health
    test_results.append(("MCP Server Health", test_service_health("MCP Server", MCP_SERVER_URL)))
    test_results.append(("Shopping Agent Health", test_service_health("Shopping Agent", SHOPPING_AGENT_URL)))
    test_results.append(("Payment Processor Health", test_service_health("Payment Processor", PAYMENT_PROCESSOR_URL)))
    
    # Test AP2 functionality
    test_results.append(("AP2 Autonomous Commerce Flow", test_ap2_autonomous_commerce_flow()))
    test_results.append(("Session Management", test_session_management()))
    test_results.append(("AP2 Message Format", test_ap2_message_format()))
    test_results.append(("Payment Integration", test_payment_integration()))
    
    # Print summary
    print("\\n" + "=" * 70)
    print("📊 AP2 AUTONOMOUS COMMERCE TEST RESULTS")
    print("=" * 70)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<35} {status}")
        if result:
            passed += 1
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\\n🎉 All tests passed! AP2 autonomous commerce flow is ready!")
        print("\\n🛍️ The complete 6-step flow is working:")
        print("   1. ✅ User Request → Shopping Agent")
        print("   2. ✅ Shopping Agent → Merchant Agents (IntentMandate)")
        print("   3. ✅ Merchant Agent → Shopping Agent (CartMandate)")
        print("   4. ✅ Shopping Agent → Contact Collection")
        print("   5. ✅ Shopping Agent → Payment Processor (PaymentMandate)")
        print("   6. ✅ Payment Result → Shopping Agent → User")
    else:
        print("\\n⚠️ Some tests failed. Check the logs and configuration.")
        
    print("\\n📝 To test manually:")
    print(f"   curl -X POST {SHOPPING_AGENT_URL}/chat \\\\")
    print('     -H "Content-Type: application/json" \\\\')
    print('     -d \'{"message": "I want to buy red shoes for $99"}\'')
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
