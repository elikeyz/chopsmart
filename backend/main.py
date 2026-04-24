import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, UTC
import logging

from evaluator import run_evaluator_agent
from planner import run_planner_agent
from optimizer import run_optimizer_agent

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChopSmart Backend", version="1.0")

# Configure CORS for development and production
cors_origins = [
    "http://localhost:3000",  # Local development
    "http://frontend:3000",  # Docker development
]

# In production, allow same-origin requests (static files served from same domain)
if os.getenv("ENVIRONMENT") == "production":
    cors_origins.append(
        "*"
    )  # Allow all origins in production since we serve frontend from same domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecipeRequest(BaseModel):
    ingredients: list[str] = Field(..., description="List of available ingredients")
    calorie_target: int = Field(..., ge=150, le=900, description="Target calorie intake for the recipe")
    dislikes: list[str] = Field(default_factory=list, description="List of ingredients to avoid")
    allergies: list[str] = Field(default_factory=list, description="List of ingredients causing allergies")

@app.post("/api/generate-recipe")
async def generate_recipe(request_body: RecipeRequest):
    """
    Generate a recipe based on user constraints.
    """

    optimization_iterations = 0
    recipe_approved = False

    recipe = await run_planner_agent(request_body)
    evaluation = await run_evaluator_agent(recipe, request_body)
    recipe_approved = evaluation.approved

    while not recipe_approved and optimization_iterations < 3:
        optimized_recipe = await run_optimizer_agent(recipe, evaluation, request_body)
        recipe = optimized_recipe.recipe
        evaluation = await run_evaluator_agent(optimized_recipe, request_body)
        recipe_approved = evaluation.approved
        optimization_iterations += 1

    return {
        "message": "Recipe generation complete",
        "success": True,
        "data": {
            "final_recipe": recipe,
            "evaluation": evaluation,
            "optimization_iterations": optimization_iterations,
            "approved": recipe_approved
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "message": "ChopSmart Backend is healthy.",
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "aws_region": os.getenv("AWS_REGION_NAME"),
        "bedrock_model_id": os.getenv("BEDROCK_MODEL_ID")
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
