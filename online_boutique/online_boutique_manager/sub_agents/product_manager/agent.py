from google.adk import Agent
from . import prompt
from flask import Flask, request, jsonify
import json
import requests
import os

MODEL = "gemini-2.5-flash"

def get_product_catalog(category: str) -> dict:
    """
    Get product catalog from MCP server.
    
    Args:
        category (str): Product category (e.g., 'clothing', 'accessories', 'shoes')
        
    Returns:
        dict: Product catalog results from MCP server
    """
    try:
        print(f"Calling MCP server for category: {category}")  # Debug log
        
        # Call MCP server
        response = requests.post(
            'http://localhost:3002/products',
            json={'category': category},
            timeout=10
        )
        
        print(f"MCP server response status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            result = response.json()
            print(f"MCP server result: {result}")  # Debug log
            
            if result['status'] == 'success':
                return result['data']
        
        return {
            'status': 'error',
            'message': f'Failed to get products for {category}. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        print(f"Error calling MCP server: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server
product_manager_agent = Agent(
    model=MODEL,
    name="product_manager_agent",
    instruction=prompt.PRODUCT_MANAGER_PROMPT,
    output_key="product_catalog_output",
    tools=[get_product_catalog],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "product_manager_agent",
    "description": "Product manager agent that provides product catalog and inventory management using MCP server",
    "version": "1.0",
    "capabilities": ["product_catalog", "inventory_management", "mcp_integration", "e_commerce"],
    "model": MODEL,
    "endpoints": {
        "chat": "/chat",
        "card": "/agent-card"
    },
    "input_format": "text",
    "output_format": "json",
    "data_source": "MCP Server"
}

@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    """Return the agent card describing capabilities"""
    return jsonify(AGENT_CARD)

@app.route('/chat', methods=['POST'])
def chat():
    """Main endpoint for A2A communication"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        print(f"A2A received message: {message}")  # Debug log
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Directly call the tool function to bypass the complex runner
        response_text = get_product_catalog(category=message)
        
        print(f"A2A direct tool response: {response_text}")
        
        return jsonify({
            "response": response_text,
            "agent": "product_manager_agent",
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in A2A chat endpoint: {str(e)}")  # Debug logging
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "agent": "product_manager_agent"})

def run_server(host="0.0.0.0", port=8080):
    """Starts a Flask web server for the agent."""
    app = Flask(__name__)

    @app.route("/health")
    def health_check():
        """A simple health check endpoint that returns a 200 OK status."""
        return jsonify({"status": "healthy"}), 200

    @app.route("/")
    def index():
        """Main endpoint for the agent."""
        # You can customize this message for each agent
        return jsonify({"message": "Agent is running and healthy."})

    # Get the port from the environment variable for GKE
    server_port = int(os.environ.get("PORT", port))
    
    print(f"🚀 Agent server starting on {host}:{server_port}")
    app.run(host=host, port=server_port)

# Optional: You can add this to make the file runnable for local testing
if __name__ == '__main__':
    run_server()

