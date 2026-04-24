import { Dispatch, SetStateAction, useState } from "react";
import TagInput from "./TagInput";
import { Recipe } from "@/types";

interface RecipeFormProps {
  loading: boolean;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setRecipe: Dispatch<SetStateAction<Recipe | null>>;
}

function RecipeForm({ loading, setLoading, setRecipe }: RecipeFormProps) {
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [calorieTarget, setCalorieTarget] = useState('');
  const [dislikes, setDislikes] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const addTag = (list: string[], setter: (v: string[]) => void) => (tag: string) => {
    if (!list.includes(tag)) setter([...list, tag]);
  };
  const removeTag = (list: string[], setter: (v: string[]) => void) => (i: number) => {
    setter(list.filter((_, idx) => idx !== i));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setRecipe(null);
    setError(null);

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/generate-recipe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ingredients,
        calorie_target: calorieTarget ? parseInt(calorieTarget) : undefined,
        dislikes,
        allergies,
      }),
    })
    .then(res => res.json())
    .then(({ data, success, message }) => {
      if (success) {
        setRecipe({
          name: data.final_recipe.name,
          ingredients: data.final_recipe.ingredients,
          steps: data.final_recipe.steps,
          calories: data.final_recipe.estimated_calories,
          suggestions: data.evaluation.suggestions,
        });
      } else {
        setError(message ?? 'Something went wrong. Please try again.');
      }
      setLoading(false);
    })
    .catch((error) => {
      setError(error?.message ?? 'Could not reach the server. Check your connection and try again.');
      setLoading(false);
    });
  };

  const canSubmit = ingredients.length > 0;

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
      className="p-6 space-y-7"
    >
      <div>
        <h1 className="text-lg font-semibold text-foreground">Build your recipe</h1>
        <p className="text-sm text-(--muted) mt-1">
          Tell us what you have and we&apos;ll find the perfect dish.
        </p>
      </div>

      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-foreground">
          Available ingredients
          <span className="ml-1 text-(--danger) font-bold">*</span>
        </legend>
        <p className="text-xs text-(--muted)">Press Enter or comma to add</p>
        <TagInput
          tags={ingredients}
          onAdd={addTag(ingredients, setIngredients)}
          onRemove={removeTag(ingredients, setIngredients)}
          placeholder="e.g. chicken, garlic, tomatoes…"
          variant="green"
        />
      </fieldset>

      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-foreground">
          Calorie target <span className="font-normal text-(--muted)">(150 - 900)</span>
        </legend>
        <div className="relative">
          <input
            type="number"
            min={150}
            max={900}
            value={calorieTarget}
            onChange={(e) => setCalorieTarget(e.target.value)}
            placeholder="e.g. 600"
            className="w-full h-11 pl-4 pr-14 rounded-xl border border-border bg-white text-sm text-foreground placeholder:text-(--muted) focus:outline-none focus:border-primary focus:ring-2 focus:ring-(--primary)/20 transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
          />
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-(--muted) pointer-events-none">
            kcal
          </span>
        </div>
      </fieldset>

      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-foreground">
          Disliked foods <span className="font-normal text-(--muted)">(optional)</span>
        </legend>
        <p className="text-xs text-(--muted)">We&apos;ll avoid these in your recipes</p>
        <TagInput
          tags={dislikes}
          onAdd={addTag(dislikes, setDislikes)}
          onRemove={removeTag(dislikes, setDislikes)}
          placeholder="e.g. mushrooms, olives…"
          variant="amber"
        />
      </fieldset>

      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-foreground">
          Allergies <span className="font-normal text-(--muted)">(optional)</span>
        </legend>
        <p className="text-xs text-(--muted)">Strictly excluded from all results</p>
        <TagInput
          tags={allergies}
          onAdd={addTag(allergies, setAllergies)}
          onRemove={removeTag(allergies, setAllergies)}
          placeholder="e.g. peanuts, gluten, dairy…"
          variant="red"
        />
      </fieldset>

      {error && (
        <div className="flex items-start gap-2.5 rounded-xl border border-(--danger)/30 bg-(--danger-light) px-4 py-3">
          <svg className="mt-0.5 shrink-0 text-(--danger)" width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M8 5v3.5M8 11h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <p className="text-sm text-(--danger)">{error}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={!canSubmit || loading}
        className="w-full h-12 rounded-xl bg-primary hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 shadow-sm"
      >
        {loading ? (
          <>
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity=".25"/>
              <path d="M12 2a10 10 0 0110 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
            </svg>
            Finding recipes…
          </>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M10.5 10.5l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
            Find Recipes
          </>
        )}
      </button>

      {!canSubmit && (
        <p className="text-xs text-center text-(--muted)">
          Add at least one ingredient to get started
        </p>
      )}
    </form>
  );
};

export default RecipeForm;
