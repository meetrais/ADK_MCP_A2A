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

class ExecutionAnalystA2AServer(A2AServer):
    """Enhanced Execution Analyst A2A Server with full protocol support"""
    
    def __init__(self):
        super().__init__(
            agent_name="execution_analyst_agent",
            description="Execution analyst agent that provides comprehensive trade execution analysis using MCP server",
            capabilities=[
                "execution_analysis", 
                "order_optimization",
                "timing_analysis",
                "cost_analysis", 
                "broker_selection",
                "risk_management",
                "order_types",
                "market_impact_analysis",
                "mcp_integration"
            ],
            model=MODEL,
            version="2.0"
        )
    
    def _process_message(self, message: str) -> str:
        """Process execution analysis message and return structured result"""
        try:
            print(f"⚡ Processing execution analysis for: {message[:100]}...")
            
            # Get execution analysis from MCP server
            execution_result = get_execution_analysis(strategy_data=message)
            
            if execution_result.get('status') == 'success':
                # Create artifacts for different execution components
                artifacts = []
                
                # Execution strategy artifact
                strategy_data = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="execution_strategy",
                    type="json",
                    content={
                        "execution_strategy": execution_result.get('execution_strategy'),
                        "order_types": execution_result.get('order_types'),
                        "timing_recommendations": execution_result.get('timing_recommendations')
                    },
                    metadata={"component": "execution_strategy", "generated_by": "mcp_server"}
                )
                artifacts.append(strategy_data)
                
                # Cost and risk analysis artifact
                cost_risk_data = TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name="cost_risk_analysis",
                    type="json",
                    content={
                        "cost_analysis": execution_result.get('cost_analysis'),
                        "risk_considerations": execution_result.get('risk_considerations'),
                        "broker_recommendations": execution_result.get('broker_recommendations')
                    },
                    metadata={"component": "cost_risk_analysis", "generated_by": "mcp_server"}
                )
                artifacts.append(cost_risk_data)
                
                # Format comprehensive response
                response = f"""
# ⚡ Trade Execution Analysis Report

## Execution Strategy
{chr(10).join([f"• {strategy}" for strategy in execution_result.get('execution_strategy', [])])}

## Recommended Order Types
{chr(10).join([f"• {order}" for order in execution_result.get('order_types', [])])}

## Timing Recommendations
{chr(10).join([f"• {timing}" for timing in execution_result.get('timing_recommendations', [])])}

## Cost Analysis
{json.dumps(execution_result.get('cost_analysis', {}), indent=2)}

## Risk Considerations
{chr(10).join([f"• {risk}" for risk in execution_result.get('risk_considerations', [])])}

## Broker Recommendations
{chr(10).join([f"• {broker}" for broker in execution_result.get('broker_recommendations', [])])}

---
*Analysis powered by MCP Execution Strategy Server*
                """.strip()
                
                print(f"✅ Execution analysis completed successfully")
                return response
                
            else:
                error_msg = execution_result.get('message', 'Unknown error occurred')
                print(f"❌ Execution analysis failed: {error_msg}")
                return f"🚨 **Execution Analysis Error**: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error processing execution analysis: {str(e)}"
            print(f"❌ {error_msg}")
            return f"🚨 **Processing Error**: {error_msg}"

# Create enhanced A2A server instance
a2a_server = ExecutionAnalystA2AServer()

def run_server(host='localhost', port=8081, debug=False):
    """Start the enhanced A2A Execution Analyst server"""
    print(f"🚀 Starting Enhanced A2A Execution Analyst Agent on http://{host}:{port}")
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
