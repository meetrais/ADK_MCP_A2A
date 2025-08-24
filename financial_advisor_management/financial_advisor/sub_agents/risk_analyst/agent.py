from google.adk.agents import LlmAgent
from . import prompt
from flask import Flask, request, jsonify
import json
import requests

MODEL = "gemini-2.5-flash"

def get_risk_analysis(portfolio_data: str) -> dict:
    """
    Get risk analysis from MCP server.
    
    Args:
        portfolio_data (str): Portfolio data to analyze for risk assessment
        
    Returns:
        dict: Risk analysis results from MCP server
    """
    try:
        print(f"Calling MCP server for risk analysis")  # Debug log
        
        # Call MCP server for risk analysis
        response = requests.post(
            'http://localhost:3001/risk-analyze',
            json={'portfolio_data': portfolio_data},
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
                    'overall_risk_score': data['overall_risk_score'],
                    'risk_level': data['risk_level'],
                    'risk_factors': data['risk_factors'],
                    'portfolio_volatility': data['portfolio_volatility'],
                    'value_at_risk': data['value_at_risk'],
                    'diversification_score': data['diversification_score'],
                    'risk_recommendations': data['risk_recommendations'],
                    'stress_test_results': data['stress_test_results'],
                    'hedging_suggestions': data['hedging_suggestions'],
                    'correlation_analysis': data['correlation_analysis']
                }
        
        return {
            'status': 'error',
            'message': f'Failed to get risk analysis. Server returned: {response.status_code}'
        }
        
    except Exception as e:
        print(f"Error calling MCP server: {str(e)}")  # Debug log
        return {
            'status': 'error',
            'message': f'Error connecting to MCP server: {str(e)}'
        }

# Agent definition using MCP server
risk_analyst_agent = LlmAgent(
    model=MODEL,
    name="risk_analyst_agent",
    description="Provides risk analysis for portfolio data.",
    instruction=prompt.RISK_ANALYST_PROMPT,
    output_key="final_risk_assessment_output",
    tools=[get_risk_analysis],
)

# Flask app for A2A protocol
app = Flask(__name__)

# Agent card
AGENT_CARD = {
    "name": "risk_analyst_agent",
    "description": "Risk analyst agent that provides risk assessment using MCP server",
    "version": "1.0",
    "capabilities": ["risk_analysis", "mcp_integration", "portfolio_assessment"],
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
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        message = data.get('message', '')
        
        print(f"A2A received message: {message}")  # Debug log
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Directly call the tool function to bypass the complex runner
        # and avoid the LLM's final response generation.
        response_text = get_risk_analysis(portfolio_data=message)
        
        print(f"A2A direct tool response: {response_text}")
        
        return jsonify({
            "response": response_text,
            "agent": "risk_analyst_agent",
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
    return jsonify({"status": "healthy", "agent": "risk_analyst_agent"})

def run_server(host='localhost', port=8083, debug=False):
    """Start the A2A agent server"""
    print(f"Starting A2A Risk Analyst Agent on http://{host}:{port}")
    print(f"Agent card available at: http://{host}:{port}/agent-card")
    print(f"Chat endpoint available at: http://{host}:{port}/chat")
    print(f"MCP Server should be running on http://localhost:3001")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server()
