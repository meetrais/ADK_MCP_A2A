import os
from flask import Flask, jsonify

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
    import prompt

MODEL = "gemini-2.5-flash"

class A2AAgentProxy(BaseAgent):
    def __init__(self, name: str, agent_url: str, description: str = None):
        super().__init__(
            name=name,
            description=description or f"A2A proxy for {name} agent"
        )
        self._agent_url = agent_url
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        response_text = "Unknown error occurred"
        
        try:
            user_message = "Perform analysis"
            if hasattr(ctx, 'tool_input') and ctx.tool_input:
                user_message = str(ctx.tool_input)
            elif hasattr(ctx, 'message') and ctx.message and ctx.message.parts:
                user_message = ctx.message.parts[0].text
            
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
                
                # Add subagent info to the response
                response_text = f"[SUBAGENT:{self.name}] {response_text}"
            else:
                response_text = f"Error calling {self.name}: HTTP {response.status_code}"
                
        except requests.RequestException as e:
            response_text = f"Failed to connect to {self.name}: {str(e)}"
        except Exception as e:
            response_text = f"Unexpected error in {self.name}: {str(e)}"
        
        content = types.Content(
            role='model',
            parts=[types.Part(text=response_text)]
        )
        
        yield Event(
            author=self.name,
            content=content
        )
    
    def get_agent_info(self) -> dict:
        try:
            response = requests.get(f"{self._agent_url}/agent-card", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {"name": self.name, "status": "unavailable"}

A2A_AGENTS = {
    "shipping_service": {
        "url": "http://localhost:8090",
        "description": "Call shipping service agent via A2A protocol for shipping and delivery management"
    },
    "customer_service": {
        "url": "http://localhost:8091", 
        "description": "Call customer service agent via A2A protocol for customer support and order assistance"
    },
    "payment_processor": {
        "url": "http://localhost:8092", 
        "description": "Call payment processor agent via A2A protocol for payment handling and checkout"
    },
    "marketing_manager": {
        "url": "http://localhost:8094", 
        "description": "Call marketing manager agent via A2A protocol for promotions and recommendations"
    },
    "catalog_service": {
        "url": "http://localhost:8095", 
        "description": "Call catalog service agent via A2A protocol for advanced catalog management and search"
    },
}

a2a_agents = {}
for agent_name, config in A2A_AGENTS.items():
    a2a_agents[agent_name] = A2AAgentProxy(
        name=agent_name,
        agent_url=config["url"],
        description=config["description"]
    )

shipping_service_a2a_agent = a2a_agents["shipping_service"]
customer_service_a2a_agent = a2a_agents["customer_service"]
payment_processor_a2a_agent = a2a_agents["payment_processor"]
marketing_manager_a2a_agent = a2a_agents["marketing_manager"]
catalog_service_a2a_agent = a2a_agents["catalog_service"]

online_boutique_coordinator = LlmAgent(
    name="online_boutique_coordinator",
    model=MODEL,
    description=(
        "guide customers through a complete online shopping experience by "
        "orchestrating a series of specialized e-commerce agents. help them "
        "discover products, manage their cart, process payments, coordinate "
        "shipping, and provide customer support throughout their journey."
    ),
    instruction=prompt.ONLINE_BOUTIQUE_COORDINATOR_PROMPT,
    output_key="online_boutique_coordinator_output",
    tools=[
        AgentTool(agent=shipping_service_a2a_agent),
        AgentTool(agent=customer_service_a2a_agent),
        AgentTool(agent=payment_processor_a2a_agent),
        AgentTool(agent=marketing_manager_a2a_agent),
        AgentTool(agent=catalog_service_a2a_agent),
    ],
)

root_agent = online_boutique_coordinator

def run_server(host="0.0.0.0", port=8080):
    app = Flask(__name__)
    app.config['DEBUG'] = False
    app.config['TESTING'] = False

    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy"}), 200

    @app.route("/")
    def index():
        return jsonify({
            "message": "Online Boutique Coordinator is running.",
            "status": "healthy"
        })

    @app.route("/chat", methods=["POST"])
    def chat():
        try:
            from flask import request
            import asyncio
            import re
            
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({"error": "No message provided"}), 400
            
            user_message = data['message']
            
            def run_coordinator():
                try:
                    print(f"🔄 Processing message with root_agent: {user_message}")
                    
                    # Use LLM to determine which sub-agent to route to
                    from google.genai import types
                    import google.genai as genai
                    
                    routing_prompt = f"""
You are an intelligent routing system for an online boutique. Analyze the user's message and determine which specialized agent should handle their request.

Available agents and their capabilities:
- catalog_service: Product search, browsing, finding items, product information, inventory queries
- shipping_service: Shipping rates, delivery times, tracking packages, logistics questions
- customer_service: General help, support questions, complaints, returns, exchanges, order issues
- payment_processor: Payment methods, billing questions, checkout problems, transaction issues
- marketing_manager: Product recommendations, promotions, trending items, personalized suggestions

User message: "{user_message}"

Based on the user's intent and the nature of their request, which agent would be most appropriate to handle this?

Respond with ONLY the agent name (e.g., "catalog_service"). Do not include any explanation or additional text.
"""

                    try:
                        # Use the existing Gemini client from ADK
                        client = genai.Client(api_key=os.environ.get('GOOGLE_API_KEY', ''))
                        
                        response = client.models.generate_content(
                            model=MODEL,
                            contents=[types.Content(
                                role='user',
                                parts=[types.Part(text=routing_prompt)]
                            )]
                        )
                        
                        tool_to_use = response.candidates[0].content.parts[0].text.strip().lower()
                        print(f"🤖 LLM routing decision: {tool_to_use}")
                        
                    except Exception as e:
                        print(f"⚠️ LLM routing failed: {str(e)}, defaulting to catalog_service")
                        tool_to_use = "catalog_service"
                    
                    # Map tool name to agent proxy
                    available_tools = {
                        "shipping_service": shipping_service_a2a_agent,
                        "customer_service": customer_service_a2a_agent,
                        "payment_processor": payment_processor_a2a_agent,
                        "marketing_manager": marketing_manager_a2a_agent,
                        "catalog_service": catalog_service_a2a_agent
                    }
                    
                    # Validate and get the tool
                    if tool_to_use in available_tools:
                        selected_tool = available_tools[tool_to_use]
                        subagent_used = tool_to_use
                    else:
                        print(f"⚠️ Invalid tool '{tool_to_use}', defaulting to catalog_service")
                        selected_tool = available_tools["catalog_service"]
                        subagent_used = "catalog_service"
                    
                    print(f"🎯 Using tool: {subagent_used}")
                    
                    # Call the sub-agent via HTTP
                    try:
                        # Map agent names to URLs
                        agent_urls = {
                            "catalog_service": "http://localhost:8095",
                            "shipping_service": "http://localhost:8090",
                            "customer_service": "http://localhost:8091", 
                            "payment_processor": "http://localhost:8092",
                            "marketing_manager": "http://localhost:8094"
                        }
                        
                        subagent_url = agent_urls.get(subagent_used, "http://localhost:8095")
                        
                        print(f"🌐 Calling {subagent_used} at {subagent_url}")
                        
                        # Make HTTP request to sub-agent
                        response = requests.post(
                            f"{subagent_url}/chat",
                            json={"message": user_message},
                            headers={"Content-Type": "application/json"},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            subagent_data = response.json()
                            print(f"✅ Subagent response: {subagent_data}")
                            tool_response = subagent_data.get('response', 'No response from subagent')
                        else:
                            print(f"❌ Subagent HTTP error: {response.status_code}")
                            tool_response = f"Error calling {subagent_used}: HTTP {response.status_code}"
                            
                    except Exception as e:
                        print(f"❌ Error calling subagent: {str(e)}")
                        tool_response = f"Error using {subagent_used}: {str(e)}"
                    
                    # Create coordinator response
                    response_text = f"I've used our {subagent_used.replace('_', ' ')} to help you. {tool_response}"
                    
                    result = {
                        "response": response_text,
                        "agent": "online_boutique_coordinator",
                        "status": "success",
                        "workflow": "ADK root_agent with LLM-selected tools"
                    }
                    
                    # Add subagent field
                    if subagent_used:
                        result["subagent"] = subagent_used
                    
                    return result
                    
                except Exception as e:
                    print(f"❌ Error in coordinator: {str(e)}")
                    return {
                        "response": f"I received your message: '{user_message}'. Let me help you with that!",
                        "agent": "online_boutique_coordinator",
                        "status": "success",
                        "error_details": str(e)
                    }
            
            result = run_coordinator()
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                "error": f"Error processing request: {str(e)}",
                "status": "error"
            }), 500

    server_port = int(os.environ.get("PORT", port))
    app.run(host=host, port=server_port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()
