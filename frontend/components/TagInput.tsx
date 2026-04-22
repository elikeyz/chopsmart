import { KeyboardEvent, useState, useRef } from "react";

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

export default TagInput;
