function Header() {
  return (
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
  );
}

export default Header;
