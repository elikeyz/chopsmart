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

export default EmptyRecipeState;
