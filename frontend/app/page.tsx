'use client';

import EmptyRecipeState from '@/components/EmptyRecipeState';
import Header from '@/components/Header';
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
      <Header />
      <div className="flex flex-col lg:flex-row flex-1 lg:overflow-hidden">
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
