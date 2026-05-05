import os
import logging

from agents import Agent, OpenAIChatCompletionsModel, Runner, trace
from openai import AsyncOpenAI

from context import PLANNER_INSTRUCTIONS
from mcp_servers import create_opennutrition_mcp_server
from output_types import Recipe

logger = logging.getLogger()

async def run_planner_agent(request_body) -> Recipe:
  ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
  anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

  if not anthropic_api_key:
    logger.error("Anthropic API key not found in environment variables.")
    raise ValueError("Anthropic API key is required to run the planner agent.")

  client = AsyncOpenAI(base_url=ANTHROPIC_BASE_URL, api_key=anthropic_api_key)
  model = OpenAIChatCompletionsModel(model="claude-sonnet-4-6", openai_client=client)

  logger.info("Running planner agent with request body: %s", request_body)
  try:
    async with create_opennutrition_mcp_server() as opennutrition_server:
      ingredients = request_body.ingredients
      calorie_target = request_body.calorie_target
      dislikes = request_body.dislikes
      allergies = request_body.allergies

      planner_prompt = f"""
      Provide a meal recipe that meets the following user constraints. Use your capabilities to search for recipes, retrieve nutrition data, and adjust ingredients as needed to satisfy the constraints.

      INPUT CONSTRAINTS:
      - Ingredients: {", ".join(ingredients)}
      - Target calories: {calorie_target} (acceptable ±10%)
      - Dislikes: {", ".join(dislikes)}
      - Allergies: {", ".join(allergies)} (STRICT)
      - Optional: cuisine, time, preferences
      """

      agent = Agent(
        name="Recipe Planner",
        model=model,
        instructions=PLANNER_INSTRUCTIONS,
        mcp_servers=[opennutrition_server],
        output_type=Recipe
      )

      with trace("ChopSmart"):
        result = await Runner.run(agent, input=planner_prompt, max_turns=15)
        logger.info("Planner agent result: %s", result)
        return result.final_output

  except Exception as e:
    logger.error(f"Error running planner agent: {e}")
    raise
