from google.adk import Agent
from . import prompt
from flask import Flask, request, jsonify
import json
import requests

MODEL = "gemini-2.5-flash"

def get_customer_support(inquiry: str) -> dict:
    """
    Get customer support response from MCP server.
    
    Args:
        inquiry (str): Customer inquiry or question
        
    Returns:
        dict: Customer support response from MCP server
    """
    try:
        print(f"Calling MCP server for inquiry: {inquiry}")  # Debug log
        
        # Call MCP server
        response = requests.post(
            'http://localhost:3002/customer-support',
            json={'inquiry': inquiry},
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
            'message': f'Failed to get support for inquiry. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        print(f"Error calling MCP server: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server
customer_service_agent = Agent(
    model=MODEL,
    name="customer_service_agent",
    instruction=prompt.CUSTOMER_SERVICE_PROMPT,
    output_key="customer_support_output",
    tools=[get_customer_support],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "customer_service_agent",
    "description": "Customer service agent that provides support and assistance using MCP server",
    "version": "1.0",
    "capabilities": ["customer_support", "order_assistance", "policy_information", "mcp_integration"],
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
        response_text = get_customer_support(inquiry=message)
        
        print(f"A2A direct tool response: {response_text}")
        
        return jsonify({
            "response": response_text,
            "agent": "customer_service_agent",
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
    return jsonify({"status": "healthy", "agent": "customer_service_agent"})

def run_server(host='localhost', port=8091, debug=False):
    """Start the A2A agent server"""
    print(f"Starting A2A Customer Service Agent on http://{host}:{port}")
    print(f"Agent card available at: http://{host}:{port}/agent-card")
    print(f"Chat endpoint available at: http://{host}:{port}/chat")
    print(f"MCP Server should be running on http://localhost:3002")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server()
