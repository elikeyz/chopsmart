"""
Evaluation test suite for ChopSmart.

Organised into three layers:
  1. Unit tests — each metric function tested in isolation with parametrized cases.
  2. Aggregate tests — RecipeEvalResult and ChatEvalResult composition.
  3. Integration scenarios — full workflow outputs evaluated end-to-end
     (agents are mocked; no network or LLM access required).

Run with:
    uv run pytest test_evals.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from main import app
from output_types import EvaluationFeedback, Ingredient, OptimizerOutput, Recipe
from evals import (
    ChatEvalResult,
    RecipeEvalResult,
    allergen_safety,
    calorie_accuracy_score,
    chat_response_length_score,
    chat_response_on_topic,
    dislike_avoidance,
    evaluate_chat_response,
    evaluate_recipe,
    evaluation_consistency,
    ingredient_utilization_rate,
    optimization_delta,
    recipe_completeness_score,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_recipe(
    name: str = "Test Dish",
    ingredients: list[Ingredient] | None = None,
    steps: list[str] | None = None,
    estimated_calories: float = 400.0,
) -> Recipe:
    return Recipe(
        name=name,
        ingredients=ingredients or [Ingredient(name="chicken", quantity="200", unit="grams")],
        steps=steps or ["Season the chicken", "Grill for 15 minutes"],
        estimated_calories=estimated_calories,
    )


def make_evaluation(
    approved: bool = True,
    verdict: str = "pass",
    score: int = 90,
    issues: list[str] | None = None,
    suggestions: list[str] | None = None,
) -> EvaluationFeedback:
    return EvaluationFeedback(
        approved=approved,
        verdict=verdict,
        score=score,
        issues=issues or [],
        suggestions=suggestions or ["Looks good!"],
    )


# ---------------------------------------------------------------------------
# 1a. calorie_accuracy_score
# ---------------------------------------------------------------------------

class TestCalorieAccuracyScore:

    @pytest.mark.parametrize("estimated,target,expected", [
        # Exact match
        (400, 400, 1.0),
        # Within tolerance (<= 10%)
        (440, 400, 1.0),   # exactly 10% over
        (360, 400, 1.0),   # exactly 10% under
        (430, 400, 1.0),   # 7.5% over
        # Between tolerance and zero-score threshold
        (480, 400, 0.75),  # 20% over  → (0.20 - 0.10) / 0.40 = 0.25 penalty
        (520, 400, 0.5),   # 30% over
        (560, 400, 0.25),  # 40% over
        # At zero-score threshold (50%)
        (600, 400, 0.0),   # exactly 50% over
        (200, 400, 0.0),   # exactly 50% under
        # Beyond threshold
        (700, 400, 0.0),   # 75% over
        (100, 400, 0.0),   # 75% under
    ])
    def test_score_values(self, estimated, target, expected):
        score = calorie_accuracy_score(estimated, target)
        assert abs(score - expected) < 1e-3

    def test_score_bounded_between_zero_and_one(self):
        for estimated in range(0, 1200, 50):
            score = calorie_accuracy_score(float(estimated), 400)
            assert 0.0 <= score <= 1.0, f"out of bounds for estimated={estimated}"

    def test_invalid_target_raises(self):
        with pytest.raises(ValueError):
            calorie_accuracy_score(400, 0)

    def test_symmetric_deviation(self):
        """Equal percentage deviation above and below should give the same score."""
        score_over = calorie_accuracy_score(480, 400)   # 20% over
        score_under = calorie_accuracy_score(320, 400)  # 20% under
        assert abs(score_over - score_under) < 1e-3


# ---------------------------------------------------------------------------
# 1b. allergen_safety
# ---------------------------------------------------------------------------

class TestAllergenSafety:

    def test_no_allergens_in_recipe(self):
        recipe = make_recipe(ingredients=[Ingredient(name="chicken", quantity="200", unit="g")])
        assert allergen_safety(recipe, ["peanuts"]) is True

    def test_allergen_present_returns_false(self):
        recipe = make_recipe(ingredients=[Ingredient(name="peanut butter", quantity="2", unit="tbsp")])
        assert allergen_safety(recipe, ["peanuts"]) is False

    def test_allergen_substring_match(self):
        recipe = make_recipe(ingredients=[Ingredient(name="peanut oil", quantity="1", unit="tbsp")])
        assert allergen_safety(recipe, ["peanut"]) is False

    def test_case_insensitive(self):
        recipe = make_recipe(ingredients=[Ingredient(name="Peanut Butter", quantity="1", unit="tbsp")])
        assert allergen_safety(recipe, ["peanuts"]) is False

    def test_empty_allergies_always_safe(self):
        recipe = make_recipe(ingredients=[Ingredient(name="peanut butter", quantity="1", unit="tbsp")])
        assert allergen_safety(recipe, []) is True

    def test_multiple_allergens_one_match(self):
        recipe = make_recipe(ingredients=[Ingredient(name="shrimp", quantity="100", unit="g")])
        assert allergen_safety(recipe, ["peanuts", "shellfish", "shrimp"]) is False

    def test_multiple_allergens_none_match(self):
        recipe = make_recipe(ingredients=[Ingredient(name="chicken breast", quantity="150", unit="g")])
        assert allergen_safety(recipe, ["peanuts", "shellfish", "gluten"]) is True


# ---------------------------------------------------------------------------
# 1c. dislike_avoidance
# ---------------------------------------------------------------------------

class TestDislikeAvoidance:

    def test_no_dislikes_in_recipe(self):
        recipe = make_recipe(ingredients=[Ingredient(name="chicken", quantity="200", unit="g")])
        assert dislike_avoidance(recipe, ["broccoli"]) is True

    def test_disliked_ingredient_present(self):
        recipe = make_recipe(ingredients=[Ingredient(name="broccoli", quantity="100", unit="g")])
        assert dislike_avoidance(recipe, ["broccoli"]) is False

    def test_empty_dislikes(self):
        recipe = make_recipe()
        assert dislike_avoidance(recipe, []) is True

    def test_case_insensitive(self):
        recipe = make_recipe(ingredients=[Ingredient(name="Broccoli Florets", quantity="1", unit="cup")])
        assert dislike_avoidance(recipe, ["broccoli"]) is False


# ---------------------------------------------------------------------------
# 1d. ingredient_utilization_rate
# ---------------------------------------------------------------------------

class TestIngredientUtilizationRate:

    def test_all_ingredients_used(self):
        recipe = make_recipe(
            ingredients=[
                Ingredient(name="chicken", quantity="200", unit="g"),
                Ingredient(name="garlic", quantity="2", unit="cloves"),
            ]
        )
        rate = ingredient_utilization_rate(recipe, ["chicken", "garlic"])
        assert rate == 1.0

    def test_no_ingredients_used(self):
        recipe = make_recipe(ingredients=[Ingredient(name="chicken", quantity="200", unit="g")])
        rate = ingredient_utilization_rate(recipe, ["broccoli", "carrots", "peas"])
        assert rate == 0.0

    def test_partial_utilization(self):
        recipe = make_recipe(
            ingredients=[Ingredient(name="chicken", quantity="200", unit="g")]
        )
        rate = ingredient_utilization_rate(recipe, ["chicken", "garlic", "olive oil"])
        # only chicken matched → 1/3
        assert abs(rate - 1 / 3) < 1e-4

    def test_empty_available_returns_one(self):
        recipe = make_recipe()
        assert ingredient_utilization_rate(recipe, []) == 1.0

    def test_case_insensitive(self):
        recipe = make_recipe(
            ingredients=[Ingredient(name="Chicken Breast", quantity="200", unit="g")]
        )
        rate = ingredient_utilization_rate(recipe, ["chicken"])
        assert rate == 1.0


# ---------------------------------------------------------------------------
# 1e. recipe_completeness_score
# ---------------------------------------------------------------------------

class TestRecipeCompletenessScore:

    def test_complete_recipe_scores_one(self):
        recipe = make_recipe(
            name="Grilled Chicken",
            ingredients=[Ingredient(name="chicken", quantity="200", unit="g")],
            steps=["Season", "Grill"],
            estimated_calories=400,
        )
        assert recipe_completeness_score(recipe) == 1.0

    def test_missing_name_reduces_score(self):
        recipe = make_recipe(name="  ")
        assert recipe_completeness_score(recipe) == 0.75

    def test_only_one_step_reduces_score(self):
        recipe = make_recipe(steps=["Cook everything"])
        assert recipe_completeness_score(recipe) == 0.75

    def test_zero_calories_reduces_score(self):
        recipe = make_recipe(estimated_calories=0.0)
        assert recipe_completeness_score(recipe) == 0.75

    def test_multiple_failures_compound(self):
        recipe = make_recipe(name="", steps=["Done"], estimated_calories=0.0)
        assert recipe_completeness_score(recipe) == 0.25  # only has >= 1 ingredient


# ---------------------------------------------------------------------------
# 1f. evaluation_consistency
# ---------------------------------------------------------------------------

class TestEvaluationConsistency:

    def test_valid_approved_evaluation(self):
        ev = make_evaluation(approved=True, score=85, verdict="pass")
        assert evaluation_consistency(ev) is True

    def test_valid_failed_evaluation(self):
        ev = make_evaluation(approved=False, score=40, verdict="fail", issues=["calories too high"])
        assert evaluation_consistency(ev) is True

    def test_score_out_of_range_high(self):
        ev = make_evaluation(score=101)
        assert evaluation_consistency(ev) is False

    def test_score_out_of_range_low(self):
        ev = make_evaluation(score=-1)
        assert evaluation_consistency(ev) is False

    def test_approved_with_low_score_is_inconsistent(self):
        ev = make_evaluation(approved=True, score=30, verdict="pass")
        assert evaluation_consistency(ev) is False

    def test_not_approved_with_no_issues_is_inconsistent(self):
        ev = make_evaluation(approved=False, score=60, verdict="fail", issues=[])
        assert evaluation_consistency(ev) is False

    def test_empty_verdict_is_inconsistent(self):
        ev = make_evaluation(verdict="")
        assert evaluation_consistency(ev) is False


# ---------------------------------------------------------------------------
# 1g. optimization_delta
# ---------------------------------------------------------------------------

class TestOptimizationDelta:

    def test_improvement(self):
        assert optimization_delta(60, 85) == 0.25

    def test_no_change(self):
        assert optimization_delta(70, 70) == 0.0

    def test_regression(self):
        assert optimization_delta(80, 70) == -0.10

    def test_full_improvement_from_zero(self):
        assert optimization_delta(0, 100) == 1.0

    def test_max_regression(self):
        assert optimization_delta(100, 0) == -1.0


# ---------------------------------------------------------------------------
# 1h. Chat metrics
# ---------------------------------------------------------------------------

class TestChatResponseLengthScore:

    @pytest.mark.parametrize("response,expected", [
        ("", 0.0),
        ("Yes.", 0.0),
        ("Grill the chicken.", 0.0),  # 3 words
        ("Season with salt and pepper and grill over medium heat for fifteen minutes.", 1.0),  # 13 words
        ("a " * 500, 1.0),     # exactly 500 words
        ("a " * 501, 0.999),   # 501 — 1 word over limit; penalty = 0.5 * 1/500 = 0.001
        ("a " * 750, 0.75),    # 750 → penalty = 0.5 * 250 / 500 = 0.25
        ("a " * 1000, 0.5),    # 1000 → penalty = 0.5 * 500 / 500 = 0.5
    ])
    def test_length_score(self, response, expected):
        score = chat_response_length_score(response)
        assert score == pytest.approx(expected, abs=1e-3)

    def test_score_bounded(self):
        for n in [0, 5, 50, 500, 5000]:
            score = chat_response_length_score("word " * n)
            assert 0.0 <= score <= 1.0


class TestChatResponseOnTopic:

    def test_cooking_response_is_on_topic(self):
        assert chat_response_on_topic("Grill the chicken over medium heat for 15 minutes.") is True

    def test_nutrition_response_is_on_topic(self):
        assert chat_response_on_topic("This recipe has approximately 400 calories and 30 grams of protein.") is True

    def test_completely_unrelated_response_is_off_topic(self):
        assert chat_response_on_topic("The stock market rose by two percent today.") is False

    def test_empty_response_is_off_topic(self):
        assert chat_response_on_topic("") is False

    def test_case_insensitive(self):
        assert chat_response_on_topic("GRILL the CHICKEN.") is True


# ---------------------------------------------------------------------------
# 2. Aggregate result types
# ---------------------------------------------------------------------------

class TestRecipeEvalResult:

    def _perfect(self) -> RecipeEvalResult:
        return RecipeEvalResult(
            calorie_accuracy=1.0,
            allergen_safe=True,
            avoids_dislikes=True,
            ingredient_utilization=1.0,
            recipe_completeness=1.0,
            evaluation_valid=True,
            agent_score=95,
        )

    def test_perfect_recipe_passes(self):
        result = self._perfect()
        assert result.passed() is True
        assert result.overall_score() == 1.0

    def test_allergen_violation_caps_score_at_zero(self):
        result = self._perfect()
        result.allergen_safe = False
        assert result.overall_score() == 0.0
        assert result.passed() is False

    def test_passes_threshold(self):
        result = self._perfect()
        result.ingredient_utilization = 0.5
        result.avoids_dislikes = False
        # 0.35*1.0 + 0.15*0.0 + 0.25*0.5 + 0.25*1.0 = 0.35 + 0 + 0.125 + 0.25 = 0.725
        assert result.passed(threshold=0.70) is True

    def test_fails_threshold(self):
        result = RecipeEvalResult(
            calorie_accuracy=0.5,
            allergen_safe=True,
            avoids_dislikes=False,
            ingredient_utilization=0.3,
            recipe_completeness=0.5,
            evaluation_valid=True,
            agent_score=55,
        )
        assert result.passed(threshold=0.70) is False


class TestChatEvalResult:

    def test_perfect_chat_response(self):
        result = ChatEvalResult(
            response_length_ok=True, is_on_topic=True, is_non_empty=True, word_count=45
        )
        assert result.overall_score() == 1.0
        assert result.passed() is True

    def test_two_of_three_checks_pass(self):
        result = ChatEvalResult(
            response_length_ok=True, is_on_topic=False, is_non_empty=True, word_count=20
        )
        score = result.overall_score()
        assert abs(score - 2 / 3) < 1e-4
        assert result.passed() is True  # default threshold is 0.67

    def test_all_checks_fail(self):
        result = ChatEvalResult(
            response_length_ok=False, is_on_topic=False, is_non_empty=False, word_count=0
        )
        assert result.overall_score() == 0.0
        assert result.passed() is False


# ---------------------------------------------------------------------------
# 3. evaluate_recipe / evaluate_chat_response helpers
# ---------------------------------------------------------------------------

class TestEvaluateRecipe:

    def test_perfect_recipe(self):
        recipe = make_recipe(
            name="Grilled Chicken",
            ingredients=[
                Ingredient(name="chicken", quantity="200", unit="g"),
                Ingredient(name="garlic", quantity="2", unit="cloves"),
            ],
            steps=["Season", "Grill for 15 minutes"],
            estimated_calories=400,
        )
        ev = make_evaluation(approved=True, score=92)
        result = evaluate_recipe(
            recipe, ev,
            calorie_target=400,
            available_ingredients=["chicken", "garlic"],
        )
        assert result.allergen_safe is True
        assert result.avoids_dislikes is True
        assert result.calorie_accuracy == 1.0
        assert result.ingredient_utilization == 1.0
        assert result.recipe_completeness == 1.0
        assert result.evaluation_valid is True
        assert result.passed() is True

    def test_allergen_detected(self):
        recipe = make_recipe(
            ingredients=[Ingredient(name="peanut butter", quantity="2", unit="tbsp")]
        )
        ev = make_evaluation()
        result = evaluate_recipe(
            recipe, ev,
            calorie_target=400,
            available_ingredients=["peanut butter"],
            allergies=["peanut"],
        )
        assert result.allergen_safe is False
        assert result.overall_score() == 0.0
        assert result.passed() is False

    def test_calorie_overshoot(self):
        recipe = make_recipe(estimated_calories=700)  # 75% over target of 400
        ev = make_evaluation()
        result = evaluate_recipe(
            recipe, ev,
            calorie_target=400,
            available_ingredients=[],
        )
        assert result.calorie_accuracy == 0.0

    def test_dislike_in_recipe(self):
        recipe = make_recipe(
            ingredients=[Ingredient(name="broccoli", quantity="1", unit="cup")]
        )
        ev = make_evaluation()
        result = evaluate_recipe(
            recipe, ev,
            calorie_target=400,
            available_ingredients=[],
            dislikes=["broccoli"],
        )
        assert result.avoids_dislikes is False
        # Not a hard failure — recipe still gets a non-zero score
        assert result.overall_score() > 0.0


class TestEvaluateChatResponse:

    def test_good_response(self):
        response = (
            "Marinate the chicken in olive oil, garlic, and herbs for at least "
            "two hours before grilling over medium-high heat for 15 minutes."
        )
        result = evaluate_chat_response(response)
        assert result.is_non_empty is True
        assert result.is_on_topic is True
        assert result.response_length_ok is True
        assert result.passed() is True

    def test_empty_response_fails(self):
        result = evaluate_chat_response("")
        assert result.is_non_empty is False
        assert result.response_length_ok is False
        assert result.passed() is False

    def test_too_short_response_fails(self):
        result = evaluate_chat_response("Yes.")
        assert result.response_length_ok is False

    def test_off_topic_response_fails_on_topic_check(self):
        result = evaluate_chat_response(
            "I am an AI and I cannot provide that information for you today."
        )
        assert result.is_on_topic is False


# ---------------------------------------------------------------------------
# 4. Integration scenarios — full workflow via mocked API
# ---------------------------------------------------------------------------

_GOOD_RECIPE = make_recipe(
    name="Herb-Grilled Chicken",
    ingredients=[
        Ingredient(name="chicken breast", quantity="200", unit="g"),
        Ingredient(name="garlic", quantity="2", unit="cloves"),
        Ingredient(name="olive oil", quantity="1", unit="tbsp"),
    ],
    steps=[
        "Combine garlic, olive oil, and herbs in a bowl.",
        "Coat chicken in the mixture and let rest for 10 minutes.",
        "Grill over medium-high heat for 7 minutes per side.",
    ],
    estimated_calories=380,
)

_GOOD_EVALUATION = make_evaluation(approved=True, score=88)

_FAILED_EVALUATION = make_evaluation(
    approved=False, score=52, verdict="fail",
    issues=["Calorie count is above target range"],
    suggestions=["Reduce chicken to 150 g"],
)

_OPTIMIZER_OUTPUT = OptimizerOutput(
    recipe=make_recipe(
        name="Herb-Grilled Chicken (Optimized)",
        ingredients=[
            Ingredient(name="chicken breast", quantity="150", unit="g"),
            Ingredient(name="garlic", quantity="2", unit="cloves"),
            Ingredient(name="olive oil", quantity="1", unit="tbsp"),
        ],
        steps=[
            "Combine garlic, olive oil, and herbs in a bowl.",
            "Coat chicken and grill for 6 minutes per side.",
        ],
        estimated_calories=310,
    ),
    changes_made=["Reduced chicken breast from 200g to 150g"],
)

_REQUEST_BODY = {
    "ingredients": ["chicken breast", "garlic", "olive oil"],
    "calorie_target": 350,
    "dislikes": ["broccoli"],
    "allergies": ["peanuts"],
}


class TestWorkflowEvaluation:
    """End-to-end evaluation of the generate-recipe workflow."""

    @pytest.mark.asyncio
    async def test_approved_recipe_meets_quality_threshold(self):
        """A recipe approved on the first attempt should score ≥ 0.70."""
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=_GOOD_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=_GOOD_EVALUATION)),
            patch("main.run_optimizer_agent", new=AsyncMock()),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=_REQUEST_BODY)

        assert response.status_code == 200
        data = response.json()["data"]

        recipe = Recipe(**data["final_recipe"])
        ev = EvaluationFeedback(**data["evaluation"])

        result = evaluate_recipe(
            recipe, ev,
            calorie_target=_REQUEST_BODY["calorie_target"],
            available_ingredients=_REQUEST_BODY["ingredients"],
            allergies=_REQUEST_BODY["allergies"],
            dislikes=_REQUEST_BODY["dislikes"],
        )

        assert result.allergen_safe is True
        assert result.avoids_dislikes is True
        assert result.calorie_accuracy == 1.0   # 380 vs 350 is ~8.6%, within ±10%
        assert result.recipe_completeness == 1.0
        assert result.passed() is True

    @pytest.mark.asyncio
    async def test_optimized_recipe_shows_positive_delta(self):
        """After optimization, the agent score should improve."""
        eval_calls = [_FAILED_EVALUATION, _GOOD_EVALUATION]

        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=_GOOD_RECIPE)),
            patch("main.run_evaluator_agent", new=AsyncMock(side_effect=eval_calls)),
            patch("main.run_optimizer_agent", new=AsyncMock(return_value=_OPTIMIZER_OUTPUT)),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=_REQUEST_BODY)

        data = response.json()["data"]
        assert data["optimization_iterations"] == 1

        delta = optimization_delta(
            before_score=_FAILED_EVALUATION.score,
            after_score=_GOOD_EVALUATION.score,
        )
        assert delta > 0, "Optimization should improve the agent score"

    @pytest.mark.asyncio
    async def test_allergen_in_recipe_fails_evaluation(self):
        """If the planner returns a recipe containing an allergen, the eval hard-fails."""
        allergenic_recipe = make_recipe(
            ingredients=[Ingredient(name="peanut sauce", quantity="2", unit="tbsp")]
        )
        with (
            patch("main.run_planner_agent", new=AsyncMock(return_value=allergenic_recipe)),
            patch("main.run_evaluator_agent", new=AsyncMock(return_value=_GOOD_EVALUATION)),
            patch("main.run_optimizer_agent", new=AsyncMock()),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/generate-recipe", json=_REQUEST_BODY)

        data = response.json()["data"]
        recipe = Recipe(**data["final_recipe"])
        ev = EvaluationFeedback(**data["evaluation"])

        result = evaluate_recipe(
            recipe, ev,
            calorie_target=_REQUEST_BODY["calorie_target"],
            available_ingredients=_REQUEST_BODY["ingredients"],
            allergies=_REQUEST_BODY["allergies"],
        )
        assert result.allergen_safe is False
        assert result.overall_score() == 0.0

    @pytest.mark.asyncio
    async def test_chat_response_evaluation(self):
        """A real assistant response should pass all chat quality checks."""
        good_reply = (
            "To marinate the chicken, combine two tablespoons of olive oil, "
            "two minced garlic cloves, salt, and pepper in a bowl. Coat the "
            "chicken thoroughly and let it rest for at least 30 minutes. This "
            "will tenderize the meat and add depth of flavor before grilling."
        )
        with patch("main.run_assistant_agent", new=AsyncMock(return_value=good_reply)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/chat",
                    json={
                        "recipe": {
                            "name": "Grilled Chicken",
                            "ingredients": [{"name": "chicken", "quantity": "200g"}],
                            "steps": ["Season", "Grill"],
                            "calories": 380,
                            "suggestions": [],
                        },
                        "messages": [{"role": "user", "content": "How do I marinate the chicken?"}],
                    },
                )

        assert response.status_code == 200
        assistant_response = response.json()["data"]["response"]

        result = evaluate_chat_response(assistant_response)
        assert result.is_non_empty is True
        assert result.is_on_topic is True
        assert result.response_length_ok is True
        assert result.passed() is True
