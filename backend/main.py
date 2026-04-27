import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, UTC
import logging

from evaluator import run_evaluator_agent
from planner import run_planner_agent
from optimizer import run_optimizer_agent
from assistant import run_assistant_agent

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

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Invalid request", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An unexpected error occurred. Please try again."},
    )

class RecipeRequest(BaseModel):
    ingredients: list[str] = Field(..., description="List of available ingredients")
    calorie_target: int = Field(..., ge=150, le=900, description="Target calorie intake for the recipe")
    dislikes: list[str] = Field(default_factory=list, description="List of ingredients to avoid")
    allergies: list[str] = Field(default_factory=list, description="List of ingredients causing allergies")

class ChatRequestPayload(BaseModel):
    name: str
    ingredients: list[dict[str, str]]
    steps: list[str]
    calories: int
    suggestions: list[str]

class ChatRequest(BaseModel):
    recipe: ChatRequestPayload
    messages: list[dict[str, str]]

@app.post("/api/generate-recipe")
async def generate_recipe(request_body: RecipeRequest):
    """
    Generate a recipe based on user constraints.
    """

    try:
        optimization_iterations = 0
        recipe_approved = False

        recipe = await run_planner_agent(request_body)
        evaluation = await run_evaluator_agent(recipe, request_body)
        recipe_approved = evaluation.approved

        while not recipe_approved and optimization_iterations < 1:
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
    except Exception as e:
        logger.error(f"Error in recipe generation: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred during recipe generation. Please try again."},
        )

@app.post("/api/chat")
async def chat_assistant(request: ChatRequest):
    """
    Chat with a cooking assistant
    """

    try:
        response = await run_assistant_agent(request.recipe, request.messages)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Assistant response generated",
                "success": True,
                "data": {
                    "response": response
                }
            }
        )
    except Exception as e:
        logger.error(f"Error in assistant chat: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "An error occurred during assistant chat. Please try again."},
        )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "message": "ChopSmart Backend is healthy.",
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "aws_region": os.getenv("AWS_REGION_NAME"),
            "bedrock_model_id": os.getenv("BEDROCK_MODEL_ID")
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
