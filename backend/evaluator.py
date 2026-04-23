import os
import logging

from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel

from context import EVALUATOR_INSTRUCTIONS
from mcp_servers import create_opennutrition_mcp_server
from output_types import EvaluationFeedback

logger = logging.getLogger()

async def run_evaluator_agent(recipe, constraints) -> EvaluationFeedback:
  model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
  bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
  os.environ["AWS_REGION_NAME"] = bedrock_region

  model = LitellmModel(model=f"bedrock/{model_id}")

  logger.info("Running evaluator agent with recipe: %s and constraints: %s", recipe, constraints)
  try:
    async with create_opennutrition_mcp_server() as opennutrition_server:
      evaluator_prompt = f"""
      Evaluate the following recipe against the given user constraints. Use the tools available to verify nutrition data and identify any issues with allergens, calorie counts, or ingredient choices.

      RECIPE TO EVALUATE:
      {recipe}

      USER CONSTRAINTS:
      - Target calories: {constraints.calorie_target} (acceptable ±10%)
      - Allergies: {constraints.allergies} (STRICT)
      - Dislikes: {constraints.dislikes}
      """

      agent = Agent(
        name="Evaluator",
        model=model,
        instructions=EVALUATOR_INSTRUCTIONS,
        mcp_servers=[opennutrition_server],
        output_type=EvaluationFeedback
      )

      with trace("ChopSmart"):
        result = await Runner.run(agent, input=evaluator_prompt, max_turns=15)
        logger.info("Evaluator agent result: %s", result)
        return result.final_output

  except Exception as e:
    logger.error(f"Error running evaluator agent: {e}")
    raise
