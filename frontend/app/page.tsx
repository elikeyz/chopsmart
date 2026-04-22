'use client';

import EmptyRecipeState from '@/components/EmptyRecipeState';
import LoadingRecipeSkeleton from '@/components/LoadingRecipeSkeleton';
import RecipeDisplay from '@/components/RecipeDisplay';
import RecipeForm from '@/components/RecipeForm';
import { Recipe } from '@/types';
import { useState } from 'react';

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [recipe, setRecipe] = useState<Recipe | null>(null);

  return (
    <div className="flex flex-col h-full">
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

      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">

        <aside className="w-full lg:w-100 xl:w-110 shrink-0 lg:overflow-y-auto lg:border-r border-b lg:border-b-0 border-border bg-(--surface-alt)">
          <RecipeForm loading={loading} setLoading={setLoading} setRecipe={setRecipe} />
        </aside>

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
