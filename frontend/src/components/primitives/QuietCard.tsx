/**
 * QuietCard — surface-level container with soft border and optional hover.
 * Premium, minimal card. No shadows by default.
 */

interface QuietCardProps {
  children: React.ReactNode;
  hover?: boolean;
  className?: string;
}

export function QuietCard({ children, hover, className }: QuietCardProps) {
  return (
    <div
      className={`
        bg-bg-surface border border-border-muted rounded-lg p-6
        ${hover
          ? "transition-all duration-200 hover:border-border-soft hover:shadow-card"
          : ""
        }
        ${className ?? ""}
      `}
    >
      {children}
    </div>
  );
}
