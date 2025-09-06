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

def process_payment(cart_data: str) -> dict:
    """
    Process payment via MCP server.
    
    Args:
        cart_data (str): Cart data as JSON string
        
    Returns:
        dict: Payment processing results from MCP server
    """
    try:
        # Parse cart data if it's a string
        if isinstance(cart_data, str):
            try:
                cart_data = json.loads(cart_data)
            except json.JSONDecodeError:
                cart_data = {"items": [], "payment_method": "Credit Card"}
        
        # Get MCP server URL from environment variable, fallback to localhost for local dev
        mcp_server_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:3002')
        payment_url = f"{mcp_server_url}/payment-process"
        
        # Call MCP server
        response = requests.post(
            payment_url,
            json={'cart_data': cart_data},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result['status'] == 'success':
                return result['data']
        
        return {
            'status': 'error',
            'message': f'Failed to process payment. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server
payment_processor_agent = Agent(
    model=MODEL,
    name="payment_processor_agent",
    instruction=prompt.PAYMENT_PROCESSOR_PROMPT,
    output_key="payment_processing_output",
    tools=[process_payment],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "payment_processor_agent",
    "description": "Payment processor agent that handles secure payment processing using MCP server",
    "version": "1.0",
    "capabilities": ["payment_processing", "checkout", "order_confirmation", "mcp_integration"],
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
        response_text = process_payment(cart_data=message)
        
        return jsonify({
            "response": response_text,
            "agent": "payment_processor_agent",
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
    return jsonify({"status": "healthy", "agent": "payment_processor_agent"})

def run_server(host="0.0.0.0", port=8080):
    """Function kept for backwards compatibility when running directly"""
    server_port = int(os.environ.get("PORT", port))
    print(f"🚀 Payment Processor Agent starting on port {server_port}...")
    app.run(host=host, port=server_port, debug=False)

if __name__ == '__main__':
    run_server()
