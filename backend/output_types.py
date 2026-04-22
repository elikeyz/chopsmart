from pydantic import BaseModel, Field

class Ingredient(BaseModel):
  name: str = Field(description="Name of the ingredient")
  quantity: str = Field(description="Quantity of the ingredient, e.g., '1', '2', '0.5'")
  unit: str = Field(description="Unit of measurement for the ingredient, e.g., 'cup', 'tablespoon', 'grams'")

class Recipe(BaseModel):
  name: str = Field(description="Name of the recipe")
  ingredients: list[Ingredient] = Field(description="List of ingredients with name, quantity, and unit")
  steps: list[str] = Field(description="Cooking steps")
  estimatedCalories: float = Field(description="Estimated calorie count for the recipe")

class EvaluationFeedback(BaseModel):
  approved: bool = Field(description="Whether the recipe meets the constraints (true/false)")
  verdict: str = Field(description="Evaluation verdict, e.g., 'pass', 'fail', 'needs adjustment'")
  issues: list[str] = Field(description="List of specific issues identified in the recipes, e.g., 'calorie count too high', 'contains allergen: peanuts'")
  suggestions: list[str] = Field(description="List of actionable suggestions for improving the recipes, e.g., 'reduce chicken quantity to 100g', 'substitute peanuts with sunflower seeds'")
  score: int = Field(description="Numerical score representing how well the recipes meet the constraints, e.g., 85")

class OptimizerOutput(BaseModel):
  recipe: Recipe = Field(description="The modified recipe that meets the constraints")
  changes_made: list[str] = Field(description="List of specific changes made to the original recipe, e.g., 'reduced chicken from 200g to 100g', 'removed peanuts'")
