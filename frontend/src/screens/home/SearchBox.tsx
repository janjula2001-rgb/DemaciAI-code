import { forwardRef } from "react";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
}

// Instant search. "/" focuses it (handled by the screen), Enter opens the best match, Esc clears.
const SearchBox = forwardRef<HTMLInputElement, Props>(function SearchBox({ value, onChange, onSubmit }, ref) {
  return (
    <label className="group relative flex items-center">
      <svg className="pointer-events-none absolute left-3.5 h-4 w-4 text-steel-dim transition-colors group-focus-within:text-gold" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onSubmit();
          if (e.key === "Escape") {
            e.stopPropagation();
            onChange("");
            e.currentTarget.blur();
          }
        }}
        placeholder="Search champions"
        aria-label="Search champions"
        className="w-full rounded-full border border-[var(--gold-line)] bg-black/30 py-2.5 pl-10 pr-12 text-gold-light placeholder:text-steel-dim/80 outline-none focus-visible:outline-none transition-[border-color,box-shadow] duration-[var(--t-quick)] focus:border-gold focus:shadow-[var(--glow-gold)]"
      />
      <kbd className="pointer-events-none absolute right-3 rounded border border-[var(--gold-line)] px-1.5 text-xs text-steel-dim">/</kbd>
    </label>
  );
});

export default SearchBox;
