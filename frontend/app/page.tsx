'use client';

import EmptyRecipeState from '@/components/EmptyRecipeState';
import LoadingRecipeSkeleton from '@/components/LoadingRecipeSkeleton';
import RecipeDisplay from '@/components/RecipeDisplay';
import TagInput from '@/components/TagInput';
import { Recipe } from '@/types';
import { useState } from 'react';

// ── Types ─────────────────────────────────────────────────────────────────────



// ── Recipe Display ────────────────────────────────────────────────────────────



// ── Demo data ─────────────────────────────────────────────────────────────────

const DEMO_RECIPE: Recipe = {
  name: 'Garlic Butter Chicken with Roasted Vegetables',
  ingredients: [
    '2 boneless, skinless chicken breasts (about 600g)',
    '4 cloves garlic, minced',
    '3 tbsp unsalted butter',
    '1 tsp dried thyme',
    '1 tsp paprika',
    '2 medium zucchini, sliced',
    '1 red bell pepper, chopped',
    '1 cup cherry tomatoes',
    'Salt and black pepper to taste',
    '2 tbsp olive oil',
  ],
  steps: [
    'Preheat oven to 200°C (400°F). Line a large baking sheet with parchment paper.',
    'Pat the chicken breasts dry. Season with salt, pepper, paprika, and thyme on both sides.',
    'In an oven-safe skillet, melt 2 tbsp butter over medium-high heat. Sear chicken for 3–4 minutes per side until golden.',
    'Add garlic to the pan and cook for 30 seconds, then transfer skillet to oven. Roast 18–20 minutes until internal temp reaches 74°C (165°F).',
    'Meanwhile, toss vegetables with olive oil, salt, and pepper on the baking sheet. Roast alongside chicken for 20 minutes.',
    'Remove from oven, rest the chicken 5 minutes. Drizzle remaining butter over everything and serve.',
  ],
  calories: 480,
  suggestions: [
    'Pairs well with a side of crusty bread or steamed rice.',
    'Leftovers keep well refrigerated for up to 3 days.',
    'Swap zucchini for asparagus or broccoli depending on what you have.',
    'For extra richness, finish with a squeeze of lemon juice before serving.',
  ],
};

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [calorieTarget, setCalorieTarget] = useState('');
  const [dislikes, setDislikes] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [recipe, setRecipe] = useState<Recipe | null>(null);

  const addTag = (list: string[], setter: (v: string[]) => void) => (tag: string) => {
    if (!list.includes(tag)) setter([...list, tag]);
  };
  const removeTag = (list: string[], setter: (v: string[]) => void) => (i: number) => {
    setter(list.filter((_, idx) => idx !== i));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setRecipe(null);
    // Simulate API call — replace with real fetch once backend is wired up
    await new Promise((r) => setTimeout(r, 1800));
    setRecipe(DEMO_RECIPE);
    setLoading(false);
  };

  const canSubmit = ingredients.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* ── Header ── */}
      <header className="shrink-0 flex items-center justify-between px-6 py-4 bg-white border-b border-border shadow-sm z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 3C8 3 5 7 5 11c0 3 1.5 5.5 4 7v2h6v-2c2.5-1.5 4-4 4-7 0-4-3-8-7-8z" fill="white" opacity=".9"/>
              <path d="M9 21h6M12 3v3" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="text-xl font-bold tracking-tight text-foreground">
            Chop<span className="text-primary">Smart</span>
          </span>
        </div>
        <p className="hidden sm:block text-sm text-(--muted)">
          Smart recipes from what you have
        </p>
      </header>

      {/* ── Body ── */}
      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">

        {/* ── Left column — Form ── */}
        <aside className="w-full lg:w-100 xl:w-110 shrink-0 lg:overflow-y-auto lg:border-r border-b lg:border-b-0 border-border bg-(--surface-alt)">
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

            {/* Ingredients */}
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

            {/* Calorie target */}
            <fieldset className="space-y-2">
              <legend className="text-sm font-semibold text-foreground">
                Calorie target <span className="font-normal text-(--muted)">(optional)</span>
              </legend>
              <div className="relative">
                <input
                  type="number"
                  min={100}
                  max={5000}
                  step={50}
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

            {/* Dislikes */}
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

            {/* Allergies */}
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

            {/* Submit */}
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
        </aside>

        {/* ── Right column — Recipe ── */}
        <main className="flex-1 overflow-y-auto recipe-scroll bg-background">
          {loading ? (
            <LoadingRecipeSkeleton />
          ) : recipe ? (
            <RecipeDisplay recipe={recipe} />
          ) : (
            <EmptyRecipeState />
          )}
        </main>
      </div>
    </div>
  );
}
