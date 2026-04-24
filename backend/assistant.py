import os
import logging

from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel

from context import create_assistant_instructions
from mcp_servers import create_opennutrition_mcp_server

logger = logging.getLogger()

async def run_assistant_agent(payload, messages) -> str:
  model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
  bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
  os.environ["AWS_REGION_NAME"] = bedrock_region

  model = LitellmModel(model=f"bedrock/{model_id}")

  logger.info("Running assistant agent with payload: %s and messages: %s", payload, messages)
  try:
    async with create_opennutrition_mcp_server() as opennutrition_server:
      agent = Agent(
        name="Cooking Assistant",
        model=model,
        instructions=create_assistant_instructions(payload),
        mcp_servers=[opennutrition_server]
      )

      with trace("ChopSmart"):
        result = await Runner.run(agent, input=messages, max_turns=15)
        logger.info("Assistant agent result: %s", result)
        return result.final_output

  except Exception as e:
    logger.error(f"Error running planner agent: {e}")
    raise
