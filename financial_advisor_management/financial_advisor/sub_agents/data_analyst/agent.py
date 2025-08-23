from google.adk import Agent
from . import prompt
from flask import Flask, request, jsonify
import json
import requests

MODEL = "gemini-2.5-flash"

def get_market_analysis(ticker: str) -> dict:
    """
    Get market analysis for a ticker from MCP server.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        dict: Analysis results from MCP server
    """
    try:
        print(f"Calling MCP server for ticker: {ticker}")  # Debug log
        
        # Call MCP server
        response = requests.post(
            'http://localhost:3001/analyze',
            json={'ticker': ticker},
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
                    'ticker': data['ticker'],
                    'price': f"${data['price']}",
                    'change': data['change'],
                    'change_percent': data['change_percent'],
                    'volume': data['volume'],
                    'market_cap': data['market_cap'],
                    'analysis': data['analysis'],
                    'recommendation': data['recommendation'],
                    'risk_level': data['risk_level']
                }
        
        return {
            'status': 'error',
            'message': f'Failed to get analysis for {ticker}. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        print(f"Error calling MCP server: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server instead of google_search
data_analyst_agent = Agent(
    model=MODEL,
    name="data_analyst_agent",
    instruction=prompt.DATA_ANALYST_PROMPT,
    output_key="market_data_analysis_output",
    tools=[get_market_analysis],  # Using MCP function instead of google_search
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card - updated to reflect MCP capabilities
AGENT_CARD = {
    "name": "data_analyst_agent",
    "description": "Data analyst agent that provides market analysis using MCP server",
    "version": "1.0",
    "capabilities": ["market_analysis", "mcp_integration", "financial_data"],
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
        response_text = get_market_analysis(ticker=message)
        
        print(f"A2A direct tool response: {response_text}")
        
        return jsonify({
            "response": response_text,
            "agent": "data_analyst_agent",
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
    return jsonify({"status": "healthy", "agent": "data_analyst_agent"})

def run_server(host='localhost', port=8080, debug=False):
    """Start the A2A agent server"""
    print(f"Starting A2A Data Analyst Agent on http://{host}:{port}")
    print(f"Agent card available at: http://{host}:{port}/agent-card")
    print(f"Chat endpoint available at: http://{host}:{port}/chat")
    print(f"MCP Server should be running on http://localhost:3001")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server()
