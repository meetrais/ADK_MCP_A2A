from google.adk.agents import LlmAgent
from . import prompt
from flask import Flask, request, jsonify
import json
import requests

MODEL = "gemini-2.5-flash"

def get_execution_analysis(strategy_data: str) -> dict:
    """
    Get execution analysis from MCP server.
    
    Args:
        strategy_data (str): Trading strategy data to analyze
        
    Returns:
        dict: Execution analysis results from MCP server
    """
    try:
        print(f"Calling MCP server for execution analysis")  # Debug log
        
        # Call MCP server for execution analysis
        response = requests.post(
            'http://localhost:3001/execution-analyze',
            json={'strategy_data': strategy_data},
            timeout=10
        )
        
        print(f"MCP server response status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            result = response.json()
            print(f"MCP server result: {result}")  # Debug log
            
            if result['status'] == 'success':
                data = result['data']
                return {
                    'status': 'success',
                    'execution_strategy': data['execution_strategy'],
                    'order_types': data['order_types'],
                    'timing_recommendations': data['timing_recommendations'],
                    'cost_analysis': data['cost_analysis'],
                    'risk_considerations': data['risk_considerations'],
                    'broker_recommendations': data['broker_recommendations']
                }
        
        return {
            'status': 'error',
            'message': f'Failed to get execution analysis. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        print(f"Error calling MCP server: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server
execution_analyst_agent = LlmAgent(
    model=MODEL,
    name="execution_analyst_agent",
    description="Provides execution analysis for trading strategies.",
    instruction=prompt.EXECUTION_ANALYST_PROMPT,
    output_key="execution_plan_output",
    tools=[get_execution_analysis],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "execution_analyst_agent",
    "description": "Execution analyst agent that provides execution analysis using MCP server",
    "version": "1.0",
    "capabilities": ["execution_analysis", "mcp_integration", "order_optimization"],
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
        # and avoid the LLM's final response generation.
        response_text = get_execution_analysis(strategy_data=message)
        
        print(f"A2A direct tool response: {response_text}")
        
        return jsonify({
            "response": response_text,
            "agent": "execution_analyst_agent",
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
    return jsonify({"status": "healthy", "agent": "execution_analyst_agent"})

def run_server(host='localhost', port=8081, debug=False):
    """Start the A2A agent server"""
    print(f"Starting A2A Execution Analyst Agent on http://{host}:{port}")
    print(f"Agent card available at: http://{host}:{port}/agent-card")
    print(f"Chat endpoint available at: http://{host}:{port}/chat")
    print(f"MCP Server should be running on http://localhost:3001")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server()
