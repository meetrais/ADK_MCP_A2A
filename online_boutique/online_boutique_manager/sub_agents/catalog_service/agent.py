from google.adk import Agent
# Handle import for both direct execution and module usage
try:
    from . import prompt
except ImportError:
    # Direct execution - use absolute import
    import prompt
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
        # Get MCP server URL from environment variable, fallback to localhost for local dev
        mcp_server_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:3002')
        catalog_url = f"{mcp_server_url}/catalog-service"
        
        # Call MCP server
        response = requests.post(
            catalog_url,
            json={'query': query},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result['status'] == 'success':
                return result['data']
        
        return {
            'status': 'error',
            'message': f'Failed to get catalog data. Server returned: {response.status_code}'
        }
        
    except Exception as e:
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
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Directly call the tool function to bypass the complex runner
        response_text = get_catalog_data(query=message)
        
        return jsonify({
            "response": response_text,
            "agent": "catalog_service_agent",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "agent": "catalog_service_agent"})

def run_server(host="0.0.0.0", port=8080):
    """Function kept for backwards compatibility when running directly"""
    server_port = int(os.environ.get("PORT", port))
    print(f"🚀 Catalog Service Agent starting on port {server_port}...")
    app.run(host=host, port=server_port, debug=False)

if __name__ == '__main__':
    run_server()
