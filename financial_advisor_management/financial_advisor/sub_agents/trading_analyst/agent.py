from google.adk.agents import LlmAgent
try:
    from . import prompt
    from ...a2a_protocol import A2AServer, TaskArtifact
except ImportError:
    # Fallback for when running as standalone module
    import prompt
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from a2a_protocol import A2AServer, TaskArtifact

import json
import requests
import uuid

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

class TradingAnalystA2AServer(A2AServer):
    """Enhanced Trading Analyst A2A Server with full protocol support"""
    
    def __init__(self):
        super().__init__(
            agent_name="trading_analyst_agent",
            description="Trading analyst agent that provides comprehensive trading strategy analysis using MCP server",
            capabilities=[
                "trading_analysis", 
                "strategy_development",
                "entry_point_analysis",
                "exit_point_analysis", 
                "risk_management",
                "position_sizing",
                "timeframe_analysis",
                "technical_analysis",
                "mcp_integration"
            ],
            model=MODEL,
            version="2.0"
        )
    
    def _process_message(self, message: str) -> str:
        """Process trading analysis message and return structured result"""
        try:
            print(f"� Processing trading analysis for: {message[:100]}...")
            
            # Get trading analysis from MCP server
            trading_result = get_trading_analysis(market_data=message)
            
            if trading_result.get('status') == 'success':
                # Create artifacts for different trading components
                artifacts = []
                
                # Trading strategies artifact
                strategies_data = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="trading_strategies",
                    type="json",
                    content={
                        "trading_strategies": trading_result.get('trading_strategies'),
                        "entry_points": trading_result.get('entry_points'),
                        "exit_points": trading_result.get('exit_points')
                    },
                    metadata={"component": "trading_strategies", "generated_by": "mcp_server"}
                )
                artifacts.append(strategies_data)
                
                # Risk management artifact
                risk_mgmt_data = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="risk_management",
                    type="json",
                    content={
                        "risk_management": trading_result.get('risk_management'),
                        "position_sizing": trading_result.get('position_sizing')
                    },
                    metadata={"component": "risk_management", "generated_by": "mcp_server"}
                )
                artifacts.append(risk_mgmt_data)
                
                # Format comprehensive response
                response = f"""
# � Trading Strategy Analysis Report

## Trading Strategies
{chr(10).join([f"• {strategy}" for strategy in trading_result.get('trading_strategies', [])])}

## Entry Points
{chr(10).join([f"• {entry}" for entry in trading_result.get('entry_points', [])])}

## Exit Points
{chr(10).join([f"• {exit}" for exit in trading_result.get('exit_points', [])])}

## Risk Management
{chr(10).join([f"• {risk}" for risk in trading_result.get('risk_management', [])])}

## Position Sizing
{chr(10).join([f"• {size}" for size in trading_result.get('position_sizing', [])])}

## Timeframe Analysis
{json.dumps(trading_result.get('timeframe_analysis', {}), indent=2)}

---
*Analysis powered by MCP Trading Strategy Server*
                """.strip()
                
                print(f"✅ Trading analysis completed successfully")
                return response
                
            else:
                error_msg = trading_result.get('message', 'Unknown error occurred')
                print(f"❌ Trading analysis failed: {error_msg}")
                return f"🚨 **Trading Analysis Error**: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error processing trading analysis: {str(e)}"
            print(f"❌ {error_msg}")
            return f"🚨 **Processing Error**: {error_msg}"

# Create enhanced A2A server instance
a2a_server = TradingAnalystA2AServer()

def run_server(host='localhost', port=8082, debug=False):
    """Start the enhanced A2A Trading Analyst server"""
    print(f"🚀 Starting Enhanced A2A Trading Analyst Agent on http://{host}:{port}")
    print(f"📋 Agent Card: http://{host}:{port}/.well-known/agent.json")
    print(f"🔌 JSON-RPC Endpoint: http://{host}:{port}/rpc")
    print(f"💬 Message Endpoint: http://{host}:{port}/message/send")
    print(f"📡 Streaming Endpoint: http://{host}:{port}/message/stream")
    print(f"🏥 Health Check: http://{host}:{port}/health")
    print(f"🔧 MCP Server should be running on http://localhost:3001")
    print(f"📊 Capabilities: {', '.join(a2a_server.capabilities)}")
    
    a2a_server.run_server(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_server()
