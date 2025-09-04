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

def get_fallback_response(agent_name, user_message):
    """Provide helpful fallback responses when sub-agents are unavailable"""
    
    fallback_responses = {
        "catalog_service": f"I'd be happy to help you find what you're looking for! While our product search system is temporarily unavailable, I can still assist you. What specific item are you interested in? You can also try browsing our main categories or contact us directly for personalized assistance.",
        
        "shipping_service": f"I can help with your shipping inquiry! While our shipping system is temporarily unavailable, here's some general information: We typically offer standard (5-7 business days) and express (2-3 business days) shipping options. For specific rates and tracking information, please contact our customer service team or try again in a few minutes.",
        
        "customer_service": f"I'm here to help you! While our customer service system is temporarily unavailable, I can still provide basic assistance. What do you need help with? For urgent matters, you can also reach us directly via phone or email.",
        
        "payment_processor": f"I can assist with your payment question! While our payment system is temporarily unavailable, we accept all major credit cards, PayPal, and other secure payment methods. For specific billing inquiries, please contact our support team or try again shortly.",
        
        "marketing_manager": f"I'd love to give you some recommendations! While our recommendation system is temporarily unavailable, I can suggest checking out our featured collections, new arrivals, or bestsellers. What type of items are you interested in?"
    }
    
    return fallback_responses.get(agent_name, f"I'm here to help with your request about '{user_message}'. While our system is temporarily unavailable, please feel free to contact us directly or try again in a few minutes.")

def format_subagent_response(agent_name, response_data, user_message):
    """Use LLM to convert sub-agent technical response into natural, user-friendly language"""
    
    try:
        from google.genai import types
        import google.genai as genai
        import json
        
        # Convert response_data to string for the LLM
        if isinstance(response_data, dict):
            data_str = json.dumps(response_data, indent=2)
        else:
            data_str = str(response_data)
        
        formatting_prompt = f"""
You are a helpful customer service representative at an online boutique. A customer asked: "{user_message}"

Our {agent_name.replace('_', ' ')} system provided this technical data:
{data_str}

Convert this technical information into a natural, helpful response that directly addresses the customer's request. Make it conversational, friendly, and actionable. Focus on what the customer actually wants to know.

Guidelines:
- Speak directly to the customer's request
- Use natural, conversational language
- Highlight relevant information from the data
- Suggest next steps or actions
- Keep it concise but helpful
- Don't mention technical terms or system names

Respond as if you're speaking directly to the customer.
"""

        # Use LLM to format the response naturally
        client = genai.Client(api_key=os.environ.get('GOOGLE_API_KEY', ''))
        
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Content(
                role='user',
                parts=[types.Part(text=formatting_prompt)]
            )]
        )
        
        formatted_response = response.candidates[0].content.parts[0].text.strip()
        return formatted_response
        
    except Exception as e:
        print(f"⚠️ LLM formatting failed: {str(e)}, using fallback")
        # Fallback to simple formatting
        agent_display_name = agent_name.replace('_', ' ').title()
        return f"I've consulted our {agent_display_name} regarding your request: '{user_message}'. Let me help you find what you're looking for!"

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

# Use environment variables for service URLs, fallback to localhost for local dev
A2A_AGENTS = {
    "shipping_service": {
        "url": os.environ.get("SHIPPING_SERVICE_URL", "http://localhost:8093"),
        "description": "Call shipping service agent via A2A protocol for shipping and delivery management"
    },
    "customer_service": {
        "url": os.environ.get("CUSTOMER_SERVICE_URL", "http://localhost:8091"), 
        "description": "Call customer service agent via A2A protocol for customer support and order assistance"
    },
    "payment_processor": {
        "url": os.environ.get("PAYMENT_PROCESSOR_URL", "http://localhost:8092"), 
        "description": "Call payment processor agent via A2A protocol for payment handling and checkout"
    },
    "marketing_manager": {
        "url": os.environ.get("MARKETING_MANAGER_URL", "http://localhost:8094"), 
        "description": "Call marketing manager agent via A2A protocol for promotions and recommendations"
    },
    "catalog_service": {
        "url": os.environ.get("CATALOG_SERVICE_URL", "http://localhost:8095"), 
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

# Create Flask app at module level for Gunicorn compatibility
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
                        # Use the same URLs from A2A_AGENTS configuration
                        subagent_url = A2A_AGENTS[subagent_used]["url"]
                        
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
                            
                            # Format the response in a user-friendly way
                            raw_response = subagent_data.get('response', 'No response from subagent')
                            
                            # If response is a dict/JSON, format it nicely
                            if isinstance(raw_response, dict):
                                tool_response = format_subagent_response(subagent_used, raw_response, user_message)
                            elif isinstance(raw_response, str) and raw_response.startswith('{'):
                                # Try to parse JSON string
                                try:
                                    import json
                                    parsed_response = json.loads(raw_response)
                                    tool_response = format_subagent_response(subagent_used, parsed_response, user_message)
                                except:
                                    tool_response = raw_response
                            else:
                                tool_response = raw_response
                        else:
                            print(f"❌ Subagent HTTP error: {response.status_code}")
                            tool_response = f"Error calling {subagent_used}: HTTP {response.status_code}"
                            
                    except Exception as e:
                        print(f"❌ Error calling subagent: {str(e)}")
                        # Provide a user-friendly fallback response when sub-agent is unavailable
                        if "Connection" in str(e) or "refused" in str(e):
                            tool_response = get_fallback_response(subagent_used, user_message)
                        else:
                            tool_response = f"I'm having trouble accessing our {subagent_used.replace('_', ' ')} system right now. Please try again in a moment."
                    
                    # Use the formatted response directly
                    response_text = tool_response
                    
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

def run_server(host="0.0.0.0", port=8080):
    """Function kept for backwards compatibility when running directly"""
    server_port = int(os.environ.get("PORT", port))
    app.run(host=host, port=server_port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()
