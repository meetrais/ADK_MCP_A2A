from google.adk.agents import LlmAgent
from . import prompt
from flask import Flask, request, jsonify
import json
import requests

MODEL = "gemini-2.5-flash"

def get_trading_analysis(market_data: str) -> dict:
    """
    Get trading analysis from MCP server.
    
    Args:
        market_data (str): Market data to analyze for trading strategies
        
    Returns:
        dict: Trading analysis results from MCP server
    """
    try:
        print(f"Calling MCP server for trading analysis")  # Debug log
        
        # Call MCP server for trading analysis
        response = requests.post(
            'http://localhost:3001/trading-analyze',
            json={'market_data': market_data},
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
                    'trading_strategies': data['trading_strategies'],
                    'entry_points': data['entry_points'],
                    'exit_points': data['exit_points'],
                    'risk_management': data['risk_management'],
                    'position_sizing': data['position_sizing'],
                    'timeframe_analysis': data['timeframe_analysis']
                }
        
        return {
            'status': 'error',
            'message': f'Failed to get trading analysis. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        print(f"Error calling MCP server: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server
trading_analyst_agent = LlmAgent(
    model=MODEL,
    name="trading_analyst_agent",
    description="Provides trading strategy analysis for market data.",
    instruction=prompt.TRADING_ANALYST_PROMPT,
    output_key="proposed_trading_strategies_output",
    tools=[get_trading_analysis],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "trading_analyst_agent",
    "description": "Trading analyst agent that provides trading strategy analysis using MCP server",
    "version": "1.0",
    "capabilities": ["trading_analysis", "mcp_integration", "strategy_optimization"],
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
        response_text = get_trading_analysis(market_data=message)
        
        print(f"A2A direct tool response: {response_text}")
        
        return jsonify({
            "response": response_text,
            "agent": "trading_analyst_agent",
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
    return jsonify({"status": "healthy", "agent": "trading_analyst_agent"})

def run_server(host='localhost', port=8082, debug=False):
    """Start the A2A agent server"""
    print(f"Starting A2A Trading Analyst Agent on http://{host}:{port}")
    print(f"Agent card available at: http://{host}:{port}/agent-card")
    print(f"Chat endpoint available at: http://{host}:{port}/chat")
    print(f"MCP Server should be running on http://localhost:3001")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server()
