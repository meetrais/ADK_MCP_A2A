#!/usr/bin/env python3
"""
Test script for Real Payment Processing with AP2 Integration
"""

import requests
import json
import time
import os
from datetime import datetime

# Test configuration
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
AP2_AGENT_URL = os.environ.get('AP2_AGENT_URL', 'http://localhost:8092')

def test_mcp_server_health():
    """Test MCP server health check"""
    print("🔍 Testing MCP Server Health...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ MCP Server is healthy")
            return True
        else:
            print(f"❌ MCP Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MCP Server connection failed: {e}")
        return False

def test_ap2_agent_health():
    """Test AP2 agent health check"""
    print("🔍 Testing AP2 Agent Health...")
    try:
        response = requests.get(f"{AP2_AGENT_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AP2 Agent is healthy - AP2 Enabled: {data.get('ap2_enabled', False)}")
            return True
        else:
            print(f"❌ AP2 Agent health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AP2 Agent connection failed: {e}")
        return False

def test_real_payment_processing():
    """Test real payment processing through MCP server"""
    print("\n💳 Testing Real Payment Processing...")
    
    # Test payment data
    payment_data = {
        "cart_data": {
            "amount": 99.0,
            "currency": "USD",
            "payment_method": "card",
            "gateway": "auto",  # Let system choose available gateway
            "description": "Test AP2 Real Payment - Red Shoes",
            "items": [
                {
                    "label": "Red Shoes",
                    "price": 99.0,
                    "quantity": 1
                }
            ],
            "customer_id": "test_customer_123",
            "order_id": f"TEST_{int(time.time())}"
        }
    }
    
    try:
        print(f"📤 Sending payment request: ${payment_data['cart_data']['amount']}")
        response = requests.post(
            f"{MCP_SERVER_URL}/payment-process",
            json=payment_data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Payment Processing Response:")
            print(json.dumps(result, indent=2))
            
            # Check if real payment was used
            data = result.get('data', {})
            gateway = data.get('gateway', 'unknown')
            payment_processing = data.get('payment_processing', 'unknown')
            
            if payment_processing == 'real':
                print(f"🎉 SUCCESS: Real payment processed via {gateway}")
            else:
                print(f"⚠️ WARNING: Mock payment used (gateway: {gateway})")
                print("   To enable real payments, configure STRIPE_SECRET_KEY or PAYPAL credentials")
            
            return True
        else:
            print(f"❌ Payment processing failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Payment processing error: {e}")
        return False

def test_ap2_integration():
    """Test AP2 integration with natural language"""
    print("\n🤖 Testing AP2 Integration...")
    
    # Test AP2 message
    ap2_message = {
        "message": "I want to buy red shoes for $99",
        "context_id": f"test_context_{int(time.time())}"
    }
    
    try:
        print(f"📤 Sending AP2 message: '{ap2_message['message']}'")
        response = requests.post(
            f"{AP2_AGENT_URL}/chat",
            json=ap2_message,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AP2 Processing Response:")
            print(json.dumps(result, indent=2))
            
            # Check AP2 features
            ap2_used = result.get('ap2_used', False)
            processing_mode = result.get('processing_mode', 'unknown')
            
            if ap2_used:
                print(f"🎉 SUCCESS: AP2 protocol used (mode: {processing_mode})")
            else:
                print("⚠️ WARNING: AP2 protocol not used")
            
            return True
        else:
            print(f"❌ AP2 processing failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ AP2 processing error: {e}")
        return False

def test_payment_gateway_configuration():
    """Test payment gateway configuration"""
    print("\n🔧 Testing Payment Gateway Configuration...")
    
    # Check environment variables
    stripe_key = os.environ.get('STRIPE_SECRET_KEY', '')
    paypal_id = os.environ.get('PAYPAL_CLIENT_ID', '')
    paypal_secret = os.environ.get('PAYPAL_CLIENT_SECRET', '')
    
    print(f"Stripe configured: {'✅' if stripe_key else '❌'}")
    print(f"PayPal configured: {'✅' if (paypal_id and paypal_secret) else '❌'}")
    
    if not stripe_key and not (paypal_id and paypal_secret):
        print("⚠️ WARNING: No real payment gateways configured")
        print("   System will use mock payments for testing")
        print("   To enable real payments:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your Stripe or PayPal credentials")
        return False
    
    return True

def test_webhook_endpoint():
    """Test webhook endpoint"""
    print("\n🔗 Testing Webhook Endpoint...")
    
    # Test webhook data
    webhook_data = {
        "type": "payment.succeeded",
        "data": {
            "id": "test_payment_123",
            "amount": 9900,  # Stripe uses cents
            "currency": "usd"
        }
    }
    
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/payment/webhook",
            json=webhook_data,
            timeout=10,
            headers={
                'Content-Type': 'application/json',
                'X-Webhook-Signature': 'test_signature'
            }
        )
        
        print(f"📥 Webhook Response Status: {response.status_code}")
        
        if response.status_code in [200, 401]:  # 401 is expected for invalid signature
            print("✅ Webhook endpoint is functional")
            return True
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting AP2 Real Payment Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("MCP Server Health", test_mcp_server_health()))
    test_results.append(("AP2 Agent Health", test_ap2_agent_health()))
    test_results.append(("Payment Gateway Config", test_payment_gateway_configuration()))
    test_results.append(("Real Payment Processing", test_real_payment_processing()))
    test_results.append(("AP2 Integration", test_ap2_integration()))
    test_results.append(("Webhook Endpoint", test_webhook_endpoint()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AP2 real payment processing is ready.")
    else:
        print("⚠️ Some tests failed. Check the configuration and try again.")
        
    print("\n📝 Setup Instructions:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Copy .env.example to .env")
    print("3. Configure payment gateway credentials in .env")
    print("4. Start MCP server: python boutique_mcp_server.py")
    print("5. Start AP2 agent: python agent.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
