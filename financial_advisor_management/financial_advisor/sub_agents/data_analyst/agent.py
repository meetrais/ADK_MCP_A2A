from google.adk import Agent
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

class DataAnalystA2AServer(A2AServer):
    """Enhanced Data Analyst A2A Server with full protocol support"""
    
    def __init__(self):
        super().__init__(
            agent_name="data_analyst_agent",
            description="Data analyst agent that provides comprehensive market data analysis using MCP server",
            capabilities=[
                "market_analysis", 
                "financial_data",
                "price_analysis",
                "volume_analysis", 
                "technical_indicators",
                "market_trends",
                "ticker_analysis",
                "mcp_integration"
            ],
            model=MODEL,
            version="2.0"
        )
    
    def _process_message(self, message: str) -> str:
        """Process market data analysis message and return structured result"""
        try:
            print(f"📊 Processing market data analysis for: {message[:100]}...")
            
            # Get market data from MCP server
            market_result = get_market_analysis(ticker=message)
            
            if market_result.get('status') == 'success':
                # Create artifacts for different data components
                artifacts = []
                
                # Market data artifact
                market_data = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="market_data",
                    type="json",
                    content={
                        "ticker": market_result.get('ticker'),
                        "price": market_result.get('price'),
                        "change": market_result.get('change'),
                        "change_percent": market_result.get('change_percent'),
                        "volume": market_result.get('volume'),
                        "market_cap": market_result.get('market_cap')
                    },
                    metadata={"component": "market_data", "generated_by": "mcp_server"}
                )
                artifacts.append(market_data)
                
                # Analysis artifact
                analysis_data = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="market_analysis",
                    type="json",
                    content={
                        "analysis": market_result.get('analysis'),
                        "recommendation": market_result.get('recommendation'),
                        "risk_level": market_result.get('risk_level')
                    },
                    metadata={"component": "analysis", "generated_by": "mcp_server"}
                )
                artifacts.append(analysis_data)
                
                # Format comprehensive response
                response = f"""
# 📊 Market Data Analysis Report

## Symbol: {market_result.get('ticker', 'N/A')}

### Current Market Data
- **Price**: {market_result.get('price', 'N/A')}
- **Change**: {market_result.get('change', 'N/A')}
- **Change %**: {market_result.get('change_percent', 'N/A')}%
- **Volume**: {market_result.get('volume', 'N/A'):,}
- **Market Cap**: {market_result.get('market_cap', 'N/A')}

### Analysis
{market_result.get('analysis', 'No analysis available')}

### Recommendation
**{market_result.get('recommendation', 'No recommendation available')}**

### Risk Level
**{market_result.get('risk_level', 'Unknown')}**

---
*Analysis powered by MCP Market Data Server*
                """.strip()
                
                print(f"✅ Market data analysis completed successfully")
                return response
                
            else:
                error_msg = market_result.get('message', 'Unknown error occurred')
                print(f"❌ Market data analysis failed: {error_msg}")
                return f"🚨 **Market Data Error**: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error processing market data analysis: {str(e)}"
            print(f"❌ {error_msg}")
            return f"🚨 **Processing Error**: {error_msg}"

# Create enhanced A2A server instance
a2a_server = DataAnalystA2AServer()

def run_server(host='localhost', port=8080, debug=False):
    """Start the enhanced A2A Data Analyst server"""
    print(f"🚀 Starting Enhanced A2A Data Analyst Agent on http://{host}:{port}")
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
