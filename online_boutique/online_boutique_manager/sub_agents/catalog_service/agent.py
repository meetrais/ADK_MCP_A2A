from google.adk import Agent
from . import prompt
from flask import Flask, request, jsonify
import json
import requests
import os

MODEL = "gemini-2.5-flash"

def get_catalog_data(query: str) -> dict:
    """
    Get catalog data from MCP server.
    
    Args:
        query (str): Catalog query (e.g., 'search', 'categories', 'featured')
        
    Returns:
        dict: Catalog data results from MCP server
    """
    try:
        print(f"Calling MCP server for catalog query: {query}")  # Debug log
        
        # Call MCP server
        response = requests.post(
            'http://localhost:3002/catalog-service',
            json={'query': query},
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
            'message': f'Failed to get catalog data. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        print(f"Error calling MCP server: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server
catalog_service_agent = Agent(
    model=MODEL,
    name="catalog_service_agent",
    instruction=prompt.CATALOG_SERVICE_PROMPT,
    output_key="catalog_service_output",
    tools=[get_catalog_data],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "catalog_service_agent",
    "description": "Catalog service agent that provides advanced catalog management and search using MCP server",
    "version": "1.0",
    "capabilities": ["catalog_management", "product_search", "category_management", "featured_products", "mcp_integration"],
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
        response_text = get_catalog_data(query=message)
        
        print(f"A2A direct tool response: {response_text}")
        
        return jsonify({
            "response": response_text,
            "agent": "catalog_service_agent",
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
    return jsonify({"status": "healthy", "agent": "catalog_service_agent"})

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
