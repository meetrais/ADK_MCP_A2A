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
except ImportError:
    # Fallback for when running as standalone module
    import prompt

MODEL = "gemini-2.5-flash"

class A2AAgentProxy(BaseAgent):
    """ADK-compliant agent that makes A2A calls to external agents"""
    
    def __init__(self, name: str, agent_url: str, description: str = None):
        # Store URL as private attribute to avoid Pydantic conflicts
        super().__init__(
            name=name,
            description=description or f"A2A proxy for {name} agent"
        )
        # Set _agent_url after initialization to avoid Pydantic validation
        self._agent_url = agent_url
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Required method for BaseAgent - makes A2A call to external agent"""
        
        # Initialize response_text to handle all error cases
        response_text = "Unknown error occurred"
        
        try:
            # Extract user message from context
            # When called as a tool, the input is in ctx.tool_input
            user_message = "Perform analysis"  # Default message
            if hasattr(ctx, 'tool_input') and ctx.tool_input:
                user_message = str(ctx.tool_input)
            elif hasattr(ctx, 'message') and ctx.message and ctx.message.parts:
                user_message = ctx.message.parts[0].text
            
            # Make HTTP request to A2A endpoint
            response = requests.post(
                f"{self._agent_url}/chat",
                json={"message": user_message},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_payload = result.get("response", f"No response from {self.name}")
                # Ensure the response is a string for the Event Part
                if isinstance(response_payload, dict):
                    response_text = json.dumps(response_payload, indent=2)
                else:
                    response_text = str(response_payload)
            else:
                response_text = f"Error calling {self.name}: HTTP {response.status_code}"
                
        except requests.RequestException as e:
            response_text = f"Failed to connect to {self.name}: {str(e)}"
        except Exception as e:
            response_text = f"Unexpected error in {self.name}: {str(e)}"
        
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
        """Get agent card information"""
        try:
            response = requests.get(f"{self._agent_url}/agent-card", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {"name": self.name, "status": "unavailable"}

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

class A2AAgentManager:
    """Enhanced A2A Agent Manager with discovery and health monitoring"""
    
    def __init__(self):
        self.agents = {}
        self.agent_info_cache = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agents with discovery and health checks"""
        print("🚀 Initializing A2A agents with discovery...")
        
        for agent_name, config in A2A_AGENTS.items():
            try:
                agent = A2AAgentProxy(
                    name=agent_name,
                    agent_url=config["url"],
                    description=config["description"]
                )
                
                # Discover agent capabilities
                agent_info = agent.get_agent_info()
                
                if agent_info.get("status") != "unavailable":
                    self.agents[agent_name] = agent
                    self.agent_info_cache[agent_name] = agent_info
                    capabilities = agent_info.get("capabilities", [])
                    print(f"✅ {agent_name}: {', '.join(capabilities)}")
                else:
                    print(f"❌ {agent_name}: Agent unavailable")
                    
            except Exception as e:
                print(f"⚠️  {agent_name}: Connection failed - {str(e)}")
    
    def get_agent(self, agent_name: str) -> A2AAgentProxy:
        """Get agent with health check"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not available")
        return self.agents[agent_name]
    
    def get_agent_capabilities(self, agent_name: str) -> list:
        """Get cached agent capabilities"""
        return self.agent_info_cache.get(agent_name, {}).get("capabilities", [])
    
    def health_check_all(self) -> dict:
        """Perform health check on all agents"""
        health_status = {}
        for agent_name, agent in self.agents.items():
            try:
                info = agent.get_agent_info()
                health_status[agent_name] = {
                    "status": "healthy" if info.get("status") != "unavailable" else "unhealthy",
                    "capabilities": info.get("capabilities", []),
                    "version": info.get("version", "unknown")
                }
            except Exception as e:
                health_status[agent_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        return health_status
    
    def find_agents_by_capability(self, capability: str) -> list:
        """Find agents that have a specific capability"""
        matching_agents = []
        for agent_name, info in self.agent_info_cache.items():
            if capability in info.get("capabilities", []):
                matching_agents.append(agent_name)
        return matching_agents

# Initialize A2A Agent Manager
agent_manager = A2AAgentManager()

# Get specific agents through manager
try:
    data_analyst_a2a_agent = agent_manager.get_agent("data_analyst")
    execution_analyst_a2a_agent = agent_manager.get_agent("execution_analyst")
    trading_analyst_a2a_agent = agent_manager.get_agent("trading_analyst")
    risk_analyst_a2a_agent = agent_manager.get_agent("risk_analyst")
    
    print(f"\n🎯 Available agents: {list(agent_manager.agents.keys())}")
    
except ValueError as e:
    print(f"⚠️  Agent initialization error: {e}")
    # Create fallback agents for testing
    data_analyst_a2a_agent = A2AAgentProxy("data_analyst", A2A_AGENTS["data_analyst"]["url"])
    execution_analyst_a2a_agent = A2AAgentProxy("execution_analyst", A2A_AGENTS["execution_analyst"]["url"])
    trading_analyst_a2a_agent = A2AAgentProxy("trading_analyst", A2A_AGENTS["trading_analyst"]["url"])
    risk_analyst_a2a_agent = A2AAgentProxy("risk_analyst", A2A_AGENTS["risk_analyst"]["url"])

# Enhanced A2A tools for the coordinator
def check_agent_health() -> str:
    """Check health status of all A2A agents"""
    try:
        health_status = agent_manager.health_check_all()
        
        result = "🏥 **Agent Health Status:**\n\n"
        for agent_name, status in health_status.items():
            if status.get("status") == "healthy":
                capabilities = ", ".join(status.get("capabilities", []))
                version = status.get("version", "unknown")
                result += f"✅ **{agent_name}** (v{version}): {capabilities}\n"
            else:
                error = status.get("error", "Unknown error")
                result += f"❌ **{agent_name}**: {error}\n"
        
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
    """Get detailed status of a specific agent"""
    try:
        if agent_name not in agent_manager.agents:
            return f"❌ Agent '{agent_name}' is not available or not registered"
        
        agent = agent_manager.get_agent(agent_name)
        info = agent.get_agent_info()
        
        result = f"📊 **{agent_name} Status:**\n\n"
        result += f"• **Status**: {'✅ Available' if info.get('status') != 'unavailable' else '❌ Unavailable'}\n"
        result += f"• **Version**: {info.get('version', 'unknown')}\n"
        result += f"• **Model**: {info.get('model', 'unknown')}\n"
        result += f"• **Capabilities**: {', '.join(info.get('capabilities', []))}\n"
        result += f"• **Data Source**: {info.get('data_source', 'unknown')}\n"
        
        endpoints = info.get('endpoints', {})
        if endpoints:
            result += f"• **Endpoints**: {', '.join(endpoints.keys())}\n"
        
        return result
    except Exception as e:
        return f"Error getting agent status: {str(e)}"

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
        check_agent_health,                          # Health monitoring tool
        find_capable_agents,                         # Capability discovery tool
        get_agent_status,                           # Individual agent status tool
    ],
)

root_agent = financial_coordinator
