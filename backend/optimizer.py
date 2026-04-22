import os
import logging

from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel

from context import OPTIMIZER_INSTRUCTIONS
from mcp_servers import create_opennutrition_mcp_server
from output_types import OptimizerOutput, Recipe

logger = logging.getLogger()

model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
logger.info(f"DEBUG: BEDROCK_REGION from env = {bedrock_region}")
os.environ["AWS_REGION_NAME"] = bedrock_region
logger.info(f"DEBUG: Set AWS_REGION_NAME to {bedrock_region}")

model = LitellmModel(model=f"bedrock/{model_id}")

async def run_optimizer_agent(recipe, evaluation, constraints) -> OptimizerOutput:
  try:
    async with create_opennutrition_mcp_server() as opennutrition_server:
      optimizer_prompt = f"""
      Here is a recipe that was evaluated against user constraints, along with feedback on how well it met those constraints. Your task is to modify the recipe to better meet the constraints while keeping it as close to the original as possible.

      ORIGINAL RECIPE:
      {recipe}

      EVALUATION FEEDBACK:
      {evaluation}

      USER CONSTRAINTS:
      - Target calories: {constraints.calorie_target} (acceptable ±10%)
      - Allergies: {constraints.allergies} (STRICT)
      - Dislikes: {constraints.dislikes}
      """

      agent = Agent(
        name="Optimizer",
        model=model,
        instructions=OPTIMIZER_INSTRUCTIONS,
        mcp_servers=[opennutrition_server],
        output_type=OptimizerOutput
      )

      with trace("ChopSmart"):
        result = await Runner.run(agent, input=optimizer_prompt)
        return result.final_output

  except Exception as e:
    logger.error(f"Error running optimizer agent: {e}")
    raise
