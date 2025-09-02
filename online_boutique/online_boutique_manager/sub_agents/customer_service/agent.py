from flask import Flask, request, jsonify
import requests
import os

# Flask app for A2A protocol
app = Flask(__name__)

def get_customer_support(inquiry: str) -> dict:
    """Get customer support response from MCP server."""
    try:
        print(f"Customer Service: Calling MCP server for inquiry: {inquiry}")
        
        # Use service name in Kubernetes, fallback to localhost for local dev
        mcp_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:3002')
        if not mcp_url.startswith('http'):
            mcp_url = f'http://{mcp_url}'
        
        response = requests.post(
            f'{mcp_url}/customer-support',
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
        "port": int(os.environ.get("PORT", 8080))
    })

if __name__ == '__main__':
    # Get the port from the environment variable for GKE, fallback to 8080
    server_port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Customer Service Agent starting on port {server_port}...")
    app.run(host="0.0.0.0", port=server_port, debug=False)
