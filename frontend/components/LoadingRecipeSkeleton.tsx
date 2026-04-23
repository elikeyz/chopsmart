'use client';

import { useEffect, useState } from 'react';

const PHRASES = [
  'Preheating the oven…',
  'Chopping the ingredients…',
  'Consulting the head chef…',
  'Raiding the pantry…',
  'Whisking it all together…',
  'Letting it simmer…',
  'Seasoning to perfection…',
  'Marinating the ideas…',
  'Reducing the sauce…',
  'Folding in the flavours…',
  'Firing up the stove…',
  'Sifting through recipes…',
  'Tasting for seasoning…',
  'Plating your dish…',
  'Sharpening the knives…',
  'Checking the spice rack…',
  'Deglazing the pan…',
  'Asking the sous-chef…',
];

function LoadingRecipeSkeleton() {
  const [index, setIndex] = useState(() => Math.floor(Math.random() * PHRASES.length));
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIndex(prev => {
          let next: number;
          do { next = Math.floor(Math.random() * PHRASES.length); } while (next === prev);
          return next;
        });
        setVisible(true);
      }, 350);
    }, 2600);

    return () => clearInterval(id);
  }, []);

  return (
    <div className="relative p-6 space-y-8 animate-pulse">
      <p
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-sm font-medium text-primary whitespace-nowrap z-10"
        style={{ transition: 'opacity 350ms ease', opacity: visible ? 1 : 0 }}
      >
        {PHRASES[index]}
      </p>
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
