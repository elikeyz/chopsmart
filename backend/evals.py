"""
ChopSmart Evaluation System — deterministic, rule-based metrics.

These metrics are designed to complement the LLM-based evaluator in
evaluator.py. Where the LLM evaluator reasons over nutrition data from
MCP tools, this module gives fast, reproducible quality signals that
can run in CI without any network or model access.

Metric summary
──────────────
Recipe metrics
  calorie_accuracy_score       0-1  how close estimated calories are to target
  allergen_safety              bool no allergen from the user's list appears
  dislike_avoidance            bool no disliked ingredient appears
  ingredient_utilization_rate  0-1  fraction of provided ingredients used
  recipe_completeness_score    0-1  all required fields populated

Evaluation-output metrics
  evaluation_consistency       bool agent evaluation fields are self-consistent

Workflow metrics
  optimization_delta           float improvement in score after optimization

Chat metrics
  chat_response_length_score   0-1  word count in acceptable range
  chat_response_on_topic       bool contains cooking / nutrition keywords

Aggregate helpers
  evaluate_recipe()            → RecipeEvalResult
  evaluate_chat_response()     → ChatEvalResult
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence

from output_types import EvaluationFeedback, Recipe


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ±10 % is the system's own calorie tolerance; scores degrade linearly
# to 0 at 50 % deviation.
_CALORIE_TOLERANCE = 0.10
_CALORIE_ZERO_SCORE_THRESHOLD = 0.50

# Chat response word-count thresholds
_CHAT_MIN_WORDS = 10
_CHAT_MAX_WORDS = 500

COOKING_KEYWORDS: frozenset[str] = frozenset({
    "cook", "heat", "add", "stir", "season", "bake", "grill", "boil",
    "simmer", "mix", "blend", "chop", "dice", "slice", "marinate", "roast",
    "fry", "saute", "sauté", "steam", "poach", "braise", "broil",
    "recipe", "ingredient", "temperature", "minute", "hour",
    "tablespoon", "teaspoon", "cup", "gram", "ounce", "pound",
    "protein", "calorie", "calories", "nutrition", "fiber", "fat",
    "carbohydrate", "carb", "vitamin", "mineral", "sodium", "sugar",
    "serve", "serving", "plate", "garnish", "taste", "flavor",
    "texture", "sauce", "marinade", "spice", "herb", "seasoning",
})


# ---------------------------------------------------------------------------
# Recipe metrics
# ---------------------------------------------------------------------------

def calorie_accuracy_score(estimated: float, target: int | float) -> float:
    """Return a [0, 1] score for how close *estimated* is to *target*.

    1.0 — within the ±10 % system tolerance
    0.0 — at or beyond 50 % deviation
    Linear between those two breakpoints.
    """
    if target <= 0:
        raise ValueError(f"calorie target must be positive, got {target}")
    deviation = abs(estimated - target) / target
    if deviation <= _CALORIE_TOLERANCE:
        return 1.0
    if deviation >= _CALORIE_ZERO_SCORE_THRESHOLD:
        return 0.0
    # linear interpolation between tolerance and zero-score threshold
    return round(
        1.0 - (deviation - _CALORIE_TOLERANCE)
        / (_CALORIE_ZERO_SCORE_THRESHOLD - _CALORIE_TOLERANCE),
        4,
    )


def allergen_safety(recipe: Recipe, allergies: Sequence[str]) -> bool:
    """Return True if *no* allergen appears (case-insensitive) in any ingredient name.

    Both the exact term and a simple de-pluralized form (trailing 's' stripped)
    are checked so that "peanuts" matches "peanut butter".
    """
    if not allergies:
        return True
    ingredient_names = [ing.name.lower() for ing in recipe.ingredients]
    for allergen in allergies:
        allergen_lower = allergen.lower().strip()
        # Also try the de-pluralized form so "peanuts" → "peanut" matches "peanut butter"
        candidates = {allergen_lower, allergen_lower.rstrip("s")} - {""}
        if any(c in name for c in candidates for name in ingredient_names):
            return False
    return True


def dislike_avoidance(recipe: Recipe, dislikes: Sequence[str]) -> bool:
    """Return True if *no* disliked ingredient appears in any ingredient name."""
    if not dislikes:
        return True
    ingredient_names = [ing.name.lower() for ing in recipe.ingredients]
    for dislike in dislikes:
        dislike_lower = dislike.lower().strip()
        if any(dislike_lower in name for name in ingredient_names):
            return False
    return True


def ingredient_utilization_rate(recipe: Recipe, available: Sequence[str]) -> float:
    """Return the fraction of *available* ingredients that appear in the recipe.

    An ingredient is considered "used" if its name (lowercased) appears as a
    substring of any recipe ingredient name.  Returns 1.0 when *available*
    is empty (nothing was provided, nothing can be missed).
    """
    if not available:
        return 1.0
    recipe_names = " ".join(ing.name.lower() for ing in recipe.ingredients)
    used = sum(1 for ing in available if ing.lower().strip() in recipe_names)
    return round(used / len(available), 4)


def recipe_completeness_score(recipe: Recipe) -> float:
    """Return a [0, 1] score based on four structural checks (equal weight).

    Checks:
      1. name is non-empty
      2. at least one ingredient
      3. at least two steps
      4. estimated_calories > 0
    """
    checks = [
        bool(recipe.name and recipe.name.strip()),
        len(recipe.ingredients) >= 1,
        len(recipe.steps) >= 2,
        recipe.estimated_calories > 0,
    ]
    return round(sum(checks) / len(checks), 4)


# ---------------------------------------------------------------------------
# Evaluation-output metrics
# ---------------------------------------------------------------------------

def evaluation_consistency(evaluation: EvaluationFeedback) -> bool:
    """Return True when the agent's EvaluationFeedback fields are self-consistent.

    Rules checked:
    - score is in [0, 100]
    - verdict is non-empty
    - if approved is True the score should be ≥ 50
    - if approved is False at least one issue should be listed
    """
    if not (0 <= evaluation.score <= 100):
        return False
    if not evaluation.verdict or not evaluation.verdict.strip():
        return False
    if evaluation.approved and evaluation.score < 50:
        return False
    if not evaluation.approved and not evaluation.issues:
        return False
    return True


# ---------------------------------------------------------------------------
# Workflow metrics
# ---------------------------------------------------------------------------

def optimization_delta(before_score: int, after_score: int) -> float:
    """Return the normalised improvement in agent score after optimization.

    Range is [-1.0, 1.0]:
      positive → improvement
      zero     → no change
      negative → regression
    """
    return round((after_score - before_score) / 100, 4)


# ---------------------------------------------------------------------------
# Chat metrics
# ---------------------------------------------------------------------------

def chat_response_length_score(response: str) -> float:
    """Return a [0, 1] score based on word count.

    < 10 words   → 0.0 (too short to be useful)
    10-500 words → 1.0 (ideal range)
    > 500 words  → linearly decreasing, flooring at 0.5 at 1 000 words
    """
    words = len(response.split())
    if words < _CHAT_MIN_WORDS:
        return 0.0
    if words <= _CHAT_MAX_WORDS:
        return 1.0
    # graceful penalty for very long responses
    excess = words - _CHAT_MAX_WORDS
    score = max(0.5, 1.0 - 0.5 * excess / 500)
    return round(score, 4)


def chat_response_on_topic(response: str) -> bool:
    """Return True if the response contains at least one cooking/nutrition keyword."""
    tokens = set(re.findall(r"[a-z]+", response.lower()))
    return bool(tokens & COOKING_KEYWORDS)


# ---------------------------------------------------------------------------
# Aggregate result types
# ---------------------------------------------------------------------------

@dataclass
class RecipeEvalResult:
    """Aggregate evaluation result for a single recipe generation run.

    Allergen safety is a hard gate: if the recipe contains an allergen,
    ``overall_score`` returns 0.0 regardless of other metrics.
    """

    calorie_accuracy: float
    allergen_safe: bool
    avoids_dislikes: bool
    ingredient_utilization: float
    recipe_completeness: float
    evaluation_valid: bool
    agent_score: int  # raw score from the LLM evaluator

    # weights used when computing overall_score (must sum to 1.0)
    _WEIGHTS: dict[str, float] = field(default_factory=lambda: {
        "calorie_accuracy": 0.35,
        "avoids_dislikes": 0.15,
        "ingredient_utilization": 0.25,
        "recipe_completeness": 0.25,
    }, repr=False)

    def overall_score(self) -> float:
        """Return a [0, 1] weighted aggregate score.

        Allergen safety is a hard gate — any violation returns 0.0.
        """
        if not self.allergen_safe:
            return 0.0
        w = self._WEIGHTS
        return round(
            w["calorie_accuracy"] * self.calorie_accuracy
            + w["avoids_dislikes"] * float(self.avoids_dislikes)
            + w["ingredient_utilization"] * self.ingredient_utilization
            + w["recipe_completeness"] * self.recipe_completeness,
            4,
        )

    def passed(self, threshold: float = 0.70) -> bool:
        """Return True if overall_score meets *threshold* AND the recipe is allergen-safe."""
        return self.allergen_safe and self.overall_score() >= threshold


@dataclass
class ChatEvalResult:
    """Aggregate evaluation result for a single assistant chat response."""

    response_length_ok: bool
    is_on_topic: bool
    is_non_empty: bool
    word_count: int

    def overall_score(self) -> float:
        """Return a simple [0, 1] score as the fraction of checks that pass."""
        checks = [self.response_length_ok, self.is_on_topic, self.is_non_empty]
        return round(sum(checks) / len(checks), 4)

    def passed(self, threshold: float = 2 / 3) -> bool:
        return self.overall_score() >= threshold


# ---------------------------------------------------------------------------
# High-level evaluation entry points
# ---------------------------------------------------------------------------

def evaluate_recipe(
    recipe: Recipe,
    evaluation: EvaluationFeedback,
    *,
    calorie_target: int,
    available_ingredients: Sequence[str],
    allergies: Sequence[str] = (),
    dislikes: Sequence[str] = (),
) -> RecipeEvalResult:
    """Run all recipe metrics and return a :class:`RecipeEvalResult`."""
    return RecipeEvalResult(
        calorie_accuracy=calorie_accuracy_score(recipe.estimated_calories, calorie_target),
        allergen_safe=allergen_safety(recipe, allergies),
        avoids_dislikes=dislike_avoidance(recipe, dislikes),
        ingredient_utilization=ingredient_utilization_rate(recipe, available_ingredients),
        recipe_completeness=recipe_completeness_score(recipe),
        evaluation_valid=evaluation_consistency(evaluation),
        agent_score=evaluation.score,
    )


def evaluate_chat_response(response: str) -> ChatEvalResult:
    """Run all chat metrics and return a :class:`ChatEvalResult`."""
    stripped = response.strip()
    return ChatEvalResult(
        response_length_ok=chat_response_length_score(stripped) > 0.0,
        is_on_topic=chat_response_on_topic(stripped),
        is_non_empty=bool(stripped),
        word_count=len(stripped.split()),
    )
