#!/usr/bin/env python3
"""
AP2 Autonomous Commerce System Startup Script
Starts all services required for the 6-step A2A + AP2 flow
"""

import os
import sys
import time
import subprocess
import requests
from threading import Thread

# Service configurations
SERVICES = {
    "mcp_server": {
        "script": "online_boutique_manager/simple_mcp_server/boutique_mcp_server.py",
        "port": 8080,
        "name": "MCP Server",
        "required": True
    },
    "payment_processor": {
        "script": "online_boutique_manager/sub_agents/payment_processor/agent.py", 
        "port": 8092,
        "name": "Payment Processor Agent",
        "required": True
    },
    "shopping_agent": {
        "script": "online_boutique_manager/shopping_agent.py",
        "port": 8090,
        "name": "AP2 Shopping Agent",
        "required": True
    },
    "catalog_service": {
        "script": "online_boutique_manager/sub_agents/catalog_service/agent.py",
        "port": 8095,
        "name": "Catalog Service Agent",
        "required": False
    }
}

def check_service_health(port, name, timeout=5):
    """Check if a service is running and healthy"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_service(service_name, config):
    """Start a service in the background"""
    script_path = config["script"]
    port = config["port"]
    name = config["name"]
    
    print(f"🚀 Starting {name} on port {port}...")
    
    try:
        # Start the service
        process = subprocess.Popen([
            sys.executable, script_path
        ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for startup
        time.sleep(2)
        
        # Check if it's running
        if check_service_health(port, name):
            print(f"✅ {name} started successfully on port {port}")
            return process
        else:
            print(f"⚠️ {name} starting (may take a moment)...")
            return process
            
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def wait_for_services():
    """Wait for all services to be healthy"""
    print("\n⏳ Waiting for all services to be ready...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        all_ready = True
        
        for service_name, config in SERVICES.items():
            if config["required"] and not check_service_health(config["port"], config["name"]):
                all_ready = False
                break
        
        if all_ready:
            print("✅ All services are ready!")
            return True
        
        print(f"   Attempt {attempt + 1}/{max_attempts} - waiting...")
        time.sleep(2)
    
    print("⚠️ Some services may still be starting...")
    return False

def show_service_status():
    """Show status of all services"""
    print("\n📊 Service Status:")
    print("=" * 50)
    
    for service_name, config in SERVICES.items():
        port = config["port"]
        name = config["name"]
        required = "Required" if config["required"] else "Optional"
        
        if check_service_health(port, name):
            status = "✅ Running"
        else:
            status = "❌ Not Running"
        
        print(f"{name:<25} Port {port:<6} {status:<12} ({required})")

def run_test():
    """Run the complete AP2 flow test"""
    print("\n🧪 Running AP2 Flow Test...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_complete_ap2_flow.py"
        ], cwd=os.getcwd(), capture_output=True, text=True, timeout=120)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠️ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main startup routine"""
    print("🚀 Starting AP2 Autonomous Commerce System")
    print("=" * 60)
    print("🛍️ 6-Step A2A + AP2 Flow Implementation")
    print("   1. User Request → Shopping Agent")
    print("   2. Shopping Agent → Merchant Agents (IntentMandate)")
    print("   3. Merchant Agent → Shopping Agent (CartMandate)")
    print("   4. Shopping Agent → Contact Collection")
    print("   5. Shopping Agent → Payment Processor (PaymentMandate)")
    print("   6. Payment Result → Shopping Agent → User")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("online_boutique_manager"):
        print("❌ Please run this script from the online_boutique directory")
        sys.exit(1)
    
    # Start all services
    processes = {}
    
    for service_name, config in SERVICES.items():
        if config["required"] or len(sys.argv) > 1 and "all" in sys.argv:
            process = start_service(service_name, config)
            if process:
                processes[service_name] = process
    
    # Wait for services to be ready
    wait_for_services()
    
    # Show status
    show_service_status()
    
    # Run test if requested
    if len(sys.argv) > 1 and "test" in sys.argv:
        test_passed = run_test()
        if test_passed:
            print("\n🎉 All tests passed! System is ready for use.")
        else:
            print("\n⚠️ Some tests failed. Check the output above.")
    
    print("\n📋 System Information:")
    print("=" * 50)
    print("🛍️ Shopping Agent (Main):     http://localhost:8090")
    print("💳 Payment Processor:         http://localhost:8092") 
    print("🏪 MCP Server:               http://localhost:8080")
    print("📦 Catalog Service:          http://localhost:8095")
    
    print("\n📝 Quick Test Commands:")
    print("=" * 50)
    print('# Test the complete AP2 flow:')
    print('curl -X POST http://localhost:8090/chat \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"message": "I want to buy red shoes for $99"}\'')
    
    print('\n# Check active sessions:')
    print('curl http://localhost:8090/sessions')
    
    print('\n# Health check all services:')
    print('python test_complete_ap2_flow.py')
    
    print(f"\n🔧 Configuration:")
    print("   Set environment variables in .env file to configure:")
    print("   - STRIPE_SECRET_KEY for real Stripe payments")
    print("   - PAYPAL_CLIENT_ID/SECRET for PayPal payments")
    print("   - MCP_SERVER_URL to change MCP server location")
    
    if processes:
        print(f"\n⚡ Services running. Press Ctrl+C to stop all services.")
        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping all services...")
            for name, process in processes.items():
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"✅ Stopped {name}")
                except:
                    process.kill()
                    print(f"🔪 Force killed {name}")
            print("👋 All services stopped.")

if __name__ == "__main__":
    main()
