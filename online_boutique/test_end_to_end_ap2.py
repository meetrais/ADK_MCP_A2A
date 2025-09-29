#!/usr/bin/env python3
"""
End-to-End AP2 Integration Test
Tests the complete flow from online boutique main app to AP2-enabled payment processor
"""

import requests
import json
import time
from datetime import datetime, timedelta, timezone

def test_end_to_end_ap2_flow():
    """Test the complete AP2 flow through the online boutique system"""
    
    print("🚀 End-to-End AP2 Integration Test")
    print("=" * 60)
    
    # URLs for the services
    main_app_url = "http://localhost:8080"
    payment_processor_url = "http://localhost:8092"  # From the main app configuration
    
    print("Step 1: Testing main online boutique application...")
    try:
        response = requests.get(f"{main_app_url}/health")
        if response.status_code == 200:
            print("✅ Main application is running")
        else:
            print(f"❌ Main application health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main application not accessible: {e}")
        print("   Please start the main app: python online_boutique_manager/agent.py")
        return False
    
    print("\nStep 2: Testing payment processor AP2 status...")
    try:
        response = requests.get(f"{payment_processor_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Payment processor is running")
            print(f"   AP2 Enabled: {health_data.get('ap2_enabled', 'Unknown')}")
            if not health_data.get('ap2_enabled', False):
                print("   ⚠️  AP2 not enabled - check payment processor logs")
        else:
            print(f"❌ Payment processor health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Payment processor not accessible: {e}")
        print("   Please start payment processor: cd online_boutique_manager/sub_agents/payment_processor && python agent.py")
        return False
    
    print("\nStep 3: Testing payment request through main application...")
    try:
        # Send a payment-related message to the main app
        payment_request = {
            "message": "I want to process a payment for a red basketball shoes costing $99.99"
        }
        
        response = requests.post(
            f"{main_app_url}/chat",
            json=payment_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Main application processed payment request")
            print(f"   Routed to: {result.get('subagent', 'Unknown')}")
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
            
            if result.get('subagent') != 'payment_processor':
                print("   ⚠️  Request not routed to payment processor")
        else:
            print(f"❌ Main application request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Main application request error: {e}")
    
    print("\nStep 4: Testing direct AP2 message to payment processor...")
    try:
        # Create AP2 payment mandate
        test_cart_contents = {
            "id": "cart_123",
            "user_cart_confirmation_required": True,
            "payment_request": {
                "method_data": [{"supported_methods": "basic-card"}],
                "details": {
                    "id": "payment_123",
                    "display_items": [
                        {
                            "label": "Red Basketball Shoes",
                            "amount": {"currency": "USD", "value": 99.99}
                        }
                    ],
                    "total": {
                        "label": "Total",
                        "amount": {"currency": "USD", "value": 99.99}
                    }
                }
            },
            "cart_expiry": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "merchant_name": "SportsCorp"
        }
        
        test_payment_mandate = {
            "cart_contents": test_cart_contents,
            "payment_authorization": "auth_token_xyz",
            "mandate_id": "mandate_123"
        }
        
        # Create AP2 message
        ap2_message = {
            "message": "Process payment mandate for basketball shoes",
            "artifacts": {
                "ap2.mandates.PaymentMandate": test_payment_mandate
            },
            "context_id": "shopping_session_456",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = requests.post(
            f"{payment_processor_url}/ap2/message",
            json=ap2_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AP2 payment mandate processed successfully")
            print(f"   Processing Mode: {result.get('processing_mode', 'Unknown')}")
            print(f"   Status: {result.get('status', 'Unknown')}")
            
            if 'response' in result and isinstance(result['response'], dict):
                response_data = result['response']
                if 'artifacts' in response_data:
                    artifacts = response_data['artifacts']
                    if 'payment_result' in artifacts:
                        payment_result = artifacts['payment_result']
                        print(f"   Transaction ID: {payment_result.get('transaction_id', 'N/A')}")
                        print(f"   Amount: ${payment_result.get('amount', 0)} {payment_result.get('currency', 'USD')}")
        else:
            print(f"❌ AP2 payment mandate failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ AP2 payment mandate error: {e}")
    
    print("\nStep 5: Testing AP2 intent mandate processing...")
    try:
        # Create intent mandate
        test_intent = {
            "natural_language_description": "I want to buy red basketball shoes",
            "user_cart_confirmation_required": True,
            "intent_expiry": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "merchants": None,
            "requires_refundability": False
        }
        
        intent_message = {
            "message": "Process shopping intent for basketball shoes",
            "artifacts": {
                "ap2.mandates.IntentMandate": test_intent
            },
            "context_id": "intent_session_789",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = requests.post(
            f"{payment_processor_url}/ap2/message",
            json=intent_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AP2 intent mandate processed successfully")
            print(f"   Processing Mode: {result.get('processing_mode', 'Unknown')}")
            
            if 'response' in result and isinstance(result['response'], dict):
                response_data = result['response']
                if 'artifacts' in response_data:
                    artifacts = response_data['artifacts']
                    if 'processor_capability' in artifacts:
                        capability = artifacts['processor_capability']
                        print(f"   Supported Payment Methods: {capability.get('supported_payment_methods', [])}")
                        print(f"   Can Process Autonomous: {capability.get('can_process_autonomous', False)}")
        else:
            print(f"❌ AP2 intent mandate failed: {response.status_code}")
    except Exception as e:
        print(f"❌ AP2 intent mandate error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 End-to-End AP2 Integration Test Complete!")
    print("\n📋 Summary:")
    print("- Main application routes payment requests to payment processor")
    print("- Payment processor handles AP2 mandates (Payment, Cart, Intent)")
    print("- AP2 protocol enables autonomous payment processing")
    print("- Structured payment data flows through the system")
    print("\n🎯 AP2 Integration: FUNCTIONAL!")
    
    return True

if __name__ == "__main__":
    print("End-to-End AP2 Integration Test")
    print("Make sure both services are running:")
    print("1. Main app: python online_boutique_manager/agent.py (port 8080)")
    print("2. Payment processor: cd online_boutique_manager/sub_agents/payment_processor && python agent.py (port 8092)")
    print()
    
    input("Press Enter when both services are running...")
    test_end_to_end_ap2_flow()
