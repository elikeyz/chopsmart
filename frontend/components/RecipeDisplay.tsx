import { Recipe } from "@/types";

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
          <ul className="space-y-2">
            {recipe.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-foreground">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-accent shrink-0" aria-hidden="true" />
                {s}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

export default RecipeDisplay;
