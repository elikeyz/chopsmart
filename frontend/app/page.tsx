'use client';

import { useState, KeyboardEvent, useRef } from 'react';

// ── Types ─────────────────────────────────────────────────────────────────────

interface RecipeSuggestion {
  id: number;
  name: string;
  calories: number;
  time: string;
}

interface Recipe {
  name: string;
  ingredients: string[];
  steps: string[];
  calories: number;
  suggestions: RecipeSuggestion[];
}

// ── Tag Input ─────────────────────────────────────────────────────────────────

interface TagInputProps {
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (index: number) => void;
  placeholder: string;
  variant?: 'green' | 'amber' | 'red';
}

function TagInput({ tags, onAdd, onRemove, placeholder, variant = 'green' }: TagInputProps) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const variantStyles = {
    green: 'bg-primary-light text-primary-dark border border-primary',
    amber: 'bg-(--accent-light) text-[#92600a] border border-accent',
    red: 'bg-(--danger-light) text-(--danger) border border-(--danger)',
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === 'Enter' || e.key === ',') && value.trim()) {
      e.preventDefault();
      onAdd(value.trim().replace(/,$/, ''));
      setValue('');
    } else if (e.key === 'Backspace' && !value && tags.length > 0) {
      onRemove(tags.length - 1);
    }
  };

  return (
    <div
      className="min-h-11 flex flex-wrap gap-1.5 items-center p-2 rounded-xl border border-border bg-white focus-within:border-primary focus-within:ring-2 focus-within:ring-(--primary)/20 transition-all cursor-text"
      onClick={() => inputRef.current?.focus()}
    >
      {tags.map((tag, i) => (
        <span
          key={i}
          className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-sm font-medium ${variantStyles[variant]}`}
        >
          {tag}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onRemove(i); }}
            className="ml-0.5 rounded-full w-4 h-4 flex items-center justify-center hover:bg-black/10 transition-colors leading-none"
            aria-label={`Remove ${tag}`}
          >
            ×
          </button>
        </span>
      ))}
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="flex-1 min-w-30 outline-none bg-transparent text-sm text-foreground placeholder:text-(--muted)"
      />
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyRecipeState() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-100 text-center px-8">
      <div className="w-24 h-24 rounded-full bg-primary-light flex items-center justify-center mb-6">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <path d="M8 16c0-4.418 3.582-8 8-8h16c4.418 0 8 3.582 8 8v4H8v-4z" fill="var(--primary)" opacity=".3"/>
          <path d="M6 20h36v4c0 9.941-8.059 18-18 18S6 33.941 6 24v-4z" fill="var(--primary)" opacity=".6"/>
          <path d="M22 10V6M26 12V4M18 12V6" stroke="var(--primary-dark)" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-2">
        Your recipe will appear here
      </h3>
      <p className="text-sm text-(--muted) max-w-xs leading-relaxed">
        Add your available ingredients and preferences on the left, then hit <strong>Find Recipes</strong> to get started.
      </p>
    </div>
  );
}

// ── Loading State ─────────────────────────────────────────────────────────────

function LoadingRecipeState() {
  return (
    <div className="p-6 space-y-8 animate-pulse">
      <div className="space-y-3">
        <div className="h-7 rounded-lg bg-(--surface-alt) w-3/4" />
        <div className="h-4 rounded-md bg-(--surface-alt) w-1/3" />
      </div>
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-4 rounded-md bg-(--surface-alt)" style={{ width: `${70 + (i % 3) * 10}%` }} />
        ))}
      </div>
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-4 rounded-md bg-(--surface-alt)" style={{ width: `${60 + (i % 4) * 10}%` }} />
        ))}
      </div>
    </div>
  );
}

// ── Recipe Display ────────────────────────────────────────────────────────────

function RecipeDisplay({ recipe }: { recipe: Recipe }) {
  return (
    <div className="p-6 space-y-8">
      {/* Recipe header */}
      <div className="pb-5 border-b border-border">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <h2 className="text-2xl font-bold text-foreground leading-tight">
            {recipe.name}
          </h2>
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-(--accent-light) text-[#92600a] text-sm font-semibold border border-accent shrink-0">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M8 2a6 6 0 100 12A6 6 0 008 2z" fill="currentColor" opacity=".2"/>
              <path d="M8 5v3l2 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            ~{recipe.calories} kcal
          </span>
        </div>
      </div>

      {/* Ingredients */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-(--muted) mb-3">
          Ingredients
        </h3>
        <ul className="space-y-2">
          {recipe.ingredients.map((ing, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm text-foreground">
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary shrink-0" aria-hidden="true" />
              {ing}
            </li>
          ))}
        </ul>
      </section>

      {/* Steps */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-(--muted) mb-3">
          Instructions
        </h3>
        <ol className="space-y-4">
          {recipe.steps.map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center mt-0.5">
                {i + 1}
              </span>
              <p className="text-sm text-foreground leading-relaxed">{step}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Suggestions */}
      {recipe.suggestions.length > 0 && (
        <section className="pt-6 border-t border-border">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-(--muted) mb-4">
            You might also like
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {recipe.suggestions.map((s) => (
              <button
                key={s.id}
                type="button"
                className="flex items-center justify-between p-3.5 rounded-xl border border-border bg-white hover:border-primary hover:bg-primary-light transition-all text-left group"
              >
                <div>
                  <p className="text-sm font-medium text-foreground group-hover:text-primary-dark">
                    {s.name}
                  </p>
                  <p className="text-xs text-(--muted) mt-0.5">{s.time} · {s.calories} kcal</p>
                </div>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-(--muted) group-hover:text-primary shrink-0 ml-2 transition-colors" aria-hidden="true">
                  <path d="M6 3l5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

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
    { id: 1, name: 'Lemon Herb Salmon', calories: 420, time: '25 min' },
    { id: 2, name: 'Chicken Stir-Fry', calories: 390, time: '20 min' },
    { id: 3, name: 'Baked Ratatouille', calories: 280, time: '45 min' },
    { id: 4, name: 'Pasta Primavera', calories: 520, time: '30 min' },
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
              <p className="text-xs text-(--muted)">We'll avoid these in your recipes</p>
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
            <LoadingRecipeState />
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
