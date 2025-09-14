from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator
import requests
import json

try:
    from . import prompt
    from .a2a_protocol import A2AClient, JSONRPCRequest
except ImportError:
    # Fallback for when running as standalone module
    import prompt
    from a2a_protocol import A2AClient, JSONRPCRequest

MODEL = "gemini-2.5-flash"

class EnhancedA2AAgentProxy(BaseAgent):
    """Enhanced ADK-compliant agent using full A2A protocol with JSON-RPC 2.0"""
    
    def __init__(self, name: str, agent_url: str, description: str = None):
        # Store URL as private attribute to avoid Pydantic conflicts
        super().__init__(
            name=name,
            description=description or f"Enhanced A2A proxy for {name} agent"
        )
        # Set _agent_url after initialization to avoid Pydantic validation
        self._agent_url = agent_url
        self._a2a_client = A2AClient(agent_url)
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Enhanced method using full A2A protocol with JSON-RPC 2.0"""
        
        # Initialize response_text to handle all error cases
        response_text = "Unknown error occurred"
        
        try:
            # Extract user message from context
            user_message = "Perform analysis"  # Default message
            if hasattr(ctx, 'tool_input') and ctx.tool_input:
                user_message = str(ctx.tool_input)
            elif hasattr(ctx, 'message') and ctx.message and ctx.message.parts:
                user_message = ctx.message.parts[0].text
            
            print(f"🔗 A2A Proxy '{self.name}' sending message: {user_message[:100]}...")
            
            # Try enhanced A2A protocol first (JSON-RPC 2.0)
            try:
                rpc_response = self._a2a_client.send_message(user_message)
                
                if "result" in rpc_response:
                    result = rpc_response["result"]
                    response_payload = result.get("response", f"No response from {self.name}")
                    
                    # Handle structured response
                    if isinstance(response_payload, dict):
                        response_text = json.dumps(response_payload, indent=2)
                    else:
                        response_text = str(response_payload)
                    
                    print(f"✅ A2A JSON-RPC success for '{self.name}'")
                
                elif "error" in rpc_response:
                    error = rpc_response["error"]
                    response_text = f"🚨 A2A RPC Error from {self.name}: {error.get('message', 'Unknown error')}"
                    print(f"❌ A2A JSON-RPC error for '{self.name}': {error}")
                
                else:
                    response_text = f"⚠️ Invalid A2A response from {self.name}"
                    
            except Exception as rpc_error:
                print(f"⚠️ JSON-RPC failed for '{self.name}', falling back to legacy: {rpc_error}")
                
                # Fallback to legacy HTTP endpoint
                response = requests.post(
                    f"{self._agent_url}/chat",
                    json={"message": user_message},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_payload = result.get("response", f"No response from {self.name}")
                    
                    if isinstance(response_payload, dict):
                        response_text = json.dumps(response_payload, indent=2)
                    else:
                        response_text = str(response_payload)
                    
                    print(f"✅ A2A Legacy fallback success for '{self.name}'")
                else:
                    response_text = f"Error calling {self.name}: HTTP {response.status_code}"
                    print(f"❌ A2A Legacy fallback failed for '{self.name}': {response.status_code}")
                
        except requests.RequestException as e:
            response_text = f"Failed to connect to {self.name}: {str(e)}"
            print(f"❌ Connection failed to '{self.name}': {e}")
        except Exception as e:
            response_text = f"Unexpected error in {self.name}: {str(e)}"
            print(f"❌ Unexpected error in '{self.name}': {e}")
        
        # Create proper ADK Event with types.Content
        content = types.Content(
            role='model',
            parts=[types.Part(text=response_text)]
        )
        
        yield Event(
            author=self.name,
            content=content
        )
    
    def get_agent_info(self) -> dict:
        """Get enhanced agent card information via discovery mechanism"""
        try:
            # Try Agent discovery first (well-known URI)
            agent_info = self._a2a_client.discover_agent()
            if agent_info.get("name") != "unknown":
                print(f"🔍 Agent discovery successful for '{self.name}'")
                return agent_info
            
            # Fallback to legacy endpoint
            response = requests.get(f"{self._agent_url}/agent-card", timeout=10)
            if response.status_code == 200:
                print(f"🔍 Legacy discovery successful for '{self.name}'")
                return response.json()
                
        except Exception as e:
            print(f"⚠️ Discovery failed for '{self.name}': {e}")
        
        return {"name": self.name, "status": "unavailable"}
    
    def get_task_status(self, task_id: str) -> dict:
        """Get task status using A2A protocol"""
        try:
            return self._a2a_client.get_task_status(task_id)
        except Exception as e:
            return {"error": f"Failed to get task status: {str(e)}"}
    
    def create_task(self, message: str) -> dict:
        """Create task using A2A protocol"""
        try:
            return self._a2a_client.create_task(message)
        except Exception as e:
            return {"error": f"Failed to create task: {str(e)}"}

# Legacy alias for backward compatibility
A2AAgentProxy = EnhancedA2AAgentProxy

# A2A Agent Configuration - easily add more agents here
A2A_AGENTS = {
    "data_analyst": {
        "url": "http://localhost:8080",
        "description": "Call data analyst agent via A2A protocol for market data analysis"
    },
    "execution_analyst": {
        "url": "http://localhost:8081", 
        "description": "Call execution analyst agent via A2A protocol for execution planning"
    },
    "trading_analyst": {
        "url": "http://localhost:8082", 
        "description": "Call trading analyst agent via A2A protocol for trading strategy analysis"
    },
    "risk_analyst": {
        "url": "http://localhost:8083", 
        "description": "Call risk analyst agent via A2A protocol for risk assessment"
    },
}

class EnhancedA2AAgentManager:
    """Enhanced A2A Agent Manager with full protocol support and monitoring"""
    
    def __init__(self):
        self.agents = {}
        self.agent_info_cache = {}
        self.task_history = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agents with Agent discovery and health checks"""
        print("🚀 Initializing Enhanced A2A agents with full protocol discovery...")
        
        for agent_name, config in A2A_AGENTS.items():
            try:
                agent = EnhancedA2AAgentProxy(
                    name=agent_name,
                    agent_url=config["url"],
                    description=config["description"]
                )
                
                # Agent discovery with protocol detection
                agent_info = agent.get_agent_info()
                
                if agent_info.get("status") != "unavailable":
                    self.agents[agent_name] = agent
                    self.agent_info_cache[agent_name] = agent_info
                    
                    capabilities = agent_info.get("capabilities", [])
                    protocols = agent_info.get("protocols", ["legacy"])
                    version = agent_info.get("version", "1.0")
                    
                    print(f"✅ {agent_name} v{version}: {', '.join(capabilities)}")
                    print(f"   📡 Protocols: {', '.join(protocols)}")
                    
                    if "json-rpc-2.0" in protocols:
                        print(f"   🎯 Enhanced A2A protocol supported")
                    
                    if agent_info.get("streaming_support"):
                        print(f"   📡 Streaming support enabled")
                else:
                    print(f"❌ {agent_name}: Agent unavailable")
                    
            except Exception as e:
                print(f"⚠️  {agent_name}: Connection failed - {str(e)}")
    
    def get_agent(self, agent_name: str) -> EnhancedA2AAgentProxy:
        """Get agent with health check"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not available")
        return self.agents[agent_name]
    
    def get_agent_capabilities(self, agent_name: str) -> list:
        """Get cached agent capabilities"""
        return self.agent_info_cache.get(agent_name, {}).get("capabilities", [])
    
    def health_check_all(self) -> dict:
        """Perform comprehensive health check on all agents"""
        health_status = {}
        print("🏥 Performing enhanced health checks...")
        
        for agent_name, agent in self.agents.items():
            try:
                info = agent.get_agent_info()
                health_status[agent_name] = {
                    "status": "healthy" if info.get("status") != "unavailable" else "unhealthy",
                    "capabilities": info.get("capabilities", []),
                    "version": info.get("version", "unknown"),
                    "protocols": info.get("protocols", ["legacy"]),
                    "streaming_support": info.get("streaming_support", False),
                    "endpoints": info.get("endpoints", {}),
                    "authentication": info.get("authentication", {}),
                    "service_endpoint": info.get("service_endpoint", "unknown")
                }
                print(f"✅ {agent_name}: Healthy (v{health_status[agent_name]['version']})")
            except Exception as e:
                health_status[agent_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                print(f"❌ {agent_name}: Unhealthy - {str(e)}")
        return health_status
    
    def find_agents_by_capability(self, capability: str) -> list:
        """Find agents that have a specific capability"""
        matching_agents = []
        for agent_name, info in self.agent_info_cache.items():
            if capability in info.get("capabilities", []):
                matching_agents.append(agent_name)
        return matching_agents

    def create_agent_task(self, agent_name: str, message: str) -> dict:
        """Create task on specific agent"""
        if agent_name not in self.agents:
            return {"error": f"Agent '{agent_name}' not available"}
        
        try:
            task_result = self.agents[agent_name].create_task(message)
            
            # Store in task history
            if "result" in task_result and "task_id" in task_result["result"]:
                task_id = task_result["result"]["task_id"]
                self.task_history[task_id] = {
                    "agent": agent_name,
                    "message": message,
                    "created_at": task_result["result"].get("created_at"),
                    "state": task_result["result"].get("state")
                }
            
            return task_result
        except Exception as e:
            return {"error": f"Failed to create task: {str(e)}"}
    
    def get_task_status(self, task_id: str) -> dict:
        """Get task status across all agents"""
        if task_id in self.task_history:
            agent_name = self.task_history[task_id]["agent"]
            if agent_name in self.agents:
                return self.agents[agent_name].get_task_status(task_id)
        
        # Search all agents if not in history
        for agent_name, agent in self.agents.items():
            try:
                result = agent.get_task_status(task_id)
                if "result" in result:
                    return result
            except Exception:
                continue
        
        return {"error": "Task not found"}
    
    def get_protocol_statistics(self) -> dict:
        """Get A2A protocol usage statistics"""
        stats = {
            "total_agents": len(self.agents),
            "enhanced_protocol_agents": 0,
            "streaming_enabled_agents": 0,
            "legacy_agents": 0,
            "total_tasks": len(self.task_history)
        }
        
        for agent_name, info in self.agent_info_cache.items():
            protocols = info.get("protocols", ["legacy"])
            if "json-rpc-2.0" in protocols:
                stats["enhanced_protocol_agents"] += 1
            else:
                stats["legacy_agents"] += 1
                
            if info.get("streaming_support"):
                stats["streaming_enabled_agents"] += 1
        
        return stats

# Initialize Enhanced A2A Agent Manager
agent_manager = EnhancedA2AAgentManager()

# Get specific agents through enhanced manager
try:
    data_analyst_a2a_agent = agent_manager.get_agent("data_analyst")
    execution_analyst_a2a_agent = agent_manager.get_agent("execution_analyst")
    trading_analyst_a2a_agent = agent_manager.get_agent("trading_analyst")
    risk_analyst_a2a_agent = agent_manager.get_agent("risk_analyst")
    
    print(f"\n🎯 Available enhanced agents: {list(agent_manager.agents.keys())}")
    
    # Display protocol statistics
    stats = agent_manager.get_protocol_statistics()
    print(f"📊 Protocol Statistics:")
    print(f"   • Enhanced A2A Protocol: {stats['enhanced_protocol_agents']} agents")
    print(f"   • Streaming Support: {stats['streaming_enabled_agents']} agents")
    print(f"   • Legacy Protocol: {stats['legacy_agents']} agents")
    print(f"   • Total Tasks: {stats['total_tasks']}")
    
except ValueError as e:
    print(f"⚠️  Agent initialization error: {e}")
    # Create fallback agents for testing
    data_analyst_a2a_agent = EnhancedA2AAgentProxy("data_analyst", A2A_AGENTS["data_analyst"]["url"])
    execution_analyst_a2a_agent = EnhancedA2AAgentProxy("execution_analyst", A2A_AGENTS["execution_analyst"]["url"])
    trading_analyst_a2a_agent = EnhancedA2AAgentProxy("trading_analyst", A2A_AGENTS["trading_analyst"]["url"])
    risk_analyst_a2a_agent = EnhancedA2AAgentProxy("risk_analyst", A2A_AGENTS["risk_analyst"]["url"])

# Enhanced A2A tools for the coordinator
def check_agent_health() -> str:
    """Check health status of all enhanced A2A agents"""
    try:
        health_status = agent_manager.health_check_all()
        
        result = "🏥 **Enhanced A2A Agent Health Status:**\n\n"
        for agent_name, status in health_status.items():
            if status.get("status") == "healthy":
                capabilities = ", ".join(status.get("capabilities", []))
                version = status.get("version", "unknown")
                protocols = ", ".join(status.get("protocols", ["legacy"]))
                streaming = "✅" if status.get("streaming_support") else "❌"
                
                result += f"✅ **{agent_name}** (v{version})\n"
                result += f"   • Capabilities: {capabilities}\n"
                result += f"   • Protocols: {protocols}\n"
                result += f"   • Streaming: {streaming}\n"
                result += f"   • Endpoint: {status.get('service_endpoint', 'unknown')}\n\n"
            else:
                error = status.get("error", "Unknown error")
                result += f"❌ **{agent_name}**: {error}\n\n"
        
        # Add protocol statistics
        stats = agent_manager.get_protocol_statistics()
        result += "📊 **Protocol Statistics:**\n"
        result += f"• Enhanced A2A: {stats['enhanced_protocol_agents']} agents\n"
        result += f"• Streaming: {stats['streaming_enabled_agents']} agents\n"
        result += f"• Legacy: {stats['legacy_agents']} agents\n"
        result += f"• Total Tasks: {stats['total_tasks']}\n"
        
        return result
    except Exception as e:
        return f"Error checking agent health: {str(e)}"

def find_capable_agents(capability: str) -> str:
    """Find agents with specific capabilities"""
    try:
        matching_agents = agent_manager.find_agents_by_capability(capability)
        
        if not matching_agents:
            return f"No agents found with capability: {capability}"
        
        result = f"🔍 **Agents with '{capability}' capability:**\n\n"
        for agent_name in matching_agents:
            capabilities = agent_manager.get_agent_capabilities(agent_name)
            result += f"• **{agent_name}**: {', '.join(capabilities)}\n"
        
        return result
    except Exception as e:
        return f"Error finding capable agents: {str(e)}"

def get_agent_status(agent_name: str) -> str:
    """Get detailed status of a specific enhanced A2A agent"""
    try:
        if agent_name not in agent_manager.agents:
            return f"❌ Agent '{agent_name}' is not available or not registered"
        
        agent = agent_manager.get_agent(agent_name)
        info = agent.get_agent_info()
        
        result = f"📊 **Enhanced A2A Agent: {agent_name}**\n\n"
        result += f"• **Status**: {'✅ Available' if info.get('status') != 'unavailable' else '❌ Unavailable'}\n"
        result += f"• **Version**: {info.get('version', 'unknown')}\n"
        result += f"• **Model**: {info.get('model', 'unknown')}\n"
        result += f"• **Service Endpoint**: {info.get('service_endpoint', 'unknown')}\n"
        result += f"• **Protocols**: {', '.join(info.get('protocols', ['legacy']))}\n"
        result += f"• **Streaming Support**: {'✅ Yes' if info.get('streaming_support') else '❌ No'}\n"
        result += f"• **Capabilities**: {', '.join(info.get('capabilities', []))}\n"
        result += f"• **Data Source**: {info.get('data_source', 'unknown')}\n"
        
        # Authentication info
        auth = info.get('authentication', {})
        if auth:
            result += f"• **Authentication**: {auth.get('type', 'unknown')} ({'Required' if auth.get('required') else 'Optional'})\n"
        
        # Available endpoints
        endpoints = info.get('endpoints', {})
        if endpoints:
            result += f"\n🔌 **Available Endpoints:**\n"
            for endpoint_name, path in endpoints.items():
                result += f"  • {endpoint_name}: {path}\n"
        
        return result
    except Exception as e:
        return f"Error getting agent status: {str(e)}"

def create_agent_task(agent_name: str, message: str) -> str:
    """Create task on specific A2A agent"""
    try:
        task_result = agent_manager.create_agent_task(agent_name, message)
        
        if "result" in task_result:
            result = task_result["result"]
            return f"✅ **Task Created on {agent_name}**\n• Task ID: {result.get('task_id')}\n• State: {result.get('state')}"
        elif "error" in task_result:
            return f"❌ **Task Creation Failed**: {task_result['error']}"
        else:
            return f"⚠️ **Unexpected Response**: {json.dumps(task_result, indent=2)}"
            
    except Exception as e:
        return f"Error creating task: {str(e)}"

def get_task_status_info(task_id: str) -> str:
    """Get status of a specific task"""
    try:
        task_result = agent_manager.get_task_status(task_id)
        
        if "result" in task_result:
            result = task_result["result"]
            status_info = f"📋 **Task Status: {task_id}**\n\n"
            status_info += f"• **State**: {result.get('state', 'unknown')}\n"
            status_info += f"• **Progress**: {result.get('progress', 0)*100:.1f}%\n"
            status_info += f"• **Created**: {result.get('created_at', 'unknown')}\n"
            status_info += f"• **Updated**: {result.get('updated_at', 'unknown')}\n"
            
            if result.get('error'):
                status_info += f"• **Error**: {result['error']}\n"
                
            if result.get('artifacts'):
                status_info += f"• **Artifacts**: {len(result['artifacts'])} generated\n"
                
            return status_info
        elif "error" in task_result:
            return f"❌ **Task Status Error**: {task_result['error']}"
        else:
            return f"⚠️ **Unexpected Response**: {json.dumps(task_result, indent=2)}"
            
    except Exception as e:
        return f"Error getting task status: {str(e)}"

financial_coordinator = LlmAgent(
    name="financial_coordinator",
    model=MODEL,
    description=(
        "guide users through a structured process to receive financial "
        "advice by orchestrating a series of expert subagents. help them "
        "analyze a market ticker, develop trading strategies, define "
        "execution plans, and evaluate the overall risk."
    ),
    instruction=prompt.FINANCIAL_COORDINATOR_PROMPT,
    output_key="financial_coordinator_output",
    tools=[
        AgentTool(agent=data_analyst_a2a_agent),     # A2A call via proxy
        AgentTool(agent=trading_analyst_a2a_agent),  # A2A call via proxy
        AgentTool(agent=execution_analyst_a2a_agent), # A2A call via proxy
        AgentTool(agent=risk_analyst_a2a_agent),     # A2A call via proxy
        check_agent_health,                          # Enhanced health monitoring tool
        find_capable_agents,                         # Capability discovery tool
        get_agent_status,                           # Individual agent status tool
        create_agent_task,                          # Task creation tool
        get_task_status_info,                       # Task status monitoring tool
    ],
)

root_agent = financial_coordinator
