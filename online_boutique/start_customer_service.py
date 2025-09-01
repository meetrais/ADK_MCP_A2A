#!/usr/bin/env python3
"""
Customer Service Agent - Port 8091
"""

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def get_customer_support(inquiry: str) -> dict:
    """Get customer support response from MCP server."""
    try:
        print(f"Customer Service: Calling MCP server for inquiry: {inquiry}")
        
        response = requests.post(
            'http://localhost:3002/customer-support',
            json={'inquiry': inquiry},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'success':
                return result['data']
        
        return {
            'status': 'error',
            'message': f'Failed to get customer support response. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

@app.route('/chat', methods=['POST'])
def chat():
    """Main endpoint for A2A communication"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        print(f"Customer Service A2A received: {message}")
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        response_data = get_customer_support(inquiry=message)
        
        return jsonify({
            "response": response_data,
            "agent": "customer_service_agent",
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in Customer Service A2A: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "agent": "customer_service_agent"})

@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    """Return the agent card"""
    return jsonify({
        "name": "customer_service_agent",
        "description": "Customer service agent using MCP server",
        "port": 8091
    })

if __name__ == '__main__':
    print("🚀 Customer Service Agent starting on port 8091...")
    app.run(host="0.0.0.0", port=8091, debug=False)
