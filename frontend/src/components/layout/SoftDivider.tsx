/**
 * SoftDivider — quiet horizontal rule between sections.
 */

interface SoftDividerProps {
  className?: string;
}

export function SoftDivider({ className }: SoftDividerProps) {
  return (
    <hr
      className={`border-t border-border-muted ${className ?? ""}`}
      aria-hidden="true"
    />
  );
}
