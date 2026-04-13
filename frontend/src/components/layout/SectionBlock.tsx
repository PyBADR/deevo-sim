/**
 * SectionBlock — vertical rhythm wrapper for page sections.
 * Enforces consistent spacing and optional background treatment.
 */

interface SectionBlockProps {
  children: React.ReactNode;
  id?: string;
  muted?: boolean;
  className?: string;
}

export function SectionBlock({ children, id, muted, className }: SectionBlockProps) {
  return (
    <section
      id={id}
      className={`
        py-20 sm:py-26
        ${muted ? "bg-bg-muted" : ""}
        ${className ?? ""}
      `}
    >
      {children}
    </section>
  );
}
