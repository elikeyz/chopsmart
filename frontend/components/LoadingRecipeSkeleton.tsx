function LoadingRecipeSkeleton() {
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

export default LoadingRecipeSkeleton;
