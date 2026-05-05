"""
Unit tests for ChopSmart backend.

Run with:
    pip install pytest pytest-asyncio httpx
    pytest test_main.py -v
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from main import app
from output_types import Recipe, Ingredient, EvaluationFeedback, OptimizerOutput


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MOCK_INGREDIENT = Ingredient(name="chicken", quantity="200", unit="grams")

MOCK_RECIPE = Recipe(
    name="Grilled Chicken",
    ingredients=[MOCK_INGREDIENT],
    steps=["Season chicken with salt and pepper", "Grill for 15 minutes"],
    estimated_calories=350.0,
)

MOCK_EVALUATION_APPROVED = EvaluationFeedback(
    approved=True,
    verdict="pass",
    issues=[],
    suggestions=["Looks great!"],
    score=92,
)

MOCK_EVALUATION_FAILED = EvaluationFeedback(
    approved=False,
    verdict="fail",
    issues=["Calorie count is too high"],
    suggestions=["Reduce chicken quantity to 150g"],
    score=58,
)

MOCK_OPTIMIZED_RECIPE = Recipe(
    name="Grilled Chicken (Optimized)",
    ingredients=[Ingredient(name="chicken", quantity="150", unit="grams")],
    steps=["Season chicken with salt and pepper", "Grill for 12 minutes"],
    estimated_calories=280.0,
)

MOCK_OPTIMIZER_OUTPUT = OptimizerOutput(
    recipe=MOCK_OPTIMIZED_RECIPE,
    changes_made=["Reduced chicken from 200g to 150g"],
)

VALID_RECIPE_REQUEST = {
    "ingredients": ["chicken", "garlic", "olive oil"],
    "calorie_target": 400,
    "dislikes": ["broccoli"],
    "allergies": ["peanuts"],
}

VALID_CHAT_REQUEST = {
    "recipe": {
        "name": "Grilled Chicken",
        "ingredients": [{"name": "chicken", "quantity": "200g"}],
        "steps": ["Season chicken", "Grill for 15 minutes"],
        "calories": 350,
        "suggestions": ["Serve with a side salad"],
    },
    "messages": [{"role": "user", "content": "How long should I marinate the chicken?"}],
}


@pytest.fixture
def client():
    """Return a synchronous TestClient for the FastAPI app."""
    from fastapi.testclient import TestClient
    return TestClient(app)


# ---------------------------------------------------------------------------
# /api/generate-recipe — success paths
# ---------------------------------------------------------------------------

class TestGenerateRecipeSuccess:

    @pytest.mark.asyncio
    async def test_approved_on_first_attempt(self):
        """Planner returns a recipe that the evaluator approves immediately — no optimization."""
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=MOCK_EVALUATION_APPROVED)),
            patch("main.run_optimizer_agent", new=AsyncMock()) as mock_optimizer,
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=VALID_RECIPE_REQUEST)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "Recipe generation complete"
        assert body["data"]["optimization_iterations"] == 0
        assert body["data"]["approved"] is True
        # Optimizer must NOT have been called
        mock_optimizer.assert_not_called()

    @pytest.mark.asyncio
    async def test_optimization_triggered_then_approved(self):
        """Evaluator fails first, optimizer runs, second evaluation approves."""
        evaluator_calls = [MOCK_EVALUATION_FAILED, MOCK_EVALUATION_APPROVED]

        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(side_effect=evaluator_calls)),
            patch("main.run_optimizer_agent", new=AsyncMock(return_value=MOCK_OPTIMIZER_OUTPUT)),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=VALID_RECIPE_REQUEST)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["optimization_iterations"] == 1
        assert body["data"]["approved"] is True

    @pytest.mark.asyncio
    async def test_optimization_limit_reached_returns_unapproved(self):
        """Evaluator fails both times; optimization limit (1) is hit and result is returned unapproved."""
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=MOCK_EVALUATION_FAILED)),
            patch("main.run_optimizer_agent", new=AsyncMock(return_value=MOCK_OPTIMIZER_OUTPUT)),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=VALID_RECIPE_REQUEST)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["optimization_iterations"] == 1
        assert body["data"]["approved"] is False

    @pytest.mark.asyncio
    async def test_response_contains_recipe_and_evaluation(self):
        """Response data includes the final recipe and evaluation details."""
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=MOCK_EVALUATION_APPROVED)),
            patch("main.run_optimizer_agent", new=AsyncMock()),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=VALID_RECIPE_REQUEST)

        data = response.json()["data"]
        assert "final_recipe" in data
        assert "evaluation" in data
        recipe = data["final_recipe"]
        assert recipe["name"] == MOCK_RECIPE.name
        evaluation = data["evaluation"]
        assert evaluation["approved"] is True
        assert evaluation["score"] == MOCK_EVALUATION_APPROVED.score

    @pytest.mark.asyncio
    async def test_default_optional_fields(self):
        """Request without dislikes/allergies uses empty-list defaults and still succeeds."""
        minimal_request = {"ingredients": ["eggs", "butter"], "calorie_target": 300}

        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=MOCK_EVALUATION_APPROVED)),
            patch("main.run_optimizer_agent", new=AsyncMock()),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=minimal_request)

        assert response.status_code == 200
        assert response.json()["success"] is True


# ---------------------------------------------------------------------------
# /api/generate-recipe — error / exception paths
# ---------------------------------------------------------------------------

class TestGenerateRecipeErrors:

    @pytest.mark.asyncio
    async def test_planner_exception_returns_500(self):
        with patch("main.run_planner_agent", new=AsyncMock(side_effect=RuntimeError("LLM unavailable"))):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=VALID_RECIPE_REQUEST)

        assert response.status_code == 500
        body = response.json()
        assert body["success"] is False
        assert "error" in body["message"].lower() or "unexpected" in body["message"].lower()

    @pytest.mark.asyncio
    async def test_evaluator_exception_returns_500(self):
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(side_effect=RuntimeError("Evaluator crashed"))),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=VALID_RECIPE_REQUEST)

        assert response.status_code == 500
        assert response.json()["success"] is False

    @pytest.mark.asyncio
    async def test_optimizer_exception_returns_500(self):
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=MOCK_EVALUATION_FAILED)),
            patch("main.run_optimizer_agent", new=AsyncMock(side_effect=RuntimeError("Optimizer failed"))),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=VALID_RECIPE_REQUEST)

        assert response.status_code == 500
        assert response.json()["success"] is False


# ---------------------------------------------------------------------------
# /api/generate-recipe — request validation
# ---------------------------------------------------------------------------

class TestGenerateRecipeValidation:

    def test_calorie_too_low_returns_422(self, client):
        payload = {**VALID_RECIPE_REQUEST, "calorie_target": 100}
        response = client.post("/api/generate-recipe", json=payload)
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False

    def test_calorie_too_high_returns_422(self, client):
        payload = {**VALID_RECIPE_REQUEST, "calorie_target": 1000}
        response = client.post("/api/generate-recipe", json=payload)
        assert response.status_code == 422
        assert response.json()["success"] is False

    def test_calorie_at_minimum_boundary_is_valid(self, client):
        """calorie_target=150 is at the ge=150 boundary and must pass validation."""
        payload = {**VALID_RECIPE_REQUEST, "calorie_target": 150}
        # Don't care about agent results here — just check that validation passes (not 422)
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=MOCK_EVALUATION_APPROVED)),
            patch("main.run_optimizer_agent", new=AsyncMock()),
        ):
            response = client.post("/api/generate-recipe", json=payload)
        assert response.status_code == 200

    def test_calorie_at_maximum_boundary_is_valid(self, client):
        """calorie_target=900 is at the le=900 boundary and must pass validation."""
        payload = {**VALID_RECIPE_REQUEST, "calorie_target": 900}
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=MOCK_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=MOCK_EVALUATION_APPROVED)),
            patch("main.run_optimizer_agent", new=AsyncMock()),
        ):
            response = client.post("/api/generate-recipe", json=payload)
        assert response.status_code == 200

    def test_missing_ingredients_returns_422(self, client):
        payload = {"calorie_target": 400}
        response = client.post("/api/generate-recipe", json=payload)
        assert response.status_code == 422

    def test_missing_calorie_target_returns_422(self, client):
        payload = {"ingredients": ["chicken"]}
        response = client.post("/api/generate-recipe", json=payload)
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        response = client.post("/api/generate-recipe", json={})
        assert response.status_code == 422

    def test_ingredients_must_be_list(self, client):
        payload = {**VALID_RECIPE_REQUEST, "ingredients": "chicken"}
        response = client.post("/api/generate-recipe", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# /api/chat — success paths
# ---------------------------------------------------------------------------

class TestChatAssistantSuccess:

    @pytest.mark.asyncio
    async def test_chat_returns_assistant_response(self):
        assistant_reply = "Marinate the chicken for at least 2 hours for best results."

        with patch("main.run_assistant_agent", new=AsyncMock(return_value=assistant_reply)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/chat", json=VALID_CHAT_REQUEST)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["message"] == "Assistant response generated"
        assert body["data"]["response"] == assistant_reply

    @pytest.mark.asyncio
    async def test_chat_passes_recipe_and_messages_to_agent(self):
        """Verify the agent is called with the correct arguments from the request."""
        with patch("main.run_assistant_agent", new=AsyncMock(return_value="Sure!")) as mock_agent:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post("/api/chat", json=VALID_CHAT_REQUEST)

        mock_agent.assert_called_once()
        call_args = mock_agent.call_args
        # First positional arg is the recipe payload
        recipe_arg = call_args.args[0]
        assert recipe_arg.name == VALID_CHAT_REQUEST["recipe"]["name"]
        # Second positional arg is the messages list
        messages_arg = call_args.args[1]
        assert messages_arg == VALID_CHAT_REQUEST["messages"]

    @pytest.mark.asyncio
    async def test_chat_with_multi_turn_conversation(self):
        """Multiple messages in history are forwarded to the agent unchanged."""
        multi_turn_request = {
            **VALID_CHAT_REQUEST,
            "messages": [
                {"role": "user", "content": "How do I prep this?"},
                {"role": "assistant", "content": "Start by washing the chicken."},
                {"role": "user", "content": "What temperature should I use?"},
            ],
        }
        with patch("main.run_assistant_agent", new=AsyncMock(return_value="Use medium-high heat.")) as mock_agent:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/chat", json=multi_turn_request)

        assert response.status_code == 200
        _, messages_arg = mock_agent.call_args.args
        assert len(messages_arg) == 3

    @pytest.mark.asyncio
    async def test_chat_with_empty_messages_list(self):
        """An empty messages list is valid and forwarded to the agent."""
        request_with_empty_messages = {**VALID_CHAT_REQUEST, "messages": []}

        with patch("main.run_assistant_agent", new=AsyncMock(return_value="Hello! How can I help?")) as mock_agent:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/chat", json=request_with_empty_messages)

        assert response.status_code == 200
        _, messages_arg = mock_agent.call_args.args
        assert messages_arg == []


# ---------------------------------------------------------------------------
# /api/chat — error paths
# ---------------------------------------------------------------------------

class TestChatAssistantErrors:

    @pytest.mark.asyncio
    async def test_agent_exception_returns_500(self):
        with patch("main.run_assistant_agent", new=AsyncMock(side_effect=RuntimeError("Bedrock unreachable"))):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/chat", json=VALID_CHAT_REQUEST)

        assert response.status_code == 500
        body = response.json()
        assert body["success"] is False
        assert "error" in body["message"].lower() or "unexpected" in body["message"].lower()


# ---------------------------------------------------------------------------
# /api/chat — request validation
# ---------------------------------------------------------------------------

class TestChatValidation:

    def test_missing_recipe_returns_422(self, client):
        payload = {"messages": [{"role": "user", "content": "Hello"}]}
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_missing_messages_returns_422(self, client):
        payload = {"recipe": VALID_CHAT_REQUEST["recipe"]}
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_recipe_missing_required_fields_returns_422(self, client):
        bad_recipe = {"name": "Chicken"}  # missing ingredients, steps, calories, suggestions
        payload = {"recipe": bad_recipe, "messages": []}
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_shape(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        assert "timestamp" in body
        assert "message" in body

    def test_health_is_get(self, client):
        """POST to /health should return 405 Method Not Allowed."""
        response = client.post("/health")
        assert response.status_code == 405
