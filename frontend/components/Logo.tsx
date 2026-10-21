export function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 font-semibold tracking-tight ${className}`}>
      <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden>
        <rect width="32" height="32" rx="8" fill="#b8f35a" />
        <path d="M8 21 L13 11 L16 17 L19 11 L24 21" stroke="#0b0f14" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span>
        Match<span className="text-accent">Gist</span>
      </span>
    </span>
  );
}
