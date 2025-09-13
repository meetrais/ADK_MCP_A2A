from google.adk.agents import LlmAgent
try:
    from . import prompt
except ImportError:
    # Fallback for when running as standalone module
    import prompt

try:
    from ...a2a_protocol import A2AServer, TaskArtifact
except ImportError:
    # Fallback for standalone execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from a2a_protocol import A2AServer, TaskArtifact

import json
import requests
import uuid

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

class RiskAnalystA2AServer(A2AServer):
    """Enhanced Risk Analyst A2A Server with full protocol support"""
    
    def __init__(self):
        super().__init__(
            agent_name="risk_analyst_agent",
            description="Risk analyst agent that provides comprehensive risk assessment using MCP server",
            capabilities=[
                "risk_analysis", 
                "portfolio_assessment", 
                "volatility_analysis",
                "value_at_risk_calculation",
                "stress_testing",
                "correlation_analysis",
                "hedging_recommendations",
                "mcp_integration"
            ],
            model=MODEL,
            version="2.0"
        )
    
    def _process_message(self, message: str) -> str:
        """Process risk analysis message and return structured result"""
        try:
            print(f"🔍 Processing risk analysis for: {message[:100]}...")
            
            # Get risk analysis from MCP server
            risk_result = get_risk_analysis(portfolio_data=message)
            
            if risk_result.get('status') == 'success':
                # Create artifacts for different risk components
                artifacts = []
                
                # Risk metrics artifact
                risk_metrics = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="risk_metrics",
                    type="json",
                    content={
                        "overall_risk_score": risk_result.get('overall_risk_score'),
                        "risk_level": risk_result.get('risk_level'),
                        "portfolio_volatility": risk_result.get('portfolio_volatility'),
                        "value_at_risk": risk_result.get('value_at_risk'),
                        "diversification_score": risk_result.get('diversification_score')
                    },
                    metadata={"component": "risk_metrics", "generated_by": "mcp_server"}
                )
                artifacts.append(risk_metrics)
                
                # Risk recommendations artifact
                recommendations = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="risk_recommendations",
                    type="json",
                    content={
                        "risk_recommendations": risk_result.get('risk_recommendations'),
                        "hedging_suggestions": risk_result.get('hedging_suggestions')
                    },
                    metadata={"component": "recommendations", "generated_by": "mcp_server"}
                )
                artifacts.append(recommendations)
                
                # Store artifacts in current task (if available)
                # This would be enhanced in a full implementation
                
                # Format comprehensive response
                response = f"""
# 📊 Risk Analysis Report

## Overall Risk Assessment
- **Risk Score**: {risk_result.get('overall_risk_score', 'N/A')}/10
- **Risk Level**: {risk_result.get('risk_level', 'N/A')}
- **Portfolio Volatility**: {risk_result.get('portfolio_volatility', 'N/A')}%

## Key Risk Metrics
- **Value at Risk (VaR)**: {risk_result.get('value_at_risk', 'N/A')}
- **Diversification Score**: {risk_result.get('diversification_score', 'N/A')}/10

## Risk Factors
{chr(10).join([f"• {factor}" for factor in risk_result.get('risk_factors', [])])}

## Recommendations
{chr(10).join([f"• {rec}" for rec in risk_result.get('risk_recommendations', [])])}

## Hedging Suggestions
{chr(10).join([f"• {hedge}" for hedge in risk_result.get('hedging_suggestions', [])])}

## Stress Test Results
{json.dumps(risk_result.get('stress_test_results', {}), indent=2)}

## Correlation Analysis
{json.dumps(risk_result.get('correlation_analysis', {}), indent=2)}

---
*Analysis powered by MCP Risk Analytics Server*
                """.strip()
                
                print(f"✅ Risk analysis completed successfully")
                return response
                
            else:
                error_msg = risk_result.get('message', 'Unknown error occurred')
                print(f"❌ Risk analysis failed: {error_msg}")
                return f"🚨 **Risk Analysis Error**: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error processing risk analysis: {str(e)}"
            print(f"❌ {error_msg}")
            return f"🚨 **Processing Error**: {error_msg}"

# Create enhanced A2A server instance
a2a_server = RiskAnalystA2AServer()

def run_server(host='localhost', port=8083, debug=False):
    """Start the enhanced A2A Risk Analyst server"""
    print(f"🚀 Starting Enhanced A2A Risk Analyst Agent on http://{host}:{port}")
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
