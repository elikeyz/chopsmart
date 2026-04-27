'use client';

import { useEffect, useRef, useState } from 'react';
import Markdown from 'react-markdown';
import { Recipe } from '@/types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const INITIAL: Message = {
  role: 'assistant',
  content: "Got questions about this recipe? Ask me anything — substitutions, techniques, timing, scaling, you name it.",
};

function RecipeChat({ recipe }: { recipe: Recipe }) {
  const [messages, setMessages] = useState<Message[]>([INITIAL]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const pendingRef = useRef<Message[]>([]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const doSend = (messagesToSend: Message[]) => {
    setLoading(true);
    setError(null);

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipe, messages: messagesToSend }),
    })
      .then(res => res.json())
      .then(({ success, data, message }) => {
        if (success) {
          setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        } else {
          setError(message ?? 'Something went wrong. Please try again.');
        }
        setLoading(false);
      })
      .catch(() => {
        setError('Could not reach the server. Check your connection and try again.');
        setLoading(false);
      });
  };

  const send = () => {
    const text = input.trim();
    if (!text || loading) return;

    const next = [...messages, { role: 'user' as const, content: text }];
    pendingRef.current = next;
    setMessages(next);
    setInput('');
    doSend(next);
  };

  const retry = () => doSend(pendingRef.current);

  return (
    <section className="border-t border-border pt-6">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-(--muted) mb-4">
        Ask the assistant
      </h3>

      <div className="space-y-3 mb-4 max-h-80 overflow-y-auto pr-1 recipe-scroll">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary rounded-br-sm'
                  : 'bg-(--surface-alt) rounded-bl-sm'
              }`}
            >
              <div className={`prose prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 ${msg.role === 'assistant' ? 'text-foreground' : 'text-white'}`}>
                <Markdown>{msg.content}</Markdown>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-(--surface-alt) rounded-2xl rounded-bl-sm px-4 py-3.5 flex gap-1.5 items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-(--muted) animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-(--muted) animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-(--muted) animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="flex items-start gap-2.5 rounded-xl border border-(--danger)/30 bg-(--danger-light) px-4 py-3 mb-3">
          <svg className="mt-0.5 shrink-0 text-(--danger)" width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M8 5v3.5M8 11h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <p className="flex-1 text-sm text-(--danger)">{error}</p>
          <button
            onClick={retry}
            className="shrink-0 text-sm font-medium text-(--danger) underline underline-offset-2 hover:opacity-70 transition-opacity"
          >
            Retry
          </button>
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask about substitutions, timing, techniques…"
          disabled={loading}
          className="flex-1 h-11 pl-4 pr-3 rounded-xl border border-border bg-white text-sm text-foreground placeholder:text-(--muted) focus:outline-none focus:border-primary focus:ring-2 focus:ring-(--primary)/20 transition-all disabled:opacity-60"
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          aria-label="Send message"
          className="h-11 w-11 rounded-xl bg-primary hover:bg-primary-dark disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center shrink-0 transition-colors"
        >
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M2 8h12M8 2l6 6-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </section>
  );
}

export default RecipeChat;
