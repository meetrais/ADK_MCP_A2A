from google.adk import Agent
from . import prompt

MODEL="gemini-2.5-pro"

risk_analyst_agent = Agent(
    model=MODEL,
    name="risk_analyst_agent",
    instruction=prompt.RISK_ANALYST_PROMPT,
    output_key="final_risk_assessment_output",
)