from google.adk import Agent
from . import prompt

MODEL="gemini-pro"

trading_analyst_agent = Agent(
    model=MODEL,
    name="trading_analyst_agent",
    instruction=prompt.TRADING_ANALYST_PROMPT,
    output_key="proposed_trading_strategies_output",
)
