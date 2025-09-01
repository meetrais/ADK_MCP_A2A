#!/usr/bin/env python3
"""
Diagnostic script to identify where agent.py is getting stuck
"""

print("Starting diagnostic...")

try:
    print("1. Testing basic imports...")
    import os
    from flask import Flask, jsonify
    print("   ✓ Flask imports OK")
    
    print("2. Testing Google ADK imports...")
    from google.adk.agents import LlmAgent, BaseAgent
    print("   ✓ LlmAgent, BaseAgent OK")
    
    from google.adk.tools.agent_tool import AgentTool
    print("   ✓ AgentTool OK")
    
    from google.adk.agents.invocation_context import InvocationContext
    print("   ✓ InvocationContext OK")
    
    from google.adk.events import Event
    print("   ✓ Event OK")
    
    from google.genai import types
    print("   ✓ types OK")
    
    print("3. Testing other imports...")
    from typing import AsyncGenerator
    import requests
    import json
    print("   ✓ Other imports OK")
    
    print("4. Testing local imports...")
    try:
        from online_boutique_manager import prompt
        print("   ✓ Prompt import OK")
    except ImportError as e:
        print(f"   ✗ Prompt import failed: {e}")
        # Try alternative import
        import sys
        sys.path.append('online_boutique_manager')
        import prompt
        print("   ✓ Prompt import OK (alternative path)")
    
    print("5. Testing agent class creation...")
    
    class TestA2AAgentProxy(BaseAgent):
        """Test version of A2AAgentProxy"""
        
        def __init__(self, name: str, agent_url: str, description: str = None):
            super().__init__(
                name=name,
                description=description or f"A2A proxy for {name} agent"
            )
            self._agent_url = agent_url
        
        async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
            """Test implementation"""
            content = types.Content(
                role='model',
                parts=[types.Part(text="Test response")]
            )
            yield Event(author=self.name, content=content)
    
    print("   ✓ A2AAgentProxy class created")
    
    print("6. Testing agent instantiation...")
    test_agent = TestA2AAgentProxy(
        name="test_agent",
        agent_url="http://localhost:8090",
        description="Test agent"
    )
    print("   ✓ Agent instantiation OK")
    
    print("7. Testing LlmAgent creation...")
    MODEL = "gemini-2.5-flash"
    
    test_llm_agent = LlmAgent(
        name="test_coordinator",
        model=MODEL,
        description="Test coordinator",
        instruction="Test instruction",
        output_key="test_output",
        tools=[AgentTool(agent=test_agent)]
    )
    print("   ✓ LlmAgent creation OK")
    
    print("8. Testing Flask app creation...")
    app = Flask(__name__)
    print("   ✓ Flask app creation OK")
    
    print("\n✅ All tests passed! The issue might be in the specific configuration or environment.")
    print("Try running the original agent.py again - it should work now.")
    
except Exception as e:
    print(f"\n❌ Error at step: {e}")
    import traceback
    traceback.print_exc()

print("\nDiagnostic complete.")
