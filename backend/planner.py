import os
import logging

from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel

from context import PLANNER_INSTRUCTIONS
from mcp_servers import create_opennutrition_mcp_server
from output_types import Recipe

logger = logging.getLogger()

model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
logger.info(f"DEBUG: BEDROCK_REGION from env = {bedrock_region}")
os.environ["AWS_REGION_NAME"] = bedrock_region
logger.info(f"DEBUG: Set AWS_REGION_NAME to {bedrock_region}")

model = LitellmModel(model=f"bedrock/{model_id}")

async def run_planner_agent(request_body) -> Recipe:
  try:
    async with create_opennutrition_mcp_server() as opennutrition_server:
      ingredients = request_body.ingredients
      calorie_target = request_body.calorie_target
      dislikes = request_body.dislikes
      allergies = request_body.allergies

      planner_prompt = f"""
      Provide a meal recipe that meets the following user constraints. Use your capabilities to search for recipes, retrieve nutrition data, and adjust ingredients as needed to satisfy the constraints.

      INPUT CONSTRAINTS:
      - Ingredients: {ingredients}
      - Target calories: {calorie_target} (acceptable ±10%)
      - Dislikes: {dislikes}
      - Allergies: {allergies} (STRICT)
      - Optional: cuisine, time, preferences
      """

      agent = Agent(
        name="Planner",
        model=model,
        instructions=PLANNER_INSTRUCTIONS,
        mcp_servers=[opennutrition_server],
        output_type=Recipe
      )

      with trace("ChopSmart"):
        result = await Runner.run(agent, input=planner_prompt)
        return result.final_output

  except Exception as e:
    logger.error(f"Error running planner agent: {e}")
    raise
