from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator
import requests
import json

from . import prompt

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

# Create A2A agent proxies from configuration
a2a_agents = {}
for agent_name, config in A2A_AGENTS.items():
    a2a_agents[agent_name] = A2AAgentProxy(
        name=agent_name,  # Use the exact name without suffix for tool recognition
        agent_url=config["url"],
        description=config["description"]
    )

# Get specific agents
data_analyst_a2a_agent = a2a_agents["data_analyst"]
execution_analyst_a2a_agent = a2a_agents["execution_analyst"]
trading_analyst_a2a_agent = a2a_agents["trading_analyst"]
risk_analyst_a2a_agent = a2a_agents["risk_analyst"]

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
    ],
)

root_agent = financial_coordinator
